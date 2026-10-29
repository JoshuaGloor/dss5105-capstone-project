import json
from dataclasses import asdict
from datetime import date

import pytest

from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import DispatchDesk
from dss5105.intake import (
    Conversation,
    IntakeError,
    apply_selection,
    interpret_turn,
    parse_date_phrase,
    preview_conversation,
)


class Extractor:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def with_structured_output(self, schema):
        assert schema["title"] == "DispatchPatch"
        return self

    def invoke(self, messages):
        self.calls.append(messages)
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def patch(*updates, exclusions=None, needs=None):
    return {
        "updates": [{"field": key, "value": value, "evidence": evidence} for key, value, evidence in updates],
        "exclusions": exclusions or [],
        "needs": needs or [],
    }


def turn(text, output, previous=None):
    return interpret_turn(previous or Conversation(), text, DispatchDesk(), model=Extractor(output))


def test_reference_and_raw_date_reach_allocator_without_model_arithmetic():
    text = "ORD-109, 500 vests, delivery Apr 13."
    model = Extractor(
        patch(
            ("order_id", "ORD-109", text),
            ("pieces", "500", text),
            ("product", "vests", text),
            ("due_date", "Apr 13", text),
        )
    )
    desk = DispatchDesk()
    conversation = interpret_turn(Conversation(), text, desk, model=model)
    result = preview_conversation(conversation, desk, ObjectiveWeights())
    assert result["status"] == "RECOMMEND"
    assert result["batch"]["due_date"] == "2026-04-13"
    assert result["batch"]["pieces"] == 500
    assert result["conversation"]["traces"][0]["version"] == "intake-v3"
    prompt = json.loads(model.calls[0][1].content)
    assert "queues" not in prompt and "cost" not in prompt
    assert prompt["latest_user_message"] == text


def test_clarification_merges_with_exclusions_and_imposer_provenance():
    text = "ORD-109: Boss says no BudgetWorks. The revised date is not known."
    first = turn(
        text,
        patch(
            ("order_id", "ORD-109", text),
            ("date_uncertain", "true", "date is not known"),
            exclusions=[{"workshop": "BudgetWorks", "imposed_by": "Boss", "evidence": "Boss says no BudgetWorks"}],
            needs=["deadline"],
        ),
    )
    before = preview_conversation(first, DispatchDesk(), ObjectiveWeights())
    assert before["status"] == "CLARIFY" and not before["candidates"]
    second = turn("Delivery Apr 15.", patch(("due_date", "Apr 15", "Delivery Apr 15")), first)
    after = preview_conversation(second, DispatchDesk(), ObjectiveWeights())
    assert after["status"] == "RECOMMEND"
    assert second.request.exclusions == first.request.exclusions
    assert second.request.exclusions[0]["imposed_by"] == "Boss"
    assert "W3" not in {candidate["estimate"]["workshop_id"] for candidate in after["candidates"]}
    assert first.request.date_uncertain is True
    assert second.request.date_uncertain is False


def test_indirect_reference_never_guesses_an_order():
    first = turn("The TrendCart order please", patch(("customer", "TrendCart", "TrendCart"), needs=["order"]))
    assert preview_conversation(first, DispatchDesk(), ObjectiveWeights())["status"] == "CLARIFY"
    second = turn("ORD-120", patch(("order_id", "ORD-120", "ORD-120")), first)
    assert not second.needs
    assert second.request.customer == "TrendCart"
    assert preview_conversation(second, DispatchDesk(), ObjectiveWeights())["status"] == "NEEDS_REVIEW"


@pytest.mark.parametrize(
    "field,value,evidence",
    [
        ("cost", "100", "100"),
        ("order_id", "ORD-109", "the order"),
        ("due_date", "2026-04-13", "Apr 13"),
        ("pieces", "500", "usual quantities"),
    ],
)
def test_unsupported_or_calculated_values_are_rejected(field, value, evidence):
    with pytest.raises(IntakeError):
        turn(evidence, patch((field, value, evidence)))


