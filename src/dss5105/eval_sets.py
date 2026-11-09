"""Generated chat evaluation sets, labelled by construction and checked against the tools.

Each case is built from known structured facts, so its extraction labels are known without a
model. Its expected state comes from the deterministic preview of those facts. Train and test
use disjoint message templates; tune prompts on train only and report test.

The supplements (train_extra, test_extra) are separate files with their own seeds and
builder, drawn after the base splits so they never repeat a supplied or base message.
"""

import argparse
import json
import random
from collections import Counter
from datetime import date, timedelta

from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput, read_inbox
from dss5105.harness import eligible_workshops
from dss5105.intake import QUESTIONS

VERSION = "generated-v1"
SEED = 5105
OUTPUT = ROOT / "examples" / "eval_sets"
PER_KIND = {"train": 10, "test": 5}
SPEAKERS = ("Chen", "Ravi", "Priya", "Boss", "Mei")
PLURALS = {
    "Scarf": "scarves",
    "Beanie": "beanies",
    "Hoodie": "hoodies",
    "Vest": "vests",
    "Cardigan": "cardigans",
    "Polo shirt": "polo shirts",
    "Crewneck sweater": "crewneck sweaters",
}
CATEGORY = {
    "complete_meetable": "complete",
    "complete_impossible": "deadline_exception",
    "ambiguous": "clarification",
    "missing_number_or_date": "clarification",
    "ineligible_suggestion": "refusal",
    "unanswerable": "missing_data",
}
REVIEW_FLAGS = ("NO_ON_TIME_OPTION", "PAST_DEADLINE", "SPLIT_REVIEW")
STATUS = "Generated: fields are labelled by construction, states by the deterministic preview. Not human gold."


def say_date(day: date, rng: random.Random) -> str:
    suffix = "th" if 11 <= day.day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day.day % 10, "th")
    return rng.choice(
        (
            day.strftime("%b %d"),
            day.strftime("%B ") + str(day.day),
            day.isoformat(),
            day.strftime("%b ") + str(day.day) + suffix,
        )
    )


