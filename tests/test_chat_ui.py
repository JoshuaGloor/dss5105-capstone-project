import pytest
from streamlit.testing.v1 import AppTest

from dss5105 import llm
from dss5105.dispatch import ROOT


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


def test_validated_chat_can_be_saved_without_another_provider_call(tmp_path, monkeypatch):
    from dss5105 import records

    monkeypatch.setattr(records, "DEFAULT_STORE_PATH", tmp_path / "chat-plan.sqlite3")
    fake = FakeModel([patch(("order_id", "ORD-109"))])
    monkeypatch.setattr(llm, "get_model", lambda **kwargs: fake)
    app = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=15).run()
    app.radio(key="workspace_mode").set_value("saved").run()
    app.radio(key="input_source").set_value("chat").run()
    app.chat_input(key="dispatch_chat").set_value("Please allocate ORD-109.").run()
    assert not app.exception
    assert app.session_state["preview"]["commit_allowed"]
    app.button(key="review_confirmation").click().run()
    app.text_input(key="confirmed_by").set_value("Chat dispatcher").run()
    app.button(key="confirm_allocation").click().run()
    assert not app.exception
    assert fake.calls == 1
    saved = records.AllocationStore().records()
    assert len(saved) == 1
    assert saved[0]["intake_evidence"]["conversation"]["turns"][0]["text"] == "Please allocate ORD-109."
    assert app.session_state["preview"]["status"] == "ALREADY_ALLOCATED"


@pytest.fixture
def ui(monkeypatch):
    fake = FakeModel([])
    monkeypatch.setattr(llm, "get_model", lambda **kwargs: fake)
    app = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=15).run()
    app.radio(key="input_source").set_value("chat").run()
    assert fake.calls == 0
    assert "preview" not in app.session_state
    return app, fake


def test_chat_clarifies_then_allocates_without_losing_exclusion(ui):
    app, fake = ui
    fake.outputs = [
        patch(
            ("order_id", "ORD-109"),
            exclusions=[
                {
                    "workshop": "BudgetWorks",
                    "imposed_by": "",
                    "evidence": "no BudgetWorks",
                }
            ],
            needs=["deadline"],
        ),
        patch(("due_date", "Apr 15")),
    ]
    app.chat_input(key="dispatch_chat").set_value("ORD-109, no BudgetWorks; I will confirm the new deadline.").run()
    assert not app.exception
    assert app.session_state["preview"]["status"] == "CLARIFY"
    assert app.button(key="review_confirmation").disabled
    app.chat_input(key="dispatch_chat").set_value("Apr 15").run()
    assert not app.exception
    assert app.session_state["preview"]["status"] == "RECOMMEND"
    assert "W3" not in {row["estimate"]["workshop_id"] for row in app.session_state["preview"]["candidates"]}
    assert fake.calls == 2
    app.radio(key="objective").set_value("hybrid").run()
    assert fake.calls == 2
    assert len(app.session_state["conversation"].turns) == 2


def test_failed_followup_hides_old_preview_and_retry_is_explicit(ui):
    app, fake = ui
    fake.outputs = [
        patch(("order_id", "ORD-109")),
        RuntimeError("private-error-secret"),
        patch(("due_date", "Apr 15")),
    ]
    app.chat_input(key="dispatch_chat").set_value("ORD-109").run()
    app.button(key="review_confirmation").click().run()
    app.chat_input(key="dispatch_chat").set_value("Apr 15").run()
    assert not app.exception
    assert "preview" not in app.session_state
    assert "reviewing_preview" not in app.session_state
    assert app.chat_input(key="dispatch_chat").disabled
    assert "private-error-secret" not in app.error[0].value
    assert len(app.session_state["conversation"].turns) == 1
    app.run()
    assert fake.calls == 2
    app.button(key="retry_intake").click().run()
    assert fake.calls == 3
    assert app.session_state["preview"]["status"] == "RECOMMEND"
    assert "pending_turn" not in app.session_state


