"""Small, deterministic allocation policies. No LLM or simulator outcome access."""

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import date
from math import isfinite
from typing import TypedDict

from dss5105.harness import Workshop, eligible_workshops

# The four course objectives plus cost, in the order the UI and evidence list them.
OBJECTIVES = ("lateness", "defects", "fairness", "robustness", "cost")


class Batch(TypedDict):
    order_id: str
    category: str
    pieces: int
    sent_date: date
    due_date: date


class NoEligibleWorkshop(ValueError):
    """The harness needs a workshop ID and has no defer/escalate protocol."""


@dataclass(frozen=True)
class ObjectiveWeights:
    """Objective configuration: one relative weight per objective, plus two lateness settings.

    The weights cover the four course objectives (lateness, defects, fairness, robustness)
    and cost. They are relative preferences, not probabilities, and need not sum to one.

    `deadline_buffer_days` penalizes a candidate unless its expected turnaround plus the
    buffer fits before the due date. `capacity_reservation` charges the lateness objective
    for capacity that only shared workshops can offer another product category: a tops
    batch at a workshop that also makes accessories uses up scarce accessory capacity.
    `deadline_miss_days` adds a fixed charge, in days, to any candidate whose expected
    turnaround misses the date, so an on-time option beats a late one unless the other
    terms differ by more than that. All three only change the lateness score; estimates
    and the "meets deadline" test are unchanged. Zero for all three is the original score.
    """

    lateness: float = 1.0
    defects: float = 0.0
    cost: float = 0.0
    fairness: float = 0.0
    robustness: float = 0.0
    deadline_buffer_days: float = 0.0
    capacity_reservation: float = 0.0
    deadline_miss_days: float = 0.0

    def __post_init__(self):
        weights = tuple(getattr(self, name) for name in OBJECTIVES)
        if any(not isfinite(value) or value < 0 for value in weights) or not any(weights):
            raise ValueError("Weights must be finite, nonnegative, and not all zero")
        if not isfinite(self.deadline_buffer_days) or self.deadline_buffer_days < 0:
            raise ValueError("The deadline buffer must be finite and nonnegative")
        if not isfinite(self.capacity_reservation) or self.capacity_reservation < 0:
            raise ValueError("The capacity reservation must be finite and nonnegative")
        if not isfinite(self.deadline_miss_days) or self.deadline_miss_days < 0:
            raise ValueError("The deadline miss charge must be finite and nonnegative")


@dataclass(frozen=True)
class ScoreScales:
    """Fixed reference units; do not rescale using future orders or outcomes.

    Each objective term is divided by its unit, which puts the terms on one common scale:
    a week of lateness, a 10% defect risk on a typical 750-piece batch, a quarter of all
    allocated pieces, and one cost unit per piece. `stress_days` is the stoppage the
    robustness term asks a plan to absorb: the course's two-week closure.
    """

    lateness_days: float = 7.0
    defect_probability: float = 0.1
    cost_per_piece: float = 1.0
    batch_pieces: float = 750.0
    workload_share: float = 0.25
    stress_days: float = 14.0

    def __post_init__(self):
        if any(not isfinite(value) or value <= 0 for value in asdict(self).values()):
            raise ValueError("Score scales must be finite and positive")


@dataclass(frozen=True)
class DeliveryEstimate:
    workshop_id: str
    queue_days: float
    process_days: float
    transport_days: float
    turnaround_days: float
    expected_turnaround_days: float
    available_days: float
    lateness_days: float
    defect_risk: float
    cost: float


