import copy
import json
from dataclasses import asdict, replace
from datetime import date

import pytest

from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput, read_inbox
from dss5105.evaluate import PRESETS


@pytest.fixture
def desk():
    return DispatchDesk()


def envelope(text="Please allocate the order."):
    return {"request_id": "test", "time": "09:00", "requester": "Dispatcher", "text": text}


def preview(desk, **kwargs):
    return desk.preview(envelope(), DispatchInput(order_id="ORD-109", **kwargs), ObjectiveWeights())


def test_inbox_and_draft_fixtures_cover_source_without_claiming_accuracy(desk):
    inbox = read_inbox()
    fixtures = json.loads((ROOT / "examples" / "dispatch_inputs.json").read_text())
    assert len(inbox) == 30
    assert set(fixtures) == {item["request_id"] for item in inbox}
    before = copy.deepcopy(desk.queues)
    for item in inbox:
        result = desk.preview(item, DispatchInput(**fixtures[item["request_id"]]), ObjectiveWeights())
        assert result["request"] == item
        assert result["commit_allowed"] is False
        assert result["status"]
    assert desk.queues == before


def test_unknown_explicit_id_does_not_fall_back_to_customer(desk):
    result = desk.resolve_order(DispatchInput(order_id="ORD-999", customer="Harbor Knits"))
    assert result == {"status": "NOT_FOUND", "matches": []}


def test_ambiguous_reference_is_not_guessed(desk):
    result = desk.preview(envelope(), DispatchInput(customer="TrendCart"), ObjectiveWeights())
    assert result["status"] == "CLARIFY"
    assert len(result["resolution"]["matches"]) > 1
    assert result["candidates"] == []


@pytest.mark.parametrize(
    "fields",
    [
        {"pieces": 501},
        {"customer": "Different customer"},
        {"date_uncertain": True},
        {"date_kind": "shipping", "due_date": "2026-04-11"},
    ],
)
def test_unresolved_conflicts_block_ranking(desk, fields):
    result = preview(desk, **fields)
    assert result["status"] == "CLARIFY"
    assert not result["candidates"]


def test_ship_date_matching_the_recorded_due_date_needs_no_question(desk):
    result = preview(desk, date_kind="shipping", due_date="2026-04-13")
    assert result["status"] == "RECOMMEND"
    assert result["batch"]["due_date"] == result["order"]["due_date"] == "2026-04-13"
    assert "recorded due date" in result["deadline_note"]
    assert "deadline_note" not in preview(desk, due_date="2026-04-13")


def test_status_of_unknown_order_is_declined_but_allocation_asks(desk):
    status = desk.preview(envelope(), DispatchInput(order_id="ORD-999", intent="status"), ObjectiveWeights())
    assert status["status"] == "DECLINE"
    assert "orders.csv" in status["message"]
    allocate = desk.preview(envelope(), DispatchInput(order_id="ORD-999"), ObjectiveWeights())
    assert allocate["status"] == "CLARIFY"


def test_explicit_due_date_keeps_original_evidence(desk):
    result = preview(desk, due_date="2026-05-01")
    assert result["batch"]["due_date"] == "2026-05-01"
    assert result["order"]["due_date"] == "2026-04-13"
    assert result["deadline_source"] == "request"


@pytest.mark.parametrize("intent", ["quote", "history"])
def test_missing_data_is_declined_without_inventing_answer(desk, intent):
    result = preview(desk, intent=intent)
    assert result["status"] == "DECLINE"
    assert not result["candidates"]


@pytest.mark.parametrize(
    "order_id,workshop_id,reason",
    [("ORD-073", "W8", "limit"), ("ORD-008", "W7", "SUSPENDED"), ("ORD-103", "W1", "ACCESSORIES")],
)
def test_invalid_suggestion_is_refused_with_evidence(desk, order_id, workshop_id, reason):
    result = desk.preview(
        envelope(), DispatchInput(order_id=order_id, suggested_workshop=workshop_id), ObjectiveWeights()
    )
    assert result["status"] == "REFUSE_SUGGESTION"
    excluded = next(item for item in result["excluded"] if item["workshop_id"] == workshop_id)
    assert reason in " ".join(excluded["reasons"])
    assert result["alternative"] in {row["estimate"]["workshop_id"] for row in result["candidates"]}


def test_exclusion_is_hard_constraint_with_provenance(desk):
    text = "Boss says no QuickStitch."
    request = DispatchInput(
        order_id="ORD-053",
        exclusions=[{"workshop_id": "W1", "imposed_by": "Boss", "evidence": text}],
    )
    result = desk.preview(envelope(text), request, ObjectiveWeights())
    assert "W1" not in {row["estimate"]["workshop_id"] for row in result["candidates"]}
    assert "Boss" in result["excluded"][0]["reasons"][0]
    with pytest.raises(ValueError, match="evidence"):
        desk.preview(envelope(), request, ObjectiveWeights())


