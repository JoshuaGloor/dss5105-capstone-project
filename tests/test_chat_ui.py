import pytest
from streamlit.testing.v1 import AppTest

from dss5105 import llm
from dss5105.dispatch import ROOT
from dss5105.replies import build_reply


class FakeModel:
    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = 0

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        self.calls += 1
        output = self.outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        return output


def patch(*updates, exclusions=None, needs=None):
    return {
        "updates": [{"field": field, "value": value, "evidence": value} for field, value in updates],
        "exclusions": exclusions or [],
        "needs": needs or [],
    }


@pytest.fixture
def ui(monkeypatch):
    fake = FakeModel([])
    monkeypatch.setattr(llm, "get_model", lambda **kwargs: fake)
    app = AppTest.from_file(ROOT / "tests" / "desk_page.py", default_timeout=15).run()
    assert fake.calls == 0
    assert "history" not in app.session_state
    return app, fake


def say(app, text):
    return app.chat_input(key="dispatch_chat").set_value(text).run()


def requests(app):
    return [row for row in app.session_state["history"] if row["type"] == "request"]


def test_validated_chat_can_be_saved_without_another_provider_call(tmp_path, monkeypatch):
    from dss5105 import records

    monkeypatch.setattr(records, "DEFAULT_STORE_PATH", tmp_path / "chat-plan.sqlite3")
    fake = FakeModel([patch(("order_id", "ORD-109"))])
    monkeypatch.setattr(llm, "get_model", lambda **kwargs: fake)
    app = AppTest.from_file(ROOT / "tests" / "desk_page.py", default_timeout=15).run()
    app.radio(key="workspace_mode").set_value("saved").run()
    say(app, "Please allocate ORD-109.")
    assert not app.exception
    entry = requests(app)[-1]
    assert entry["kind"] == "chat"
    assert entry["result"]["commit_allowed"]
    app.button(key=f"review_{entry['uid']}").click().run()
    app.text_input(key="confirmed_by").set_value("Chat dispatcher").run()
    app.button(key="confirm_allocation").click().run()
    assert not app.exception
    assert fake.calls == 1
    saved = records.AllocationStore().records()
    assert len(saved) == 1
    assert saved[0]["intake_evidence"]["conversation"]["turns"][0]["text"] == "Please allocate ORD-109."
    assert requests(app)[-1]["saved"]


def test_chat_clarifies_then_allocates_without_losing_exclusion(ui):
    app, fake = ui
    fake.outputs = [
        patch(
            ("order_id", "ORD-109"),
            exclusions=[{"workshop": "BudgetWorks", "imposed_by": "", "evidence": "no BudgetWorks"}],
            needs=["deadline"],
        ),
        patch(("due_date", "Apr 15")),
    ]
    say(app, "ORD-109, no BudgetWorks; I will confirm the new deadline.")
    assert not app.exception
    assert requests(app)[-1]["result"]["status"] == "CLARIFY"
    assert not [button.key for button in app.button if button.key.startswith("review_")]
    say(app, "Apr 15")
    assert not app.exception
    assert [row["result"]["status"] for row in requests(app)] == ["CLARIFY", "RECOMMEND"]
    final = requests(app)[-1]["result"]
    assert "W3" not in {row["estimate"]["workshop_id"] for row in final["candidates"]}
    assert fake.calls == 2
    app.radio(key="objective").set_value("hybrid").run()
    assert fake.calls == 2
    assert len(app.session_state["conversation"].turns) == 2


def test_failed_followup_adds_nothing_and_retry_is_explicit(ui):
    app, fake = ui
    fake.outputs = [
        patch(("order_id", "ORD-109")),
        RuntimeError("private-error-secret"),
        patch(("due_date", "Apr 15")),
    ]
    say(app, "ORD-109")
    entry = requests(app)[-1]
    app.button(key=f"review_{entry['uid']}").click().run()
    say(app, "Apr 15")
    assert not app.exception
    assert len(requests(app)) == 1
    assert "reviewing" not in app.session_state
    assert app.chat_input(key="dispatch_chat").disabled
    assert "private-error-secret" not in app.error[0].value
    assert len(app.session_state["conversation"].turns) == 1
    app.run()
    assert fake.calls == 2
    app.button(key="retry_intake").click().run()
    assert fake.calls == 3
    assert [row["result"]["status"] for row in requests(app)] == ["RECOMMEND", "RECOMMEND"]
    assert "pending_turn" not in app.session_state


def test_new_request_discards_constraints_but_keeps_the_thread(ui):
    app, fake = ui
    fake.outputs = [patch(("order_id", "ORD-109"))]
    say(app, "ORD-109")
    app.button(key="new_chat").click().run()
    assert not app.exception
    assert "conversation" not in app.session_state
    assert len(requests(app)) == 1
    assert fake.calls == 1


def test_examples_do_not_call_the_model_and_do_not_need_a_new_request(ui):
    app, fake = ui
    app.button(key="scenario_R07").click().run()
    assert not app.exception
    assert fake.calls == 0
    assert requests(app)[-1]["kind"] == "example"
    assert "conversation" not in app.session_state


def test_clicking_a_matching_order_resolves_without_a_model_call(ui):
    app, fake = ui
    fake.outputs = [patch(("customer", "TrendCart"), needs=["order"])]
    say(app, "Can we get the TrendCart order moving?")
    first = requests(app)[-1]
    assert first["result"]["status"] == "CLARIFY"
    choices = [choice["value"] for choice in build_reply(first["result"])["choices"]]
    app.button(key=f"choice_{choices.index('ORD-017')}").click().run()
    assert not app.exception
    assert fake.calls == 1
    final = requests(app)[-1]
    assert final["result"]["status"] == "RECOMMEND"
    assert final["result"]["order"]["order_id"] == "ORD-017"
    assert final["text"] == "ORD-017"
    assert len(requests(app)) == 2


def test_clicking_the_alternative_replaces_a_refused_workshop(ui):
    app, fake = ui
    fake.outputs = [patch(("order_id", "ORD-008"), ("suggested_workshop", "OldMill"))]
    say(app, "OldMill is free right now - give them ORD-008.")
    first = requests(app)[-1]["result"]
    assert first["status"] == "REFUSE_SUGGESTION"
    app.button(key="choice_0").click().run()
    assert not app.exception
    assert fake.calls == 1
    result = requests(app)[-1]["result"]
    assert result["status"] == "RECOMMEND"
    assert result["recommendation"] == first["alternative"]
    provenance = result["conversation"]["provenance"][-1]
    assert (provenance["field"], provenance["speaker"]) == ("suggested_workshop", "Dispatcher")


def test_earlier_answer_keeps_its_objective_when_settings_change(ui):
    app, fake = ui
    fake.outputs = [patch(("order_id", "ORD-109"))]
    say(app, "ORD-109")
    before = requests(app)[0]["result"]
    app.radio(key="objective").set_value("defects").run()
    assert fake.calls == 1
    assert requests(app)[0]["result"] == before
    assert requests(app)[0]["objective"] == "hybrid"