def estimate_delivery(batch: Batch, workshop: Workshop, queues: dict[str, float]) -> DeliveryEstimate:
    """Estimate from the current queue; unknown closures cannot be predicted.

    Expected processing includes the harness's chance of redoing half a batch.
    Lateness is a continuous point-estimate penalty, not a probability of being late.
    """
    queue = queues[workshop.workshop_id]
    process = batch["pieces"] / workshop.capacity
    turnaround = queue + process + workshop.lead_days
    expected = turnaround + process * 0.5 * workshop.defect_rate
    time_available = (batch["due_date"] - batch["sent_date"]).days
    return DeliveryEstimate(
        workshop_id=workshop.workshop_id,
        queue_days=queue,
        process_days=process,
        transport_days=workshop.lead_days,
        turnaround_days=turnaround,
        expected_turnaround_days=expected,
        available_days=float(time_available),
        lateness_days=max(0.0, expected - time_available),
        defect_risk=workshop.defect_rate,
        cost=batch["pieces"] * workshop.cost,
    )


def category_capacity(register: Mapping[str, Workshop]) -> dict[str, int]:
    """Pieces per day each product category can get from ACTIVE workshops in the register."""
    capacity = {}
    for workshop in register.values():
        if workshop.status == "ACTIVE":
            for category in workshop.makes:
                capacity[category] = capacity.get(category, 0) + workshop.capacity
    return capacity


def reserved_days(batch: Batch, workshop: Workshop, capacity: Mapping[str, int]) -> float:
    """Days of other categories' total capacity this batch would occupy at this workshop.

    A tops batch at a tops-only shop reserves nothing. At a shop that also makes
    accessories it takes pieces / (all accessory capacity) days from accessory work.
    Own-category use is the same at every shop (pieces / category capacity), so only
    the cross-category part can tell candidates apart.
    """
    return sum(batch["pieces"] / capacity[c] for c in workshop.makes if c != batch["category"] and capacity.get(c))


@dataclass(frozen=True)
class CandidateScore:
    estimate: DeliveryEstimate
    reserved_days: float
    projected_share: float | None
    stress_lateness_days: float
    lateness_component: float
    defects_component: float
    cost_component: float
    fairness_component: float
    robustness_component: float
    score: float


def rank_candidates(
    batch: Batch,
    workshops: dict[str, Workshop],
    queues: dict[str, float],
    weights: ObjectiveWeights,
    scales: ScoreScales = ScoreScales(),
    *,
    ledger: Mapping[str, float] | None = None,
    register: Mapping[str, Workshop] | None = None,
) -> list[CandidateScore]:
    """Filter with the course rule, then rank using one configurable formula.

    `ledger` holds pieces already allocated per workshop; fairness uses it and has no
    effect while it is empty. `register` is the full workshop register for category
    capacity, for callers that pass only a permitted subset as `workshops`.
    Ties use expected turnaround, then workshop ID, for every objective.
    An empty list means no eligible workshop; no constraint is relaxed.
    """
    capacity = category_capacity(register if register is not None else workshops)
    ledger = ledger or {}
    allocated = sum(ledger.values())
    ranked = []
    for workshop in eligible_workshops(batch, workshops):
        estimate = estimate_delivery(batch, workshop, queues)
        expected = estimate.expected_turnaround_days
        buffered = max(0.0, expected + weights.deadline_buffer_days - estimate.available_days)
        reserve = reserved_days(batch, workshop, capacity)
        share = (ledger.get(workshop.workshop_id, 0) + batch["pieces"]) / (allocated + batch["pieces"])
        projected = share if allocated > 0 else None
        stress = max(0.0, expected + scales.stress_days - estimate.available_days)
        missed = weights.deadline_miss_days if estimate.lateness_days > 0 else 0.0
        lateness = (
            weights.lateness * (buffered + weights.capacity_reservation * reserve + missed) / scales.lateness_days
        )
        defects = (
            weights.defects * estimate.defect_risk / scales.defect_probability * batch["pieces"] / scales.batch_pieces
        )
        cost = weights.cost * workshop.cost / scales.cost_per_piece
        fairness = weights.fairness * projected / scales.workload_share if projected is not None else 0.0
        robustness = weights.robustness * stress / scales.lateness_days
        total = lateness + defects + cost + fairness + robustness
        ranked.append(
            CandidateScore(estimate, reserve, projected, stress, lateness, defects, cost, fairness, robustness, total)
        )
    return sorted(ranked, key=lambda row: (row.score, row.estimate.expected_turnaround_days, row.estimate.workshop_id))