def test_no_constraints_are_silently_relaxed(desk):
    request = DispatchInput(
        order_id="ORD-109",
        exclusions=[
            {"workshop_id": key, "imposed_by": "Dispatcher", "evidence": "no shops"} for key in desk.workshops
        ],
    )
    result = desk.preview(envelope("no shops"), request, ObjectiveWeights())
    assert result["status"] == "NO_FEASIBLE_OPTION"
    assert result["recommendation"] is None
    assert not result["candidates"]


def test_cheapest_on_time_enforces_deadline_before_cost(desk):
    result = desk.preview(
        envelope(), DispatchInput(order_id="ORD-081", preference="cheapest_on_time"), ObjectiveWeights()
    )
    eligible = [item for item in result["candidates"] if item["meets_deadline"]]
    chosen = next(item for item in eligible if item["estimate"]["workshop_id"] == result["recommendation"])
    assert chosen["estimate"]["cost"] == min(item["estimate"]["cost"] for item in eligible)
    assert result["effective_weights"] == asdict(ObjectiveWeights(lateness=0, cost=1))
    infeasible = preview(desk, due_date="2026-04-01", preference="cheapest_on_time")
    assert infeasible["status"] == "NO_FEASIBLE_OPTION"
    assert infeasible["recommendation"] is None


def test_late_preferred_or_split_candidate_requires_review(desk):
    late = preview(desk, due_date="2026-03-30")
    assert late["status"] == "NEEDS_REVIEW"
    assert "PAST_DEADLINE" in late["flags"]
    assert late["split_option"]["summary"] in late["review_options"]
    split = preview(desk, due_date="2026-05-01", split_requested=True)
    assert split["status"] == "NEEDS_REVIEW"
    assert "SPLIT_REVIEW" in split["flags"]
    assert split["commit_allowed"] is False
    assert split["review_options"] == [split["split_option"]["summary"]]


def test_split_option_uses_permitted_workshops_and_tool_strings(desk):
    text = "Split it, and keep it away from BudgetWorks"
    request = DispatchInput(
        order_id="ORD-109",
        split_requested=True,
        exclusions=[{"workshop_id": "W3", "imposed_by": "Mei", "evidence": "keep it away from BudgetWorks"}],
    )
    result = desk.preview(envelope(text), request, ObjectiveWeights())
    split = result["split_option"]
    permitted = {row["estimate"]["workshop_id"] for row in result["candidates"]}
    assert {part["workshop_id"] for part in split["parts"]} <= permitted
    assert "W3" not in permitted
    assert sum(part["pieces"] for part in split["parts"]) == int(result["order"]["pieces"])
    assert split["expected_turnaround_days"] == max(
        part["estimate"]["expected_turnaround_days"] for part in split["parts"]
    )
    earliest = result["earliest_option"]["estimate"]["expected_turnaround_days"]
    assert split["days_saved"] == earliest - split["expected_turnaround_days"]
    assert split["display"]["eta"] in split["summary"]


def test_snapshot_changes_with_state_and_previews_never_mutate_it(desk):
    first = preview(desk)
    assert first == preview(desk)
    desk.queues["W6"] += 100
    second = preview(desk)
    assert first["snapshot"]["id"] != second["snapshot"]["id"]
    assert first["recommendation"] != second["recommendation"]
    desk.as_of = date(2026, 4, 2)
    assert second["snapshot"]["id"] != preview(desk)["snapshot"]["id"]


@pytest.mark.parametrize(
    "fields",
    [
        {"pieces": True},
        {"pieces": 1.5},
        {"pieces": 0},
        {"split_requested": "yes"},
        {"due_date": "tomorrow"},
        {"preference": "random"},
        {"exclusions": [{}]},
    ],
)
def test_invalid_payload_is_rejected(fields):
    with pytest.raises((ValueError, TypeError)):
        DispatchInput(**fields)


def test_invalid_queue_and_workshop_are_not_repaired(desk):
    with pytest.raises(ValueError, match="Unknown workshop"):
        preview(desk, suggested_workshop="W99")
    desk.queues["W1"] = float("nan")
    with pytest.raises(ValueError, match="snapshot"):
        preview(desk)


