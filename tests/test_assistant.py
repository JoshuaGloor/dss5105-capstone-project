import json
import re

import pytest
from streamlit.testing.v1 import AppTest

from dss5105 import assistant, llm, memory, records
from dss5105.assistant import Services, Session, apply_event, build_view, handle_utterance
from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput, read_inbox
from dss5105.evaluate import PRESETS
from dss5105.memory import MemoryStore
from dss5105.records import AllocationStore

ORDER = "ORD-109, 500 vests for Harbor Knits, due April 13. Keep it away from BudgetWorks."


class Extractor:
    """Returns prepared patches and counts calls; never a real provider."""

    audit_model_name = "fake extractor"

    def __init__(self, *patches):
        self.patches = list(patches)
        self.calls = 0

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        self.calls += 1
        result = self.patches.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def patch(text, *updates, exclusions=(), needs=()):
    return {
        "updates": [{"field": field, "value": value, "evidence": text} for field, value in updates],
        "exclusions": list(exclusions),
        "needs": list(needs),
    }


def order_patch():
    return patch(
        ORDER,
        ("order_id", "ORD-109"),
        ("pieces", "500"),
        ("due_date", "April 13"),
        exclusions=[{"workshop": "BudgetWorks", "imposed_by": "", "evidence": "Keep it away from BudgetWorks"}],
    )


@pytest.fixture
def services(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "get_model", lambda **kwargs: pytest.fail("tests never build a real model"))

    def build(*patches, weights=PRESETS["hybrid"]):
        return Services(
            store=AllocationStore(tmp_path / "plan.sqlite3"),
            memory=MemoryStore(tmp_path / "memory.sqlite3"),
            weights=weights,
            model=Extractor(*patches),
            speaker="Ravi",
        )

    return build


def last_card(session):
    return session.thread[-1]["card"]


@pytest.mark.parametrize(
    "text,command",
    [
        ("Book it", "book"),
        ("yes, book it please", "book"),
        ("Okay, book it.", "book"),
        ("Great, book it", "book"),
        ("Okay.", "book"),
        ("go ahead", "book"),
        ("cancel", "cancel"),
        ("never mind", "cancel"),
        ("Start over", "new"),
        ("new request", "new"),
        ("say that again", "repeat"),
        ("What can you do?", "help"),
        ("Send ORD-073 to FreshStart", None),
        ("book ORD-109 with GiantWeave by Friday", None),
    ],
)
def test_only_whole_short_phrases_are_commands(text, command):
    assert assistant.parse_command(text) == command


def test_memory_questions_are_recognised_but_course_history_is_not():
    assert assistant.parse_recall("What did we book today?") == "bookings"
    assert assistant.parse_recall("show me what was sent to SteadyHands") == "bookings"
    assert assistant.parse_recall("What rules do you remember?") == "rules"
    for envelope in read_inbox():
        assert assistant.parse_recall(envelope["text"]) is None, envelope["request_id"]
        assert assistant.parse_command(envelope["text"]) is None, envelope["request_id"]


def test_recommendation_card_and_speech_use_only_tool_strings(services):
    current = services(order_patch())
    session = handle_utterance(Session(), ORDER, current, channel="voice")
    card = last_card(session)
    result = session.result
    assert session.thread[-2] == {**session.thread[-2], "role": "user", "text": ORDER, "channel": "voice"}
    assert card["status"] == "RECOMMEND" and result["status"] == "RECOMMEND"
    chosen = next(row for row in result["candidates"] if row["estimate"]["workshop_id"] == result["recommendation"])
    pick = card["pick"]
    assert pick["workshop_id"] == result["recommendation"]
    assert (pick["eta"], pick["cost"], pick["defects"]) == tuple(
        chosen["display"][k] for k in ("eta", "cost", "defects")
    )
    assert pick["slack"] == f"{result['decision_basis']['slack_days']:.2f} days"
    assert card["actions"] == [{"id": "book", "label": f"Book {pick['name']}", "primary": True}]
    assert "W3" not in [option["workshop_id"] for option in card["options"]]
    # Every numeral spoken is copied from a tool string, an order ID or a formatted tool date.
    allowed = json.dumps(result) + " " + " ".join(str(int(pick[k][8:10])) for k in ("eta", "due"))
    for number in re.findall(r"\d[\d,.]*\d|\d", card["speak"]):
        assert number.rstrip(".") in allowed, number
    assert current.model.calls == 1


