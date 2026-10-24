"""The answer view: one request and its tool-authored answer at a time, plus saving.

Provider calls happen only when the dispatcher sends or retries a typed message. Supplied examples and
clicked answers never call a model. Buttons only queue an action; `process_pending` runs it once at the top
of the next run, so the page always renders from the stored result. Earlier answers are kept in `history`
(to mark sent examples and pick the next one) but only the newest is shown.
"""

import html
import sqlite3
from dataclasses import dataclass, replace
from uuid import uuid4

import streamlit as st

from dss5105 import intake
from dss5105.allocator import ObjectiveWeights
from dss5105.cards import chosen_candidate, option_tiles, render_working, tone
from dss5105.dispatch import DispatchDesk, DispatchInput
from dss5105.evaluate import PRESETS
from dss5105.records import AllocationError, AllocationStore
from dss5105.replies import build_reply

LABELS = {"lateness": "Lateness", "defects": "Defect", "hybrid": "Hybrid", "custom": "Custom"}
CUSTOM_DEFAULTS = {"lateness": 1.0, "defects": 0.05, "cost": 0.1}
SESSION_KEYS = (
    "history",
    "conversation",
    "pending_send",
    "pending_turn",
    "intake_error",
    "send_error",
    "reviewing",
    "confirmation_key",
    "working",
)
TILE_STATUSES = ("RECOMMEND", "REFUSE_SUGGESTION", "NEEDS_REVIEW")
FIXTURE_SOURCE = "Hand-authored development fixture; not model extraction or gold labels."


@dataclass(frozen=True)
class DeskContext:
    desk: DispatchDesk
    inbox: dict
    fixtures: dict
    fixture_sha256: str
    weights: ObjectiveWeights | None
    weights_error: str
    store: AllocationStore | None


def objective_mode() -> str:
    return st.session_state.get("objective", "lateness")


def read_weights() -> tuple[ObjectiveWeights | None, str]:
    """The weights chosen in the Objectives panel, or the reason they cannot be used."""
    mode = objective_mode()
    if mode != "custom":
        return PRESETS[mode], ""
    try:
        values = {term: st.session_state.get("weight_" + term, value) for term, value in CUSTOM_DEFAULTS.items()}
        return ObjectiveWeights(**values), ""
    except ValueError as error:
        return None, str(error)


def history() -> list[dict]:
    return st.session_state.get("history", [])


def push(row: dict):
    st.session_state.setdefault("history", []).append(row)


def sent_examples() -> set[str]:
    return {row["request_id"] for row in history() if row["type"] == "request" and row["kind"] == "example"}


def next_example(ctx: DeskContext) -> str | None:
    sent = sent_examples()
    return next((request_id for request_id in ctx.inbox if request_id not in sent), None)


def shown_example() -> str | None:
    """The example on screen, if the newest answer came from the Examples."""
    shown = [row for row in history() if row["type"] == "request"][-1:]
    return shown[0]["request_id"] if shown and shown[0]["kind"] == "example" else None


def queue(action: dict):
    """Button callback: remember what to do on the next run, and scroll to the answer when it arrives."""
    st.session_state["pending_send"] = action
    st.session_state["scroll_top"] = True


def reset_all():
    for key in SESSION_KEYS:
        st.session_state.pop(key, None)


def reset_conversation():
    for key in ("conversation", "pending_turn", "intake_error"):
        st.session_state.pop(key, None)


def clear_review():
    for key in ("reviewing", "confirmation_key"):
        st.session_state.pop(key, None)


def toggle_working(uid: str):
    """Show the working for one answer in the right column, or hide it if it is already open."""
    if st.session_state.get("working") == uid:
        st.session_state.pop("working", None)
    else:
        st.session_state["working"] = uid


def open_entry() -> dict | None:
    uid = st.session_state.get("working")
    return next((row for row in history() if row["type"] == "request" and row["uid"] == uid), None)


def start_review(uid: str):
    st.session_state["reviewing"] = uid
    st.session_state["confirmation_key"] = str(uuid4())