def test_fabricated_quotation_and_imposer_are_rejected():
    with pytest.raises(IntakeError, match="quotation"):
        turn("hello", patch(("order_id", "ORD-109", "ORD-109")))
    with pytest.raises(IntakeError, match="quotation"):
        turn(
            "no BudgetWorks",
            patch(exclusions=[{"workshop": "BudgetWorks", "imposed_by": "Boss", "evidence": "no BudgetWorks"}]),
        )


def test_shipping_date_is_checked_against_the_order_record_by_python():
    recorded = turn(
        "ORD-109 ship Apr 13",
        patch(
            ("order_id", "ORD-109", "ORD-109"),
            ("due_date", "Apr 13", "Apr 13"),
            ("date_kind", "shipping", "ship Apr 13"),
        ),
    )
    assert recorded.needs == ()
    assert preview_conversation(recorded, DispatchDesk(), ObjectiveWeights())["status"] == "RECOMMEND"
    first = turn(
        "ORD-109 ship Apr 11",
        patch(
            ("order_id", "ORD-109", "ORD-109"),
            ("due_date", "Apr 11", "Apr 11"),
            ("date_kind", "shipping", "ship Apr 11"),
        ),
    )
    assert preview_conversation(first, DispatchDesk(), ObjectiveWeights())["status"] == "CLARIFY"
    second = turn("I mean delivery", patch(("date_kind", "delivery", "delivery")), first)
    assert preview_conversation(second, DispatchDesk(), ObjectiveWeights())["status"] == "RECOMMEND"


def test_unsupported_date_and_quantity_prompt_for_explicit_values():
    first = turn(
        "ORD-109 usual quantities by next Friday",
        patch(
            ("order_id", "ORD-109", "ORD-109"),
            ("pieces", "usual quantities", "usual quantities"),
            ("due_date", "next Friday", "next Friday"),
        ),
    )
    assert set(first.needs) == {"quantity", "deadline"}
    assert preview_conversation(first, DispatchDesk(), ObjectiveWeights())["status"] == "CLARIFY"


@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("Apr 13", date(2026, 4, 13)),
        ("April 13, 2027", date(2027, 4, 13)),
        ("15 April", date(2026, 4, 15)),
        ("15th April 2027", date(2027, 4, 15)),
        ("15 of Apr", date(2026, 4, 15)),
        ("2026-04-13", date(2026, 4, 13)),
        ("today", date(2026, 4, 1)),
        ("tomorrow", date(2026, 4, 2)),
        ("03/04/26", None),
        ("Apr 31", None),
        ("2026-02-30", None),
    ],
)
def test_date_normalization_is_python_owned(phrase, expected):
    assert parse_date_phrase(phrase, date(2026, 4, 1)) == expected


def test_lowest_cost_with_deadline_maps_to_tool_constraint():
    text = "ORD-081 cheapest that meets Apr 13"
    state = turn(
        text,
        patch(
            ("order_id", "ORD-081", text),
            ("due_date", "Apr 13", text),
            ("preference", "cheapest_on_time", "cheapest that meets Apr 13"),
        ),
    )
    result = preview_conversation(state, DispatchDesk(), ObjectiveWeights(lateness=0, defects=1))
    assert result["effective_weights"] == asdict(ObjectiveWeights(lateness=0, cost=1))
    choice = next(row for row in result["candidates"] if row["estimate"]["workshop_id"] == result["recommendation"])
    assert choice["meets_deadline"]


def test_no_unverified_model_prose_is_accepted():
    payload = patch()
    payload["answer"] = "Guaranteed delivery tomorrow for free"
    with pytest.raises(IntakeError):
        turn("Please allocate", payload)