class Builder:
    """One method per course kind; each returns message text and the facts it states.

    `turn` cycles the templates so every phrasing is covered evenly; facts stay random.
    """

    turn = 0

    def __init__(self, desk: DispatchDesk, rng: random.Random):
        self.desk, self.rng = desk, rng
        self.open = [row for row in desk.orders if row["status"] == "IN_PROGRESS"]
        self.feasible = [
            row for row in self.open if self.preview(DispatchInput(order_id=row["order_id"]))[0] == "RECOMMEND"
        ]
        counts = {}
        for row in desk.orders:
            counts.setdefault((row["customer"], row["product"]), []).append(row)
        self.shared = sorted(key for key, rows in counts.items() if len(rows) > 1)
        self.customers = sorted({row["customer"] for row in desk.orders})

    def preview(self, request: DispatchInput, text: str = "") -> tuple[str, list[str]]:
        envelope = {"request_id": "GEN", "time": "00:00", "requester": "Generator", "text": text}
        result = self.desk.preview(envelope, request, ObjectiveWeights())
        return result["status"], result["flags"]

    def facts(self, row: dict, due: date | None = None) -> dict:
        due = due or date.fromisoformat(row["due_date"])
        return {
            "oid": row["order_id"],
            "pieces": int(row["pieces"]),
            "plural": PLURALS[row["product"]],
            "customer": row["customer"],
            "date": say_date(due, self.rng),
            "fields": {
                "order_id": row["order_id"],
                "pieces": int(row["pieces"]),
                "product": row["product"],
                "customer": row["customer"],
                "due_date": due.isoformat(),
            },
        }

    def complete(self, split: str, meetable: bool) -> dict:
        rng = self.rng
        if meetable:
            row = rng.choice(self.feasible)
            due = date.fromisoformat(row["due_date"]) + timedelta(days=rng.choice((0, 0, 3, 7)))
        elif rng.random() < 0.3:
            row = rng.choice(self.feasible)
            due = self.desk.as_of + timedelta(days=1)
        else:
            row = rng.choice([row for row in self.open if row not in self.feasible])
            due = None
        f = self.facts(row, due)
        fields, omit = f["fields"], ()
        if split == "train":
            # The pulled-forward wording only fits a date that differs from orders.csv.
            template = self.turn % (4 if f["fields"]["due_date"] != row["due_date"] else 3)
            text = (
                "{oid} - {pieces} {plural} for {customer}, due {date}.",
                "Please place {oid}: {pieces:,} {plural}, {customer}, back by {date}.",
                "{oid} ready to go outside. {pieces} {plural} for {customer}, needed by {date}.",
                "{customer} pulled {oid} forward: {pieces} {plural}, now due {date}.",
            )[template].format(**f)
        else:
            template = 4 + self.turn % 2
            if template == 4:
                text = (
                    "Can someone find a workshop for {oid}? "
                    "It's {pieces} {plural} for {customer} and has to be back {date}."
                )
            else:
                text = "{oid_lower} {pieces} {plural} {customer_lower} due {date} pls"
                f.update(oid_lower=f["oid"].lower(), customer_lower=f["customer"].lower())
                fields = {**fields, "customer": f["customer_lower"]}
                omit = ("customer",)
            text = text.format(**f)
        return {"text": text, "fields": fields, "omit": omit, "template": f"complete-{template}"}

    def constraint(self, split: str) -> dict:
        rng = self.rng
        row = rng.choice(self.feasible)
        f = self.facts(row)
        base = "{oid} - {pieces} {plural} for {customer}, due {date}. ".format(**f)
        batch = {**f["fields"], "category": row["category"], "sent_date": self.desk.as_of}
        batch["due_date"] = date.fromisoformat(batch["due_date"])
        eligible = [w for w in eligible_workshops(batch, self.desk.workshops)]
        workshop = rng.choice(eligible)
        imposer = rng.choice(SPEAKERS)
        variants = {
            "train": (
                ("Keep it away from {w}, the last batch came back rough.", {"exclude": "speaker"}),
                ("{i} says nothing new to {w} this week, they're swamped.", {"exclude": "named"}),
                ("Cost doesn't matter, just the fastest turnaround.", {"preference": "fastest"}),
                ("Margin is thin - cheapest shop that can still make {date}.", {"preference": "cheapest_on_time"}),
                (
                    "They rejected a batch last month, so lowest defect rate you can get.",
                    {"preference": "lowest_defects"},
                ),
            ),
            "test": (
                ("Not {w} please, they've been unreliable.", {"exclude": "speaker"}),
                ("{i} wants it kept off {w}.", {"exclude": "named"}),
                ("Quality first on this one, lowest defect risk please.", {"preference": "lowest_defects"}),
                ("Split it across two shops if that gets it back faster.", {"split_requested": True}),
            ),
        }[split]
        template = self.turn % len(variants)
        phrase, spec = variants[template]
        text = base + phrase.format(w=workshop.name, i=imposer, date=f["date"])
        fields = dict(f["fields"])
        exclusions = {}
        if spec.get("exclude"):
            exclusions[workshop.workshop_id] = imposer if spec["exclude"] == "named" else None
        for key in ("preference", "split_requested"):
            if key in spec:
                fields[key] = spec[key]
        category = "exclusion" if exclusions else "split" if "split_requested" in spec else "preference"
        return {
            "text": text,
            "fields": fields,
            "exclusions": exclusions,
            "category": category,
            "template": f"constraint-{split}-{template}",
        }

    def ambiguous(self, split: str) -> dict:
        rng = self.rng
        customer, product = rng.choice(self.shared)
        plural = PLURALS[product]
        fields = {"order_id": None, "customer": customer, "product": product}
        templates = {
            "train": (
                "Can we get the {c} {p} moving? They are chasing.",
                "The {c} {p} need a workshop today.",
                "Send the {c} {p} to whoever is fastest.",
            ),
            "test": ("Get the {c} {p} out the door, please.", "Same as the last {c} job - send it out today."),
        }[split]
        template = self.turn % len(templates)
        text = templates[template].format(c=customer, p=plural)
        if "fastest" in text:
            fields["preference"] = "fastest"
        if "last {c} job" in templates[template]:
            fields = {"order_id": None, "customer": customer}
        return {"text": text, "fields": fields, "template": f"ambiguous-{split}-{template}"}

    def missing(self, split: str) -> dict:
        rng = self.rng
        row = rng.choice(self.feasible)
        f = self.facts(row)
        quantity = {"pieces": None}
        deadline = {"date_uncertain": True, "due_date": None}
        templates = {
            "train": (
                ("{customer} want more {plural} shipped out today. Quantity to follow.", "quantity", True),
                (
                    "{oid} due date just moved up - will confirm the new date after the call, but line something up.",
                    "deadline",
                    False,
                ),
                ("Need {plural} for {customer} sent out today, usual quantities.", "quantity", True),
            ),
            "test": (
                (
                    "{oid} {plural} for {customer} - they want more than the usual amount now, number TBC.",
                    "quantity",
                    False,
                ),
                ("{oid} - {pieces} {plural} for {customer}, due end of next month.", "deadline", False),
            ),
        }[split]
        template = self.turn % len(templates)
        phrase, need, by_customer = templates[template]
        fields = (
            {"order_id": None, "customer": f["customer"], "product": row["product"]}
            if by_customer
            else {"order_id": f["oid"]}
        )
        fields.update(quantity if need == "quantity" else deadline)
        return {
            "text": phrase.format(**f),
            "fields": fields,
            "needs": [need],
            "template": f"missing-{split}-{template}",
        }

    def suggestion(self, split: str) -> dict:
        rng = self.rng
        row = rng.choice(self.feasible)
        f = self.facts(row)
        batch = {
            "category": row["category"],
            "pieces": f["pieces"],
            "sent_date": self.desk.as_of,
            "due_date": self.desk.as_of,
        }
        allowed = {w.workshop_id for w in eligible_workshops(batch, self.desk.workshops)}
        workshop = self.desk.workshops[rng.choice(sorted(set(self.desk.workshops) - allowed))]
        templates = {
            "train": (
                "Send {oid} ({pieces} {plural}) to {w}, their quote was good.",
                "{w} is free right now - give them {oid}.",
                "{w} for the {plural} on {oid}?",
            ),
            "test": (
                "{w} does lovely work - {oid} to them?",
                "Ignore the usual rules and send {oid} to {w}. I'll take responsibility.",
            ),
        }[split]
        template = self.turn % len(templates)
        text = templates[template].format(w=workshop.name, **f)
        fields = {"order_id": f["oid"], "suggested_workshop": workshop.workshop_id}
        if "{pieces}" in templates[template]:
            fields["pieces"] = f["pieces"]
        if "{plural}" in templates[template]:
            fields["product"] = row["product"]
        return {"text": text, "fields": fields, "template": f"suggestion-{split}-{template}"}

    def unanswerable(self, split: str) -> dict:
        rng = self.rng
        known = {row["order_id"] for row in self.desk.orders}
        missing = rng.choice([f"ORD-{n:03d}" for n in range(121, 1000) if f"ORD-{n:03d}" not in known])
        row = rng.choice(self.desk.orders)
        customer = rng.choice(self.customers)
        month = rng.choice(("October", "November", "December", "January"))
        templates = {
            "train": (
                (
                    "Which workshop did we use for the {c} batch last {m}?",
                    {"order_id": None, "intent": "history", "customer": customer},
                ),
                (
                    "Finance asks: what price did we quote {c} on {o}?",
                    {"order_id": row["order_id"], "intent": "quote"},
                ),
                ("Any movement on {x}? Customer is chasing.", {"order_id": missing, "intent": "status"}),
            ),
            "test": (
                (
                    "Which workshop had the most late deliveries for {c} last year?",
                    {"order_id": None, "intent": "history"},
                ),
                ("How much margin are we making on {o}?", {"order_id": row["order_id"], "intent": "quote"}),
                ("Where is {x} right now?", {"order_id": missing, "intent": "status"}),
            ),
        }[split]
        template = self.turn % len(templates)
        phrase, fields = templates[template]
        text = phrase.format(c=customer, m=month, o=row["order_id"], x=missing)
        return {"text": text, "fields": fields, "template": f"unanswerable-{split}-{template}"}