def retry():
    pending = st.session_state["pending_turn"]
    queue({"kind": "message", "text": pending["text"], "speaker": pending["speaker"]})


def new_uid(prefix: str) -> str:
    return prefix + str(len(history()) + 1) + "-" + uuid4().hex[:6]


def add_entry(kind: str, result: dict, *, speaker: str, time: str, text: str):
    uid = new_uid("m")
    if "working" in st.session_state:
        st.session_state["working"] = uid
    push(
        {
            "type": "request",
            "uid": uid,
            "kind": kind,
            "request_id": result["request"]["request_id"],
            "speaker": speaker,
            "time": time,
            "text": text,
            "result": result,
            "objective": objective_mode(),
            "saved": False,
            "confirmed": False,
        }
    )


def add_note(text: str, next_id: str | None):
    push({"type": "note", "uid": new_uid("n"), "text": text, "next": next_id})


def with_storage(ctx: DeskContext, result: dict, request: DispatchInput) -> dict:
    """In the saved plan, answer from the saved planning queues and keep the intake evidence."""
    if ctx.store is None:
        return result
    saved = ctx.store.preview(result["request"], request, ctx.weights)
    for key in ("conversation", "interpretation_source", "fixture_sha256"):
        if key in result:
            saved[key] = result[key]
    return saved


def remember_reply(conversation: intake.Conversation, result: dict) -> intake.Conversation:
    """Keep the tool's reply in the history the model sees on the next turn."""
    if conversation.turns[-1].get("reply"):
        return conversation
    turns = (*conversation.turns[:-1], {**conversation.turns[-1], "reply": result["message"]})
    return replace(conversation, turns=turns)


def answer_conversation(ctx: DeskContext, conversation: intake.Conversation, speaker: str, text: str):
    result = with_storage(ctx, intake.preview_conversation(conversation, ctx.desk, ctx.weights), conversation.request)
    st.session_state["conversation"] = remember_reply(conversation, result)
    add_entry("chat", result, speaker=speaker, time="", text=text)


def process_pending(ctx: DeskContext):
    """Run the queued action, if any, and store its result in the history."""
    action = st.session_state.pop("pending_send", None)
    if action is None:
        return
    st.session_state.pop("send_error", None)
    if ctx.weights is None:
        st.session_state["send_error"] = "Cannot generate a preview: " + ctx.weights_error
        return
    clear_review()
    try:
        if action["kind"] == "example":
            envelope = ctx.inbox[action["request_id"]]
            request = DispatchInput(**ctx.fixtures[action["request_id"]])
            result = ctx.desk.preview(envelope, request, ctx.weights)
            result["interpretation_source"] = FIXTURE_SOURCE
            result["fixture_sha256"] = ctx.fixture_sha256
            result = with_storage(ctx, result, request)
            add_entry("example", result, speaker=envelope["requester"], time=envelope["time"], text=envelope["text"])
        elif action["kind"] == "message":
            conversation = st.session_state.get("conversation", intake.Conversation())
            speaker = action.get("speaker", "Dispatcher")
            st.session_state["pending_turn"] = {"text": action["text"], "speaker": speaker}
            with st.spinner("Reading the request; Python tools will check every number..."):
                updated = intake.interpret_turn(conversation, action["text"], ctx.desk, speaker=speaker)
            st.session_state.pop("pending_turn", None)
            st.session_state.pop("intake_error", None)
            answer_conversation(ctx, updated, speaker, action["text"])
        else:
            choice = action["choice"]
            conversation = st.session_state.get("conversation")
            if conversation is None:
                raise intake.IntakeError("Send a request before choosing an answer.")
            updated = intake.apply_selection(conversation, choice["field"], choice["value"], choice["text"], ctx.desk)
            answer_conversation(ctx, updated, "Dispatcher", choice["text"])
    except intake.IntakeError as error:
        if action["kind"] == "message":
            st.session_state["intake_error"] = str(error)
        else:
            st.session_state["send_error"] = str(error)
    except (ValueError, TypeError, KeyError, sqlite3.Error, OSError) as error:
        st.session_state.pop("pending_turn", None)
        st.session_state["send_error"] = "Cannot generate a preview: " + str(error)


