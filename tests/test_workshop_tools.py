import json
from dataclasses import replace
from datetime import date

import pytest
from streamlit.testing.v1 import AppTest

from dss5105.allocator import ObjectiveWeights, estimate_delivery
from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput, LoadScenario, WorkshopQuery, read_inbox
from dss5105.harness import eligible_workshops
from dss5105.records import AllocationStore


def test_register_checks_helper_membership_and_snapshot_without_mutating():
    desk = DispatchDesk()
    before = desk.snapshot()
    query = WorkshopQuery(category="TOPS", pieces=1500, due_date="2026-04-15")
    result = desk.query_register(query)
    batch = {
        "order_id": "test",
        "category": query.category,
        "pieces": query.pieces,
        "sent_date": desk.as_of,
        "due_date": desk.as_of,
    }
    expected = {w.workshop_id for w in eligible_workshops(batch, desk.workshops)}
    assert {row["workshop_id"] for row in result["matches"] if row["eligible"]} == expected
    assert {row["workshop_id"] for row in result["matches"] if not row["eligible"]} == {"W7", "W8"}
    assert result["snapshot"] == before == desk.snapshot()
    for row in result["matches"]:
        if row["estimate"]:
            estimate = estimate_delivery(
                {**batch, "due_date": date.fromisoformat(query.due_date)},
                desk.workshops[row["workshop_id"]],
                desk.queues,
            )
            for key, value in desk.display_fields(estimate).items():
                assert row["display"][key] == value
        else:
            assert "eta" not in row["display"]


def test_register_profile_filters_and_empty_match():
    desk = DispatchDesk()
    result = desk.query_register(WorkshopQuery(status="SUSPENDED"))
    assert [row["workshop_id"] for row in result["matches"]] == ["W7"]
    assert result["matches"][0]["eligible"] is None
    desk.workshops = {key: w for key, w in desk.workshops.items() if w.status == "ACTIVE"}
    desk.queues = {key: value for key, value in desk.queues.items() if key in desk.workshops}
    for key in desk.workshops:
        desk.workshops[key] = replace(desk.workshops[key], status="SUSPENDED")
    # A known status can legitimately have no matching category.
    desk.workshops["W1"] = replace(desk.workshops["W1"], status="ACTIVE")
    assert desk.query_register(WorkshopQuery(category="ACCESSORIES", status="ACTIVE"))["status"] == "NO_MATCHES"


@pytest.mark.parametrize(
    "payload",
    [
        {"pieces": 100},
        {"category": "TOPS", "pieces": True},
        {"category": "TOPS", "pieces": 0},
        {"due_date": "2026-04-15"},
        {"category": "TOPS", "pieces": 100, "due_date": "bad"},
    ],
)
def test_invalid_register_inputs_fail_closed(payload):
    with pytest.raises(ValueError):
        WorkshopQuery(**payload)


@pytest.mark.parametrize("query", [WorkshopQuery(category="unknown"), WorkshopQuery(status="unknown")])
def test_unknown_filters_fail_closed(query):
    with pytest.raises(ValueError):
        DispatchDesk().query_register(query)


@pytest.mark.parametrize("queues", [{}, {"W1": float("nan")}, {"W1": -1}, {"W1": True}])
def test_register_requires_valid_queue_snapshot(queues):
    desk = DispatchDesk()
    desk.queues = {**desk.queues, **queues} if queues else {}
    with pytest.raises(ValueError, match="queue snapshot"):
        desk.query_register(WorkshopQuery())


def test_extra_work_turns_an_on_time_option_late_and_preserves_state():
    desk = DispatchDesk()
    snapshot = desk.snapshot()
    scenario = LoadScenario("W1", "TOPS", 1500, 1500, "2026-04-15")
    result = desk.probe_load(scenario)
    assert result["status"] == "ASSESSED"
    assert result["before"]["meets_deadline"]
    assert not result["after"]["meets_deadline"]
    increment = result["additional_processing_days"]
    assert increment == pytest.approx(
        1500 / desk.workshops["W1"].capacity * (1 + 0.5 * desk.workshops["W1"].defect_rate)
    )
    assert result["after"]["estimate"]["expected_turnaround_days"] - result["before"]["estimate"][
        "expected_turnaround_days"
    ] == pytest.approx(increment)
    assert result["after"]["estimate"]["cost"] == result["before"]["estimate"]["cost"]
    assert result["fastest_alternative"]["workshop_id"] != "W1"
    assert result["snapshot"] == snapshot == desk.snapshot()
    assert result["queues_after"]["W2"] == desk.queues["W2"]


@pytest.mark.parametrize(
    "scenario",
    [
        LoadScenario("W7", "TOPS", 100, 100, "2026-04-15"),
        LoadScenario("W8", "TOPS", 100, 301, "2026-04-15"),
        LoadScenario("W4", "TOPS", 100, 100, "2026-04-15"),
    ],
)
def test_ineligible_workload_is_an_explicit_unsupported_scenario(scenario):
    result = DispatchDesk().probe_load(scenario)
    assert result["status"] == "UNSUPPORTED"
    assert result["reasons"]
    assert result["before"] is None and result["after"] is None


def test_saved_tools_use_current_queues_but_never_reserve(tmp_path):
    store = AllocationStore(tmp_path / "plan.sqlite3")
    query = WorkshopQuery(category="TOPS", pieces=1500, due_date="2026-04-15")
    before = store.query_register(query)
    fixture = json.loads((ROOT / "examples" / "dispatch_inputs.json").read_text())["R25"]
    envelope = next(row for row in read_inbox() if row["request_id"] == "R25")
    receipt = store.commit_allocation(
        store.preview(envelope, DispatchInput(**fixture), ObjectiveWeights()), "Tester", "save", confirmed=True
    )
    after = store.query_register(query)
    assert after["snapshot"]["queues"] == receipt["queues_after"]
    assert after["snapshot"]["id"] != before["snapshot"]["id"]
    assert after["storage"]["revision"] == receipt["revision_after"]
    store.probe_load(LoadScenario("W1", "TOPS", 1500, 1500, "2026-04-15"))
    assert store.query_register(query) == after
    assert store.records() == [receipt]


def test_workshop_workspace_never_calls_model_and_recomputes_on_mode_switch(monkeypatch, tmp_path):
    from dss5105 import llm, records

    monkeypatch.setattr(llm, "get_model", lambda **kwargs: pytest.fail("Workshop tools must stay offline"))
    monkeypatch.setattr(records, "DEFAULT_STORE_PATH", tmp_path / "ui.sqlite3")
    app = AppTest.from_function(workshops_page, default_timeout=15).run()
    assert not app.exception
    app.button(key="check_capacity").click().run()
    assert app.session_state["register_result"]["query"]["pieces"] == 1500
    app.button(key="check_load").click().run()
    assert not app.exception
    assert app.session_state["load_result"]["status"] == "ASSESSED"
    app.radio(key="workspace_mode").set_value("saved").run()
    assert "storage" in app.session_state["register_result"]
    assert "storage" in app.session_state["load_result"]
    assert not records.AllocationStore().records()


def workshops_page():
    from dss5105.workshop_ui import render_page

    render_page()
