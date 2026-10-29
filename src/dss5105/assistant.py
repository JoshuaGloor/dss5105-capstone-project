"""Voice-first dispatch assistant: the turn logic behind the mobile assistant page.

Each utterance goes to exactly one handler. Short control phrases ("book it", "cancel",
"new request") and memory questions ("what did we book today?") are matched by Python and
never reach the model. Everything else goes through the existing language intake, which
only extracts quoted fields. Python tools then rank workshops, and Python templates write
every card and every spoken sentence from tool output. Booking needs a separate, explicit
confirmation by a named dispatcher; voice alone never commits an allocation.
"""

import json
import re
from dataclasses import asdict, dataclass, field, replace
from datetime import date, datetime
from uuid import uuid4

from dss5105 import intake, llm
from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput, WorkshopQuery, read_inbox
from dss5105.memory import MemoryStore, rule_suggestions
from dss5105.records import AllocationError, AllocationStore, fingerprint
from dss5105.replies import STATUS_LABELS, build_reply

TONES = {
    "RECOMMEND": "ok",
    "CAPACITY": "info",
    "CLARIFY": "ask",
    "RECORDED_STATUS": "info",
    "DECLINE": "info",
    "REFUSE_SUGGESTION": "warn",
    "NEEDS_REVIEW": "warn",
    "NO_FEASIBLE_OPTION": "bad",
    "ALREADY_ALLOCATED": "info",
}
# A finished exchange: the next utterance starts a fresh request instead of patching this one.
TERMINAL = {"DECLINE", "CAPACITY", "RECORDED_STATUS", "ALREADY_ALLOCATED"}
SEGMENTS = (
    ("queue_days", "queue", "Queue"),
    ("process_days", "processing", "Processing"),
    ("transport_days", "transport", "Transport"),
    (None, "expected_rework", "Expected rework"),
)
COMMANDS = {
    "book": r"(yes|yeah|yep|sure|ok|okay)|((yes|yeah|ok|okay|great|perfect|alright|good)[,.!]?\s*)?(please\s+)?"
    r"(book|confirm|lock|go ahead|do it|place|send)"
    r"(\s+(it|that|this|them))?(\s+(in|now|please))*",
    "cancel": r"(no|cancel|stop|never ?mind|not now|hold on|wait)(\s+(that|it|this))?",
    "new": r"(start (a )?new( request)?|new (request|order|one)|start over|start again|reset|clear( (it|that))?)",
    "repeat": r"(repeat( that)?|say (that|it) again|what was that|come again|pardon)",
    "help": r"(help|what can (you|i) (do|say|ask)|how does this work)",
    # Voice for the two taps on a card: the remember offer and the list of other workshops.
    "remember": r"((yes|yeah|ok|okay|sure)[,.!]?\s*)?(please\s+)?(remember|save|keep)\s+"
    r"(that|it|this|that rule|the rule)(\s+(please|for next time|too))*",
    "options": r"((ok|okay|so)[,.!]?\s*)?(can you\s+)?(show|tell|give)( me)? (the |all (the )?)?(other )?"
    r"(options|workshops|alternatives|choices)(\s+please)?|what (are|were) the (other )?options|why not (the )?others",
}
EXAMPLES = (
    "ORD-109, 500 vests for Harbor Knits, due April 13. Keep it away from BudgetWorks.",
    "Who can take 1,500 crewnecks by April 15?",
    "Mei: ORD-066 due date just moved up, line something up.",
    "What did we book today?",
)
MAX_THREAD = 80


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().casefold()).strip(" .!?")


def parse_command(text: str) -> str | None:
    """A whole-utterance control phrase, or None. Anything longer goes to the language intake."""
    cleaned = _clean(text)
    for name, pattern in COMMANDS.items():
        if re.fullmatch(pattern, cleaned):
            return name
    return None


def parse_recall(text: str) -> str | None:
    """Questions about this desk's own memory, answered from saved records without the model."""
    cleaned = _clean(text)
    if re.search(r"\b(what|which|show|list)\b.*\b(rules?|remember)\b", cleaned):
        return "rules"
    if re.search(r"\b(what|which|show|list|any)\b.*\b(book(ed|ings?)?|sent|allocated|placed|confirmed)\b", cleaned):
        if not re.search(r"\b(last (year|month|week|october|november|december)|in 20\d\d)\b", cleaned):
            return "bookings"
    return None


def parse_workshop(text: str, names: dict[str, str]) -> str | None:
    """'How busy is SteadyHands?' or 'Tell me about W4' names one workshop; the register answers."""
    cleaned = _clean(text)
    if not re.match(r"(how (busy|loaded|full|free) is|tell me about|what about|how is|status of|show me) ", cleaned):
        return None
    tail = re.sub(r"^(how (busy|loaded|full|free) is|tell me about|what about|how is|status of|show me) ", "", cleaned)
    tail = re.sub(r"\b(right now|today|now|at the moment)\b", "", tail).strip(" ?.")
    for key, name in names.items():
        if tail in (key.casefold(), name.casefold()):
            return key
    return None


def day_label(stamp: str, *, long: bool = False) -> str:
    """'2026-04-10 17:17' -> 'Fri 10 Apr' (or 'Friday 10 April'); formatting only, no arithmetic."""
    day = date.fromisoformat(stamp[:10])
    return day.strftime("%A %-d %B" if long else "%a %-d %b")


