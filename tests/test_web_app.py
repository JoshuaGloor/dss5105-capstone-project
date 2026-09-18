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
    return AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=15).run()


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
    assert result["effective_weights"] == {"lateness": 0.0, "defects": 1.0, "cost": 0.0}
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


def test_request_preference_overrides_global_preset(app):
    app.radio(key="objective").set_value("defects").run()
    app.radio(key="request_id").set_value("R21").run()
    assert not app.exception
    result = app.session_state["preview"]
    assert result["effective_weights"] == {"lateness": 0.0, "defects": 0.0, "cost": 1.0}
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
    separate = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=15).run()
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
