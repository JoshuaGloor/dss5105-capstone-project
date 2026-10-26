import copy
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput, read_inbox
from dss5105.records import AllocationError, AllocationStore


@pytest.fixture
def store(tmp_path):
    return AllocationStore(tmp_path / "plan.sqlite3")


def preview(store, request_id="R25"):
    item = next(item for item in read_inbox() if item["request_id"] == request_id)
    fields = json.loads((ROOT / "examples" / "dispatch_inputs.json").read_text())[request_id]
    return store.preview(item, DispatchInput(**fields), ObjectiveWeights())


def test_save_survives_restart_and_reserves_processing_without_transport(store):
    reviewed = preview(store)
    initial = DispatchDesk().queues
    assert not store.records()
    record = store.commit_allocation(reviewed, "Dispatcher", "save-a", confirmed=True)
    reopened = AllocationStore(store.path)
    assert reopened.records() == [record]
    candidate = next(row for row in reviewed["candidates"] if row["estimate"]["workshop_id"] == record["workshop_id"])
    estimate = candidate["estimate"]
    assert estimate["transport_days"] > 0
    occupancy = estimate["process_days"] + estimate["process_days"] * 0.5 * estimate["defect_risk"]
    assert record["reserved_processing_days"] == pytest.approx(occupancy)
    for key, queue in initial.items():
        expected = queue + occupancy if key == record["workshop_id"] else queue
        assert record["queues_after"][key] == pytest.approx(expected)
    subsequent = preview(reopened, "R07")
    assert subsequent["snapshot"]["queues"] == record["queues_after"]
    assert subsequent["storage"]["revision"] == record["revision_after"]
    assert DispatchDesk().queues == initial
    assert preview(reopened)["status"] == "ALREADY_ALLOCATED"
    assert not preview(reopened)["commit_allowed"]


def test_retries_return_original_record_and_key_reuse_cannot_change_actor_or_payload(store):
    reviewed = preview(store)
    record = store.commit_allocation(reviewed, "Dispatcher", "same-key", confirmed=True)
    assert store.commit_allocation(reviewed, "Dispatcher", "same-key", confirmed=True) == record
    with pytest.raises(AllocationError, match="different content"):
        store.commit_allocation(reviewed, "Other", "same-key", confirmed=True)
    changed = copy.deepcopy(reviewed)
    changed["interpretation_source"] = "new content"
    with pytest.raises(AllocationError, match="different content"):
        store.commit_allocation(changed, "Dispatcher", "same-key", confirmed=True)
    assert store.records() == [record]


def test_stale_preview_and_duplicate_order_cannot_reserve_again(store):
    first, second = preview(store), preview(store, "R07")
    store.commit_allocation(first, "A", "first", confirmed=True)
    with pytest.raises(AllocationError, match="stale"):
        store.commit_allocation(second, "B", "second", confirmed=True)
    duplicate = preview(store)
    duplicate["request"]["request_id"] = "another message about the same order"
    with pytest.raises(AllocationError, match="not ready"):
        store.commit_allocation(duplicate, "B", "duplicate", confirmed=True)
    assert len(store.records()) == 1
    refreshed = preview(store, "R07")
    store.commit_allocation(refreshed, "B", "second", confirmed=True)
    assert len(store.records()) == 2


def test_concurrent_confirmations_serialize_and_require_second_review(store):
    other = AllocationStore(store.path)
    reviews = [preview(store), preview(other, "R07")]

    def save(index):
        try:
            return (store if index == 0 else other).commit_allocation(
                reviews[index], "Dispatcher", str(index), confirmed=True
            )
        except AllocationError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(save, [0, 1]))
    assert sum(isinstance(result, dict) for result in results) == 1
    assert any(isinstance(result, str) and "stale" in result for result in results)
    assert len(store.records()) == 1


@pytest.mark.parametrize("request_id", ["R03", "R08", "R13", "R20", "R23", "R28", "R30"])
def test_exception_states_cannot_commit(store, request_id):
    reviewed = preview(store, request_id)
    assert not reviewed["commit_allowed"]
    with pytest.raises(AllocationError, match="not ready"):
        store.commit_allocation(reviewed, "Dispatcher", "blocked", confirmed=True)
    assert not store.records()


