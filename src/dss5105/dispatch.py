"""Read-only dispatch previews from explicit structured inputs, never guessed chat."""

import argparse
import csv
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field, replace
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
from dss5105.evaluate import DEFAULT_PRESET, PRESETS
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
RULE_FIELDS = {"rule_id", "workshop_id", "customer", "imposed_by", "evidence", "created_on"}
CAPACITY_QUESTIONS = {
    "product": "Which product is it? Name it as orders do, for example hoodies or scarves.",
    "quantity": "Please confirm the quantity using digits.",
    "deadline": "Please confirm the delivery deadline using an explicit date, preferably YYYY-MM-DD.",
}
# Metric, its formatting as shown in display_fields (defect risk in percent), and its superlative.
SHOWN = {
    "expected_turnaround_days": ("{:.2f}", 1, "Earliest delivery"),
    "cost": ("{:,.2f}", 1, "Lowest cost"),
    "defect_risk": ("{:.1f}", 100, "Lowest defect risk"),
}


def _shown(estimate: dict, key: str) -> float:
    """The value exactly as the user sees it, so differences agree with the table."""
    text, scale, _ = SHOWN[key]
    return float(text.format(estimate[key] * scale).replace(",", ""))


def _difference(value: float, text: str, more: str, less: str, same: str) -> str:
    if value == 0:
        return same
    return f"{text.format(abs(value))} {more if value > 0 else less}"


def decision_basis(result: dict) -> dict | None:
    """Why the chosen workshop: tool-computed comparisons with the other permitted candidates.

    Explains a ranking that has already happened; it never chooses or reorders anything.
    Every difference is taken between displayed values, so it matches the comparison table.
    """
    candidates = result["candidates"]
    chosen_id = result["recommendation"] or result["alternative"]
    chosen = next((row for row in candidates if row["estimate"]["workshop_id"] == chosen_id), None)
    if chosen is None:
        return None
    mine = chosen["estimate"]
    on_time = [row for row in candidates if row["meets_deadline"]]
    pools = [(candidates, f"of the {len(candidates)} permitted workshops")]
    if chosen["meets_deadline"] and 1 < len(on_time) < len(candidates):
        pools.append((on_time, f"of the {len(on_time)} that meet the deadline"))
    reasons = ["The only permitted workshop for this batch."] if len(candidates) == 1 else []
    for pool, scope in pools if len(candidates) > 1 else ():
        found = False
        for key, (_, _, label) in SHOWN.items():
            best = min(_shown(row["estimate"], key) for row in pool)
            if _shown(mine, key) == best:
                tied = [row["name"] for row in pool if row is not chosen and _shown(row["estimate"], key) == best]
                shared = f", shared with {', '.join(tied)}" if tied else ""
                reasons.append(f"{label} {scope}{shared}.")
                found = True
        if found:
            break
    reservation = result.get("reservation_note")
    if reservation and chosen is candidates[0] and reservation["workshop_id"] == chosen_id:
        reasons.append(reservation["text"])
    slack = mine["available_days"] - _shown(mine, "expected_turnaround_days")
    if chosen["meets_deadline"]:
        reasons.append(f"Expected {slack:.2f} days before the deadline.")
    else:
        reasons.append(f"Expected {mine['lateness_days']:.2f} days after the deadline.")
    basis = {"workshop_id": chosen_id, "permitted": len(candidates), "slack_days": slack, "compared_with": None}
    other = next((row for row in candidates if row is not chosen), None)
    if other is not None:
        theirs = other["estimate"]
        delivery, cost, defects = (
            round(_shown(theirs, key) - _shown(mine, key), 2)
            for key in ("expected_turnaround_days", "cost", "defect_risk")
        )
        parts = [
            _difference(delivery, "{:.2f}", "days slower", "days faster", "same delivery"),
            _difference(cost, "{:,.2f}", "more in cost", "less in cost", "same cost"),
            _difference(defects, "{:.1f}", "points more defect risk", "points less defect risk", "same defect risk"),
        ]
        if chosen["meets_deadline"] != other["meets_deadline"]:
            parts.append("meets the deadline" if other["meets_deadline"] else "misses the deadline")
        rank = "Next ranked" if candidates[0] is chosen else "Ranked first"
        reasons.append(f"{rank}: {other['name']}, " + ", ".join(parts) + ".")
        basis.update(
            compared_with=theirs["workshop_id"],
            delivery_days_difference=delivery,
            cost_difference=cost,
            defect_points_difference=defects,
        )
    return {**basis, "reasons": reasons}


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
            "intent": ("allocate", "quote", "history", "status", "capacity"),
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