def test_voice_never_books_without_a_named_slide_to_confirm(services):
    current = services(order_patch())
    session = handle_utterance(Session(), ORDER, current)
    session = handle_utterance(session, "book it", current, channel="voice")
    assert session.booking and last_card(session)["kind"] == "confirm"
    assert current.store.records() == []
    unchanged, notice = apply_event(session, {"type": "confirm", "actor": "  "}, current)
    assert notice and unchanged is session and current.store.records() == []
    session, _ = apply_event(session, {"type": "confirm", "actor": "Ravi"}, current)
    card = last_card(session)
    assert card["kind"] == "receipt" and session.status == "BOOKED" and session.booking is None
    saved = current.store.records()
    assert len(saved) == 1 and saved[0]["confirmed_by"] == "Ravi"
    assert card["receipt"]["reference"] == saved[0]["allocation_id"][:8].upper()
    assert current.memory.profile()["dispatcher"] == "Ravi"
    assert [episode["kind"] for episode in current.memory.episodes()] == ["booking", "answer"]
    assert current.model.calls == 1


def test_a_stale_answer_cannot_be_booked(services):
    current = services(order_patch())
    session = handle_utterance(Session(), ORDER, current)
    session = assistant.request_booking(session, current)
    session = assistant.replace(session, result={**session.result, "message": "changed"})
    session = assistant.confirm_booking(session, current, "Ravi")
    assert "changed" in last_card(session)["headline"] and current.store.records() == []


def test_booking_teaches_a_rule_that_the_next_order_uses(services):
    current = services(order_patch())
    session = handle_utterance(Session(), ORDER, current)
    session = assistant.request_booking(session, current)
    session = assistant.confirm_booking(session, current, "Ravi")
    offer = last_card(session)["offers"][0]
    assert offer["text"] == "Always avoid BudgetWorks for Harbor Knits?"
    session, _ = apply_event(session, {"type": "remember", "index": 0}, current)
    assert last_card(session)["kind"] == "memory"
    text = "ORD-081 needs to go out."
    following = assistant.replace(current, model=Extractor(patch(text, ("order_id", "ORD-081"))))
    session = handle_utterance(session, text, following)
    card = last_card(session)
    assert session.result["order"]["customer"] == "Harbor Knits"
    assert [m["text"] for m in card["memory"]] == ["Avoid BudgetWorks for Harbor Knits"]
    assert any(stage["stage"] == "Memory" for stage in card["trace"])


def test_a_capacity_question_after_an_answer_is_a_new_request_from_one_model_call(services):
    question = "Who can take 1,500 crewnecks by April 15?"
    current = services(
        order_patch(),
        patch(
            question, ("intent", "capacity"), ("product", "crewnecks"), ("pieces", "1,500"), ("due_date", "April 15")
        ),
    )
    session = handle_utterance(Session(), ORDER, current)
    session = handle_utterance(session, question, current)
    card = last_card(session)
    assert card["status"] == "CAPACITY" and card["pick"] is not None
    assert card["sub"].startswith("1,500 crewneck sweaters. Best option:")
    assert session.result["batch"]["category"] == "TOPS" and session.result["batch"]["pieces"] == 1500
    assert session.conversation.turns == ({"speaker": "Ravi", "text": question},)
    assert session.conversation.traces[-1]["restarted"] is True
    assert current.model.calls == 2
    assert session.result["commit_allowed"] is False


def test_a_named_workshop_leads_the_capacity_card():
    desk = DispatchDesk()
    request = DispatchInput(
        intent="capacity", product="tops", pieces=400, due_date="2026-04-15", suggested_workshop="W1"
    )
    envelope = {"request_id": "CHAT", "time": "now", "requester": "Charles", "text": "QuickStitch, 400 tops?"}
    card = assistant.card_for_result(desk.preview(envelope, request, PRESETS["hybrid"]), desk.workshops)
    assert card["headline"] == "QuickStitch can deliver 400 tops by Wed 15 Apr"
    assert card["sub"].startswith("Arrives ") and card["speak"].endswith("Nothing is reserved.")


def test_another_order_starts_a_fresh_request_without_a_second_call(services):
    text = "Now ORD-053, due Apr 10."
    current = services(order_patch(), patch(text, ("order_id", "ORD-053"), ("due_date", "Apr 10")))
    session = handle_utterance(Session(), ORDER, current)
    session = handle_utterance(session, text, current)
    assert session.result["order"]["order_id"] == "ORD-053"
    assert session.result["input"]["exclusions"] == []
    assert current.model.calls == 2