@pytest.mark.parametrize("field,value", [("recommendation", "W7"), ("commit_allowed", False), ("message", "Changed")])
def test_client_cannot_replace_regenerated_tool_evidence(store, field, value):
    reviewed = preview(store)
    reviewed[field] = value
    with pytest.raises(AllocationError, match="stale or changed"):
        store.commit_allocation(reviewed, "Dispatcher", "tampered", confirmed=True)
    assert not store.records()


def test_forged_eta_and_queue_revision_are_rejected(store):
    reviewed = preview(store)
    reviewed["candidates"][0]["display"]["eta"] = "tomorrow"
    with pytest.raises(AllocationError):
        store.commit_allocation(reviewed, "Dispatcher", "bad-eta", confirmed=True)
    reviewed = preview(store)
    reviewed["storage"]["revision"] += 1
    with pytest.raises(AllocationError):
        store.commit_allocation(reviewed, "Dispatcher", "bad-revision", confirmed=True)
    assert not store.records()


def test_completed_order_is_not_redispatched(store):
    order = next(row for row in DispatchDesk().orders if row["status"] == "COMPLETE")
    reviewed = store.preview(
        {"request_id": "test", "time": "now", "requester": "A", "text": "Send this completed order"},
        DispatchInput(order_id=order["order_id"], due_date="2026-12-01"),
        ObjectiveWeights(),
    )
    assert reviewed["status"] == "NEEDS_REVIEW"
    with pytest.raises(AllocationError, match="not ready"):
        store.commit_allocation(reviewed, "Dispatcher", "completed", confirmed=True)


@pytest.mark.parametrize("actor,key,confirmed", [("", "key", True), ("A", "", True), ("A", "key", False)])
def test_identity_and_explicit_confirmation_are_required(store, actor, key, confirmed):
    with pytest.raises(AllocationError):
        store.commit_allocation(preview(store), actor, key, confirmed=confirmed)
    assert not store.records()


def test_failed_queue_update_rolls_back_allocation_insert(store):
    reviewed = preview(store)
    with sqlite3.connect(store.path) as connection:
        connection.execute(
            "CREATE TRIGGER reject_state BEFORE UPDATE ON state BEGIN SELECT RAISE(ABORT, 'test write failure'); END"
        )
    with pytest.raises(sqlite3.Error, match="test write failure"):
        store.commit_allocation(reviewed, "Dispatcher", "failed", confirmed=True)
    assert not store.records()
    assert preview(store) == reviewed


def test_source_change_rejects_workspace_without_resetting_it(store, monkeypatch):
    from dss5105 import records

    original = records.DispatchDesk

    def changed_desk():
        desk = original()
        desk.source_hashes["orders.csv"] = "changed source"
        return desk

    reviewed = preview(store)
    monkeypatch.setattr(records, "DispatchDesk", changed_desk)
    with pytest.raises(AllocationError, match="sources have changed"):
        store.commit_allocation(reviewed, "Dispatcher", "changed-source", confirmed=True)
    with pytest.raises(AllocationError, match="sources have changed"):
        AllocationStore(store.path)
    assert not store.records()


def test_preview_from_another_database_is_rejected(store, tmp_path):
    foreign = AllocationStore(tmp_path / "foreign.sqlite3")
    with pytest.raises(AllocationError, match="stale"):
        store.commit_allocation(preview(foreign), "Dispatcher", "foreign", confirmed=True)


def test_intake_evidence_is_separate_from_authoritative_tool_evidence(store):
    reviewed = preview(store)
    reviewed["conversation"] = {"turns": [{"text": "original request"}], "traces": []}
    record = store.commit_allocation(reviewed, "Dispatcher", "with-chat", confirmed=True)
    assert record["intake_evidence"]["conversation"] == reviewed["conversation"]
    assert "conversation" not in record["tool_evidence"]


def test_archive_moves_the_plan_aside_and_starts_from_the_snapshot(tmp_path):
    store = AllocationStore(tmp_path / "plan.sqlite3")
    database = store.summary()["database_id"]
    target = store.archive()
    assert target.exists() and target.parent == tmp_path / "archive"
    fresh = store.summary()
    assert fresh["database_id"] != database and fresh["revision"] == 0 and fresh["ledger"] == {}