def _initials(name: str) -> str:
    parts = re.findall(r"[A-Z][a-z]*|[a-z]+", name)
    return (parts[0][0] + (parts[1][0] if len(parts) > 1 else parts[0][1:2])).upper() if parts else "?"


def _clock() -> str:
    return datetime.now().strftime("%H:%M")


@dataclass(frozen=True)
class Services:
    """Everything a turn may touch. Tests inject a fake model; the page passes None."""

    store: AllocationStore
    memory: MemoryStore
    weights: ObjectiveWeights
    desk: DispatchDesk = field(default_factory=DispatchDesk)
    model: object = None
    speaker: str = "Dispatcher"

    @property
    def register(self) -> dict:
        return self.desk.workshops


@dataclass(frozen=True)
class Session:
    conversation: intake.Conversation = field(default_factory=intake.Conversation)
    thread: tuple[dict, ...] = ()
    result: dict | None = None
    status: str | None = None
    booking: dict | None = None
    rule_offers: tuple[dict, ...] = ()
    retry: dict | None = None
    offline: bool = False


def _message(role: str, *, text: str = "", card: dict | None = None, channel: str = "text") -> dict:
    return {"id": uuid4().hex[:10], "role": role, "text": text, "card": card, "channel": channel, "time": _clock()}


def _append(session: Session, *messages: dict, **changes) -> Session:
    thread = (session.thread + messages)[-MAX_THREAD:]
    return replace(session, thread=thread, **changes)


def _spoken_amount(shown: str) -> str:
    """'1,950.00' reads as '1,950': the same tool string, without the trailing cents."""
    return shown[:-3] if shown.endswith(".00") else shown


def _speakable(text: str) -> str:
    return text.replace("ORD-", "order ")


def _quantity(pieces: int, product: str) -> str:
    """'800 hoodies', '1,500 crewneck sweaters', '1,000 scarves': the tool's count and product name."""
    word = product.lower()
    if pieces != 1:
        word = word[:-1] + "ves" if word.endswith("f") else word if word.endswith("s") else word + "s"
    return f"{pieces:,} {word}"


# Cards -----------------------------------------------------------------------------------------


def _chosen(result: dict) -> dict | None:
    chosen_id = result.get("recommendation") or result.get("alternative")
    return next((row for row in result["candidates"] if row["estimate"]["workshop_id"] == chosen_id), None)


def _pick(result: dict, row: dict, register: dict) -> dict:
    estimate, shown = row["estimate"], row["display"]
    workshop = register[estimate["workshop_id"]]
    basis = result.get("decision_basis") or {}
    slack = basis.get("slack_days") if basis.get("workshop_id") == estimate["workshop_id"] else None
    return {
        "workshop_id": estimate["workshop_id"],
        "name": row["name"],
        "initials": _initials(row["name"]),
        "notes": workshop.notes,
        "eta": shown["eta"],
        "eta_day": day_label(shown["eta"]),
        "turnaround": shown["turnaround"],
        "cost": shown["cost"],
        "defects": shown["defects"],
        "on_time": row["meets_deadline"],
        "lateness": shown["lateness"],
        "slack": f"{slack:.2f} days" if slack is not None and row["meets_deadline"] else None,
        "due": result["batch"]["due_date"],
        "due_day": day_label(result["batch"]["due_date"]),
    }


def _timeline(row: dict) -> dict:
    estimate, shown = row["estimate"], row["display"]
    segments = []
    for key, display_key, label in SEGMENTS:
        days = estimate[key] if key else estimate["expected_turnaround_days"] - estimate["turnaround_days"]
        segments.append({"key": display_key, "label": label, "days": days, "shown": shown[display_key]})
    return {
        "segments": segments,
        "total_days": estimate["expected_turnaround_days"],
        "total": shown["turnaround"],
        "deadline_days": estimate["available_days"],
    }


def _options(result: dict, chosen: dict | None) -> list[dict]:
    rows = []
    for rank, row in enumerate(result["candidates"], 1):
        shown = row["display"]
        rows.append(
            {
                "rank": rank,
                "workshop_id": row["estimate"]["workshop_id"],
                "name": row["name"],
                "initials": _initials(row["name"]),
                "eta_day": day_label(shown["eta"]),
                "eta": shown["eta"],
                "turnaround": shown["turnaround"],
                "cost": shown["cost"],
                "defects": shown["defects"],
                "on_time": row["meets_deadline"],
                "lateness": shown["lateness"],
                "selected": row is chosen,
                "timeline": _timeline(row),
            }
        )
    return rows


def _order(result: dict) -> dict | None:
    order = result.get("order")
    if order:
        keys = ("order_id", "customer", "product", "pieces", "due_date", "status")
        return {key: order[key] for key in keys}
    query = result.get("capacity_query")
    if query and "batch" in result:
        return {
            "order_id": None,
            "customer": None,
            "product": query["product"],
            "pieces": f"{result['batch']['pieces']:,}",
            "due_date": result["batch"]["due_date"],
            "status": "CAPACITY CHECK",
        }
    return None


