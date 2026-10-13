import json
from datetime import date

import pytest

from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import DispatchDesk
from dss5105.intake import (
    Conversation,
    IntakeError,
    apply_patch,
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
    assert result["conversation"]["traces"][0]["version"] == "intake-v2"
    prompt = json.loads(model.calls[0][1].content)
    assert "queues" not in prompt and "cost" not in prompt
    assert prompt["latest_user_message"] == text


def test_r14_registered_quantity_does_not_block_ineligible_suggestion_refusal():
    text = "QuickStitch for the scarves on ORD-103?"
    state = turn(
        text,
        patch(
            ("order_id", "ORD-103", "ORD-103"),
            ("product", "scarves", "scarves"),
            ("suggested_workshop", "QuickStitch", "QuickStitch"),
            needs=["quantity"],
        ),
    )
    result = preview_conversation(state, DispatchDesk(), ObjectiveWeights())
    assert state.request.pieces is None
    assert state.request.product == "Scarf"
    assert state.request.suggested_workshop == "W1"
    assert result["resolution"]["status"] == "RESOLVED"
    assert len(result["resolution"]["matches"]) == 1
    assert result["order"]["order_id"] == "ORD-103"
    assert int(result["order"]["pieces"]) == 2000
    assert result["status"] == "REFUSE_SUGGESTION", result["message"]
    assert result["batch"]["pieces"] == 2000
    refused = next(row for row in result["excluded"] if row["workshop_id"] == "W1")
    assert "Cannot make ACCESSORIES." in refused["reasons"]


def test_quantity_alternatives_with_product_words_remain_unresolved():
    text = "ORD-103, either 2000 scarves or 2500 scarves"
    state = turn(text, patch(("order_id", "ORD-103", "ORD-103"), needs=["quantity"]))
    assert "quantity" in state.needs
    result = preview_conversation(state, DispatchDesk(), ObjectiveWeights())
    assert result["status"] == "CLARIFY"
    assert not result["candidates"]


def test_quantity_alternatives_without_quantity_keywords_remain_unresolved():
    text = "ORD-103, unsure whether 2000 or 2500 scarves"
    state = turn(text, patch(("order_id", "ORD-103", "ORD-103"), needs=["quantity"]))
    assert "quantity" in state.needs
    result = preview_conversation(state, DispatchDesk(), ObjectiveWeights())
    assert result["status"] == "CLARIFY"
    assert not result["candidates"]


@pytest.mark.parametrize(
    "phrase",
    ["unsure", "uncertain", "not sure", "unknown", "maybe", "perhaps", "whether 2000", "either 2000 or 2500"],
)
def test_uncertainty_language_preserves_quantity_need(phrase):
    state = turn(f"ORD-103, {phrase} scarves", patch(("order_id", "ORD-103", "ORD-103"), needs=["quantity"]))
    assert "quantity" in state.needs
    result = preview_conversation(state, DispatchDesk(), ObjectiveWeights())
    assert result["status"] == "CLARIFY"
    assert not result["candidates"]


@pytest.mark.parametrize(
    "text",
    [
        "ORD-103, 2000 scarves",
        "ORD-103, 2,000 scarves or 2,500 scarves",
        "ORD-103, 103 scarves",
        "ORD-103, delivery 2026-04-15",
        "ORD-103, W1 or W3",
        "ORD-103 / ORD-1030",
        "ORD-103 / XORD-103",
    ],
)
def test_numeric_content_beyond_explicit_order_id_preserves_quantity_need(text):
    state = turn(text, patch(("order_id", "ORD-103", "ORD-103"), needs=["quantity"]))
    assert "quantity" in state.needs
    result = preview_conversation(state, DispatchDesk(), ObjectiveWeights())
    assert result["status"] == "CLARIFY"
    assert not result["candidates"]


@pytest.mark.parametrize("text", ["ORD-103", "(ord-103)?", "ORD-103 / ord-103"])
def test_explicit_order_id_digits_alone_do_not_block_quantity_fallback(text):
    evidence = "ord-103" if text == "(ord-103)?" else "ORD-103"
    state = turn(text, patch(("order_id", evidence, evidence), needs=["quantity"]))
    assert "quantity" not in state.needs
    assert state.request.pieces is None


def test_workshop_alternative_does_not_block_registered_quantity_fallback():
    state = turn(
        "ORD-103, either QuickStitch or BudgetWorks",
        patch(("order_id", "ORD-103", "ORD-103"), needs=["quantity"]),
    )
    assert "quantity" not in state.needs


@pytest.mark.parametrize("quantity", [None, "", "0", "000", "-1", "2000.0", "malformed", "\u00b2", 2000])
def test_invalid_registered_quantity_preserves_quantity_need(quantity):
    desk = DispatchDesk()
    next(row for row in desk.orders if row["order_id"] == "ORD-103")["pieces"] = quantity
    state = apply_patch(
        Conversation(), "ORD-103", patch(("order_id", "ORD-103", "ORD-103"), needs=["quantity"]), desk, "Dispatcher"
    )
    assert "quantity" in state.needs
    assert state.request.clarification


@pytest.mark.parametrize("duplicate", [False, True])
def test_unresolved_order_preserves_quantity_need(duplicate):
    desk = DispatchDesk()
    order = next(row for row in desk.orders if row["order_id"] == "ORD-103")
    if duplicate:
        desk.orders.append(order.copy())
    else:
        desk.orders.remove(order)
    state = apply_patch(
        Conversation(), "ORD-103", patch(("order_id", "ORD-103", "ORD-103"), needs=["quantity"]), desk, "Dispatcher"
    )
    assert "quantity" in state.needs
    result = preview_conversation(state, desk, ObjectiveWeights())
    assert result["status"] == "CLARIFY"
    assert not result["candidates"]


def test_registered_quantity_fallback_preserves_other_needs():
    state = turn("ORD-103", patch(("order_id", "ORD-103", "ORD-103"), needs=["quantity", "deadline"]))
    assert state.needs == ("deadline",)
    result = preview_conversation(state, DispatchDesk(), ObjectiveWeights())
    assert result["status"] == "CLARIFY"
    assert not result["candidates"]


def test_explicit_quantity_uncertainty_is_not_discharged_by_registered_quantity():
    state = turn(
        "QuickStitch for ORD-103, but I'm not sure about the quantity yet.",
        patch(
            ("order_id", "ORD-103", "ORD-103"),
            ("suggested_workshop", "QuickStitch", "QuickStitch"),
            needs=["quantity"],
        ),
    )
    assert "quantity" in state.needs
    result = preview_conversation(state, DispatchDesk(), ObjectiveWeights())
    assert int(result["order"]["pieces"]) == 2000
    assert result["status"] == "CLARIFY"
    assert not result["candidates"]


def test_unresolved_quantity_survives_an_order_only_follow_up():
    first = turn("usual quantities", patch(("pieces", "usual quantities", "usual quantities")))
    second = turn("ORD-103", patch(("order_id", "ORD-103", "ORD-103")), first)
    assert "quantity" in second.needs
    result = preview_conversation(second, DispatchDesk(), ObjectiveWeights())
    assert result["status"] == "CLARIFY"
    assert not result["candidates"]


def test_explicit_quantity_conflict_is_not_replaced_by_registered_quantity():
    state = turn(
        "ORD-103, 2001 scarves",
        patch(("order_id", "ORD-103", "ORD-103"), ("pieces", "2001", "2001"), needs=["quantity"]),
    )
    result = preview_conversation(state, DispatchDesk(), ObjectiveWeights())
    assert state.request.pieces == 2001
    assert int(result["order"]["pieces"]) == 2000
    assert result["status"] == "CLARIFY"
    assert "quantity amendment" in result["message"]
    assert not result["candidates"]


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


def test_ambiguous_order_clarification_is_not_repeated():
    state = turn(
        "Can we get the TrendCart order moving? They are chasing.",
        patch(("customer", "TrendCart", "TrendCart"), needs=["order", "quantity"]),
    )
    result = preview_conversation(state, DispatchDesk(), ObjectiveWeights())
    assert result["status"] == "CLARIFY"
    assert result["resolution"]["status"] == "AMBIGUOUS"
    question = "Which order do you mean? Please confirm its order ID."
    assert result["message"].count(question) == 1, result["message"]
    assert result["message"] == question + " Please confirm the quantity using digits."
    assert state.needs == ("order", "quantity")
    assert not result["candidates"]


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
    assert result["effective_weights"] == {"lateness": 0, "defects": 0, "cost": 1, "deadline_buffer_days": 0}
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