def label(builder: Builder, kind: str, case: dict, speaker: str) -> dict | None:
    """Expected state is the tool outcome on the constructed facts; None rejects the draw."""
    exclusions = [
        {"workshop_id": key, "imposed_by": imposer or speaker, "evidence": case["text"]}
        for key, imposer in case.get("exclusions", {}).items()
    ]
    needs = case.get("needs", [])
    request = DispatchInput(
        **case["fields"],
        exclusions=exclusions,
        clarification=" ".join(QUESTIONS[code] for code in needs) or None,
    )
    status, flags = builder.preview(request, case["text"])
    if kind == "complete_meetable" and status != "RECOMMEND":
        return None
    if kind == "complete_impossible" and "NO_ON_TIME_OPTION" not in flags:
        return None
    expected = {
        "ambiguous": "CLARIFY",
        "missing_number_or_date": "CLARIFY",
        "ineligible_suggestion": "REFUSE_SUGGESTION",
        "unanswerable": "DECLINE",
    }
    if kind in expected and status != expected[kind]:
        return None
    rule = {
        "course_kind": kind,
        "category": case.get("category", CATEGORY.get(kind)),
        "template": case["template"],
        "fields": {key: value for key, value in case["fields"].items() if key not in case.get("omit", ())},
        "statuses": [status],
    }
    if exclusions:
        rule["exclusions"] = {item["workshop_id"]: item["imposed_by"] for item in exclusions}
    if needs:
        rule["needs"] = needs
    if review := [flag for flag in REVIEW_FLAGS if flag in flags]:
        rule["flags"] = review
    return rule