def _trace(result: dict, conversation: intake.Conversation | None, source: str) -> list[dict]:
    """The pipeline behind one answer, for the 'behind the answer' panel. Every value is copied."""
    stages = []
    if conversation is not None and conversation.turns:
        latest = conversation.traces[-1] if conversation.traces else {}
        fields = [
            f"{item['field']} = {item['normalized']!s} (quoted: '{item['evidence']}')"
            for item in conversation.provenance
            if item.get("turn") == len(conversation.turns) - 1 and item["field"] != "exclusion"
        ]
        fields += [
            f"exclude {item['workshop_id']} (by {item['imposed_by']}: '{item['evidence']}')"
            for item in conversation.provenance
            if item.get("turn") == len(conversation.turns) - 1 and item["field"] == "exclusion"
        ]
        stages.append(
            {
                "stage": "Understand",
                "actor": latest.get("model", source),
                "detail": "; ".join(fields) or "No new fields in this message.",
            }
        )
        if conversation.needs:
            stages.append(
                {
                    "stage": "Validate",
                    "actor": "Python",
                    "detail": "Still needed: " + ", ".join(conversation.needs) + ".",
                }
            )
    for title, detail in build_reply(result)["steps"]:
        stages.append({"stage": title, "actor": "Python tools", "detail": detail})
    if result.get("applied_rules"):
        stages.insert(
            -1,
            {
                "stage": "Memory",
                "actor": "Standing rules",
                "detail": "; ".join(
                    f"avoid {rule['workshop_id']} for {rule['customer'] or 'every order'} ({rule['imposed_by']})"
                    for rule in result["applied_rules"]
                ),
            },
        )
    if result["candidates"]:
        weights = result["effective_weights"]
        active = ", ".join(f"{key} {value:g}" for key, value in weights.items() if value)
        stages.insert(-1, {"stage": "Rank", "actor": "Allocator", "detail": "Weights: " + active + "."})
    return stages


def card_for_result(
    result: dict, register: dict, *, conversation: intake.Conversation | None = None, source: str = "model"
) -> dict:
    """One assistant card from one tool result. Python writes every word and number."""
    status = result["status"]
    reply = build_reply(result)
    chosen = _chosen(result)
    order = _order(result)
    order_id = order["order_id"] if order else None
    card = {
        "kind": "result",
        "status": status,
        "label": STATUS_LABELS[status],
        "tone": TONES.get(status, "warn"),
        "headline": reply["headline"],
        "sub": None,
        "order": order,
        "pick": _pick(result, chosen, register) if chosen and "batch" in result else None,
        "timeline": _timeline(chosen) if chosen else None,
        "reasons": (result.get("decision_basis") or {}).get("reasons", []),
        "options": _options(result, chosen),
        "excluded": [{"name": row["name"], "reason": " ".join(row["reasons"])} for row in result["excluded"]],
        "notes": [
            note for note in reply["notes"] if note not in (result.get("decision_basis") or {}).get("reasons", [])
        ],
        "memory": [
            {
                "rule_id": rule["rule_id"],
                "text": f"Avoid {register[rule['workshop_id']].name} for {rule['customer'] or 'every order'}",
                "by": f"{rule['imposed_by']}, {rule['created_on']}",
                "evidence": rule["evidence"],
            }
            for rule in result.get("applied_rules", [])
        ],
        "choices": reply["choices"],
        "actions": [],
        "trace": _trace(result, conversation, source),
        "source": source,
        "evidence_id": fingerprint(result)[:12],
    }
    pick = card["pick"]
    if status == "RECOMMEND" and pick:
        card["headline"] = f"Send {order_id} to {pick['name']}"
        card["sub"] = f"Arrives {pick['eta_day']}, {pick['slack']} before the {pick['due_day']} deadline"
        if result.get("commit_allowed"):
            card["actions"].append({"id": "book", "label": f"Book {pick['name']}", "primary": True})
        # Spoken replies stay short on the floor: the decision and the date. The card keeps the rest.
        speak = (
            f"{pick['name']}, by {day_label(pick['eta'], long=True)}, {pick['slack']} early. Say book it to confirm."
        )
    elif status == "CAPACITY" and pick:
        permitted = len(result["candidates"])
        on_time = sum(row["meets_deadline"] for row in result["candidates"])
        quantity = _quantity(result["batch"]["pieces"], result["capacity_query"]["product"])
        suggested = result.get("suggested")
        best = f"Best option: {pick['name']}, arriving {pick['eta_day']}."
        if suggested and suggested["workshop_id"] == pick["workshop_id"]:
            best = "It is also the best option."
        if suggested and suggested["meets_deadline"]:
            card["headline"] = f"{suggested['name']} can deliver {quantity} by {pick['due_day']}"
            card["sub"] = f"Arrives {day_label(suggested['eta'])}. {best}"
        elif suggested and suggested["eta"]:
            card["headline"] = f"{suggested['name']} cannot deliver {quantity} by {pick['due_day']}"
            card["sub"] = f"Earliest {day_label(suggested['eta'])}, {suggested['lateness']} late. {best}"
        elif suggested:
            card["headline"] = f"{suggested['name']} cannot take {quantity}"
            card["sub"] = f"{' '.join(suggested['reasons'])} {best}"
        elif on_time:
            card["headline"] = f"{on_time} of {permitted} workshops can deliver by {pick['due_day']}"
            card["sub"] = f"{quantity}. {best}"
        else:
            card["headline"] = f"No workshop can deliver {quantity} by {pick['due_day']}"
            card["sub"] = f"{quantity}. {best}"
        card["notes"] = ["Nothing is reserved until an order is booked.", *card["notes"]]
        if suggested:
            speak = f"{card['headline']}. {card['sub']} Nothing is reserved."
        else:
            speak = (
                f"{card['headline']}, for {quantity}. Best option: {pick['name']}, "
                f"{day_label(pick['eta'], long=True)}. Nothing is reserved."
            )
    elif status == "REFUSE_SUGGESTION":
        refused = next(
            (row for row in result["excluded"] if row["workshop_id"] == result["input"]["suggested_workshop"]), None
        )
        reason = refused["reasons"][0] if refused else "it fails a hard constraint."
        speak = reply["headline"] + " " + reason
        if pick and pick["on_time"]:
            card["sub"] = f"Instead: {pick['name']}, arriving {pick['eta_day']}"
            speak += f" {pick['name']} can, by {day_label(pick['eta'], long=True)}."
        elif pick:
            card["sub"] = f"Best alternative: {pick['name']}, {pick['eta_day']}, {pick['lateness']} late"
            speak += f" Best alternative: {pick['name']}, {pick['lateness']} late."
    elif status == "NEEDS_REVIEW" and pick:
        if "NO_ON_TIME_OPTION" in result["flags"]:
            card["headline"] = f"No workshop can make {order_id} by {pick['due_day']}"
            card["sub"] = f"Earliest: {pick['name']}, {pick['eta_day']}, {pick['lateness']} late"
            speak = (
                f"No workshop can meet {day_label(pick['due'], long=True)}. Earliest is {pick['name']}, "
                f"{day_label(pick['eta'], long=True)}, {pick['lateness']} late. Ask the customer for a new date."
            )
            if result.get("split_option"):
                split = result["split_option"]
                speak += f" A two-workshop split would arrive {day_label(split['display']['eta'], long=True)}."
        else:
            card["sub"] = f"Whole batch: {pick['name']}, arriving {pick['eta_day']}"
            speak = reply["headline"] + " " + result["message"]
    else:
        speak = result["message"]
    card["speak"] = _speakable(speak)
    return card