class Allocator:
    """The simulator callback for one configuration, with a memory of its own decisions.

    Fairness needs to know where earlier batches went. The harness passes only queues,
    so the allocator keeps a ledger of the pieces it has placed in the current replay.
    The harness has no run-start hook: a repeated order ID means a new replay, and
    the ledger starts again. No future order, outcome or closure is ever read.
    """

    def __init__(self, weights: ObjectiveWeights, scales: ScoreScales = ScoreScales()):
        self.weights = weights
        self.scales = scales
        self.ledger: dict[str, float] = {}
        self.last_ranking: list[CandidateScore] = []
        self._seen: set[str] = set()

    def reset(self):
        self.ledger = {}
        self.last_ranking = []
        self._seen = set()

    def __call__(self, batch, workshops, queues):
        if batch["order_id"] in self._seen:
            self.reset()
        ranked = rank_candidates(batch, workshops, queues, self.weights, self.scales, ledger=self.ledger)
        if not ranked:
            raise NoEligibleWorkshop(f"No eligible workshop for {batch['order_id']}")
        choice = ranked[0].estimate.workshop_id
        self._seen.add(batch["order_id"])
        self.ledger[choice] = self.ledger.get(choice, 0) + batch["pieces"]
        self.last_ranking = ranked
        return choice


def make_allocator(weights: ObjectiveWeights, scales: ScoreScales = ScoreScales()) -> Allocator:
    """Bind configuration to the exact callback signature expected by Simulator.run."""
    return Allocator(weights, scales)


@dataclass(frozen=True)
class SplitPlan:
    parts: tuple[DeliveryEstimate, DeliveryEstimate]
    pieces: tuple[int, int]
    expected_turnaround_days: float
    lateness_days: float
    cost: float


def assess_split(batch: Batch, workshops: dict[str, Workshop], queues: dict[str, float]) -> SplitPlan | None:
    """Fastest two-workshop split of one batch, for the chat layer only.

    Each part must pass the course eligibility rule at its own size. The plan
    finishes when its slower part does; ties prefer lower total cost, then IDs.
    The simulator sends one batch to one workshop, so it never evaluates this.
    Returns None when fewer than two workshops can take a part.
    """
    total = batch["pieces"]
    estimates = {}
    for pieces in range(1, total):
        part = {**batch, "pieces": pieces}
        for workshop in eligible_workshops(part, workshops):
            estimates[workshop.workshop_id, pieces] = estimate_delivery(part, workshop, queues)
    best = None
    for first in sorted(workshops):
        for second in sorted(workshops):
            if second <= first:
                continue
            for pieces in range(1, total):
                a = estimates.get((first, pieces))
                b = estimates.get((second, total - pieces))
                if a is None or b is None:
                    continue
                finish = max(a.expected_turnaround_days, b.expected_turnaround_days)
                key = (finish, a.cost + b.cost, first, second, pieces)
                if best is None or key < best[0]:
                    best = (key, a, b, pieces)
    if best is None:
        return None
    (finish, cost, *_), a, b, pieces = best
    return SplitPlan(
        parts=(a, b),
        pieces=(pieces, total - pieces),
        expected_turnaround_days=finish,
        lateness_days=max(a.lateness_days, b.lateness_days),
        cost=cost,
    )


def earliest_finish(batch: Batch, workshops: dict[str, Workshop], queues: dict[str, float]) -> str:
    """Short queue-aware reference policy, without expected defect adjustment."""
    estimates = [estimate_delivery(batch, w, queues) for w in eligible_workshops(batch, workshops)]
    if not estimates:
        raise NoEligibleWorkshop(f"No eligible workshop for {batch['order_id']}")
    return min(estimates, key=lambda estimate: (estimate.turnaround_days, estimate.workshop_id)).workshop_id
