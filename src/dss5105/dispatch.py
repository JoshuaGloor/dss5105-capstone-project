"""Read-only dispatch previews from explicit structured inputs, never guessed chat."""

import argparse
import csv
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timedelta
from math import ceil, isfinite
from pathlib import Path

from dss5105.allocator import (
    ObjectiveWeights,
    ScoreScales,
    assess_split,
    earliest_finish,
    estimate_delivery,
    rank_candidates,
)
from dss5105.evaluate import PRESETS
from dss5105.harness import HARNESS_PATH, Simulator, cheapest, eligible_workshops, greedy_biggest, random_choice

ROOT = HARNESS_PATH.parents[2]
DATA = ROOT / "track2" / "data"
AS_OF = date(2026, 4, 1)
PREFERENCES = {
    "fastest": ObjectiveWeights(lateness=1),
    "lowest_defects": ObjectiveWeights(lateness=0, defects=1),
    "cheapest_on_time": ObjectiveWeights(lateness=0, cost=1),
}
BASELINES = {
    "earliest_finish": ("Earliest finish (short heuristic)", earliest_finish),
    "cheapest": ("Cheapest eligible", cheapest),
    "greedy_biggest": ("Biggest capacity", greedy_biggest),
    "random_choice": ("Random eligible (seeded)", random_choice),
}


@dataclass(frozen=True)
class DispatchInput:
    order_id: str | None = None
    customer: str | None = None
    product: str | None = None
    intent: str = "allocate"
    pieces: int | None = None
    due_date: str | None = None
    date_uncertain: bool = False
    date_kind: str = "delivery"
    suggested_workshop: str | None = None
    exclusions: list[dict[str, str]] = field(default_factory=list)
    preference: str = "configured"
    split_requested: bool = False
    clarification: str | None = None

    def __post_init__(self):
        for key in ("order_id", "customer", "product", "due_date", "suggested_workshop", "clarification"):
            value = getattr(self, key)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{key} must be a nonempty string or null")
        if self.pieces is not None and (type(self.pieces) is not int or self.pieces <= 0):
            raise ValueError("pieces must be a positive integer")
        for key in ("date_uncertain", "split_requested"):
            if type(getattr(self, key)) is not bool:
                raise ValueError(f"{key} must be a boolean")
        for key, choices in {
            "intent": ("allocate", "quote", "history", "status"),
            "date_kind": ("delivery", "shipping"),
            "preference": ("configured", *PREFERENCES),
        }.items():
            if getattr(self, key) not in choices:
                raise ValueError(f"Invalid {key}")
        if self.due_date is not None:
            date.fromisoformat(self.due_date)
        if not isinstance(self.exclusions, list):
            raise ValueError("exclusions must be a list")
        for constraint in self.exclusions:
            if not isinstance(constraint, dict) or set(constraint) != {"workshop_id", "imposed_by", "evidence"}:
                raise ValueError("Each exclusion needs workshop_id, imposed_by, and evidence")
            if any(not isinstance(value, str) or not value.strip() for value in constraint.values()):
                raise ValueError("Exclusion fields must be nonempty strings")
        if len({item["workshop_id"] for item in self.exclusions}) != len(self.exclusions):
            raise ValueError("Duplicate workshop exclusions must be consolidated with their provenance")


def ship_date_is_due_date(request: DispatchInput, order: dict) -> bool:
    """A stated ship date needs no question when it is the order's recorded due date."""
    return request.date_kind == "shipping" and request.due_date == order["due_date"]


def read_inbox(path: Path = DATA / "dispatch_requests.txt") -> list[dict]:
    """Parse envelopes only; message interpretation is a separate boundary."""
    requests = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Z]+\d+) \[([^]]+)\] ([^:]+): (.+)", line)
        if not match:
            raise ValueError(f"Invalid inbox envelope: {line}")
        requests.append(dict(zip(("request_id", "time", "requester", "text"), match.groups(), strict=True)))
    if len({request["request_id"] for request in requests}) != len(requests):
        raise ValueError("Duplicate request IDs")
    return requests