def info_card(headline: str, *, label: str = "Assistant", tone: str = "info", notes=(), kind: str = "info", **extra):
    card = {
        "kind": kind,
        "status": kind.upper(),
        "label": label,
        "tone": tone,
        "headline": headline,
        "sub": None,
        "notes": list(notes),
        "choices": [],
        "actions": [],
        "options": [],
        "excluded": [],
        "memory": [],
        "reasons": [],
        "trace": [],
        "speak": _speakable(headline),
    }
    card.update(extra)
    return card


def _options_card(session: Session) -> dict:
    """The last answer's permitted workshops, ranked, and why the rest cannot take it: its own tool result."""
    result = session.result
    if not result or not result.get("candidates"):
        return info_card("There is nothing to compare yet. Name an order first.")
    rows = _options(result, _chosen(result))
    notes = [
        f"{row['rank']}. {row['name']}: {row['eta_day']}, "
        + ("on time" if row["on_time"] else f"{row['lateness']} late")
        + f", cost {row['cost']}, defect risk {row['defects']}"
        for row in rows
    ]
    notes += [f"{row['name']} cannot take it: {' '.join(row['reasons'])}" for row in result["excluded"]]
    permitted, blocked = len(rows), len(result["excluded"])
    return info_card(
        f"{permitted} workshops can take it; {blocked} cannot",
        label="Options",
        notes=notes,
        speak=f"Here are the {permitted} workshops that can take it, ranked, and why the other {blocked} cannot.",
    )


def help_card() -> dict:
    return info_card(
        "Tell me what needs to go out, in your own words.",
        label="What you can say",
        notes=[
            "Name an order and its date: I check every workshop and recommend one.",
            "Add constraints like 'keep it away from BudgetWorks': I honour them and record who asked.",
            "Ask 'who can take 1,500 crewnecks by April 15?' to check capacity without booking.",
            "Say 'show me the other options' to compare every workshop, and why the rest cannot take it.",
            "Say 'book it' to open the confirmation; booking always needs your slide to confirm.",
            "After a booking, say 'remember that' to keep its constraint for the customer's next orders.",
            "Ask 'what did we book today?' or 'what rules do you remember?' for memory.",
        ],
        suggestions=list(EXAMPLES),
        speak="You can name an order and a date, add constraints, ask who has capacity, or say book it.",
    )


# Turns -----------------------------------------------------------------------------------------


def _offline_fixture(text: str) -> tuple[dict, dict] | None:
    """Inbox messages have hand-authored interpretations, so the demo works without a model."""
    fixtures = json.loads((ROOT / "examples" / "dispatch_inputs.json").read_text())
    for envelope in read_inbox():
        if _clean(envelope["text"]) == _clean(text):
            return envelope, fixtures[envelope["request_id"]]
    return None


def _preview(session: Session, conversation: intake.Conversation, services: Services, source: str) -> dict:
    result = services.store.preview(
        intake.conversation_envelope(conversation),
        conversation.request,
        services.weights,
        rules=services.memory.rule_payloads(),
    )
    result["interpretation_source"] = source
    result["conversation"] = intake.conversation_evidence(conversation)
    return result


def _answer(session: Session, conversation: intake.Conversation, services: Services, source: str, label: str):
    result = _preview(session, conversation, services, source)
    card = card_for_result(result, services.register, conversation=conversation, source=label)
    if result["input"]["intent"] == "history":
        card = _history_card(card, result, services)
    reply = _message("assistant", card=card)
    services.memory.log_episode(
        {
            "kind": "answer",
            "speaker": conversation.turns[-1]["speaker"],
            "utterance": conversation.turns[-1]["text"],
            "status": result["status"],
            "order_id": (result.get("order") or {}).get("order_id"),
            "recommendation": result.get("recommendation"),
            "evidence_id": card.get("evidence_id"),
            "source": label,
        }
    )
    return reply, result


