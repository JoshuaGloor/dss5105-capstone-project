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


@pytest.fixture
def shared():
    """A tops-only shop and a slightly faster shop that also makes scarce accessories."""
    tops = Workshop("TOPS_ONLY", "Tops only", 200, 1, 0.05, 1.0, {"TOPS"}, "ACTIVE", None, 0.0, "")
    both = replace(tops, workshop_id="SHARED", capacity=210, makes={"TOPS", "ACCESSORIES"})
    return {tops.workshop_id: tops, both.workshop_id: both}


def test_reservation_keeps_shared_capacity_free_when_both_meet_the_date(batch, shared):
    batch["due_date"] = date(2026, 4, 20)
    queues = dict.fromkeys(shared, 0.0)
    assert make_allocator(ObjectiveWeights())(batch, shared, queues) == "SHARED"
    reserving = ObjectiveWeights(capacity_reservation=1.0)
    ranked = rank_candidates(batch, shared, queues, reserving)
    assert ranked[0].estimate.workshop_id == "TOPS_ONLY"
    reserved = {row.estimate.workshop_id: row.reserved_days for row in ranked}
    # 200 tops pieces at the shared shop take 200 / 210 days of all accessory capacity.
    assert reserved == {"TOPS_ONLY": 0.0, "SHARED": pytest.approx(200 / 210)}
    assert [row.estimate for row in ranked] == sorted(
        (row.estimate for row in rank_candidates(batch, shared, queues, ObjectiveWeights())),
        key=lambda estimate: estimate.workshop_id != "TOPS_ONLY",
    )


def test_reservation_uses_the_full_register_not_the_permitted_subset(batch, shared):
    accessories = Workshop("ACC", "Accessories", 90, 1, 0.02, 1.0, {"ACCESSORIES"}, "ACTIVE", None, 0.0, "")
    register = {**shared, "ACC": accessories}
    queues = dict.fromkeys(register, 0.0)
    weights = ObjectiveWeights(capacity_reservation=1.0)
    subset = rank_candidates(batch, shared, queues, weights)
    full = rank_candidates(batch, shared, queues, weights, register=register)
    shared_row = {row.estimate.workshop_id: row for row in full}["SHARED"]
    assert shared_row.reserved_days == pytest.approx(200 / 300)
    assert {row.estimate.workshop_id: row.reserved_days for row in subset}["SHARED"] == pytest.approx(200 / 210)


def test_reservation_never_overrides_a_real_deadline_gain(batch, shared):
    queues = {"TOPS_ONLY": 3.0, "SHARED": 0.0}
    weights = ObjectiveWeights(capacity_reservation=1.0)
    assert make_allocator(weights)(batch, shared, queues) == "SHARED"


def test_fairness_uses_the_ledger_and_has_no_effect_without_one(batch, shared):
    batch["due_date"] = date(2026, 4, 20)
    queues = dict.fromkeys(shared, 0.0)
    weights = ObjectiveWeights(fairness=1.0)
    empty = rank_candidates(batch, shared, queues, weights)
    assert all(row.projected_share is None and row.fairness_component == 0 for row in empty)
    assert empty[0].estimate.workshop_id == "SHARED"
    ranked = rank_candidates(batch, shared, queues, weights, ledger={"SHARED": 800})
    assert ranked[0].estimate.workshop_id == "TOPS_ONLY"
    shares = {row.estimate.workshop_id: row.projected_share for row in ranked}
    assert shares == {"TOPS_ONLY": pytest.approx(200 / 1000), "SHARED": pytest.approx(1.0)}


def test_allocator_remembers_its_own_choices_and_restarts_on_a_new_replay(batch, shared):
    batch["due_date"] = date(2026, 4, 20)
    queues = dict.fromkeys(shared, 0.0)
    policy = make_allocator(ObjectiveWeights(fairness=1.0))
    first = policy(batch, shared, queues)
    second = policy({**batch, "order_id": "NEXT"}, shared, queues)
    assert first != second
    assert policy.ledger == {first: 200, second: 200}
    assert policy.last_ranking[0].estimate.workshop_id == second
    assert policy(batch, shared, queues) == first  # the first order again: a new replay
    assert policy.ledger == {first: 200}


def test_robustness_prefers_slack_that_absorbs_a_stoppage(batch, shared):
    batch["due_date"] = date(2026, 4, 20)
    shared["SHARED"] = replace(shared["SHARED"], cost=1.5)
    queues = {"TOPS_ONLY": 6.0, "SHARED": 0.0}
    # Both meet the date; only the busy shop would miss it after a two-week stoppage.
    assert make_allocator(ObjectiveWeights(lateness=1, cost=1))(batch, shared, queues) == "TOPS_ONLY"
    ranked = rank_candidates(batch, shared, queues, ObjectiveWeights(lateness=1, cost=1, robustness=2))
    stress = {row.estimate.workshop_id: row.stress_lateness_days for row in ranked}
    assert stress["SHARED"] == 0.0 and stress["TOPS_ONLY"] == pytest.approx(3.025)
    assert all(row.estimate.lateness_days == 0 for row in ranked)
    assert ranked[0].estimate.workshop_id == "SHARED"


def test_defect_term_is_weighted_by_batch_pieces(batch, workshops):
    queues = dict.fromkeys(workshops, 0.0)
    weights = ObjectiveWeights(lateness=0, defects=1)
    small = {
        row.estimate.workshop_id: row.defects_component for row in rank_candidates(batch, workshops, queues, weights)
    }
    batch["pieces"] = 750
    typical = {
        row.estimate.workshop_id: row.defects_component for row in rank_candidates(batch, workshops, queues, weights)
    }
    assert typical["FAST"] == pytest.approx(1.0)  # 10% risk on a 750-piece batch is one unit
    assert small["FAST"] == pytest.approx(200 / 750)


@pytest.mark.parametrize("field", ["capacity_reservation", "fairness", "robustness"])
def test_new_terms_validate_like_the_others(field):
    with pytest.raises(ValueError):
        ObjectiveWeights(**{field: -1.0})
    with pytest.raises(ValueError):
        ObjectiveWeights(**{field: float("nan")})
    if field != "capacity_reservation":
        assert getattr(ObjectiveWeights(lateness=0, **{field: 1.0}), field) == 1.0
    else:
        with pytest.raises(ValueError, match="not all zero"):
            ObjectiveWeights(lateness=0, capacity_reservation=1.0)


def test_deadline_miss_charge_puts_an_on_time_shop_ahead_of_capacity_reservation(batch, shared):
    # The tops-only shop misses the date by a little; the shared shop meets it.
    batch["due_date"] = date(2026, 4, 4)
    queues = {"TOPS_ONLY": 1.2, "SHARED": 0.0}
    reserving = ObjectiveWeights(capacity_reservation=1.0)
    assert make_allocator(reserving)(batch, shared, queues) == "TOPS_ONLY"
    on_time_first = ObjectiveWeights(capacity_reservation=1.0, deadline_miss_days=7.0)
    ranked = rank_candidates(batch, shared, queues, on_time_first)
    assert ranked[0].estimate.workshop_id == "SHARED" and ranked[0].estimate.lateness_days == 0
    assert ranked[1].estimate.lateness_days > 0
    with pytest.raises(ValueError, match="miss"):
        ObjectiveWeights(deadline_miss_days=-1)