def generate(seed: int = SEED) -> dict:
    desk, rng = DispatchDesk(), random.Random(seed)
    builder = Builder(desk, rng)
    draws = {
        "complete_meetable": lambda split: builder.complete(split, True),
        "complete_impossible": lambda split: builder.complete(split, False),
        "constraint": builder.constraint,
        "ambiguous": builder.ambiguous,
        "missing_number_or_date": builder.missing,
        "ineligible_suggestion": builder.suggestion,
        "unanswerable": builder.unanswerable,
    }
    seen = {item["text"] for item in read_inbox()}
    sets = {}
    for split, prefix in (("train", "TR"), ("test", "TE")):
        cases, lines = {}, []
        for kind, draw in draws.items():
            made = 0
            for _ in range(500):
                if made == PER_KIND[split]:
                    break
                speaker = rng.choice(SPEAKERS)
                builder.turn = made
                case = draw(split)
                if case["text"] in seen:
                    continue
                rule = label(builder, kind, case, speaker)
                if rule is None:
                    continue
                seen.add(case["text"])
                request_id = f"{prefix}{len(cases) + 1:03d}"
                cases[request_id] = rule
                lines.append(
                    f"{request_id} [{9 + len(cases) // 12:02d}:{len(cases) * 5 % 60:02d}] {speaker}: {case['text']}"
                )
                made += 1
            if made != PER_KIND[split]:
                raise RuntimeError(f"Could not draw enough {kind} cases for {split}")
        sets[split] = {
            "title": f"{split} split",
            "requests": lines,
            "rubric": {
                "version": VERSION,
                "split": split,
                "seed": seed,
                "status": STATUS,
                "course_kind_counts": {kind: PER_KIND[split] for kind in draws},
                "cases": cases,
            },
        }
    return {**sets, **generate_supplements(seed, seen)}


