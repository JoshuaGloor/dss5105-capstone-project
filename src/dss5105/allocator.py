"""Small, deterministic allocation policies. No LLM or simulator outcome access."""

from dataclasses import asdict, dataclass
from datetime import date
from math import isfinite
from typing import TypedDict

from dss5105.harness import Workshop, eligible_workshops


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
    """Objective configuration: three relative weights and a deadline safety buffer.

    The buffer only changes the lateness score: a candidate is penalized unless its
    expected turnaround plus the buffer fits before the due date. Estimates and the
    "meets deadline" test are unchanged. A buffer of 0 is the original score.
    """

    lateness: float = 1.0
    defects: float = 0.0
    cost: float = 0.0
    deadline_buffer_days: float = 0.0

    def __post_init__(self):
        weights = (self.lateness, self.defects, self.cost)
        if any(not isfinite(value) or value < 0 for value in weights) or not any(weights):
            raise ValueError("Weights must be finite, nonnegative, and not all zero")
        if not isfinite(self.deadline_buffer_days) or self.deadline_buffer_days < 0:
            raise ValueError("The deadline buffer must be finite and nonnegative")


@dataclass(frozen=True)
class ScoreScales:
    """Fixed reference units; do not rescale using future orders or outcomes."""

    lateness_days: float = 7.0
    defect_probability: float = 0.1
    cost_per_piece: float = 1.0

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


@dataclass(frozen=True)
class CandidateScore:
    estimate: DeliveryEstimate
    lateness_component: float
    defects_component: float
    cost_component: float
    score: float


def rank_candidates(
    batch: Batch,
    workshops: dict[str, Workshop],
    queues: dict[str, float],
    weights: ObjectiveWeights,
    scales: ScoreScales = ScoreScales(),
) -> list[CandidateScore]:
    """Filter with the course rule, then rank using one configurable formula.

    Ties use expected turnaround, then workshop ID, for every objective.
    An empty list means no eligible workshop; no constraint is relaxed.
    """
    ranked = []
    for workshop in eligible_workshops(batch, workshops):
        estimate = estimate_delivery(batch, workshop, queues)
        buffered = estimate.expected_turnaround_days + weights.deadline_buffer_days - estimate.available_days
        lateness = weights.lateness * max(0.0, buffered) / scales.lateness_days
        defects = weights.defects * estimate.defect_risk / scales.defect_probability
        cost = weights.cost * workshop.cost / scales.cost_per_piece
        ranked.append(CandidateScore(estimate, lateness, defects, cost, lateness + defects + cost))
    return sorted(ranked, key=lambda row: (row.score, row.estimate.expected_turnaround_days, row.estimate.workshop_id))


def make_allocator(weights: ObjectiveWeights, scales: ScoreScales = ScoreScales()):
    """Bind configuration to the exact callback signature expected by Simulator.run."""

    def allocate(batch, workshops, queues):
        ranked = rank_candidates(batch, workshops, queues, weights, scales)
        if not ranked:
            raise NoEligibleWorkshop(f"No eligible workshop for {batch['order_id']}")
        return ranked[0].estimate.workshop_id

    return allocate


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
