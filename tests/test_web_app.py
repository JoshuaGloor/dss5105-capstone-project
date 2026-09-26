import json

import pytest
from streamlit.testing.v1 import AppTest

from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput, read_inbox


@pytest.fixture
def app(monkeypatch):
    from dss5105 import llm

    def no_provider(*args, **kwargs):
        raise AssertionError("The demo page must not construct a live model")

    monkeypatch.setattr(llm, "get_model", no_provider)
    return offline_app()


def offline_app():
    """The page opens on the chat; these tests exercise the offline examples mode."""
    app = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=15).run()
    assert "preview" not in app.session_state
    return app.radio(key="input_source").set_value("examples").run()


def test_page_opens_on_chat_without_calling_a_model(monkeypatch):
    from dss5105 import llm

    monkeypatch.setattr(llm, "get_model", lambda **kwargs: pytest.fail("no model call on page load"))
    app = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=15).run()
    assert not app.exception
    assert app.radio(key="input_source").value == "chat"
    assert app.button(key="interpret_inbox")
    assert "preview" not in app.session_state


def test_page_uses_live_python_tools_not_bundled_html_results(app):
    assert not app.exception
    assert app.radio(key="request_id").value == "R25"
    assert app.session_state["preview"]["status"] == "RECOMMEND"
    assert app.button(key="review_confirmation").disabled is False
    envelope = next(item for item in read_inbox() if item["request_id"] == "R25")
    inputs = json.loads((ROOT / "examples" / "dispatch_inputs.json").read_text())
    expected = DispatchDesk().preview(envelope, DispatchInput(**inputs["R25"]), ObjectiveWeights())
    assert app.session_state["preview"]["candidates"] == expected["candidates"]
    assert "W3" not in {row["estimate"]["workshop_id"] for row in expected["candidates"]}


def test_custom_weights_recompute_and_invalid_weights_fail_closed(app):
    app.radio(key="objective").set_value("custom").run()
    app.slider(key="weight_lateness").set_value(0.0)
    app.slider(key="weight_defects").set_value(1.0)
    app.slider(key="weight_cost").set_value(0.0).run()
    assert not app.exception
    result = app.session_state["preview"]
    assert result["effective_weights"] == {"lateness": 0.0, "defects": 1.0, "cost": 0.0, "deadline_buffer_days": 0}
    assert result["recommendation"] == "W2"
    app.slider(key="weight_defects").set_value(0.0).run()
    assert not app.exception
    assert "not all zero" in app.error[0].value
    assert "preview" not in app.session_state
    assert "confirmed_preview" not in app.session_state
    assert not app.button
    app.slider(key="weight_lateness").set_value(1.0).run()
    assert not app.error
    assert app.session_state["preview"]["status"] == "RECOMMEND"


@pytest.mark.parametrize(
    "request_id,status",
    [
        ("R03", "CLARIFY"),
        ("R05", "CLARIFY"),
        ("R08", "REFUSE_SUGGESTION"),
        ("R13", "DECLINE"),
        ("R18", "DECLINE"),
        ("R20", "NEEDS_REVIEW"),
        ("R23", "NEEDS_REVIEW"),
    ],
)
def test_exception_states_cannot_be_confirmed(app, request_id, status):
    app.radio(key="request_id").set_value(request_id).run()
    assert not app.exception
    assert app.session_state["preview"]["status"] == status
    assert app.button(key="review_confirmation").disabled
    assert "confirmed_preview" not in app.session_state


def test_ship_date_on_record_is_used_and_split_evidence_is_shown(app):
    app.radio(key="request_id").set_value("R06").run()
    assert not app.exception
    assert app.session_state["preview"]["status"] == "RECOMMEND"
    assert any("recorded due date" in caption.value for caption in app.caption)
    app.radio(key="request_id").set_value("R23").run()
    assert not app.exception
    split = app.session_state["preview"]["split_option"]
    assert any(split["summary"] == block.value for block in app.markdown)


def test_request_preference_overrides_global_preset(app):
    app.radio(key="objective").set_value("defects").run()
    app.radio(key="request_id").set_value("R21").run()
    assert not app.exception
    result = app.session_state["preview"]
    assert result["effective_weights"] == {"lateness": 0.0, "defects": 0.0, "cost": 1.0, "deadline_buffer_days": 0}
    app.radio(key="objective").set_value("hybrid").run()
    assert app.session_state["preview"]["effective_weights"] == result["effective_weights"]
    assert app.session_state["preview"]["recommendation"] == result["recommendation"]
    chosen = next(row for row in result["candidates"] if row["estimate"]["workshop_id"] == result["recommendation"])
    assert chosen["meets_deadline"]


def test_demo_confirmation_is_two_step_and_invalidated_by_settings(app):
    queues = app.session_state["preview"]["snapshot"]["queues"].copy()
    app.button(key="review_confirmation").click().run()
    assert "confirmed_preview" not in app.session_state
    assert app.session_state["reviewing_preview"] == app.session_state["preview_id"]
    app.button(key="confirm_demo").click().run()
    assert not app.exception
    assert app.session_state["confirmed_preview"] == app.session_state["preview_id"]
    assert app.session_state["preview"]["snapshot"]["queues"] == queues
    assert app.session_state["preview"]["commit_allowed"] is False
    app.radio(key="objective").set_value("defects").run()
    assert "confirmed_preview" not in app.session_state
    assert "reviewing_preview" not in app.session_state
    app.radio(key="objective").set_value("lateness").run()
    assert "confirmed_preview" not in app.session_state


