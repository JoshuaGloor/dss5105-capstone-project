import json

import pytest
from streamlit.testing.v1 import AppTest

from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput, read_inbox
from dss5105.web_app import SCENARIOS


@pytest.fixture
def app(monkeypatch):
    from dss5105 import llm

    monkeypatch.setattr(llm, "get_model", lambda **kwargs: pytest.fail("the examples must not construct a model"))
    return AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=15).run()


def send(app, request_id):
    """Click an example in the Examples list, as a dispatcher would."""
    return app.button(key=f"example_{request_id}").click().run()


def requests(app):
    return [row for row in app.session_state["history"] if row["type"] == "request"]


def latest(app):
    return requests(app)[-1]


def markup(app):
    return "".join(element.body for element in app.main if element.type == "html")


def test_page_opens_on_start_screen_without_calling_a_model(app):
    assert not app.exception
    assert "history" not in app.session_state
    assert app.chat_input(key="dispatch_chat")
    assert "Which order needs a workshop today?" in markup(app)
    assert "Try an example scenario" in markup(app)


def test_example_runs_live_python_tools_not_bundled_html_results(app):
    send(app, "R25")
    assert not app.exception
    result = latest(app)["result"]
    assert result["status"] == "RECOMMEND"
    envelope = next(item for item in read_inbox() if item["request_id"] == "R25")
    inputs = json.loads((ROOT / "examples" / "dispatch_inputs.json").read_text())
    expected = DispatchDesk().preview(envelope, DispatchInput(**inputs["R25"]), ObjectiveWeights())
    assert result["candidates"] == expected["candidates"]
    assert "W3" not in {row["estimate"]["workshop_id"] for row in result["candidates"]}


def test_only_the_newest_request_is_shown_but_history_is_kept(app):
    send(app, "R25")
    first = latest(app)["result"]
    send(app, "R08")
    send(app, "R01")
    assert not app.exception
    assert [row["request_id"] for row in requests(app)] == ["R25", "R08", "R01"]
    assert requests(app)[0]["result"] == first
    page = markup(app)
    assert requests(app)[-1]["text"] in page
    assert requests(app)[0]["text"] not in page
    assert requests(app)[1]["text"] not in page
    assert len([button for button in app.button if button.key.startswith("work_")]) == 1
    marked = [button.key for button in app.button if button.label.startswith("\u2713")]
    assert marked == ["example_R01"]


def test_sending_scrolls_back_to_the_top_once(app):
    assert "scrollTo" not in markup(app)
    send(app, "R25")
    assert "scrollTo" in markup(app)
    app.radio(key="objective").set_value("hybrid").run()
    assert "scrollTo" not in markup(app)
    send(app, "R08")
    assert "scrollTo" in markup(app)
    assert "(function ()" in markup(app), "the script must not redeclare globals when it runs again"


EXPECTED = {
    "R07": "RECOMMEND",
    "R30": "NEEDS_REVIEW",
    "R25": "RECOMMEND",
    "R01": "CLARIFY",
    "R05": "CLARIFY",
    "R08": "REFUSE_SUGGESTION",
    "R02": "DECLINE",
}


def test_scenario_cards_cover_the_seven_course_request_kinds():
    assert len(SCENARIOS) == 7
    assert {request_id for request_id, *_ in SCENARIOS} == set(EXPECTED)
    assert {request_id for request_id, *_ in SCENARIOS} <= {item["request_id"] for item in read_inbox()}


@pytest.mark.parametrize("request_id,status", sorted(EXPECTED.items()))
def test_scenario_cards_run_offline_examples(app, request_id, status):
    app.button(key=f"scenario_{request_id}").click().run()
    assert not app.exception
    assert latest(app)["kind"] == "example"
    assert latest(app)["result"]["status"] == status


def test_custom_weights_apply_to_the_next_request_and_zero_weights_fail_closed(app):
    app.radio(key="objective").set_value("custom").run()
    app.slider(key="weight_lateness").set_value(0.0)
    app.slider(key="weight_defects").set_value(1.0)
    app.slider(key="weight_cost").set_value(0.0).run()
    send(app, "R25")
    result = latest(app)["result"]
    assert result["effective_weights"] == {"lateness": 0.0, "defects": 1.0, "cost": 0.0, "deadline_buffer_days": 0}
    assert result["recommendation"] == "W2"
    app.slider(key="weight_defects").set_value(0.0).run()
    assert any("every weight is zero" in error.value.lower() for error in app.error)
    send(app, "R07")
    assert not app.exception
    assert "not all zero" in app.session_state["send_error"]
    assert [row["request_id"] for row in requests(app)] == ["R25"]
    app.slider(key="weight_lateness").set_value(1.0).run()
    send(app, "R07")
    assert "send_error" not in app.session_state
    assert latest(app)["result"]["status"] == "RECOMMEND"


