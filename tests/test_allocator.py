from dataclasses import replace
from datetime import date

import pytest

from dss5105.allocator import (
    NoEligibleWorkshop,
    ObjectiveWeights,
    ScoreScales,
    assess_split,
    earliest_finish,
    estimate_delivery,
    make_allocator,
    rank_candidates,
)
from dss5105.evaluate import PRESETS, run_experiment
from dss5105.harness import Simulator, Workshop, eligible_workshops


@pytest.fixture
def batch():
    return {
        "order_id": "TEST",
        "category": "TOPS",
        "pieces": 200,
        "sent_date": date(2026, 4, 1),
        "due_date": date(2026, 4, 4),
    }


@pytest.fixture
def workshops():
    fast = Workshop("FAST", "Fast", 200, 1, 0.1, 2.0, {"TOPS"}, "ACTIVE", None, 0.0, "")
    careful = replace(fast, workshop_id="CAREFUL", capacity=100, defect_rate=0.01, cost=1.0)
    return {fast.workshop_id: fast, careful.workshop_id: careful}


def test_current_queue_changes_choice_without_mutating_state(batch, workshops):
    policy = make_allocator(ObjectiveWeights())
    empty = {"FAST": 0.0, "CAREFUL": 0.0}
    backlog = {"FAST": 10.0, "CAREFUL": 0.0}
    assert policy(batch, workshops, empty) == "FAST"
    assert policy(batch, workshops, backlog) == "CAREFUL"
    assert earliest_finish(batch, workshops, backlog) == "CAREFUL"
    assert backlog == {"FAST": 10.0, "CAREFUL": 0.0}


def test_config_changes_decision(batch, workshops):
    queues = {"FAST": 0.0, "CAREFUL": 4.0}
    assert make_allocator(ObjectiveWeights(lateness=1))(batch, workshops, queues) == "FAST"
    assert make_allocator(ObjectiveWeights(lateness=0, defects=1))(batch, workshops, queues) == "CAREFUL"
    assert make_allocator(ObjectiveWeights(lateness=0, cost=1))(batch, workshops, queues) == "CAREFUL"
    assert make_allocator(ObjectiveWeights(lateness=0.7, defects=0.3))(batch, workshops, queues) == "FAST"
    assert make_allocator(ObjectiveWeights(lateness=0.1, defects=0.9))(batch, workshops, queues) == "CAREFUL"


def test_estimate_includes_transport_expected_rework_and_due_date(batch, workshops):
    estimate = estimate_delivery(batch, workshops["FAST"], {"FAST": 2.0})
    assert estimate.process_days == 1.0
    assert estimate.turnaround_days == 4.0
    assert estimate.expected_turnaround_days == pytest.approx(4.05)
    assert estimate.lateness_days == pytest.approx(1.05)
    assert estimate.cost == 400.0


def test_pure_lateness_differs_by_expected_rework_not_deadline_priority(batch, workshops):
    workshops["CAREFUL"] = replace(workshops["CAREFUL"], capacity=200)
    queues = {"FAST": 0.0, "CAREFUL": 0.02}
    assert earliest_finish(batch, workshops, queues) == "FAST"
    for deadline in [date(2026, 4, 1), date(2026, 4, 30)]:
        batch["due_date"] = deadline
        assert make_allocator(ObjectiveWeights())(batch, workshops, queues) == "CAREFUL"


def test_eligibility_is_checked_before_score(batch, workshops):
    template = workshops["FAST"]
    for workshop_id, overrides in {
        "SUSPENDED": {"status": "SUSPENDED"},
        "WRONG_CATEGORY": {"makes": {"ACCESSORIES"}},
        "CAPPED": {"max_batch": 100},
    }.items():
        workshops[workshop_id] = replace(template, workshop_id=workshop_id, cost=0, **overrides)
    queues = dict.fromkeys(workshops, 0.0)
    ranked = rank_candidates(batch, workshops, queues, ObjectiveWeights(lateness=0, cost=1))
    assert {row.estimate.workshop_id for row in ranked} == {"FAST", "CAREFUL"}
    assert make_allocator(ObjectiveWeights(lateness=0, cost=1))(batch, workshops, queues) == "CAREFUL"


def test_empty_candidates_fail_explicitly(batch, workshops):
    batch["category"] = "UNKNOWN"
    assert rank_candidates(batch, workshops, {}, ObjectiveWeights()) == []
    for policy in [earliest_finish, make_allocator(ObjectiveWeights())]:
        with pytest.raises(NoEligibleWorkshop, match="TEST"):
            policy(batch, workshops, {})