def _history_card(card: dict, result: dict, services: Services) -> dict:
    """Prior allocations are absent from the course data; this desk's own bookings are not."""
    request = result["input"]
    records = services.store.records()
    matches = [
        record
        for record in records
        if (request["order_id"] and record["order_id"] == request["order_id"])
        or (
            request["customer"]
            and record["tool_evidence"]["order"]["customer"].casefold() == request["customer"].casefold()
        )
    ]
    if matches:
        card["notes"].append(
            "This desk's own saved bookings that match: "
            + "; ".join(f"{record['order_id']} to {record['workshop_name']}" for record in matches)
            + ". Nothing earlier than the planning snapshot is recorded."
        )
    return card


def _bookings_card(services: Services) -> dict:
    records = services.store.records()
    rows = [
        {
            "order_id": record["order_id"],
            "workshop": record["workshop_name"],
            "customer": record["tool_evidence"]["order"]["customer"],
            "product": record["tool_evidence"]["order"]["product"],
            "pieces": f"{record['tool_evidence']['batch']['pieces']:,}",
            "by": record["confirmed_by"],
            "eta_day": day_label(
                next(
                    row["display"]["eta"]
                    for row in record["tool_evidence"]["candidates"]
                    if row["estimate"]["workshop_id"] == record["workshop_id"]
                )
            ),
        }
        for record in records
    ]
    headline = (
        f"{len(rows)} booking{'s' if len(rows) != 1 else ''} saved in this plan."
        if rows
        else "Nothing is booked in this plan yet."
    )
    speak = headline + (
        " " + "; ".join(f"{row['order_id']} to {row['workshop']}" for row in rows[-3:]) + "." if rows else ""
    )
    return info_card(headline, label="From memory", kind="recall", bookings=rows, speak=_speakable(speak))


def _rules_card(services: Services) -> dict:
    rules = services.memory.rules(active_only=True)
    headline = (
        f"I remember {len(rules)} standing rule{'s' if len(rules) != 1 else ''}."
        if rules
        else "I have no standing rules yet. I learn one only when you confirm a booking that had a constraint."
    )
    rows = [
        {"rule_id": rule["rule_id"], "text": rule["summary"], "by": rule["imposed_by"], "evidence": rule["evidence"]}
        for rule in rules
    ]
    speak = headline + (" " + "; ".join(row["text"] for row in rows) + "." if rows else "")
    return info_card(headline, label="From memory", kind="recall", rules=rows, speak=speak)


def _workshop_card(workshop_id: str, services: Services) -> dict:
    register = services.store.query_register(WorkshopQuery())
    row = next(item for item in register["matches"] if item["workshop_id"] == workshop_id)
    workshop = services.register[workshop_id]
    booked = services.store.summary()["ledger"].get(workshop_id, 0)
    facts = [
        ["Status", row["status"].title()],
        ["Makes", " and ".join(category.lower() for category in row["makes"])],
        ["Capacity", row["display"]["capacity"]],
        ["Queue now", row["display"]["queue"]],
        ["Batch limit", row["display"]["max_batch"]],
        ["Defect risk", f"{workshop.defect_rate:.1%}"],
        ["Booked in this plan", f"{booked:,} pieces"],
    ]
    headline = f"{row['name']}: {row['display']['queue']} of work queued"
    if row["status"] != "ACTIVE":
        headline = f"{row['name']} is {row['status'].lower()} and cannot take new work"
    return info_card(
        headline,
        label="Workshop",
        kind="workshop",
        facts=facts,
        notes=[workshop.notes],
        speak=_speakable(headline + "."),
    )


def welcome(session: Session, name: str) -> Session:
    if session.thread:
        return session
    greeting = f"Hi {name}," if name else "Hi,"
    card = info_card(
        f"{greeting} what needs to go out today?",
        label="StitchFlow",
        kind="welcome",
        notes=["Hold the microphone and speak, or type. I check every workshop before I suggest one."],
        suggestions=list(EXAMPLES),
        speak="",
    )
    return _append(session, _message("assistant", card=card))


def handle_utterance(session: Session, text: str, services: Services, *, channel: str = "text") -> Session:
    """One spoken or typed message in, one assistant card out."""
    text = (text or "").strip()
    if not text:
        return session
    said = _message("user", text=text, channel=channel)
    command = parse_command(text)
    if command == "book":
        return request_booking(_append(session, said), services)
    if command == "cancel":
        note = "Okay, nothing was booked." if session.booking else "Okay. I'm here when you need me."
        return _append(session, said, _message("assistant", card=info_card(note)), booking=None)
    if command == "new":
        return _append(
            Session(thread=session.thread),
            said,
            _message("assistant", card=info_card("New request. What needs to go out?", kind="divider")),
        )
    if command == "repeat":
        last = next((m["card"] for m in reversed(session.thread) if m["role"] == "assistant" and m["card"]), None)
        return _append(session, said, _message("assistant", card=last or help_card()))
    if command == "help":
        return _append(session, said, _message("assistant", card=help_card()))
    if command == "remember":
        if not session.rule_offers:
            return _append(session, said, _message("assistant", card=info_card("There is nothing new to remember.")))
        actor = services.memory.profile()["dispatcher"] or services.speaker or "Dispatcher"
        return remember_offer(_append(session, said), 0, services, actor)
    if command == "options":
        return _append(session, said, _message("assistant", card=_options_card(session)))
    recall = parse_recall(text)
    if recall:
        card = _rules_card(services) if recall == "rules" else _bookings_card(services)
        return _append(session, said, _message("assistant", card=card))
    workshop = parse_workshop(text, {key: w.name for key, w in services.register.items()})
    if workshop:
        return _append(session, said, _message("assistant", card=_workshop_card(workshop, services)))
    return interpret(session, text, services, channel=channel, said=said)