@dataclass(frozen=True)
class WorkshopQuery:
    category: str | None = None
    status: str | None = None
    pieces: int | None = None
    due_date: str | None = None

    def __post_init__(self):
        for name in ("category", "status"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be a nonempty string or null")
        if self.pieces is not None:
            if type(self.pieces) is not int or self.pieces <= 0:
                raise ValueError("pieces must be a positive integer")
            if self.category is None:
                raise ValueError("A batch quantity requires a product category")
        if self.due_date is not None:
            if not isinstance(self.due_date, str) or self.pieces is None:
                raise ValueError("A delivery deadline requires a batch quantity")
            date.fromisoformat(self.due_date)


@dataclass(frozen=True)
class LoadScenario:
    workshop_id: str
    category: str
    pieces: int
    additional_pieces: int
    due_date: str

    def __post_init__(self):
        if not isinstance(self.workshop_id, str) or not self.workshop_id.strip():
            raise ValueError("A workshop ID is required")
        if self.category is None or self.pieces is None or self.due_date is None:
            raise ValueError("Category, batch quantity and delivery deadline are required")
        WorkshopQuery(category=self.category, pieces=self.pieces, due_date=self.due_date)
        if type(self.additional_pieces) is not int or self.additional_pieces <= 0:
            raise ValueError("additional_pieces must be a positive integer")


def ship_date_is_due_date(request: DispatchInput, order: dict) -> bool:
    """A stated ship date needs no question when it is the order's recorded due date."""
    return request.date_kind == "shipping" and request.due_date == order["due_date"]


def read_inbox(path: Path = DATA / "dispatch_requests.txt") -> list[dict]:
    """Parse envelopes only; message interpretation is a separate boundary."""
    requests = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"(R\d+) \[([^]]+)\] ([^:]+): (.+)", line)
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
        # Pieces already allocated per workshop in this plan; fairness reads it. Empty for
        # independent previews, so fairness has no effect there.
        self.ledger: dict[str, float] = {}
        self.as_of = AS_OF
        self.source_hashes = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (DATA / "orders.csv", DATA / "workshops.csv", DATA / "dispatch_requests.txt", HARNESS_PATH)
        }

    def snapshot(self) -> dict:
        """Validate and identify the exact state used by every read-only tool."""
        if set(self.queues) != set(self.workshops) or any(
            isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value) or value < 0
            for value in self.queues.values()
        ):
            raise ValueError("A complete finite nonnegative queue snapshot is required")
        snapshot = {
            "as_of": self.as_of.isoformat(),
            "queues": self.queues.copy(),
            "sources": self.source_hashes.copy(),
        }
        return {**snapshot, "id": hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()}

    @staticmethod
    def eligibility_reasons(batch: dict, workshop) -> list[str]:
        """Explain helper exclusions; the course helper alone decides membership."""
        reasons = []
        if workshop.status != "ACTIVE":
            reasons.append(f"Status is {workshop.status}.")
        if batch["category"] not in workshop.makes:
            reasons.append(f"Cannot make {batch['category']}.")
        if workshop.max_batch is not None and batch["pieces"] > workshop.max_batch:
            reasons.append(f"Batch exceeds the {workshop.max_batch}-piece limit.")
        return reasons or ["Excluded by the course eligibility helper."]

    def query_register(self, query: WorkshopQuery) -> dict:
        snapshot = self.snapshot()
        if query.category is not None and query.category not in {c for w in self.workshops.values() for c in w.makes}:
            raise ValueError("Unknown product category")
        if query.status is not None and query.status not in {w.status for w in self.workshops.values()}:
            raise ValueError("Unknown workshop status")
        batch = None
        eligible = None
        if query.pieces is not None:
            batch = {
                "order_id": "WORKSHOP_QUERY",
                "category": query.category,
                "pieces": query.pieces,
                "sent_date": self.as_of,
                "due_date": date.fromisoformat(query.due_date) if query.due_date else self.as_of,
            }
            eligible = {w.workshop_id for w in eligible_workshops(batch, self.workshops)}
        matches = []
        for key, workshop in sorted(self.workshops.items()):
            if query.category is not None and query.category not in workshop.makes:
                continue
            if query.status is not None and query.status != workshop.status:
                continue
            estimate = estimate_delivery(batch, workshop, self.queues) if query.due_date and key in eligible else None
            matches.append(
                {
                    "workshop_id": key,
                    "name": workshop.name,
                    "status": workshop.status,
                    "makes": sorted(workshop.makes),
                    "capacity": workshop.capacity,
                    "max_batch": workshop.max_batch,
                    "queue_days": self.queues[key],
                    "eligible": key in eligible if eligible is not None else None,
                    "reasons": self.eligibility_reasons(batch, workshop)
                    if eligible is not None and key not in eligible
                    else [],
                    "estimate": asdict(estimate) if estimate else None,
                    "meets_deadline": estimate.lateness_days == 0 if estimate else None,
                    "display": {
                        "capacity": f"{workshop.capacity:,} pieces/day",
                        "max_batch": f"{workshop.max_batch:,} pieces"
                        if workshop.max_batch is not None
                        else "No batch cap",
                        "queue": f"{self.queues[key]:.2f} days",
                        **(self.display_fields(estimate) if estimate else {}),
                    },
                }
            )
        return {
            "status": "MATCHES" if matches else "NO_MATCHES",
            "query": asdict(query),
            "snapshot": snapshot,
            "tool_sources": {
                name: hashlib.sha256((ROOT / "src" / "dss5105" / name).read_bytes()).hexdigest()
                for name in ("allocator.py", "dispatch.py")
            },
            "matches": matches,
            "display": {"pieces": f"{query.pieces:,} pieces" if query.pieces is not None else "No batch specified"},
            "assumption": "Current queue snapshot. Delivery includes expected rework and is an estimate.",
        }

    def probe_load(self, scenario: LoadScenario) -> dict:
        register = self.query_register(
            WorkshopQuery(category=scenario.category, pieces=scenario.pieces, due_date=scenario.due_date)
        )
        if scenario.workshop_id not in self.workshops:
            raise ValueError("Unknown workshop ID")
        batch = {
            "order_id": "LOAD_PROBE",
            "category": scenario.category,
            "pieces": scenario.pieces,
            "sent_date": self.as_of,
            "due_date": date.fromisoformat(scenario.due_date),
        }
        extra = {**batch, "pieces": scenario.additional_pieces}
        workshop = self.workshops[scenario.workshop_id]
        result = {
            "scenario": asdict(scenario),
            "snapshot": register["snapshot"],
            "tool_sources": register["tool_sources"],
            "workshop_name": workshop.name,
            "status": "UNSUPPORTED",
            "reasons": [],
            "before": None,
            "after": None,
            "candidates_after": [],
            "fastest_alternative": None,
            "assumption": "Additional work waits ahead of the reference batch at the same planning date. "
            "Expected rework occupies capacity; transport does not. No planning queues change.",
        }
        for label, work in (("Reference batch", batch), ("Additional batch", extra)):
            if scenario.workshop_id not in {w.workshop_id for w in eligible_workshops(work, self.workshops)}:
                result["reasons"].extend(label + ": " + reason for reason in self.eligibility_reasons(work, workshop))
        if result["reasons"]:
            return result
        before = estimate_delivery(batch, workshop, self.queues)
        extra_estimate = estimate_delivery(extra, workshop, self.queues)
        increment = extra_estimate.process_days * (1 + 0.5 * extra_estimate.defect_risk)
        queues_after = {**self.queues, scenario.workshop_id: self.queues[scenario.workshop_id] + increment}
        after = estimate_delivery(batch, workshop, queues_after)
        for candidate in eligible_workshops(batch, self.workshops):
            estimate = estimate_delivery(batch, candidate, queues_after)
            result["candidates_after"].append(
                {
                    "workshop_id": candidate.workshop_id,
                    "name": candidate.name,
                    "estimate": asdict(estimate),
                    "display": self.display_fields(estimate),
                    "meets_deadline": estimate.lateness_days == 0,
                }
            )
        result["candidates_after"].sort(
            key=lambda row: (row["estimate"]["expected_turnaround_days"], row["workshop_id"])
        )
        alternatives = [row for row in result["candidates_after"] if row["workshop_id"] != scenario.workshop_id]
        result.update(
            status="ASSESSED",
            queues_after=queues_after,
            additional_processing_days=increment,
            before={
                "estimate": asdict(before),
                "display": self.display_fields(before),
                "meets_deadline": before.lateness_days == 0,
            },
            after={
                "estimate": asdict(after),
                "display": self.display_fields(after),
                "meets_deadline": after.lateness_days == 0,
            },
            fastest_alternative=alternatives[0] if alternatives else None,
            display={
                "additional_pieces": f"{scenario.additional_pieces:,} pieces",
                "additional_processing": f"{increment:.2f} days",
            },
        )
        return result

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

    @staticmethod
    def validate_rules(rules) -> list[dict]:
        """Standing rules come from dispatcher-confirmed memory; malformed ones fail closed."""
        checked = []
        for rule in rules:
            if not isinstance(rule, dict) or not RULE_FIELDS <= set(rule):
                raise ValueError("Each standing rule needs " + ", ".join(sorted(RULE_FIELDS)))
            if any(not isinstance(rule[key], str) or not rule[key].strip() for key in RULE_FIELDS - {"customer"}):
                raise ValueError("Standing rule fields must be nonempty strings")
            if rule["customer"] is not None and (
                not isinstance(rule["customer"], str) or not rule["customer"].strip()
            ):
                raise ValueError("A standing rule customer must be a nonempty string or null")
            checked.append({key: rule[key] for key in sorted(RULE_FIELDS)})
        return checked

    def rank(self, result: dict, batch: dict, constraints: dict, effective: ObjectiveWeights):
        """Eligibility, exclusions with provenance, ranked candidates and reference policies."""
        eligible = {w.workshop_id for w in eligible_workshops(batch, self.workshops)}
        permitted = {key: w for key, w in self.workshops.items() if key in eligible and key not in constraints}
        for key, workshop in self.workshops.items():
            reasons = []
            if key not in eligible:
                reasons.extend(self.eligibility_reasons(batch, workshop))
            if key in constraints:
                constraint = constraints[key]
                if "rule_id" in constraint:
                    reasons.append(
                        f"Remembered rule from {constraint['imposed_by']} ({constraint['created_on']}): "
                        f"{constraint['evidence']}"
                    )
                else:
                    reasons.append(f"Excluded by {constraint['imposed_by']}: {constraint['evidence']}")
            if reasons:
                result["excluded"].append({"workshop_id": key, "name": workshop.name, "reasons": reasons})
        ranked = rank_candidates(batch, permitted, self.queues, effective, ledger=self.ledger, register=self.workshops)
        for candidate in ranked:
            estimate = candidate.estimate
            result["candidates"].append(
                {
                    **asdict(candidate),
                    "name": self.workshops[estimate.workshop_id].name,
                    "makes": sorted(self.workshops[estimate.workshop_id].makes),
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
        result["has_on_time_option"] = any(row["meets_deadline"] for row in candidates)
        result["reservation_note"] = self.reservation_note(batch, permitted, effective, ranked)
        return permitted

    def reservation_note(self, batch, permitted, effective, ranked) -> dict | None:
        """Say so only when reserving shared capacity decided the ranking: without it, a shared shop wins."""
        if not ranked or not effective.capacity_reservation or ranked[0].estimate.lateness_days > 0:
            return None
        plain = rank_candidates(
            batch,
            permitted,
            self.queues,
            replace(effective, capacity_reservation=0.0),
            ledger=self.ledger,
            register=self.workshops,
        )
        held = plain[0]
        if held.estimate.workshop_id == ranked[0].estimate.workshop_id or not held.reserved_days:
            return None
        workshop = self.workshops[held.estimate.workshop_id]
        other = sorted(workshop.makes - {batch["category"]})
        makers = {
            category: sum(1 for w in self.workshops.values() if w.status == "ACTIVE" and category in w.makes)
            for category in other
        }
        scarce = " and ".join(
            f"{category.lower()} ({count} active workshops make it)" for category, count in makers.items()
        )
        return {
            "workshop_id": ranked[0].estimate.workshop_id,
            "held_workshop_id": workshop.workshop_id,
            "text": f"Leaves {workshop.name} free for {scarce}; the chosen workshop still meets the date.",
        }

    def capacity_category(self, product: str | None) -> str | None:
        """A category word, or a recorded product that belongs to exactly one category."""
        if product is None:
            return None
        categories = {category for workshop in self.workshops.values() for category in workshop.makes}
        if product.upper() in categories:
            return product.upper()
        matches = {row["category"] for row in self.orders if row["product"].casefold() == product.casefold()}
        return matches.pop() if len(matches) == 1 else None

    def preview(self, envelope: dict, request: DispatchInput, weights: ObjectiveWeights, *, rules=()) -> dict:
        snapshot = self.snapshot()
        rules = self.validate_rules(rules)
        for workshop_id in [
            request.suggested_workshop,
            *(item["workshop_id"] for item in request.exclusions),
            *(rule["workshop_id"] for rule in rules),
        ]:
            if workshop_id is not None and workshop_id not in self.workshops:
                raise ValueError(f"Unknown workshop: {workshop_id}")
        for constraint in request.exclusions:
            if constraint["evidence"] not in envelope["text"]:
                raise ValueError("Exclusion evidence must occur in the original message")
        effective = PREFERENCES.get(request.preference, weights)
        result = {
            "request": envelope,
            "input": asdict(request),
            "snapshot": snapshot,
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
            "standing_rules": rules,
            "applied_rules": [],
            "ledger": dict(sorted(self.ledger.items())),
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
            result.update(status=status, message=message, decision_basis=decision_basis(result))
            return result

        if request.intent in ("quote", "history"):
            return finish(
                "DECLINE", "The supplied data contains neither customer quotes nor past workshop allocations."
            )
        if request.intent == "capacity":
            return self.capacity_preview(result, request, effective, finish)
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
        constraints = {item["workshop_id"]: item for item in request.exclusions}
        for rule in rules:
            if rule["customer"] is not None and rule["customer"].casefold() != order["customer"].casefold():
                continue
            # A message constraint already excludes the workshop; keep its own provenance.
            if rule["workshop_id"] not in constraints:
                constraints[rule["workshop_id"]] = rule
                result["applied_rules"].append(rule)
        permitted = self.rank(result, batch, constraints, effective)
        candidates = result["candidates"]
        selectable = candidates
        if request.preference == "cheapest_on_time":
            selectable = [row for row in candidates if row["meets_deadline"]]
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

    def capacity_preview(self, result: dict, request: DispatchInput, effective: ObjectiveWeights, finish) -> dict:
        """Who can take a quantity of a product by a date: the same estimates, with no order to book."""
        category = self.capacity_category(request.product)
        issues = []
        if category is None:
            issues.append(CAPACITY_QUESTIONS["product"])
        if request.pieces is None:
            issues.append(CAPACITY_QUESTIONS["quantity"])
        if request.due_date is None or request.date_uncertain:
            issues.append(CAPACITY_QUESTIONS["deadline"])
        known = request.clarification or ""
        issues = [issue for issue in issues if issue not in known]
        if request.clarification:
            issues.append(request.clarification)
        if issues:
            return finish("CLARIFY", " ".join(issues))
        due = date.fromisoformat(request.due_date)
        batch = {
            "order_id": "CAPACITY_CHECK",
            "category": category,
            "pieces": request.pieces,
            "sent_date": self.as_of,
            "due_date": due,
        }
        result["batch"] = {**batch, "sent_date": self.as_of.isoformat(), "due_date": due.isoformat()}
        result["deadline_source"] = "request"
        result["capacity_query"] = {"product": request.product, "category": category}
        self.rank(result, batch, {item["workshop_id"]: item for item in request.exclusions}, effective)
        candidates = result["candidates"]
        on_time = [row for row in candidates if row["meets_deadline"]]
        if due < self.as_of:
            result["flags"].append("PAST_DEADLINE")
        if not on_time:
            result["flags"].append("NO_ON_TIME_OPTION")
        if candidates:
            result["recommendation"] = (on_time or candidates)[0]["estimate"]["workshop_id"]
        quantity = f"{request.pieces:,} pieces of {request.product.lower()}"
        if not candidates:
            message = f"No active workshop can take {quantity} as one batch."
        elif on_time:
            message = (
                f"{len(on_time)} of {len(candidates)} permitted workshops can deliver {quantity} by {due.isoformat()}."
            )
        else:
            earliest = result["earliest_option"]
            message = (
                f"No permitted workshop can deliver {quantity} by {due.isoformat()}. Earliest: "
                f"{earliest['name']} on {earliest['display']['eta']}, {earliest['display']['lateness']} late."
            )
        return finish("CAPACITY", message + " Nothing is reserved until an order is booked.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", help="Inbox ID; uses a draft structured fixture unless --input is supplied")
    parser.add_argument("--input", type=Path, help="Reviewed structured JSON for the chosen inbox request")
    parser.add_argument("--preset", choices=PRESETS, default=DEFAULT_PRESET)
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