def test_switching_request_clears_pending_confirmation_and_sessions_are_separate(app):
    app.button(key="review_confirmation").click().run()
    app.radio(key="request_id").set_value("R03").run()
    assert "reviewing_preview" not in app.session_state
    separate = offline_app()
    assert separate.radio(key="request_id").value == "R25"
    assert "reviewing_preview" not in separate.session_state
    assert "confirmed_preview" not in separate.session_state


def test_cancel_does_not_confirm(app):
    app.button(key="review_confirmation").click().run()
    app.button(key="cancel_confirmation").click().run()
    assert not app.exception
    assert "reviewing_preview" not in app.session_state
    assert "confirmed_preview" not in app.session_state


def test_chart_and_baseline_table_render_from_tool_fields(app):
    assert not app.exception
    preview = app.session_state["preview"]
    charts = [element for element in app.main if element.type in ("arrow_vega_lite_chart", "vega_lite_chart")]
    assert charts, "the candidate comparison must include a chart"
    markup = "".join(element.body for element in app.main if element.type == "html")
    assert "Cheapest eligible" in markup
    assert "This desk (effective weights)" in markup
    cheapest_row = next(row for row in preview["baselines"] if row["policy"] == "cheapest")
    assert cheapest_row["name"] in markup
    assert cheapest_row["display"]["turnaround"] in markup


def test_baseline_row_shows_when_a_reference_policy_breaks_an_exclusion(app):
    preview = app.session_state["preview"]
    assert preview["input"]["exclusions"], "R25 excludes BudgetWorks"
    cheapest_row = next(row for row in preview["baselines"] if row["policy"] == "cheapest")
    assert cheapest_row["respects_exclusions"] is False
    markup = "".join(element.body for element in app.main if element.type == "html")
    assert "Ignores an exclusion" in markup


def test_changing_weights_recomputes_the_baseline_comparison(app):
    before = app.session_state["preview"]
    app.radio(key="objective").set_value("defects").run()
    after = app.session_state["preview"]
    assert after["effective_weights"] != before["effective_weights"]
    assert after["baselines"] == before["baselines"], "reference policies do not follow our weights"
    assert app.session_state["preview_id"] != app.session_state.get("confirmed_preview")


@pytest.mark.parametrize("request_id", ["R20", "R28", "R30"])
def test_impossible_request_displays_tool_options_and_blocks_confirmation(app, request_id):
    app.radio(key="request_id").set_value(request_id).run()
    result = app.session_state["preview"]
    assert not app.exception
    content = " ".join(element.value for element in app.markdown)
    assert result["review_options"][0] in content
    assert app.button(key="review_confirmation").disabled


def test_saved_plan_requires_identity_and_persists_across_sessions(app, tmp_path, monkeypatch):
    from dss5105 import records

    path = tmp_path / "ui-plan.sqlite3"
    monkeypatch.setattr(records, "DEFAULT_STORE_PATH", path)
    initial_queues = app.session_state["preview"]["snapshot"]["queues"]
    app.radio(key="workspace_mode").set_value("saved").run()
    assert not app.exception
    assert app.session_state["preview"]["commit_allowed"]
    app.button(key="review_confirmation").click().run()
    assert app.button(key="confirm_allocation").disabled
    app.text_input(key="confirmed_by").set_value("Test dispatcher").run()
    assert not app.button(key="confirm_allocation").disabled
    app.button(key="confirm_allocation").click().run()
    assert not app.exception
    assert app.session_state["preview"]["status"] == "ALREADY_ALLOCATED"
    assert app.button(key="review_confirmation").disabled
    saved = records.AllocationStore(path).records()
    assert len(saved) == 1
    assert saved[0]["confirmed_by"] == "Test dispatcher"
    assert app.session_state["allocation_receipt"]["allocation_id"] == saved[0]["allocation_id"]
    separate = offline_app()
    assert separate.session_state["preview"]["snapshot"]["queues"] == initial_queues
    separate.radio(key="workspace_mode").set_value("saved").run()
    assert separate.session_state["preview"]["status"] == "ALREADY_ALLOCATED"
    assert separate.session_state["preview"]["snapshot"]["queues"] == saved[0]["queues_after"]


def test_switching_mode_cancels_pending_save_and_does_not_reserve(app, tmp_path, monkeypatch):
    from dss5105 import records

    monkeypatch.setattr(records, "DEFAULT_STORE_PATH", tmp_path / "mode-plan.sqlite3")
    app.radio(key="workspace_mode").set_value("saved").run()
    app.button(key="review_confirmation").click().run()
    assert "confirmation_key" in app.session_state
    app.radio(key="workspace_mode").set_value("independent").run()
    assert "reviewing_preview" not in app.session_state
    assert "confirmation_key" not in app.session_state
    assert not records.AllocationStore().records()


def test_failed_save_never_shows_success_receipt(app, tmp_path, monkeypatch):
    from dss5105 import records

    monkeypatch.setattr(records, "DEFAULT_STORE_PATH", tmp_path / "failed-plan.sqlite3")
    app.radio(key="workspace_mode").set_value("saved").run()
    app.button(key="review_confirmation").click().run()
    app.text_input(key="confirmed_by").set_value("Test dispatcher").run()

    def reject(*args, **kwargs):
        raise records.AllocationError("The preview is stale. Refresh and review again.")

    monkeypatch.setattr(records.AllocationStore, "commit_allocation", reject)
    app.button(key="confirm_allocation").click().run()
    assert not app.exception
    assert any("stale" in error.value for error in app.error)
    assert "allocation_receipt" not in app.session_state
    assert not records.AllocationStore().records()