def interpret(session: Session, text: str, services: Services, *, channel: str, said: dict | None = None) -> Session:
    said = said or _message("user", text=text, channel=channel)
    fresh = session.status in TERMINAL or session.status == "BOOKED"
    base = intake.Conversation() if fresh else session.conversation
    speaker = services.speaker or "Dispatcher"
    if services.model is None and not llm.model_configured():
        fixture = _offline_fixture(text)
        if fixture is None:
            card = info_card(
                "The language model is not configured, so I can only read the course inbox examples.",
                label="Model unavailable",
                tone="warn",
                kind="error",
                notes=["Set LLM_MODEL and its API key in .env, or try one of the inbox examples."],
                suggestions=[envelope["text"] for envelope in read_inbox()[:4]],
            )
            return _append(session, said, _message("assistant", card=card))
        envelope, payload = fixture
        conversation = intake.Conversation(
            request=DispatchInput(**payload), turns=({"speaker": envelope["requester"], "text": envelope["text"]},)
        )
        reply, result = _answer(
            session, conversation, services, "Hand-authored inbox interpretation; no model call.", "inbox fixture"
        )
        return _append(
            replace(session, conversation=conversation),
            said,
            reply,
            result=result,
            status=result["status"],
            retry=None,
            offline=True,
            booking=None,
        )
    try:
        conversation = intake.interpret_turn(
            base, text, services.desk, speaker=speaker, model=services.model, restart_new_requests=True
        )
        reply, result = _answer(
            session,
            conversation,
            services,
            "Model-extracted patches with deterministic validation; not ground truth.",
            conversation.traces[-1]["model"] if conversation.traces else "model",
        )
    except intake.IntakeError as error:
        card = info_card(
            str(error),
            label="Not understood",
            tone="warn",
            kind="error",
            actions=[{"id": "retry", "label": "Try again", "primary": True}],
        )
        return _append(session, said, _message("assistant", card=card), retry={"text": text, "channel": channel})
    return _append(
        replace(session, conversation=conversation),
        said,
        reply,
        result=result,
        status=result["status"],
        retry=None,
        offline=False,
        booking=None,
    )


def choose(session: Session, choice: dict, services: Services) -> Session:
    """A tapped answer to a clarification: validated like model output, with no model call."""
    if not session.conversation.turns:
        return session
    said = _message("user", text=choice["text"], channel="tap")
    try:
        conversation = intake.apply_selection(
            session.conversation,
            choice["field"],
            choice["value"],
            choice["text"],
            services.desk,
            speaker=services.speaker or "Dispatcher",
        )
        reply, result = _answer(
            session, conversation, services, "Dispatcher selection; no model call.", "your selection"
        )
    except (intake.IntakeError, KeyError, ValueError) as error:
        return _append(session, said, _message("assistant", card=info_card(str(error), tone="warn", kind="error")))
    return _append(
        replace(session, conversation=conversation), said, reply, result=result, status=result["status"], booking=None
    )


def rerank(session: Session, services: Services, label: str = "Re-ranked with your priorities") -> Session:
    """The same request re-ranked by the tools after a settings change, with no model call."""
    if session.result is None or not session.conversation.turns or session.status in ("BOOKED",):
        return session
    try:
        reply, result = _answer(
            session, session.conversation, services, session.result["interpretation_source"], "settings change"
        )
    except (ValueError, KeyError) as error:
        return _append(session, _message("assistant", card=info_card(str(error), tone="warn", kind="error")))
    reply["card"]["label"] = label
    return _append(session, reply, result=result, status=result["status"], booking=None)


def request_booking(session: Session, services: Services) -> Session:
    """Open the confirmation sheet for the latest bookable answer; never commits by itself."""
    result = session.result
    if result is None or session.status != "RECOMMEND" or not result.get("commit_allowed"):
        reason = (
            "There is nothing ready to book yet. Tell me which order needs to go out."
            if result is None or session.status in (None, "BOOKED")
            else "That answer is not bookable yet: " + result["message"]
        )
        return _append(session, _message("assistant", card=info_card(reason, tone="warn")), booking=None)
    chosen = _chosen(result)
    pick = _pick(result, chosen, services.register)
    booking = {
        "key": str(uuid4()),
        "preview_fingerprint": fingerprint(result),
        "order_id": result["order"]["order_id"],
        "customer": result["order"]["customer"],
        "product": result["order"]["product"],
        "pieces": f"{result['batch']['pieces']:,}",
        "workshop_id": pick["workshop_id"],
        "workshop": pick["name"],
        "initials": pick["initials"],
        "eta_day": pick["eta_day"],
        "eta": pick["eta"],
        "due_day": pick["due_day"],
        "slack": pick["slack"],
        "cost": pick["cost"],
        "defects": pick["defects"],
        "constraints": [
            f"{row['name']}: {row['reasons'][-1]}"
            for row in result["excluded"]
            if any(r.startswith(("Excluded by", "Remembered rule")) for r in row["reasons"])
        ],
    }
    card = info_card(
        f"Ready to book {booking['order_id']} with {booking['workshop']}.",
        label="Confirm booking",
        tone="ok",
        kind="confirm",
        notes=["Slide to confirm. This saves the booking and reserves capacity in the plan."],
        speak="Slide to confirm.",
    )
    return _append(session, _message("assistant", card=card), booking=booking)