def test_model_failure_offers_a_retry_without_losing_the_request(services):
    current = services(RuntimeError("provider down"), order_patch())
    session = handle_utterance(Session(), ORDER, current)
    assert last_card(session)["kind"] == "error" and session.retry == {"text": ORDER, "channel": "text"}
    session, _ = apply_event(session, {"type": "retry"}, current)
    assert last_card(session)["status"] == "RECOMMEND" and session.retry is None


def test_without_a_model_only_inbox_examples_use_their_fixtures(services, monkeypatch):
    monkeypatch.setattr(llm, "model_configured", lambda: False)
    current = assistant.replace(services(), model=None)
    envelope = next(item for item in read_inbox() if item["request_id"] == "R25")
    session = handle_utterance(Session(), envelope["text"], current)
    assert last_card(session)["status"] == "RECOMMEND" and session.offline
    assert last_card(session)["source"] == "inbox fixture"
    session = handle_utterance(session, "Send something somewhere", current)
    assert last_card(session)["kind"] == "error"


def test_new_priorities_rerank_without_a_model_call_and_are_remembered(services):
    current = services(order_patch())
    session = handle_utterance(Session(), ORDER, current)
    session, notice = apply_event(
        session, {"type": "set_weights", "weights": {"lateness": 0, "defects": 1, "deadline_buffer_days": 0}}, current
    )
    assert notice == "Priorities saved." and current.model.calls == 1
    assert last_card(session)["label"] == "Re-ranked with your priorities"
    assert session.result["effective_weights"]["defects"] == 1.0
    assert current.memory.profile()["weights"]["lateness"] == 0.0
    same, notice = apply_event(session, {"type": "set_weights", "weights": {"lateness": 0}}, current)
    assert same is session and "not all zero" in notice


def test_recall_workshop_and_help_answers_need_no_model(services):
    current = services()
    session = handle_utterance(Session(), "What did we book today?", current)
    assert last_card(session)["headline"] == "Nothing is booked in this plan yet."
    session = handle_utterance(session, "What rules do you remember?", current)
    assert "no standing rules" in last_card(session)["headline"]
    session = handle_utterance(session, "How busy is OldMill?", current)
    assert "suspended" in last_card(session)["headline"]
    session = handle_utterance(session, "help", current)
    assert last_card(session)["suggestions"]
    assert current.model.calls == 0


def test_history_questions_stay_unanswerable_but_list_this_desks_own_bookings(services):
    text = "Which workshop did we use for the Harbor Knits batch last October?"
    current = services(order_patch(), patch(text, ("intent", "history"), ("customer", "Harbor Knits")))
    session = handle_utterance(Session(), ORDER, current)
    session = assistant.confirm_booking(assistant.request_booking(session, current), current, "Ravi")
    session = handle_utterance(session, text, current)
    card = last_card(session)
    assert card["status"] == "DECLINE"
    assert any("ORD-109" in note and "Nothing earlier" in note for note in card["notes"])


def test_view_has_every_workshop_objective_and_preset(services):
    current = services()
    view = build_view(assistant.welcome(Session(), ""), current, version=3)
    assert view["v"] == 3 and len(view["workshops"]) == 8
    assert {w["id"] for w in view["workshops"] if w["status"] != "ACTIVE"} == {"W7"}
    assert [o["id"] for o in view["objectives"]] == ["lateness", "defects", "fairness", "robustness", "cost"]
    assert view["preset"] == "hybrid" and view["preset_label"] == "Recommended"
    assert {p["id"] for p in view["presets"]} == set(PRESETS)
    assert view["thread"][0]["card"]["kind"] == "welcome"
    json.dumps(view, allow_nan=False)


def test_assistant_page_renders_offline(tmp_path, monkeypatch):
    monkeypatch.setattr(records, "DEFAULT_STORE_PATH", tmp_path / "plan.sqlite3")
    monkeypatch.setattr(memory, "DEFAULT_MEMORY_PATH", tmp_path / "memory.sqlite3")
    monkeypatch.setattr(llm, "get_model", lambda **kwargs: pytest.fail("no model on page load"))
    app = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=30).run()
    assert not app.exception and not app.error
    session = app.session_state["assistant_session"]
    assert [m["card"]["kind"] for m in session.thread] == ["welcome"]