def test_new_request_discards_previous_constraints_and_confirmation(ui):
    app, fake = ui
    fake.outputs = [patch(("order_id", "ORD-109"))]
    app.chat_input(key="dispatch_chat").set_value("ORD-109").run()
    app.button(key="review_confirmation").click().run()
    app.button(key="confirm_demo").click().run()
    assert "confirmed_preview" in app.session_state
    app.button(key="new_chat").click().run()
    assert not app.exception
    assert "conversation" not in app.session_state
    assert "confirmed_preview" not in app.session_state
    assert "preview" not in app.session_state
    assert fake.calls == 1


def test_switching_modes_clears_confirmation_without_provider_call(ui):
    app, fake = ui
    fake.outputs = [patch(("order_id", "ORD-109"))]
    app.chat_input(key="dispatch_chat").set_value("ORD-109").run()
    app.button(key="review_confirmation").click().run()
    app.radio(key="input_source").set_value("examples").run()
    assert "reviewing_preview" not in app.session_state
    app.radio(key="input_source").set_value("chat").run()
    assert fake.calls == 1
    assert not app.exception


def test_inbox_mode_sends_raw_request_not_fixture(ui):
    app, fake = ui
    fake.outputs = [patch(("order_id", "ORD-109"))]
    app.selectbox(key="chat_seed").set_value("R25").run()
    assert fake.calls == 0
    app.button(key="interpret_inbox").click().run()
    assert fake.calls == 1
    assert app.session_state["conversation"].turns[0]["speaker"] == "Mei"
    assert app.session_state["preview"]["input"]["exclusions"] == []  # Not backfilled from a fixture.


def test_clicking_a_matching_order_resolves_without_a_model_call(ui):
    app, fake = ui
    fake.outputs = [patch(("customer", "TrendCart"), needs=["order"])]
    app.chat_input(key="dispatch_chat").set_value("Can we get the TrendCart order moving?").run()
    assert app.session_state["preview"]["status"] == "CLARIFY"
    choices = app.session_state["chat_replies"][0]["choices"]
    index = [choice["value"] for choice in choices].index("ORD-017")
    app.button(key=f"choice_{index}").click().run()
    assert not app.exception
    assert fake.calls == 1
    assert app.session_state["preview"]["status"] == "RECOMMEND"
    assert app.session_state["preview"]["order"]["order_id"] == "ORD-017"
    replies = app.session_state["chat_replies"]
    assert replies[0]["label"] == "Clarification needed"
    assert replies[1]["headline"].startswith("Send ORD-017 to ")


def test_clicking_the_alternative_replaces_a_refused_workshop(ui):
    app, fake = ui
    fake.outputs = [patch(("order_id", "ORD-008"), ("suggested_workshop", "OldMill"))]
    app.chat_input(key="dispatch_chat").set_value("OldMill is free right now - give them ORD-008.").run()
    first = app.session_state["preview"]
    assert first["status"] == "REFUSE_SUGGESTION"
    app.button(key="choice_0").click().run()
    assert not app.exception
    assert fake.calls == 1
    result = app.session_state["preview"]
    assert result["status"] == "RECOMMEND"
    assert result["recommendation"] == first["alternative"]
    provenance = result["conversation"]["provenance"][-1]
    assert (provenance["field"], provenance["speaker"]) == ("suggested_workshop", "Dispatcher")


def test_latest_card_follows_settings_but_history_is_kept(ui):
    app, fake = ui
    fake.outputs = [patch(("order_id", "ORD-109"))]
    app.chat_input(key="dispatch_chat").set_value("ORD-109").run()
    before = app.session_state["chat_replies"][0]
    app.radio(key="objective").set_value("defects").run()
    after = app.session_state["chat_replies"][0]
    assert fake.calls == 1
    assert after["headline"] == "Send ORD-109 to " + app.session_state["preview"]["candidates"][0]["name"] + "."
    assert before != after