def confirm_booking(session: Session, services: Services, actor: str) -> Session:
    """The deliberate gesture: recompute, check for staleness, save, and offer to remember rules."""
    booking = session.booking
    if booking is None or session.result is None:
        return _append(session, _message("assistant", card=info_card("Nothing is waiting for confirmation.")))
    if fingerprint(session.result) != booking["preview_fingerprint"]:
        return _append(
            session,
            _message("assistant", card=info_card("The answer changed. Review it again.", tone="warn")),
            booking=None,
        )
    try:
        record = services.store.commit_allocation(session.result, actor, booking["key"], confirmed=True)
    except AllocationError as error:
        card = info_card(str(error), label="Not booked", tone="bad", kind="error")
        return _append(session, _message("assistant", card=card), booking=None)
    offers = tuple(rule_suggestions(record, services.memory))
    services.memory.log_episode(
        {
            "kind": "booking",
            "speaker": actor,
            "order_id": record["order_id"],
            "workshop_id": record["workshop_id"],
            "allocation_id": record["allocation_id"],
            "evidence_id": booking["preview_fingerprint"][:12],
        }
    )
    reference = record["allocation_id"][:8].upper()
    card = info_card(
        f"Booked. {record['order_id']} goes to {record['workshop_name']}.",
        label="Booked",
        tone="ok",
        kind="receipt",
        receipt={
            **{key: booking[key] for key in ("order_id", "workshop", "initials", "eta_day", "cost", "pieces")},
            "reference": reference,
            "by": record["confirmed_by"],
            "effect": record["effect"],
            "reserved": f"{record['reserved_processing_days']:.2f} days",
        },
        offers=[
            {
                "index": index,
                "text": f"Always avoid {offer['workshop_name']} for {offer['customer']}?",
                "by": offer["imposed_by"],
                "evidence": offer["evidence"],
            }
            for index, offer in enumerate(offers)
        ],
        speak=f"Booked with {record['workshop_name']}, arriving {day_label(booking['eta'], long=True)}.",
    )
    return _append(
        replace(session, conversation=intake.Conversation()),
        _message("assistant", card=card),
        booking=None,
        status="BOOKED",
        rule_offers=offers,
    )


def remember_offer(session: Session, index: int, services: Services, actor: str) -> Session:
    offer = session.rule_offers[index] if 0 <= index < len(session.rule_offers) else None
    if offer is None:
        return session
    rule = services.memory.remember_rule(
        workshop_id=offer["workshop_id"],
        customer=offer["customer"],
        imposed_by=offer["imposed_by"],
        evidence=offer["evidence"],
        created_on=services.desk.as_of.isoformat(),
        created_by=actor,
        source_allocation_id=offer["source_allocation_id"],
    )
    remaining = tuple(item for i, item in enumerate(session.rule_offers) if i != index)
    card = info_card(
        f"Remembered: {rule['summary']}.",
        label="Memory updated",
        tone="ok",
        kind="memory",
        notes=[
            f"From {rule['imposed_by']}: '{rule['evidence']}'",
            "I apply it to every new request for this customer, and say so. Pause it any time in Memory.",
        ],
    )
    return _append(session, _message("assistant", card=card), rule_offers=remaining)


def retry(session: Session, services: Services) -> Session:
    if not session.retry:
        return session
    return interpret(replace(session, retry=None), session.retry["text"], services, channel=session.retry["channel"])


# Page glue: one event in, one view out ----------------------------------------------------------

OBJECTIVE_VIEW = (
    ("lateness", "On time", "Minimise late batches and late days. Our primary objective.", "#0f9f55"),
    ("defects", "Quality", "Minimise expected defective pieces. Our secondary objective.", "#7c4dff"),
    ("fairness", "Fair share", "Spread booked pieces across workshops, using this plan's bookings.", "#2f6fec"),
    ("robustness", "Resilience", "Keep enough slack to absorb a two-week workshop stoppage.", "#c77700"),
    ("cost", "Cost", "Prefer cheaper workshops. A measured tradeoff, not a course objective.", "#ff3d6e"),
)
PRESET_VIEW = {
    "hybrid": ("Recommended", "On time first, then quality"),
    "lateness": ("On time", "Fewest late days"),
    "defects": ("Quality", "Fewest defective pieces"),
    "fairness": ("Fair share", "Spread the work"),
    "robustness": ("Resilient", "Absorb a stoppage"),
}


def profile_weights(profile: dict) -> tuple[ObjectiveWeights, str]:
    """The dispatcher's saved priorities, or the team's recommended preset."""
    from dss5105.evaluate import DEFAULT_PRESET, PRESETS

    if profile.get("weights"):
        weights = ObjectiveWeights(**profile["weights"])
        preset = next((name for name, value in PRESETS.items() if value == weights), "custom")
        return weights, preset
    preset = profile.get("preset") if profile.get("preset") in PRESETS else DEFAULT_PRESET
    return PRESETS[preset], preset


