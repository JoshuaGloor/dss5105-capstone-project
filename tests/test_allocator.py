from dataclasses import replace
from datetime import date

import pytest

from dss5105.allocator import (
    NoEligibleWorkshop,
    ObjectiveWeights,
    ScoreScales,
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


def test_ties_are_independent_of_workshop_insertion_order(batch, workshops):
    workshops["CAREFUL"] = replace(workshops["FAST"], workshop_id="CAREFUL")
    queues = dict.fromkeys(workshops, 0.0)
    policy = make_allocator(ObjectiveWeights())
    assert policy(batch, workshops, queues) == policy(batch, dict(reversed(list(workshops.items()))), queues)


@pytest.mark.parametrize("value", [-1.0, float("nan"), float("inf")])
def test_invalid_weights_and_scales(value):
    with pytest.raises(ValueError):
        ObjectiveWeights(lateness=value)
    with pytest.raises(ValueError):
        ScoreScales(lateness_days=value)


def test_zero_weights_and_scales():
    with pytest.raises(ValueError):
        ObjectiveWeights(lateness=0)
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