# Supplementary sets: (base split, seed offset, request prefix, first number, cases per kind).
SUPPLEMENTS = {
    "train_extra": ("train", 1, "TR", 71, (10, 10, 10, 10, 10, 10, 10)),
    # The course inbox mix: 7 meetable, 3 impossible, 6 constraint, 4 ambiguous, 3 missing, 4 suggestion, 3 none.
    "test_extra": ("test", 2, "TE", 71, (7, 3, 6, 4, 3, 4, 3)),
}
KINDS = (
    "complete_meetable",
    "complete_impossible",
    "constraint",
    "ambiguous",
    "missing_number_or_date",
    "ineligible_suggestion",
    "unanswerable",
)
PAST_MONTHS = ("October", "November", "December", "January", "February", "March")
# Supplement templates. train_extra reuses the train phrasings; test_extra wording appears nowhere else.
EXTRA_COMPLETE = {
    "train": {
        "complete-0": "{oid} - {n} {plural} for {cust}, due {date}.",
        "complete-1": "Please place {oid}: {n_comma} {plural}, {cust}, back by {date}.",
        "complete-2": "{oid} ready to go outside. {n} {plural} for {cust}, needed by {date}.",
        "complete-3": "{cust} pulled {oid} forward: {n} {plural}, now due {date}.",
    },
    "test": {
        "complete-test2-0": "Got a slot for {oid}? {n} {plural} ({cust}), they need them by {date}.",
        "complete-test2-1": "{cust} order {oid}: {n_comma} {plural}. Deadline is {date}. Where can it go?",
        "complete-test2-2": "Outsourcing {oid} today - {n} {plural} for {cust}, delivery by {date}.",
    },
}
# (template, constraint shape, suffix). {w} = workshop name, {who} = named imposer.
EXTRA_CONSTRAINT = {
    "train": [
        ("constraint-train-0", "exclude_speaker", "Keep it away from {w}, the last batch came back rough."),
        ("constraint-train-1", "exclude_named", "{who} says nothing new to {w} this week, they're swamped."),
        ("constraint-train-2", "fastest", "Cost doesn't matter, just the fastest turnaround."),
        ("constraint-train-3", "cheapest_on_time", "Margin is thin - cheapest shop that can still make {date}."),
        (
            "constraint-train-4",
            "lowest_defects",
            "They rejected a batch last month, so lowest defect rate you can get.",
        ),
    ],
    "test": [
        ("constraint-test2-0", "exclude_speaker", "Please don't use {w} for this one, we had problems with them."),
        ("constraint-test2-1", "exclude_named", "{who} wants {w} kept off this order."),
        ("constraint-test2-2", "fastest", "Speed is everything on this one, price is secondary."),
        ("constraint-test2-3", "cheapest_on_time", "Go with the lowest price that still lands by {date}."),
        (
            "constraint-test2-4",
            "lowest_defects",
            "Quality comes first here, pick the shop with the lowest defect rate.",
        ),
    ],
}
EXTRA_CONSTRAINT_BASE = {
    "train": "{oid} - {n} {plural} for {cust}, due {date}.",
    "test": "{oid}: {n} {plural} for {cust}, due {date}.",
}
EXTRA_AMBIGUOUS = {
    "train": [
        ("ambiguous-train-0", "Can we get the {cust} {plural} moving? They are chasing.", None),
        ("ambiguous-train-1", "The {cust} {plural} need a workshop today.", None),
        ("ambiguous-train-2", "Send the {cust} {plural} to whoever is fastest.", "fastest"),
    ],
    "test": [
        ("ambiguous-test2-0", "Where are we with the {cust} {plural}? Need them placed.", None),
        ("ambiguous-test2-1", "Can you book a workshop for the {cust} {plural}?", None),
        ("ambiguous-test2-2", "Rush the {cust} {plural} out, quickest turnaround please.", "fastest"),
    ],
}
# need: "quantity" (customer + product, no number) or "deadline" (order ID, revised date unknown)
EXTRA_MISSING = {
    "train": [
        ("missing-train-0", "quantity", "{cust} want more {plural} shipped out today. Quantity to follow."),
        (
            "missing-train-1",
            "deadline",
            "{oid} due date just moved up - will confirm the new date after the call, but line something up.",
        ),
        ("missing-train-2", "quantity", "Need {plural} for {cust} sent out today, usual quantities."),
    ],
    "test": [
        ("missing-test2-0", "quantity", "{cust} called - they need extra {plural} made, numbers coming later."),
        (
            "missing-test2-1",
            "deadline",
            "{oid}: the customer is changing the deadline, new date TBC. Start lining up a workshop.",
        ),
        ("missing-test2-2", "quantity", "Book some {plural} for {cust} with a workshop, same amount as last time."),
    ],
}
# stated: which optional fields the message states (pieces, product)
EXTRA_SUGGESTION = {
    "train": [
        ("suggestion-train-0", ("pieces", "product"), "Send {oid} ({n} {plural}) to {w}, their quote was good."),
        ("suggestion-train-1", (), "{w} is free right now - give them {oid}."),
        ("suggestion-train-2", ("product",), "{w} for the {plural} on {oid}?"),
    ],
    "test": [
        ("suggestion-test2-0", ("pieces", "product"), "{w} would be good for the {n} {plural} on {oid}."),
        ("suggestion-test2-1", (), "Can {w} take {oid}? They said they have capacity."),
        ("suggestion-test2-2", ("product",), "Let's give the {plural} on {oid} to {w}."),
    ],
}
EXTRA_UNANSWERABLE = {
    "train": [
        ("unanswerable-train-0", "history", "Which workshop did we use for the {cust} batch last {month}?"),
        ("unanswerable-train-1", "quote", "Finance asks: what price did we quote {cust} on {oid}?"),
        ("unanswerable-train-2", "status", "Any movement on {bad}? Customer is chasing."),
    ],
    "test": [
        ("unanswerable-test2-0", "history", "Who did we send the {cust} work to back in {month}?"),
        ("unanswerable-test2-1", "quote", "What selling price did we agree with {cust} for {oid}?"),
        ("unanswerable-test2-2", "status", "Is {bad} on track? The client keeps emailing."),
    ],
}