def apply_event(session: Session, event: dict, services: Services) -> tuple[Session, str | None]:
    """Route one component event. Returns the new session and an optional notice for a toast."""
    kind = event.get("type")
    memory = services.memory
    actor = memory.profile()["dispatcher"] or services.speaker or "Dispatcher"
    if kind == "utterance":
        channel = event.get("channel") if event.get("channel") in ("voice", "text", "chip") else "text"
        return handle_utterance(session, str(event.get("text", ""))[:1000], services, channel=channel), None
    if kind == "choice" and isinstance(event.get("choice"), dict):
        return choose(session, event["choice"], services), None
    if kind == "book":
        return request_booking(session, services), None
    if kind == "cancel_booking":
        return replace(session, booking=None), None
    if kind == "confirm":
        name = str(event.get("actor") or "").strip()[:60]
        if not name:
            return session, "Enter your name: every booking records who confirmed it."
        if not memory.profile()["dispatcher"]:
            memory.update_profile(dispatcher=name)
        return confirm_booking(session, services, name), None
    if kind == "remember":
        return remember_offer(session, int(event.get("index", -1)), services, actor), None
    if kind == "retry":
        return retry(session, services), None
    if kind == "set_weights":
        try:
            weights = ObjectiveWeights(**{key: float(value) for key, value in dict(event.get("weights", {})).items()})
        except (TypeError, ValueError) as error:
            return session, "Those priorities are not valid: " + str(error)
        memory.update_profile(weights=asdict(weights))
        _, preset = profile_weights(memory.profile())
        memory.update_profile(preset=preset if preset != "custom" else memory.profile()["preset"])
        return rerank(session, replace(services, weights=weights)), "Priorities saved."
    if kind == "rule_toggle":
        rule = memory.set_rule_active(str(event.get("rule_id")), bool(event.get("active")), actor)
        state = "resumed" if rule["active"] else "paused"
        return rerank(session, services, f"Re-ranked: rule {state}"), f"{rule['summary']}: {state}."
    if kind == "profile":
        name = str(event.get("name") or "").strip()[:60]
        memory.update_profile(dispatcher=name, speak_replies=bool(event.get("speak")))
        return session, "Settings saved."
    return session, None


def _episode_view(episode: dict) -> dict:
    stamp = episode["created_at_utc"][11:16] + " UTC"
    if episode.get("kind") == "booking":
        return {
            "title": f"Booked {episode['order_id']} to {episode['workshop_id']}",
            "detail": f"by {episode['speaker']} \u00b7 {stamp}",
        }
    status = STATUS_LABELS.get(episode.get("status"), episode.get("status") or "")
    utterance = episode.get("utterance", "")
    return {
        "title": utterance if len(utterance) <= 90 else utterance[:87] + "...",
        "detail": " \u00b7 ".join(x for x in (status, episode.get("order_id"), episode.get("source"), stamp) if x),
    }


def build_view(session: Session, services: Services, *, version: int, notice: dict | None = None) -> dict:
    """Everything the assistant page draws. Text and numbers come from tools, memory or templates."""
    from dss5105.evaluate import PRESETS

    profile = services.memory.profile()
    weights, preset = profile_weights(profile)
    summary = services.store.summary()
    register = services.store.query_register(WorkshopQuery())
    workshops = []
    for row in register["matches"]:
        workshop = services.register[row["workshop_id"]]
        booked = summary["ledger"].get(row["workshop_id"], 0)
        workshops.append(
            {
                "id": row["workshop_id"],
                "name": row["name"],
                "initials": _initials(row["name"]),
                "status": row["status"],
                "status_label": row["status"].title(),
                "makes": " and ".join(category.lower() for category in row["makes"]),
                "capacity": row["display"]["capacity"],
                "queue": row["display"]["queue"],
                "load": min(1.0, row["queue_days"] / 10.0),
                "lead": f"{workshop.lead_days} day{'s' if workshop.lead_days != 1 else ''}",
                "defects": f"{workshop.defect_rate:.1%}",
                "cost": f"{workshop.cost:,.2f}",
                "limit": row["display"]["max_batch"],
                "booked": f"{booked:,} pieces",
                "notes": workshop.notes,
                "tag": f"\u2264{workshop.max_batch}" if workshop.max_batch else None,
            }
        )
    bookings = _bookings_card(services)["bookings"]
    name = profile["dispatcher"]
    configured = services.model is not None or llm.model_configured()
    return {
        "v": version,
        "lang": "en-US",
        "profile": {"name": name, "initials": (name[:1] or "D").upper(), "speak": profile["speak_replies"]},
        "plan": {
            "as_of": summary["as_of"],
            "as_of_label": date.fromisoformat(summary["as_of"]).strftime("%a %-d %b %Y"),
            "revision": summary["revision"],
            "bookings": len(bookings),
        },
        "workshops": workshops,
        "thread": list(session.thread),
        "booking": session.booking,
        "weights": asdict(weights),
        "preset": preset,
        "preset_label": PRESET_VIEW.get(preset, ("Custom", ""))[0],
        "presets": [
            {"id": key, "label": label, "hint": hint, "weights": asdict(PRESETS[key])}
            for key, (label, hint) in PRESET_VIEW.items()
        ],
        "objectives": [
            {"id": key, "label": label, "short": label, "hint": hint, "max": 1, "color": color}
            for key, label, hint, color in OBJECTIVE_VIEW
        ],
        "memory": {
            "rules": [
                {key: rule[key] for key in ("rule_id", "summary", "imposed_by", "evidence", "created_on", "active")}
                for rule in services.memory.rules()
            ],
            "bookings": bookings,
            "episodes": [_episode_view(episode) for episode in services.memory.episodes(limit=40)],
        },
        "model": {"configured": configured, "label": llm.model_label() if configured else "not configured"},
        "notice": notice,
    }