def test_change_of_order_requires_new_conversation():
    first = turn("ORD-109", patch(("order_id", "ORD-109", "ORD-109")))
    with pytest.raises(IntakeError, match="different order"):
        turn("ORD-081", patch(("order_id", "ORD-081", "ORD-081")), first)


def test_provider_failure_is_masked_and_does_not_advance_state():
    previous = Conversation()
    with pytest.raises(IntakeError) as caught:
        interpret_turn(previous, "hello", DispatchDesk(), model=Extractor(RuntimeError("secret-key=hidden")))
    assert "hidden" not in str(caught.value)
    assert not previous.turns


def test_production_factory_is_only_called_on_interpret(monkeypatch):
    from dss5105 import llm

    called = []

    def factory(**kwargs):
        called.append(kwargs)
        return Extractor(patch(("order_id", "ORD-109", "ORD-109")))

    monkeypatch.setattr(llm, "get_model", factory)
    state = interpret_turn(Conversation(), "ORD-109", DispatchDesk())
    assert len(called) == 1
    preview_conversation(state, DispatchDesk(), ObjectiveWeights())
    preview_conversation(state, DispatchDesk(), ObjectiveWeights(lateness=0, defects=1))
    assert len(called) == 1


def test_clicked_answer_is_validated_like_model_output_without_a_model():
    desk = DispatchDesk()
    first = turn("Can we get the TrendCart order moving?", patch(("customer", "TrendCart", "TrendCart")))
    chosen = apply_selection(first, "order_id", "ORD-017", "ORD-017", desk)
    assert chosen.request.order_id == "ORD-017"
    assert chosen.request.customer == "TrendCart"
    assert chosen.turns[-1] == {"speaker": "Dispatcher", "text": "ORD-017"}
    assert chosen.traces[-1]["model"] == "dispatcher selection; no model call"
    assert preview_conversation(chosen, desk, ObjectiveWeights())["status"] == "RECOMMEND"
    with pytest.raises(IntakeError, match="different order"):
        apply_selection(chosen, "order_id", "ORD-010", "ORD-010", desk)
    with pytest.raises(IntakeError):
        apply_selection(first, "suggested_workshop", "Nowhere", "Use Nowhere instead.", desk)
    with pytest.raises(IntakeError, match="Send a request"):
        apply_selection(Conversation(), "order_id", "ORD-017", "ORD-017", desk)


def test_capacity_question_is_extracted_as_quoted_fields_and_needs_a_product():
    text = "Who can take 1,500 crewnecks by April 15?"
    conversation = turn(
        text,
        patch(
            ("intent", "capacity", text),
            ("product", "crewnecks", text),
            ("pieces", "1,500", text),
            ("due_date", "April 15", text),
        ),
    )
    request = conversation.request
    assert (request.intent, request.product, request.pieces, request.due_date) == (
        "capacity",
        "Crewneck sweater",
        1500,
        "2026-04-15",
    )
    asked = turn("Who has room for 300 by Friday?", patch(("intent", "capacity", "Who has room"), needs=["product"]))
    assert "Which product" in asked.request.clarification


@pytest.mark.parametrize(
    "value,expected",
    [("400", 400), ("1,500", 1500), ("400 pieces", 400), ("400 pieces of tops", 400), ("400 or so", None)],
)
def test_a_count_with_unit_words_is_a_quantity_but_a_hedge_still_asks(value, expected):
    text = f"ORD-109, {value}, due April 13."
    state = turn(text, patch(("order_id", "ORD-109", text), ("pieces", value, text)))
    assert state.request.pieces == expected
    assert ("quantity" in state.needs) is (expected is None)