def test_baselines_are_reported_for_every_reference_policy(desk):
    result = preview(desk, pieces=500, due_date="2026-04-13")
    assert [row["policy"] for row in result["baselines"]] == [
        "earliest_finish",
        "cheapest",
        "greedy_biggest",
        "random_choice",
    ]
    for row in result["baselines"]:
        assert row["workshop_id"] in desk.workshops
        assert row["name"] == desk.workshops[row["workshop_id"]].name
        assert row["display"]["turnaround"] == f"{row['estimate']['expected_turnaround_days']:.2f} days"
        assert row["meets_deadline"] == (row["estimate"]["lateness_days"] == 0)
        assert "score" not in row["display"]


def test_baselines_are_deterministic_so_a_preview_keeps_one_identity(desk):
    first = preview(desk, pieces=500, due_date="2026-04-13")
    second = preview(desk, pieces=500, due_date="2026-04-13")
    assert first["baselines"] == second["baselines"]
    assert first["snapshot"]["id"] == second["snapshot"]["id"]


def test_a_reference_policy_may_ignore_an_exclusion_this_desk_respects(desk):
    text = "keep it away from BudgetWorks"
    request = DispatchInput(
        order_id="ORD-109",
        pieces=500,
        due_date="2026-04-13",
        exclusions=[{"workshop_id": "W3", "imposed_by": "Mei", "evidence": text}],
    )
    result = desk.preview(envelope(text), request, ObjectiveWeights())
    assert "W3" not in {row["estimate"]["workshop_id"] for row in result["candidates"]}
    cheapest_row = next(row for row in result["baselines"] if row["policy"] == "cheapest")
    assert cheapest_row["workshop_id"] == "W3"
    assert cheapest_row["respects_exclusions"] is False


def test_unresolved_requests_report_no_baselines(desk):
    result = desk.preview(envelope(), DispatchInput(customer="Harbor Knits"), ObjectiveWeights())
    assert result["status"] == "CLARIFY"
    assert result["baselines"] == []


def test_available_days_is_a_tool_field_the_chart_can_plot(desk):
    result = preview(desk, pieces=500, due_date="2026-04-13")
    assert result["candidates"][0]["estimate"]["available_days"] == 12.0
    past = preview(desk, pieces=500, due_date="2026-03-01")
    assert past["candidates"][0]["estimate"]["available_days"] < 0
    assert "PAST_DEADLINE" in past["flags"]


@pytest.mark.parametrize("request_id", ["R20", "R28", "R30"])
def test_declared_impossible_requests_expose_earliest_delivery_and_options(desk, request_id):
    item = next(item for item in read_inbox() if item["request_id"] == request_id)
    fields = json.loads((ROOT / "examples" / "dispatch_inputs.json").read_text())[request_id]
    result = desk.preview(item, DispatchInput(**fields), ObjectiveWeights(lateness=0, defects=1))
    assert result["status"] == "NEEDS_REVIEW"
    assert not result["has_on_time_option"]
    earliest = result["earliest_option"]
    assert earliest["estimate"]["expected_turnaround_days"] == min(
        row["estimate"]["expected_turnaround_days"] for row in result["candidates"]
    )
    assert earliest["display"]["eta"] in result["review_options"][0]
    assert earliest["display"]["lateness"] in result["review_options"][0]
    assert len(result["review_options"]) == 3
    assert not result["commit_allowed"]


def test_revised_v3_cases_and_queue_evidence(desk):
    inputs = json.loads((ROOT / "examples" / "dispatch_inputs.json").read_text())
    for item in read_inbox():
        result = desk.preview(item, DispatchInput(**inputs[item["request_id"]]), ObjectiveWeights())
        if item["request_id"] in {"R04", "R07", "R17", "R22", "R26", "R27"}:
            assert result["status"] == "RECOMMEND"
            assert result["has_on_time_option"]
            assert inputs[item["request_id"]]["order_id"] in item["text"]
        for row in result["candidates"]:
            assert row["display"]["queue"] == f"{desk.queues[row['estimate']['workshop_id']]:.2f} days"
        assert "workshops.csv" in result["assumption"]


def test_impossible_hard_date_keeps_earliest_evidence(desk):
    result = preview(desk, due_date="2026-04-01", preference="cheapest_on_time")
    assert result["status"] == "NO_FEASIBLE_OPTION"
    assert result["earliest_option"]
    assert result["review_options"]
    assert result["recommendation"] is None


def _shown_days(row):
    return float(row["display"]["turnaround"].split()[0])