def bubble(speaker: str, time: str, request_id: str, text: str):
    meta = " &middot; ".join(part for part in (html.escape(time), html.escape(request_id)) if part)
    st.html(
        '<div class="qr-bubble"><span class="qr-avatar">'
        + html.escape(speaker[:1])
        + '</span><div><div class="qr-who"><strong>'
        + html.escape(speaker)
        + "</strong> "
        + meta
        + '</div><p class="qr-say">'
        + html.escape(text)
        + "</p></div></div>"
    )


def confirmation(ctx: DeskContext, entry: dict, chosen: dict):
    result = entry["result"]
    with st.container(border=True, key="confirmation_panel"):
        st.subheader("Review the allocation")
        st.write(
            f"{result['order']['order_id']} to {chosen['name']}. "
            f"Estimated delivery: {chosen['display']['eta']}. Cost: {chosen['display']['cost']} source units."
        )
        if ctx.store is not None:
            st.caption("Save this allocation and reserve capacity in the local plan. No workshop will be contacted.")
            actor = st.text_input("Confirming dispatcher", key="confirmed_by")
        else:
            st.caption("Preview only. No allocation is saved, no queue changes, and no workshop is contacted.")
        approve, cancel = st.columns(2)
        if ctx.store is not None and approve.button(
            "Confirm and save allocation", key="confirm_allocation", type="primary", disabled=not actor.strip()
        ):
            try:
                receipt = ctx.store.commit_allocation(
                    result, actor, st.session_state["confirmation_key"], confirmed=True
                )
            except (AllocationError, sqlite3.Error, OSError) as error:
                st.error(
                    str(error)
                    if isinstance(error, AllocationError)
                    else "Save failed. Refresh the plan before retrying."
                )
            else:
                entry["saved"] = True
                add_note(
                    f"Saved {receipt['order_id']} to {receipt['workshop_name']}. {receipt['effect']}",
                    next_example(ctx),
                )
                clear_review()
                st.rerun()
        if ctx.store is None and approve.button("Confirm preview only", key="confirm_demo", type="primary"):
            entry["confirmed"] = True
            add_note(
                f"Preview confirmed for {result['order']['order_id']} to {chosen['name']}. Nothing was saved.",
                next_example(ctx),
            )
            clear_review()
            st.rerun()
        if cancel.button("Back", key="cancel_confirmation"):
            clear_review()
            st.rerun()


