import pytest

from dss5105.dispatch import DispatchDesk, DispatchInput, read_inbox
from dss5105.evaluate import PRESETS
from dss5105.memory import MemoryStore, MemoryUpdateError, rule_suggestions
from dss5105.records import AllocationStore


@pytest.fixture
def memory(tmp_path):
    return MemoryStore(tmp_path / "memory.sqlite3")


def remember(memory, **overrides):
    values = {
        "workshop_id": "W3",
        "customer": "Harbor Knits",
        "imposed_by": "Mei",
        "evidence": "keep it away from BudgetWorks",
        "created_on": "2026-04-01",
        "created_by": "Ravi",
    }
    return memory.remember_rule(**{**values, **overrides})


def test_rules_keep_provenance_and_identical_active_rules_are_reused(memory):
    rule = remember(memory)
    assert rule["summary"] == "Avoid BudgetWorks for Harbor Knits orders"
    assert rule["active"] and rule["imposed_by"] == "Mei" and rule["created_by"] == "Ravi"
    assert remember(memory)["rule_id"] == rule["rule_id"]
    assert memory.rule_payloads() == [
        {
            "rule_id": rule["rule_id"],
            "workshop_id": "W3",
            "customer": "Harbor Knits",
            "imposed_by": "Mei",
            "evidence": "keep it away from BudgetWorks",
            "created_on": "2026-04-01",
        }
    ]


def test_memory_survives_a_new_store_on_the_same_file(memory):
    rule = remember(memory)
    memory.update_profile(dispatcher="Ravi", speak_replies=False)
    memory.log_episode({"kind": "answer", "utterance": "hello"})
    again = MemoryStore(memory.path)
    assert [r["rule_id"] for r in again.rules()] == [rule["rule_id"]]
    assert again.profile()["dispatcher"] == "Ravi" and again.profile()["speak_replies"] is False
    assert again.episodes()[0]["utterance"] == "hello"


@pytest.mark.parametrize(
    "overrides,message",
    [
        ({"workshop_id": "W99"}, "Unknown workshop"),
        ({"customer": "Nobody Ltd"}, "recorded customer"),
        ({"evidence": "  "}, "evidence"),
        ({"imposed_by": "x" * 700}, "imposed_by"),
    ],
)
def test_invalid_rules_are_rejected(memory, overrides, message):
    with pytest.raises(MemoryUpdateError, match=message):
        remember(memory, **overrides)
    assert memory.rules() == []


def test_pausing_a_rule_is_explicit_attributed_and_reversible(memory):
    rule = remember(memory)
    paused = memory.set_rule_active(rule["rule_id"], False, "Priya")
    assert not paused["active"] and paused["changed_by"] == "Priya"
    assert memory.rule_payloads() == []
    second = remember(memory)
    assert second["rule_id"] != rule["rule_id"]
    with pytest.raises(MemoryUpdateError, match="already active"):
        memory.set_rule_active(rule["rule_id"], True, "Priya")
    with pytest.raises(MemoryUpdateError, match="Unknown"):
        memory.set_rule_active("rule-missing", True, "Priya")


def test_profile_validates_weights_and_settings(memory):
    profile = memory.update_profile(weights={"lateness": 1.0, "fairness": 0.1})
    assert profile["weights"]["fairness"] == 0.1 and profile["weights"]["defects"] == 0.0
    with pytest.raises(MemoryUpdateError, match="not all zero"):
        memory.update_profile(weights={"lateness": 0.0})
    with pytest.raises(MemoryUpdateError, match="Unknown objective"):
        memory.update_profile(weights={"speed": 1.0})
    with pytest.raises(MemoryUpdateError, match="Unknown profile"):
        memory.update_profile(color="red")


def test_a_remembered_rule_becomes_an_attributed_exclusion_for_that_customer_only(memory):
    remember(memory)
    desk = DispatchDesk()
    envelope = {"request_id": "CHAT", "time": "now", "requester": "Ravi", "text": "ORD-081 please"}
    harbor = desk.preview(envelope, DispatchInput(order_id="ORD-081"), PRESETS["hybrid"], rules=memory.rule_payloads())
    assert harbor["order"]["customer"] == "Harbor Knits"
    assert [rule["workshop_id"] for rule in harbor["applied_rules"]] == ["W3"]
    assert "W3" not in {row["estimate"]["workshop_id"] for row in harbor["candidates"]}
    reason = next(row for row in harbor["excluded"] if row["workshop_id"] == "W3")["reasons"][-1]
    assert reason.startswith("Remembered rule from Mei (2026-04-01)")
    cheapest = next(row for row in harbor["baselines"] if row["policy"] == "cheapest")
    assert cheapest["respects_exclusions"] is (cheapest["workshop_id"] != "W3")
    other = desk.preview(envelope, DispatchInput(order_id="ORD-053"), PRESETS["hybrid"], rules=memory.rule_payloads())
    assert other["order"]["customer"] != "Harbor Knits"
    assert other["applied_rules"] == []


def test_message_constraints_keep_their_own_provenance_over_memory(memory):
    remember(memory)
    envelope = next(item for item in read_inbox() if item["request_id"] == "R25")
    request = DispatchInput(
        order_id="ORD-109",
        exclusions=[{"workshop_id": "W3", "imposed_by": "Mei", "evidence": "keep it away from BudgetWorks"}],
    )
    result = DispatchDesk().preview(envelope, request, PRESETS["hybrid"], rules=memory.rule_payloads())
    assert result["applied_rules"] == []
    assert any(
        r.startswith("Excluded by Mei")
        for r in next(x for x in result["excluded"] if x["workshop_id"] == "W3")["reasons"]
    )


def test_malformed_rules_fail_closed():
    envelope = {"request_id": "CHAT", "time": "now", "requester": "Ravi", "text": "ORD-081"}
    with pytest.raises(ValueError, match="standing rule"):
        DispatchDesk().preview(
            envelope, DispatchInput(order_id="ORD-081"), PRESETS["hybrid"], rules=[{"workshop_id": "W3"}]
        )


def test_booking_offers_only_new_customer_rules_and_commit_keeps_reviewed_rules(memory, tmp_path):
    store = AllocationStore(tmp_path / "plan.sqlite3")
    envelope = next(item for item in read_inbox() if item["request_id"] == "R25")
    request = DispatchInput(
        order_id="ORD-109",
        exclusions=[{"workshop_id": "W3", "imposed_by": "Mei", "evidence": "keep it away from BudgetWorks"}],
    )
    preview = store.preview(envelope, request, PRESETS["hybrid"], rules=memory.rule_payloads())
    record = store.commit_allocation(preview, "Ravi", "key-1", confirmed=True)
    offers = rule_suggestions(record, memory)
    assert [(o["workshop_id"], o["customer"], o["imposed_by"]) for o in offers] == [("W3", "Harbor Knits", "Mei")]
    remember(memory)
    assert rule_suggestions(record, memory) == []
    assert store.summary()["ledger"] == {record["workshop_id"]: 500}