def test_decision_basis_differences_agree_with_the_displayed_table(desk):
    result = preview(desk, pieces=500, due_date="2026-04-13")
    basis = result["decision_basis"]
    chosen, other = result["candidates"][0], result["candidates"][1]
    assert basis["workshop_id"] == result["recommendation"] == chosen["estimate"]["workshop_id"]
    assert basis["compared_with"] == other["estimate"]["workshop_id"]
    gap = _shown_days(other) - _shown_days(chosen)
    assert f"Next ranked: {other['name']}, {gap:.2f} days slower" in basis["reasons"][-1]
    slack = chosen["estimate"]["available_days"] - _shown_days(chosen)
    assert f"Expected {slack:.2f} days before the deadline." in basis["reasons"]
    assert f"Earliest delivery of the {len(result['candidates'])} permitted workshops." in basis["reasons"]


def test_decision_basis_scopes_a_hard_date_preference_to_on_time_options(desk):
    item = next(item for item in read_inbox() if item["request_id"] == "R21")
    fields = json.loads((ROOT / "examples" / "dispatch_inputs.json").read_text())["R21"]
    assert fields["preference"] == "cheapest_on_time"
    result = desk.preview(item, DispatchInput(**fields), ObjectiveWeights())
    on_time = [row for row in result["candidates"] if row["meets_deadline"]]
    assert 1 < len(on_time) < len(result["candidates"])
    chosen = next(row for row in on_time if row["estimate"]["workshop_id"] == result["recommendation"])
    assert chosen["estimate"]["cost"] == min(row["estimate"]["cost"] for row in on_time)
    reasons = result["decision_basis"]["reasons"]
    assert f"Lowest cost of the {len(on_time)} that meet the deadline." in reasons
    assert reasons[-1].startswith(f"Ranked first: {result['candidates'][0]['name']}, ")
    assert reasons[-1].endswith("misses the deadline.")


def test_decision_basis_is_absent_without_a_chosen_workshop(desk):
    result = desk.preview(envelope(), DispatchInput(customer="Harbor Knits"), ObjectiveWeights())
    assert result["status"] == "CLARIFY"
    assert result["decision_basis"] is None


CAPACITY_ENVELOPE = {"request_id": "CHAT", "time": "now", "requester": "Ravi", "text": "Who can take crewnecks?"}


def test_capacity_question_ranks_without_an_order_and_never_books(desk):
    request = DispatchInput(intent="capacity", product="Crewneck sweater", pieces=1500, due_date="2026-04-15")
    result = desk.preview(CAPACITY_ENVELOPE, request, PRESETS["hybrid"])
    assert result["status"] == "CAPACITY" and result["commit_allowed"] is False
    assert result["batch"]["category"] == "TOPS" and "order" not in result
    on_time = [row for row in result["candidates"] if row["meets_deadline"]]
    assert result["message"].startswith(f"{len(on_time)} of {len(result['candidates'])} permitted workshops")
    assert result["recommendation"] == on_time[0]["estimate"]["workshop_id"]
    assert {row["workshop_id"] for row in result["excluded"]} >= {"W4", "W7"}


@pytest.mark.parametrize(
    "fields,question",
    [
        ({"product": "Widget", "pieces": 100, "due_date": "2026-04-15"}, "Which product"),
        ({"product": "Scarf", "due_date": "2026-04-15"}, "quantity"),
        ({"product": "accessories", "pieces": 100}, "deadline"),
    ],
)
def test_capacity_question_asks_for_what_it_needs(desk, fields, question):
    result = desk.preview(CAPACITY_ENVELOPE, DispatchInput(intent="capacity", **fields), PRESETS["hybrid"])
    assert result["status"] == "CLARIFY" and question in result["message"]
    assert result["candidates"] == []


def test_capacity_question_reports_the_earliest_option_when_none_is_on_time(desk):
    request = DispatchInput(intent="capacity", product="Scarf", pieces=2000, due_date="2026-04-04")
    result = desk.preview(CAPACITY_ENVELOPE, request, PRESETS["hybrid"])
    assert "NO_ON_TIME_OPTION" in result["flags"]
    assert result["earliest_option"]["name"] in result["message"]


def test_reservation_reason_appears_only_when_it_decided_the_ranking(desk):
    envelope = next(item for item in read_inbox() if item["request_id"] == "R07")
    request = DispatchInput(order_id="ORD-063", pieces=100, due_date="2026-04-29")
    reserving = desk.preview(envelope, request, PRESETS["hybrid"])
    plain = desk.preview(envelope, request, replace(PRESETS["hybrid"], capacity_reservation=0.0))
    assert reserving["recommendation"] != plain["recommendation"]
    note = reserving["reservation_note"]
    assert note["held_workshop_id"] == plain["recommendation"]
    assert note["text"] in reserving["decision_basis"]["reasons"]
    assert plain["reservation_note"] is None
