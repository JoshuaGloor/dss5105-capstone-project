"""Generate supplementary train/test chat evaluation cases in the generated-v1 format.

Extends the existing generated-v1 split (TR001-TR070, seed 5105) with:
  - 70 more train cases (TR071-TR140), 10 per course kind, reusing the train templates
  - 30 more test cases (TE071-TE100), in the course inbox mix (7/3/6/4/3/4/3), using
    test templates whose wording never appears in train

Fields are labelled by construction. States and flags for complete and constraint cases
come from the deterministic DispatchDesk preview, exactly as in the original split.
Labels are generated, not human gold.

    uv run python scripts/extend_eval_sets.py [--avoid path/to/existing_requests.txt ...]
"""

import argparse
import json
import random
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput
from dss5105.harness import eligible_workshops

OUT = ROOT / "examples" / "eval_sets"
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
MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
PAST_MONTHS = ("October", "November", "December", "January", "February", "March")
KINDS = (
    ("complete_meetable", "complete"),
    ("complete_impossible", "deadline_exception"),
    ("constraint", None),
    ("ambiguous", "clarification"),
    ("missing_number_or_date", "clarification"),
    ("ineligible_suggestion", "refusal"),
    ("unanswerable", "missing_data"),
)

# Each split has its own phrasing. Test templates never reuse train wording.
COMPLETE = {
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
CONSTRAINT = {
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
CONSTRAINT_BASE = {
    "train": "{oid} - {n} {plural} for {cust}, due {date}.",
    "test": "{oid}: {n} {plural} for {cust}, due {date}.",
}
AMBIGUOUS = {
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
# kind: "quantity" (customer + product, no number) or "deadline" (order ID, revised date unknown)
MISSING = {
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
# fields: which optional fields the message states (pieces, product)
SUGGESTION = {
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
UNANSWERABLE = {
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


def date_phrase(rng: random.Random, value: date) -> str:
    """Only formats intake.parse_date_phrase supports, so labels stay deterministic."""
    month = MONTHS[value.month - 1]
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


class Builder:
    def __init__(self, split: str, seed: int, avoid: set[str]):
        self.split, self.rng, self.avoid = split, random.Random(seed), avoid
        self.desk = DispatchDesk()
        self.orders = self.desk.orders
        self.open_orders = [row for row in self.orders if row["status"] == "IN_PROGRESS"]
        self.seen = set(avoid)
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
            "date": date_phrase(self.rng, due),
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

    def complete(self, impossible: bool) -> dict:
        templates = list(COMPLETE[self.split].items())
        while True:
            name, template = self.rng.choice(templates)
            order = self.rng.choice(self.open_orders)
            due = self.pick_due(order, impossible)
            values = self.fmt(order, due)
            text = template.format(**values)
            fields = self.base_fields(order, due)
            result = self.preview(text, DispatchInput(**fields))
            if result["has_on_time_option"] == impossible or not self.text_ok(text):
                continue
            case = {
                "course_kind": "complete_impossible" if impossible else "complete_meetable",
                "category": "deadline_exception" if impossible else "complete",
                "template": name,
                "fields": fields,
                "statuses": [result["status"]],
            }
            flags = [flag for flag in ("NO_ON_TIME_OPTION", "PAST_DEADLINE") if flag in result["flags"]]
            if flags:
                case["flags"] = flags
            return case, text

    def constraint(self, slot: int, speaker: str) -> tuple[dict, str]:
        name, shape, suffix = CONSTRAINT[self.split][slot % len(CONSTRAINT[self.split])]
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
                evidence = suffix.format(**values)
                exclusions = [{"workshop_id": target, "imposed_by": imposer, "evidence": evidence}]
                extra = {"exclusions": {target: imposer}}
            else:
                fields["preference"] = shape
            text = CONSTRAINT_BASE[self.split].format(**values) + " " + suffix.format(**values)
            request = {key: value for key, value in fields.items()}
            result = self.preview(text, DispatchInput(**request, exclusions=exclusions))
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
        name, template, preference = AMBIGUOUS[self.split][slot % 3]
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
                "category": "clarification",
                "template": name,
                "fields": fields,
                "statuses": ["CLARIFY"],
            }, text

    def missing(self, slot: int) -> tuple[dict, str]:
        name, need, template = MISSING[self.split][slot % 3]
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
                "category": "clarification",
                "template": name,
                "fields": fields,
                "statuses": ["CLARIFY"],
                "needs": [need],
            }, text

    def suggestion(self, slot: int) -> tuple[dict, str]:
        name, stated, template = SUGGESTION[self.split][slot % 3]
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
                "category": "refusal",
                "template": name,
                "fields": fields,
                "statuses": ["REFUSE_SUGGESTION"],
            }, text

    def unanswerable(self, slot: int) -> tuple[dict, str]:
        name, intent, template = UNANSWERABLE[self.split][slot % 3]
        known = {row["order_id"] for row in self.orders}
        customers = sorted({row["customer"] for row in self.orders})
        while True:
            order = self.rng.choice(self.orders)
            bad = next(oid for oid in iter(lambda: f"ORD-{self.rng.randint(121, 999)}", None) if oid not in known)
            customer = self.rng.choice(customers) if intent == "history" else order["customer"]
            text = template.format(
                cust=customer,
                month=self.rng.choice(PAST_MONTHS),
                oid=order["order_id"],
                bad=bad,
            )
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
                "category": "missing_data",
                "template": name,
                "fields": fields,
                "statuses": ["DECLINE"],
            }, text

    def build(self, counts: dict[str, int], prefix: str, start: int, clock: str) -> tuple[list[str], dict]:
        lines, cases = [], {}
        hour, minute = map(int, clock.split(":"))
        number = start
        for kind, _ in KINDS:
            for slot in range(counts[kind]):
                speaker = self.rng.choice(SPEAKERS)
                if kind in ("complete_meetable", "complete_impossible"):
                    case, text = self.complete(kind == "complete_impossible")
                elif kind == "constraint":
                    case, text = self.constraint(slot, speaker)
                else:
                    case, text = getattr(
                        self,
                        {
                            "ambiguous": "ambiguous",
                            "missing_number_or_date": "missing",
                            "ineligible_suggestion": "suggestion",
                            "unanswerable": "unanswerable",
                        }[kind],
                    )(slot)
                request_id = f"{prefix}{number:03d}"
                lines.append(f"{request_id} [{hour:02d}:{minute:02d}] {speaker}: {text}")
                cases[request_id] = case
                number += 1
                minute += 5
                hour, minute = hour + minute // 60, minute % 60
        return lines, cases


def write(split: str, seed: int, prefix: str, start: int, counts: dict, avoid: set[str], tag: str):
    builder = Builder(split, seed, avoid)
    lines, cases = builder.build(counts, prefix, start, "09:05")
    first, last = f"{prefix}{start:03d}", f"{prefix}{start + len(lines) - 1:03d}"
    header = (
        f"# generated-v1 {split} supplement {first}-{last}, seed {seed}. "
        "Generated by scripts/extend_eval_sets.py; do not edit.\n\n"
    )
    (OUT / f"{tag}_requests.txt").write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
    rubric = {
        "version": "generated-v1",
        "split": split,
        "seed": seed,
        "status": "Generated: fields are labelled by construction, states by the deterministic preview. "
        "Not human gold.",
        "course_kind_counts": {kind: counts[kind] for kind, _ in KINDS},
        "cases": cases,
    }
    (OUT / f"{tag}_rubric.json").write_text(json.dumps(rubric, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    statuses = Counter(case["statuses"][0] for case in cases.values())
    print(f"{tag}: {len(cases)} cases {first}-{last}; states {dict(statuses)}")
    return builder.seen


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--avoid", type=Path, nargs="*", default=[], help="Existing inbox files to never duplicate")
    args = parser.parse_args()
    avoid = set()
    for path in args.avoid:
        if not path.is_file():
            print(f"Warning: {path} not found; duplicates against it are not checked.")
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#") and ": " in line:
                avoid.add(line.split(": ", 1)[1])
    OUT.mkdir(parents=True, exist_ok=True)
    train_counts = {kind: 10 for kind, _ in KINDS}
    # The course inbox mix: 7 meetable, 3 impossible, 6 constraint, 4 ambiguous, 3 missing, 4 suggestion, 3 none.
    test_counts = dict(zip((kind for kind, _ in KINDS), (7, 3, 6, 4, 3, 4, 3), strict=True))
    seen = write("train", 5106, "TR", 71, train_counts, avoid, "train_extra")
    write("test", 5107, "TE", 71, test_counts, seen, "test_extra")


if __name__ == "__main__":
    main()