def render_request(ctx: DeskContext, entry: dict):
    result = entry["result"]
    card = build_reply(result)
    status = result["status"]
    kind = tone(status)
    chosen = chosen_candidate(result)
    uid = entry["uid"]
    bubble(entry["speaker"], entry["time"], entry["request_id"] if entry["kind"] == "example" else "", entry["text"])
    st.html(
        '<div class="qr-who bot"><span class="qr-avatar bot">D</span>'
        "<strong>Dispatch desk</strong> checked with Python tools</div>"
    )
    if entry["saved"]:
        label = "Saved"
    elif entry["confirmed"]:
        label = "Confirmed (preview only)"
    else:
        label = card["label"]
    preference = result["input"]["preference"]
    chip = (
        "Request asks for: <b>" + html.escape(preference.replace("_", " ")) + "</b>"
        if preference != "configured"
        else "Objective: <b>" + html.escape(LABELS[entry["objective"]]) + "</b>"
    )
    with st.container(border=True, key=f"oc_{kind}_{uid}"):
        st.html(
            f'<div class="qr-card-top"><span class="qr-badge qr-{kind}">{html.escape(label)}</span>'
            f'<span class="qr-chip">{chip}</span></div><h3 class="qr-h3">{html.escape(card["headline"])}</h3>'
        )
        if chosen and status in TILE_STATUSES:
            lead = (
                None
                if status == "RECOMMEND"
                else "Allowed alternative"
                if status == "REFUSE_SUGGESTION"
                else "Best whole-batch option, for discussion"
            )
            option_tiles(result, chosen, lead)
        if card["notes"]:
            notes = "".join(f"<li>{html.escape(note)}</li>" for note in card["notes"])
            heading = "How it was ranked" if status == "RECOMMEND" else "What to know"
            st.html(f'<div class="qr-blk"><h4>{heading}</h4><ul>{notes}</ul></div>')
        earliest = result.get("earliest_option")
        if earliest and status != "RECOMMEND" and not any("earliest" in note.lower() for note in card["notes"]):
            st.html(
                '<p class="qr-line">Earliest permitted delivery: <b>'
                + html.escape(earliest["name"])
                + "</b>, "
                + html.escape(earliest["display"]["eta"])
                + " ("
                + html.escape(earliest["display"]["turnaround"])
                + ").</p>"
            )
        if entry["kind"] == "chat" and card["choices"]:
            st.caption("Tap an answer. This applies it directly, with no model call.")
            for index, choice in enumerate(card["choices"]):
                st.button(
                    choice["label"],
                    key=f"choice_{index}",
                    on_click=queue,
                    args=({"kind": "choice", "choice": choice},),
                    width="stretch",
                )
        ready = status == "RECOMMEND" and not entry["saved"] and not entry["confirmed"]
        can_save = ready and (ctx.store is None or bool(result.get("commit_allowed")))
        if ready and not can_save:
            st.caption("Send this request again while the saved local plan is on to save it.")
        with st.container(horizontal=True):
            if can_save:
                st.button(
                    "Review and save" if ctx.store is not None else "Review confirmation",
                    key=f"review_{uid}",
                    type="primary",
                    on_click=start_review,
                    args=(uid,),
                )
            st.button(
                "Hide working" if st.session_state.get("working") == uid else "Show working",
                key=f"work_{uid}",
                on_click=toggle_working,
                args=(uid,),
            )
        if can_save and st.session_state.get("reviewing") == uid:
            confirmation(ctx, entry, chosen)


def render_working_panel(entry: dict):
    """The right-hand column: one answer's working, as in the HTML prototype."""
    result = entry["result"]
    with st.container(border=True, key="working_panel"):
        st.html(
            '<div class="qr-eyebrow">Show your working</div><h3 class="qr-h3" style="margin-top:0.2rem">'
            + html.escape(entry["request_id"] + ": " + entry["speaker"])
            + "</h3>"
        )
        render_working(result, build_reply(result)["steps"], entry["uid"])


def render_answer(ctx: DeskContext):
    """The newest request, its answer and any note that followed it."""
    entries = history()
    last = max((index for index, row in enumerate(entries) if row["type"] == "request"), default=-1)
    for entry in entries[last:] if last >= 0 else []:
        if entry["type"] == "note":
            st.html(f'<div class="qr-note">{html.escape(entry["text"])}</div>')
            if entry["next"]:
                st.button(
                    "Next: " + entry["next"],
                    key="next_" + entry["uid"],
                    on_click=queue,
                    args=({"kind": "example", "request_id": entry["next"]},),
                )
        else:
            render_request(ctx, entry)
    if pending := st.session_state.get("pending_turn"):
        bubble(pending["speaker"], "", "", pending["text"])
        st.error(st.session_state.get("intake_error", "The request has not been interpreted yet."))
        st.button("Retry interpretation", key="retry_intake", on_click=retry)
    if error := st.session_state.get("send_error"):
        st.error(error)


def render_composer(*, start: bool):
    """The free-text box. It is inline so the Start here screen can centre it."""
    if not start and "conversation" in st.session_state:
        st.button(
            "New request",
            key="new_chat",
            on_click=reset_conversation,
            help="Start over with a different order or exclusions.",
        )
    message = st.chat_input(
        "Type or paste a message from the group chat" if start else "Type or paste the next message",
        key="dispatch_chat",
        disabled="pending_turn" in st.session_state,
    )
    if message:
        queue({"kind": "message", "text": message, "speaker": "Dispatcher"})
        st.rerun()
    st.caption(
        "Typing a message uses the model configured in .env and may incur provider charges. "
        "Examples never call a model."
    )