def test_each_answer_keeps_the_objective_it_was_produced_with(app):
    send(app, "R25")
    first = latest(app)
    app.radio(key="objective").set_value("defects").run()
    send(app, "R25")
    assert [row["objective"] for row in requests(app)] == ["lateness", "defects"]
    assert requests(app)[0]["result"] == first["result"]
    assert requests(app)[1]["result"]["effective_weights"] != first["result"]["effective_weights"]
    assert "Objective: <b>Defect</b>" in markup(app)


def test_objective_can_be_chosen_before_the_first_request(app):
    app.radio(key="objective").set_value("hybrid").run()
    assert not app.exception
    app.button(key="scenario_R07").click().run()
    assert latest(app)["objective"] == "hybrid"
    assert app.radio(key="objective").value == "hybrid"


def test_request_preference_overrides_global_preset(app):
    app.radio(key="objective").set_value("defects").run()
    send(app, "R21")
    result = latest(app)["result"]
    assert result["effective_weights"] == {"lateness": 0.0, "defects": 0.0, "cost": 1.0, "deadline_buffer_days": 0}
    chosen = next(row for row in result["candidates"] if row["estimate"]["workshop_id"] == result["recommendation"])
    assert chosen["meets_deadline"]
    assert "Request asks for: <b>cheapest on time</b>" in markup(app)


@pytest.mark.parametrize("request_id", ["R03", "R05", "R08", "R13", "R18", "R20", "R23", "R28", "R30"])
def test_only_ready_answers_offer_saving(app, request_id):
    send(app, request_id)
    assert not app.exception
    assert latest(app)["result"]["status"] != "RECOMMEND"
    assert not [button.key for button in app.button if button.key.startswith("review_")]


def test_ship_date_on_record_is_used_and_split_evidence_is_shown(app):
    send(app, "R06")
    assert not app.exception
    assert latest(app)["result"]["status"] == "RECOMMEND"
    assert "recorded due date" in markup(app)
    send(app, "R23")
    split = latest(app)["result"]["split_option"]
    assert split["summary"] in markup(app)


def open_working(app, entry=None):
    entry = entry or latest(app)
    return app.button(key=f"work_{entry['uid']}").click().run()


def test_working_column_renders_chart_and_reference_policies_from_tool_fields(app):
    send(app, "R25")
    result = latest(app)["result"]
    assert not [element for element in app.main if element.type in ("arrow_vega_lite_chart", "vega_lite_chart")]
    open_working(app)
    charts = [element for element in app.main if element.type in ("arrow_vega_lite_chart", "vega_lite_chart")]
    assert charts, "the comparison must include a chart"
    html = markup(app)
    assert "This desk (effective weights)" in html
    cheapest = next(row for row in result["baselines"] if row["policy"] == "cheapest")
    assert cheapest["respects_exclusions"] is False
    assert "Ignores an exclusion" in html
    assert cheapest["display"]["turnaround"] in html


def test_working_opens_beside_the_answer_and_follows_the_newest_one(app):
    send(app, "R25")
    first = latest(app)
    assert "working" not in app.session_state
    open_working(app, first)
    assert not app.exception
    assert app.session_state["working"] == first["uid"]
    assert "R25: Mei" in markup(app)
    assert app.button(key=f"work_{first['uid']}").label == "Hide working"
    send(app, "R08")
    second = latest(app)
    assert app.session_state["working"] == second["uid"]
    assert "R08: " in markup(app)
    assert "R25: Mei" not in markup(app)
    assert len([e for e in app.main if e.type in ("arrow_vega_lite_chart", "vega_lite_chart")]) == 1


def test_hide_working_closes_it_even_after_it_followed_a_newer_answer(app):
    send(app, "R25")
    open_working(app)
    send(app, "R08")
    assert app.session_state["working"] == latest(app)["uid"]
    assert app.button(key=f"work_{latest(app)['uid']}").label == "Hide working"
    app.button(key=f"work_{latest(app)['uid']}").click().run()
    assert "working" not in app.session_state
    assert app.button(key=f"work_{latest(app)['uid']}").label == "Show working"


def test_working_is_cleared_with_the_chat(app):
    send(app, "R25")
    open_working(app)
    app.button(key="clear_chat").click().run()
    assert "working" not in app.session_state
    assert "Which order needs a workshop today?" in markup(app)


@pytest.mark.parametrize("request_id", ["R20", "R28", "R30"])
def test_impossible_request_shows_tool_options(app, request_id):
    send(app, request_id)
    result = latest(app)["result"]
    assert result["review_options"][0] in markup(app)


def test_demo_confirmation_is_two_step_and_changes_nothing(app):
    send(app, "R25")
    queues = latest(app)["result"]["snapshot"]["queues"].copy()
    uid = latest(app)["uid"]
    app.button(key=f"review_{uid}").click().run()
    assert app.session_state["reviewing"] == uid
    assert not latest(app)["confirmed"]
    app.button(key="confirm_demo").click().run()
    assert not app.exception
    assert latest(app)["confirmed"]
    assert latest(app)["result"]["snapshot"]["queues"] == queues
    assert latest(app)["result"]["commit_allowed"] is False
    assert app.session_state["history"][-1]["type"] == "note"
    assert "Nothing was saved" in app.session_state["history"][-1]["text"]