def test_split_finishes_with_its_slower_part_and_beats_whole_batch_here(batch, workshops):
    queues = dict.fromkeys(workshops, 0.0)
    plan = assess_split(batch, workshops, queues)
    assert sum(plan.pieces) == batch["pieces"]
    assert plan.expected_turnaround_days == max(part.expected_turnaround_days for part in plan.parts)
    assert plan.cost == sum(part.cost for part in plan.parts)
    whole = min(estimate_delivery(batch, w, queues).expected_turnaround_days for w in workshops.values())
    assert plan.expected_turnaround_days < whole
    for part, pieces in zip(plan.parts, plan.pieces, strict=True):
        assert part.process_days == pieces / workshops[part.workshop_id].capacity


def test_split_parts_pass_eligibility_at_their_own_size(batch, workshops):
    workshops["FAST"] = replace(workshops["FAST"], max_batch=50)
    plan = assess_split(batch, workshops, dict.fromkeys(workshops, 0.0))
    assert dict(zip((part.workshop_id for part in plan.parts), plan.pieces, strict=True))["FAST"] <= 50
    assert assess_split(batch, {"FAST": workshops["FAST"]}, {"FAST": 0.0}) is None


def test_ties_are_independent_of_workshop_insertion_order(batch, workshops):
    workshops["CAREFUL"] = replace(workshops["FAST"], workshop_id="CAREFUL")
    queues = dict.fromkeys(workshops, 0.0)
    policy = make_allocator(ObjectiveWeights())
    assert policy(batch, workshops, queues) == policy(batch, dict(reversed(list(workshops.items()))), queues)


def test_deadline_buffer_changes_only_the_score_not_the_estimate(batch, workshops):
    batch["due_date"] = date(2026, 4, 10)
    queues = dict.fromkeys(workshops, 0.0)
    plain = rank_candidates(batch, workshops, queues, ObjectiveWeights(lateness=1, cost=0.01))
    buffered = rank_candidates(
        batch, workshops, queues, ObjectiveWeights(lateness=1, cost=0.01, deadline_buffer_days=7)
    )
    # Both fit the date; the buffer stops the cheap, slower shop from using all the slack.
    assert plain[0].estimate.workshop_id == "CAREFUL"
    assert buffered[0].estimate.workshop_id == "FAST"
    assert [row.estimate for row in sorted(plain, key=lambda r: r.estimate.workshop_id)] == [
        row.estimate for row in sorted(buffered, key=lambda r: r.estimate.workshop_id)
    ]
    assert all(row.estimate.lateness_days == 0 for row in buffered)
    unbuffered = ObjectiveWeights(lateness=1, cost=0.01, deadline_buffer_days=0)
    assert rank_candidates(batch, workshops, queues, unbuffered) == plain


@pytest.mark.parametrize("value", [-1.0, float("nan"), float("inf")])
def test_invalid_weights_and_scales(value):
    with pytest.raises(ValueError):
        ObjectiveWeights(lateness=value)
    with pytest.raises(ValueError, match="buffer"):
        ObjectiveWeights(deadline_buffer_days=value)
    with pytest.raises(ValueError):
        ScoreScales(lateness_days=value)


def test_zero_weights_and_scales():
    with pytest.raises(ValueError):
        ObjectiveWeights(lateness=0)
    with pytest.raises(ValueError, match="not all zero"):
        ObjectiveWeights(lateness=0, deadline_buffer_days=5)
    with pytest.raises(ValueError):
        ScoreScales(lateness_days=0)


@pytest.mark.parametrize("shock", [False, True])
def test_all_policies_run_reproducibly_and_only_choose_eligible_workshops(shock):
    first = run_experiment(shock=shock)
    assert first == run_experiment(shock=shock)
    sim = Simulator()
    for name, decisions in first["policies"].items():
        assert len(decisions) == len(sim.batches)
        for batch, decision in zip(sim.batches, decisions, strict=True):
            assert decision["order_id"] == batch["order_id"]
            assert decision["choice"] in {w.workshop_id for w in eligible_workshops(batch, sim.workshops)}
            assert decision["choice"] == decision["outcome"]["workshop"]
            if name in PRESETS:
                assert decision["choice"] == decision["candidates"][0]["estimate"]["workshop_id"]