def ordinal(day: int) -> str:
    return str(day) + ("th" if 11 <= day % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th"))


def supplement_date(rng: random.Random, value: date) -> str:
    """Only formats intake.parse_date_phrase supports, so labels stay deterministic.

    The repeated ordinal entry weights that form; changing the tuple changes every supplement draw.
    """
    month = value.strftime("%B")
    return rng.choice(
        (
            f"{month[:3]} {value.day:02d}",
            f"{month[:3]} {value.day}",
            f"{month[:3]} {ordinal(value.day)}",
            f"{month} {value.day}",
            f"{month[:3]} {ordinal(value.day)}",
            value.isoformat(),
        )
    )


class SupplementBuilder:
    """Draws supplement cases, retrying until the text is new and the tool outcome fits the kind.

    Kept separate from Builder: its draw order fixes the committed supplement files.
    """

    def __init__(self, desk: DispatchDesk, split: str, seed: int, seen: set[str]):
        self.desk, self.split, self.rng, self.seen = desk, split, random.Random(seed), seen
        self.orders = desk.orders
        self.open_orders = [row for row in self.orders if row["status"] == "IN_PROGRESS"]
        pairs = Counter((row["customer"], row["product"]) for row in self.orders)
        self.ambiguous_pairs = sorted(pair for pair, count in pairs.items() if count > 1)

    def text_ok(self, text: str) -> bool:
        if text in self.seen:
            return False
        self.seen.add(text)
        return True

    def preview(self, text: str, request: DispatchInput) -> dict:
        envelope = {"request_id": "GEN", "time": "00:00", "requester": "gen", "text": text}
        return self.desk.preview(envelope, request, ObjectiveWeights())

    def base_fields(self, order: dict, due: date) -> dict:
        return {
            "order_id": order["order_id"],
            "pieces": int(order["pieces"]),
            "product": order["product"],
            "customer": order["customer"],
            "due_date": due.isoformat(),
        }

    def fmt(self, order: dict, due: date) -> dict:
        pieces = int(order["pieces"])
        return {
            "oid": order["order_id"],
            "n": pieces,
            "n_comma": f"{pieces:,}",
            "plural": PLURALS[order["product"]],
            "cust": order["customer"],
            "date": supplement_date(self.rng, due),
        }

    def pick_due(self, order: dict, impossible: bool) -> date:
        recorded = date.fromisoformat(order["due_date"])
        if impossible:
            # Past recorded deadlines, or a few days from the snapshot.
            if recorded < self.desk.as_of and self.rng.random() < 0.5:
                return recorded
            return self.desk.as_of + timedelta(days=self.rng.randint(1, 5))
        if recorded > self.desk.as_of + timedelta(days=8) and self.rng.random() < 0.5:
            return recorded
        return self.desk.as_of + timedelta(days=self.rng.randint(10, 35))

    def complete(self, impossible: bool) -> tuple[dict, str]:
        templates = list(EXTRA_COMPLETE[self.split].items())
        while True:
            name, template = self.rng.choice(templates)
            order = self.rng.choice(self.open_orders)
            due = self.pick_due(order, impossible)
            text = template.format(**self.fmt(order, due))
            fields = self.base_fields(order, due)
            result = self.preview(text, DispatchInput(**fields))
            if result["has_on_time_option"] == impossible or not self.text_ok(text):
                continue
            case = {
                "course_kind": "complete_impossible" if impossible else "complete_meetable",
                "category": CATEGORY["complete_impossible" if impossible else "complete_meetable"],
                "template": name,
                "fields": fields,
                "statuses": [result["status"]],
            }
            if flags := [flag for flag in ("NO_ON_TIME_OPTION", "PAST_DEADLINE") if flag in result["flags"]]:
                case["flags"] = flags
            return case, text

    def constraint(self, slot: int, speaker: str) -> tuple[dict, str]:
        variants = EXTRA_CONSTRAINT[self.split]
        name, shape, suffix = variants[slot % len(variants)]
        while True:
            order = self.rng.choice(self.open_orders)
            due = self.pick_due(order, impossible=False)
            values = self.fmt(order, due)
            fields = self.base_fields(order, due)
            plain = self.preview("", DispatchInput(**fields))
            if not plain["has_on_time_option"]:
                continue
            exclusions, extra = [], {}
            if shape.startswith("exclude"):
                # Exclude the workshop the unconstrained preview would pick, so the constraint matters.
                target = plain["recommendation"]
                values["w"] = self.desk.workshops[target].name
                values["who"] = self.rng.choice(SPEAKERS)
                imposer = speaker if shape == "exclude_speaker" else values["who"]
                exclusions = [{"workshop_id": target, "imposed_by": imposer, "evidence": suffix.format(**values)}]
                extra = {"exclusions": {target: imposer}}
            else:
                fields["preference"] = shape
            text = EXTRA_CONSTRAINT_BASE[self.split].format(**values) + " " + suffix.format(**values)
            result = self.preview(text, DispatchInput(**fields, exclusions=exclusions))
            if result["status"] in ("NO_FEASIBLE_OPTION", "REFUSE_SUGGESTION") or not self.text_ok(text):
                continue
            case = {
                "course_kind": "constraint",
                "category": "exclusion" if exclusions else "preference",
                "template": name,
                "fields": fields,
                "statuses": [result["status"]],
                **extra,
            }
            return case, text

    def ambiguous(self, slot: int) -> tuple[dict, str]:
        name, template, preference = EXTRA_AMBIGUOUS[self.split][slot % 3]
        while True:
            customer, product = self.rng.choice(self.ambiguous_pairs)
            text = template.format(cust=customer, plural=PLURALS[product])
            if not self.text_ok(text):
                continue
            fields = {"order_id": None, "customer": customer, "product": product}
            if preference:
                fields["preference"] = preference
            return {
                "course_kind": "ambiguous",
                "category": CATEGORY["ambiguous"],
                "template": name,
                "fields": fields,
                "statuses": ["CLARIFY"],
            }, text

    def missing(self, slot: int) -> tuple[dict, str]:
        name, need, template = EXTRA_MISSING[self.split][slot % 3]
        while True:
            order = self.rng.choice(self.open_orders)
            text = template.format(oid=order["order_id"], cust=order["customer"], plural=PLURALS[order["product"]])
            if not self.text_ok(text):
                continue
            if need == "quantity":
                fields = {"order_id": None, "customer": order["customer"], "product": order["product"], "pieces": None}
            else:
                fields = {"order_id": order["order_id"], "date_uncertain": True, "due_date": None}
            return {
                "course_kind": "missing_number_or_date",
                "category": CATEGORY["missing_number_or_date"],
                "template": name,
                "fields": fields,
                "statuses": ["CLARIFY"],
                "needs": [need],
            }, text

    def suggestion(self, slot: int) -> tuple[dict, str]:
        name, stated, template = EXTRA_SUGGESTION[self.split][slot % 3]
        while True:
            order = self.rng.choice(self.open_orders)
            batch = {"category": order["category"], "pieces": int(order["pieces"])}
            eligible = {w.workshop_id for w in eligible_workshops(batch, self.desk.workshops)}
            blocked = sorted(set(self.desk.workshops) - eligible)
            if not blocked:
                continue
            workshop = self.rng.choice(blocked)
            text = template.format(
                oid=order["order_id"],
                n=order["pieces"],
                plural=PLURALS[order["product"]],
                w=self.desk.workshops[workshop].name,
            )
            if not self.text_ok(text):
                continue
            fields = {"order_id": order["order_id"], "suggested_workshop": workshop}
            if "pieces" in stated:
                fields["pieces"] = int(order["pieces"])
            if "product" in stated:
                fields["product"] = order["product"]
            return {
                "course_kind": "ineligible_suggestion",
                "category": CATEGORY["ineligible_suggestion"],
                "template": name,
                "fields": fields,
                "statuses": ["REFUSE_SUGGESTION"],
            }, text

    def unanswerable(self, slot: int) -> tuple[dict, str]:
        name, intent, template = EXTRA_UNANSWERABLE[self.split][slot % 3]
        known = {row["order_id"] for row in self.orders}
        customers = sorted({row["customer"] for row in self.orders})
        while True:
            order = self.rng.choice(self.orders)
            bad = next(oid for oid in iter(lambda: f"ORD-{self.rng.randint(121, 999)}", None) if oid not in known)
            customer = self.rng.choice(customers) if intent == "history" else order["customer"]
            text = template.format(cust=customer, month=self.rng.choice(PAST_MONTHS), oid=order["order_id"], bad=bad)
            if not self.text_ok(text):
                continue
            if intent == "history":
                fields = {"order_id": None, "intent": "history", "customer": customer}
            elif intent == "quote":
                fields = {"order_id": order["order_id"], "intent": "quote"}
            else:
                fields = {"order_id": bad, "intent": "status"}
            return {
                "course_kind": "unanswerable",
                "category": CATEGORY["unanswerable"],
                "template": name,
                "fields": fields,
                "statuses": ["DECLINE"],
            }, text

    def build(self, counts: dict[str, int], prefix: str, start: int) -> tuple[list[str], dict]:
        lines, cases = [], {}
        hour, minute = 9, 5
        draws = {
            "complete_meetable": lambda slot, speaker: self.complete(False),
            "complete_impossible": lambda slot, speaker: self.complete(True),
            "constraint": self.constraint,
            "ambiguous": lambda slot, speaker: self.ambiguous(slot),
            "missing_number_or_date": lambda slot, speaker: self.missing(slot),
            "ineligible_suggestion": lambda slot, speaker: self.suggestion(slot),
            "unanswerable": lambda slot, speaker: self.unanswerable(slot),
        }
        for kind in KINDS:
            for slot in range(counts[kind]):
                speaker = self.rng.choice(SPEAKERS)
                case, text = draws[kind](slot, speaker)
                request_id = f"{prefix}{start + len(cases):03d}"
                lines.append(f"{request_id} [{hour:02d}:{minute:02d}] {speaker}: {text}")
                cases[request_id] = case
                minute += 5
                hour, minute = hour + minute // 60, minute % 60
        return lines, cases


def generate_supplements(seed: int, seen: set[str]) -> dict:
    """Draw after the base splits; `seen` holds every supplied and base text, so nothing repeats."""
    desk, sets = DispatchDesk(), {}
    for name, (split, offset, prefix, start, per_kind) in SUPPLEMENTS.items():
        counts = dict(zip(KINDS, per_kind, strict=True))
        lines, cases = SupplementBuilder(desk, split, seed + offset, seen).build(counts, prefix, start)
        sets[name] = {
            "title": f"{split} supplement {prefix}{start:03d}-{prefix}{start + len(cases) - 1:03d}",
            "requests": lines,
            "rubric": {
                "version": VERSION,
                "split": split,
                "seed": seed + offset,
                "status": STATUS,
                "course_kind_counts": counts,
                "cases": cases,
            },
        }
    return sets


def write(sets: dict, output=OUTPUT):
    output.mkdir(parents=True, exist_ok=True)
    for name, payload in sets.items():
        seed = payload["rubric"]["seed"]
        header = f"# {VERSION} {payload['title']}, seed {seed}. Generated by dss5105.eval_sets; do not edit.\n\n"
        (output / f"{name}_requests.txt").write_text(header + "\n".join(payload["requests"]) + "\n", encoding="ascii")
        (output / f"{name}_rubric.json").write_text(
            json.dumps(payload["rubric"], ensure_ascii=True, indent=1) + "\n", encoding="ascii"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    sets = generate(args.seed)
    write(sets)
    for name, payload in sets.items():
        print(f"{name}: {len(payload['rubric']['cases'])} cases -> {OUTPUT.relative_to(ROOT)}/{name}_*")


if __name__ == "__main__":
    main()