def test_cancel_does_not_confirm_and_sending_again_closes_the_review(app):
    send(app, "R25")
    app.button(key=f"review_{latest(app)['uid']}").click().run()
    app.button(key="cancel_confirmation").click().run()
    assert "reviewing" not in app.session_state
    assert not latest(app)["confirmed"]
    app.button(key=f"review_{latest(app)['uid']}").click().run()
    send(app, "R07")
    assert "reviewing" not in app.session_state


def test_next_button_sends_the_next_unsent_example(app):
    send(app, "R01")
    send(app, "R25")
    app.button(key=f"review_{latest(app)['uid']}").click().run()
    app.button(key="confirm_demo").click().run()
    note = app.session_state["history"][-1]
    assert note["next"] == "R02"
    app.button(key="next_" + note["uid"]).click().run()
    assert latest(app)["request_id"] == "R02"


def test_clear_chat_returns_to_the_start_screen(app):
    send(app, "R25")
    app.button(key="clear_chat").click().run()
    assert "history" not in app.session_state
    assert "Which order needs a workshop today?" in markup(app)


def test_saved_plan_requires_identity_and_persists_across_sessions(app, tmp_path, monkeypatch):
    from dss5105 import records

    path = tmp_path / "ui-plan.sqlite3"
    monkeypatch.setattr(records, "DEFAULT_STORE_PATH", path)
    app.radio(key="workspace_mode").set_value("saved").run()
    send(app, "R25")
    initial_queues = latest(app)["result"]["snapshot"]["queues"].copy()
    assert latest(app)["result"]["commit_allowed"]
    app.button(key=f"review_{latest(app)['uid']}").click().run()
    assert app.button(key="confirm_allocation").disabled
    app.text_input(key="confirmed_by").set_value("Test dispatcher").run()
    assert not app.button(key="confirm_allocation").disabled
    app.button(key="confirm_allocation").click().run()
    assert not app.exception
    assert latest(app)["saved"]
    saved = records.AllocationStore(path).records()
    assert len(saved) == 1
    assert saved[0]["confirmed_by"] == "Test dispatcher"
    send(app, "R25")
    assert latest(app)["result"]["status"] == "ALREADY_ALLOCATED"
    separate = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=15).run()
    separate.button(key="example_R25").click().run()
    assert latest(separate)["result"]["snapshot"]["queues"] == initial_queues
    separate.radio(key="workspace_mode").set_value("saved").run()
    separate.button(key="example_R25").click().run()
    assert latest(separate)["result"]["status"] == "ALREADY_ALLOCATED"
    assert latest(separate)["result"]["snapshot"]["queues"] == saved[0]["queues_after"]


def test_older_independent_answer_cannot_be_saved_in_the_saved_plan(app, tmp_path, monkeypatch):
    from dss5105 import records

    monkeypatch.setattr(records, "DEFAULT_STORE_PATH", tmp_path / "mixed-plan.sqlite3")
    send(app, "R25")
    app.radio(key="workspace_mode").set_value("saved").run()
    assert not [button.key for button in app.button if button.key.startswith("review_")]
    assert not records.AllocationStore().records()


def test_switching_workspace_closes_a_pending_review_and_reserves_nothing(app, tmp_path, monkeypatch):
    from dss5105 import records

    monkeypatch.setattr(records, "DEFAULT_STORE_PATH", tmp_path / "mode-plan.sqlite3")
    app.radio(key="workspace_mode").set_value("saved").run()
    send(app, "R25")
    app.button(key=f"review_{latest(app)['uid']}").click().run()
    assert "confirmation_key" in app.session_state
    app.radio(key="workspace_mode").set_value("independent").run()
    assert "reviewing" not in app.session_state
    assert "confirmation_key" not in app.session_state
    assert not records.AllocationStore().records()


def test_failed_save_never_shows_success_receipt(app, tmp_path, monkeypatch):
    from dss5105 import records

    monkeypatch.setattr(records, "DEFAULT_STORE_PATH", tmp_path / "failed-plan.sqlite3")
    app.radio(key="workspace_mode").set_value("saved").run()
    send(app, "R25")
    app.button(key=f"review_{latest(app)['uid']}").click().run()
    app.text_input(key="confirmed_by").set_value("Test dispatcher").run()

    def reject(*args, **kwargs):
        raise records.AllocationError("The preview is stale. Refresh and review again.")

    monkeypatch.setattr(records.AllocationStore, "commit_allocation", reject)
    app.button(key="confirm_allocation").click().run()
    assert not app.exception
    assert any("stale" in error.value for error in app.error)
    assert not latest(app)["saved"]
    assert not records.AllocationStore().records()