class DispatchDesk:
    """Independent hypothetical previews on a reproducible course-data snapshot."""

    def __init__(self):
        with (DATA / "orders.csv").open(encoding="utf-8", newline="") as file:
            self.orders = list(csv.DictReader(file))
        self.workshops = Simulator().workshops
        self.queues = {key: workshop.queue0 for key, workshop in self.workshops.items()}
        self.as_of = AS_OF
        self.source_hashes = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (DATA / "orders.csv", DATA / "workshops.csv", DATA / "dispatch_requests.txt", HARNESS_PATH)
        }

    def display_fields(self, estimate, score=None) -> dict:
        """Single source of the formatted strings shown to a user, for every policy."""
        eta = datetime.combine(self.as_of, time()) + timedelta(minutes=ceil(estimate.expected_turnaround_days * 1440))
        values = {
            "eta": eta.isoformat(sep=" ", timespec="minutes"),
            "turnaround": f"{estimate.expected_turnaround_days:.2f} days",
            "lateness": f"{estimate.lateness_days:.2f} days",
            "cost": f"{estimate.cost:,.2f}",
            "defects": f"{estimate.defect_risk:.1%}",
            "queue": f"{estimate.queue_days:.2f} days",
            "processing": f"{estimate.process_days:.2f} days",
            "transport": f"{estimate.transport_days:.2f} days",
            "expected_rework": f"{estimate.expected_turnaround_days - estimate.turnaround_days:.2f} days",
        }
        if score is not None:
            values["score"] = f"{score:.4f}"
        return values

    def split_fields(self, batch: dict, permitted: dict, earliest: dict) -> dict | None:
        """Tool-authored two-workshop split evidence; never an allocation."""
        plan = assess_split(batch, permitted, self.queues)
        if plan is None:
            return None
        slowest = max(plan.parts, key=lambda estimate: estimate.expected_turnaround_days)
        saved = earliest["estimate"]["expected_turnaround_days"] - plan.expected_turnaround_days
        parts = [
            {
                "workshop_id": estimate.workshop_id,
                "name": self.workshops[estimate.workshop_id].name,
                "pieces": pieces,
                "estimate": asdict(estimate),
                "display": self.display_fields(estimate),
            }
            for estimate, pieces in zip(plan.parts, plan.pieces, strict=True)
        ]
        display = {
            **self.display_fields(slowest),
            "cost": f"{plan.cost:,.2f}",
            "days_saved": f"{saved:.2f} days",
        }
        meets = plan.lateness_days == 0
        pieces = " + ".join(f"{part['name']} {part['pieces']} pieces" for part in parts)
        timing = "meets the deadline" if meets else f"{display['lateness']} late"
        if saved > 0:
            comparison = f"{display['days_saved']} sooner than the earliest whole batch"
        else:
            comparison = "no sooner than the earliest whole batch"
        return {
            "parts": parts,
            "expected_turnaround_days": plan.expected_turnaround_days,
            "lateness_days": plan.lateness_days,
            "meets_deadline": meets,
            "cost": plan.cost,
            "days_saved": saved,
            "display": display,
            "summary": (
                f"Two-workshop split: {pieces}, estimated back {display['eta']} ({timing}; {comparison}). "
                f"Total cost {display['cost']}. Splits are outside the course simulator and need dispatcher approval."
            ),
        }

    def resolve_order(self, request: DispatchInput) -> dict:
        if request.order_id is not None:
            matches = [row for row in self.orders if row["order_id"] == request.order_id]
        elif request.customer is not None or request.product is not None:
            matches = [
                row
                for row in self.orders
                if all(
                    value is None or row[key].casefold() == value.casefold()
                    for key, value in (("customer", request.customer), ("product", request.product))
                )
            ]
        else:
            return {"status": "AMBIGUOUS", "matches": []}
        status = "NOT_FOUND" if not matches else "RESOLVED" if len(matches) == 1 else "AMBIGUOUS"
        return {"status": status, "matches": matches}

    def preview(self, envelope: dict, request: DispatchInput, weights: ObjectiveWeights) -> dict:
        if set(self.queues) != set(self.workshops) or any(
            isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value) or value < 0
            for value in self.queues.values()
        ):
            raise ValueError("A complete finite nonnegative queue snapshot is required")
        for workshop_id in [request.suggested_workshop, *(item["workshop_id"] for item in request.exclusions)]:
            if workshop_id is not None and workshop_id not in self.workshops:
                raise ValueError(f"Unknown workshop: {workshop_id}")
        for constraint in request.exclusions:
            if constraint["evidence"] not in envelope["text"]:
                raise ValueError("Exclusion evidence must occur in the original message")
        effective = PREFERENCES.get(request.preference, weights)
        snapshot = {
            "as_of": self.as_of.isoformat(),
            "queues": self.queues.copy(),
            "sources": self.source_hashes.copy(),
        }
        snapshot_id = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
        result = {
            "request": envelope,
            "input": asdict(request),
            "snapshot": {**snapshot, "id": snapshot_id},
            "configured_weights": asdict(weights),
            "effective_weights": asdict(effective),
            "scales": asdict(ScoreScales()),
            "candidates": [],
            "baselines": [],
            "excluded": [],
            "flags": [],
            "recommendation": None,
            "alternative": None,
            "earliest_option": None,
            "split_option": None,
            "review_options": [],
            "commit_allowed": False,
            "tool_sources": {
                name: hashlib.sha256((ROOT / "src" / "dss5105" / name).read_bytes()).hexdigest()
                for name in ("allocator.py", "dispatch.py")
            },
            "assumption": (
                f"Independent preview using workshops.csv queues as the {self.as_of.isoformat()} inbox snapshot. "
                "Queues are used directly, not derived from the simulator replay."
            ),
        }

        def finish(status, message):
            result.update(status=status, message=message)
            return result

        if request.intent in ("quote", "history"):
            return finish(
                "DECLINE", "The supplied data contains neither customer quotes nor past workshop allocations."
            )
        resolution = self.resolve_order(request)
        result["resolution"] = resolution
        if request.intent == "status" and resolution["status"] == "NOT_FOUND":
            return finish(
                "DECLINE",
                "No matching order is recorded in orders.csv, so there is no status or movement to report. "
                "Please check the order reference.",
            )
        if resolution["status"] != "RESOLVED":
            message = (
                "No matching order is recorded. Please check the order reference."
                if resolution["status"] == "NOT_FOUND"
                else "Which order do you mean? Please confirm its order ID."
            )
            if request.clarification:
                message += " " + request.clarification
            return finish("CLARIFY", message)
        order = resolution["matches"][0]
        result["order"] = order
        if request.intent == "status":
            return finish(
                "RECORDED_STATUS", "Recorded CSV status is available below; live movement data is unavailable."
            )
        issues = []
        for key in ("customer", "product"):
            value = getattr(request, key)
            if value is not None and value.casefold() != order[key].casefold():
                issues.append(f"Confirm the {key}; the message conflicts with the source order.")
        if request.pieces is not None and request.pieces != int(order["pieces"]):
            issues.append("Confirm a quantity amendment; the message conflicts with the source order.")
        if request.date_uncertain:
            issues.append("Confirm the revised delivery deadline before ranking workshops.")
        if request.date_kind == "shipping" and not ship_date_is_due_date(request, order):
            issues.append(
                "Confirm whether the stated ship date is dispatch or delivery; it is not the recorded due date "
                "and the tool estimates delivery."
            )
        if request.clarification:
            issues.append(request.clarification)
        if issues:
            return finish("CLARIFY", " ".join(issues))
        due = date.fromisoformat(request.due_date or order["due_date"])
        batch = {
            "order_id": order["order_id"],
            "category": order["category"],
            "pieces": int(order["pieces"]),
            "sent_date": self.as_of,
            "due_date": due,
        }
        result["batch"] = {**batch, "sent_date": self.as_of.isoformat(), "due_date": due.isoformat()}
        result["deadline_source"] = "request" if request.due_date else "orders.csv"
        if ship_date_is_due_date(request, order):
            result["deadline_note"] = (
                "The stated ship date equals the recorded due date in orders.csv, so it is used as the "
                "delivery deadline."
            )
        eligible = {w.workshop_id for w in eligible_workshops(batch, self.workshops)}
        constraints = {item["workshop_id"]: item for item in request.exclusions}
        permitted = {key: w for key, w in self.workshops.items() if key in eligible and key not in constraints}
        for key, workshop in self.workshops.items():
            reasons = []
            if key not in eligible:
                # Diagnostics explain the helper's decision; membership comes only from the helper above.
                if workshop.status != "ACTIVE":
                    reasons.append(f"Status is {workshop.status}.")
                if batch["category"] not in workshop.makes:
                    reasons.append(f"Cannot make {batch['category']}.")
                if workshop.max_batch is not None and batch["pieces"] > workshop.max_batch:
                    reasons.append(f"Batch exceeds the {workshop.max_batch}-piece limit.")
                if not reasons:
                    reasons.append("Excluded by the course eligibility helper.")
            if key in constraints:
                reasons.append(f"Excluded by {constraints[key]['imposed_by']}: {constraints[key]['evidence']}")
            if reasons:
                result["excluded"].append({"workshop_id": key, "name": workshop.name, "reasons": reasons})
        for candidate in rank_candidates(batch, permitted, self.queues, effective):
            estimate = candidate.estimate
            result["candidates"].append(
                {
                    **asdict(candidate),
                    "name": self.workshops[estimate.workshop_id].name,
                    "meets_deadline": estimate.lateness_days == 0,
                    "display": self.display_fields(estimate, candidate.score),
                }
            )
        if eligible:
            for policy, (label, choose) in BASELINES.items():
                workshop_id = choose(batch, self.workshops, self.queues)
                reference = estimate_delivery(batch, self.workshops[workshop_id], self.queues)
                result["baselines"].append(
                    {
                        "policy": policy,
                        "label": label,
                        "workshop_id": workshop_id,
                        "name": self.workshops[workshop_id].name,
                        "meets_deadline": reference.lateness_days == 0,
                        "respects_exclusions": workshop_id not in constraints,
                        "estimate": asdict(reference),
                        "display": self.display_fields(reference),
                    }
                )
        candidates = result["candidates"]
        if candidates:
            result["earliest_option"] = min(
                candidates,
                key=lambda row: (row["estimate"]["expected_turnaround_days"], row["estimate"]["workshop_id"]),
            )
        selectable = candidates
        if request.preference == "cheapest_on_time":
            selectable = [row for row in candidates if row["meets_deadline"]]
        result["has_on_time_option"] = any(row["meets_deadline"] for row in candidates)
        if due < self.as_of:
            result["flags"].append("PAST_DEADLINE")
        if candidates and (request.split_requested or not result["has_on_time_option"]):
            result["split_option"] = self.split_fields(batch, permitted, result["earliest_option"])
        split = result["split_option"]
        if not result["has_on_time_option"]:
            result["flags"].append("NO_ON_TIME_OPTION")
            earliest = result["earliest_option"]
            if earliest:
                result["review_options"].append(
                    f"No permitted workshop meets the deadline. Earliest estimated whole-batch delivery: "
                    f"{earliest['name']} on {earliest['display']['eta']}, "
                    f"{earliest['display']['lateness']} late. Ask the customer to approve a revised deadline."
                )
        if split:
            result["review_options"].append(split["summary"])
        elif request.split_requested:
            result["review_options"].append("No two-workshop split is possible among the permitted workshops.")
        if request.split_requested:
            result["flags"].append("SPLIT_REVIEW")
        if not result["has_on_time_option"]:
            result["review_options"].append(
                "Escalate to the dispatcher for other capacity or a revised request before allocating."
            )
        suggestion = request.suggested_workshop
        if suggestion and suggestion not in permitted:
            result["flags"].append("SUGGESTION_REFUSED")
            result["alternative"] = selectable[0]["estimate"]["workshop_id"] if selectable else None
            return finish(
                "REFUSE_SUGGESTION", "Requested workshop cannot take this batch. Review exclusions and alternatives."
            )
        if not selectable:
            return finish(
                "NO_FEASIBLE_OPTION", "No workshop satisfies the hard constraints. Clarify a change or escalate."
            )
        chosen = next((row for row in selectable if row["estimate"]["workshop_id"] == suggestion), selectable[0])
        if suggestion and not any(row["estimate"]["workshop_id"] == suggestion for row in selectable):
            result["alternative"] = selectable[0]["estimate"]["workshop_id"]
            return finish(
                "REFUSE_SUGGESTION", "Requested workshop fails the hard delivery constraint. Review an alternative."
            )
        if not chosen["meets_deadline"]:
            result["flags"].append("SELECTED_OPTION_LATE")
        result["recommendation"] = chosen["estimate"]["workshop_id"]
        if request.split_requested or not chosen["meets_deadline"]:
            shown = "Whole-batch and split estimates" if split else "Whole-batch option"
            return finish(
                "NEEDS_REVIEW",
                f"{shown} shown for discussion. Agree a deadline or split plan before allocation; "
                "split plans cannot be saved yet.",
            )
        return finish(
            "RECOMMEND", "Eligible whole-batch preview ready for review. Delivery is an estimate, not a guarantee."
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", help="Inbox ID; uses a draft structured fixture unless --input is supplied")
    parser.add_argument("--input", type=Path, help="Reviewed structured JSON for the chosen inbox request")
    parser.add_argument("--preset", choices=PRESETS, default="lateness")
    parser.add_argument("--weights", type=Path, help="JSON object of lateness/defects/cost weights")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    inbox = read_inbox()
    if not args.request:
        if args.input or args.weights:
            parser.error("--input and --weights require --request")
        output = {"as_of": AS_OF.isoformat(), "requests": inbox}
    else:
        envelope = next((item for item in inbox if item["request_id"] == args.request), None)
        if envelope is None:
            parser.error("Unknown request ID")
        try:
            if args.input:
                payload = json.loads(args.input.read_text())
            else:
                payload = json.loads((ROOT / "examples" / "dispatch_inputs.json").read_text())[args.request]
            weights = (
                ObjectiveWeights(**json.loads(args.weights.read_text())) if args.weights else PRESETS[args.preset]
            )
            output = DispatchDesk().preview(envelope, DispatchInput(**payload), weights)
            output["interpretation_source"] = str(args.input) if args.input else "draft development fixture; not NLP"
        except (ValueError, TypeError, KeyError, OSError) as error:
            parser.error(str(error))
    serialized = json.dumps(output, indent=2, ensure_ascii=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized)
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