def test_a_new_order_without_an_id_is_checked_against_every_workshop():
    text = "I need an order for quickstitch 400 pieces of tops, ready by 15 April."
    state = turn(
        text,
        patch(
            ("suggested_workshop", "quickstitch", "quickstitch"),
            ("pieces", "400 pieces", "400 pieces"),
            ("product", "tops", "tops"),
            ("due_date", "15 April", "15 April"),
            needs=["order"],
        ),
    )
    request = state.request
    assert (request.intent, request.pieces, request.due_date, request.suggested_workshop) == (
        "capacity",
        400,
        "2026-04-15",
        "W1",
    )
    assert state.needs == () and request.clarification is None
    named = turn("It is ORD-045.", patch(("order_id", "ORD-045", "ORD-045")), previous=state)
    assert named.request.intent == "allocate" and named.request.order_id == "ORD-045"


@pytest.mark.parametrize("said,value,expected", [("order 109", "109", "ORD-109"), ("order 81", "order 81", "ORD-081")])
def test_a_spoken_order_number_is_read_as_its_recorded_id(said, value, expected):
    text = f"Hi, I've got {said} for Harbor Knits. Keep it away from budget works."
    exclusion = {"workshop": "budget works", "imposed_by": "", "evidence": "Keep it away from budget works"}
    state = turn(text, patch(("order_id", value, said), exclusions=[exclusion]))
    assert state.request.order_id == expected and state.request.exclusions[0]["workshop_id"] == "W3"
    with pytest.raises(IntakeError):
        turn(text, patch(("order_id", "110", said)))


def test_date_digits_do_not_keep_an_unprompted_quantity_question():
    text = "Next one, order 81 for Harbor Knits, due April 20th."
    state = turn(
        text, patch(("order_id", "81", "order 81"), ("due_date", "April 20th", "April 20th"), needs=["quantity"])
    )
    assert (state.request.order_id, state.request.due_date) == ("ORD-081", "2026-04-20")
    assert "quantity" not in state.needs


def test_switching_to_a_new_request_reuses_the_same_patch():
    first = turn("ORD-109 please", patch(("order_id", "ORD-109", "ORD-109")))
    text = "And ORD-053?"
    model = Extractor(patch(("order_id", "ORD-053", text)))
    with pytest.raises(IntakeError, match="different order"):
        interpret_turn(first, text, DispatchDesk(), model=model)
    model = Extractor(patch(("order_id", "ORD-053", text)))
    fresh = interpret_turn(first, text, DispatchDesk(), model=model, restart_new_requests=True)
    assert fresh.request.order_id == "ORD-053" and len(fresh.turns) == 1 and len(model.calls) == 1
    assert fresh.traces[-1]["restarted"] is True


def test_a_recorded_order_needs_no_quantity_question_so_a_refusal_is_not_blocked():
    # R14 live failure: the model asked for a quantity although ORD-103 records 2000 pieces.
    text = "QuickStitch for the scarves on ORD-103?"
    conversation = turn(
        text,
        patch(("order_id", "ORD-103", text), ("suggested_workshop", "QuickStitch", text), needs=["quantity"]),
    )
    assert conversation.needs == () and conversation.request.clarification is None
    result = preview_conversation(conversation, DispatchDesk(), ObjectiveWeights())
    assert result["status"] == "REFUSE_SUGGESTION"
    unknown = turn("Send the scarves for Harbor Knits", patch(("product", "scarves", "scarves"), needs=["quantity"]))
    assert "quantity" in unknown.needs


def test_a_recorded_order_needs_no_unprompted_deadline_question_either():
    # Live variant of R14: the model asked for a deadline that orders.csv records.
    text = "QuickStitch for the scarves on ORD-103?"
    conversation = turn(
        text,
        patch(("order_id", "ORD-103", text), ("suggested_workshop", "QuickStitch", text), needs=["deadline"]),
    )
    assert conversation.needs == ()
    assert preview_conversation(conversation, DispatchDesk(), ObjectiveWeights())["status"] == "REFUSE_SUGGESTION"
    moved = "ORD-066 due date just moved up, will confirm the new date"
    changing = turn(
        moved, patch(("order_id", "ORD-066", moved), ("date_uncertain", "true", moved), needs=["deadline"])
    )
    assert "deadline" in changing.needs
