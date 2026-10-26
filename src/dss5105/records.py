"""Transactional local planning records; never contact a workshop or edit course data."""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput, LoadScenario, WorkshopQuery

DEFAULT_STORE_PATH = ROOT / "runtime" / "dispatch.sqlite3"
INTAKE_FIELDS = {"conversation", "interpretation_source", "fixture_sha256"}


class AllocationError(ValueError):
    """An explicit business/state rejection, safe to display to the dispatcher."""


def encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


class AllocationStore:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else DEFAULT_STORE_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        desk = DispatchDesk()
        with self._transaction(write=True) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS state "
                "(singleton INTEGER PRIMARY KEY CHECK(singleton = 1), payload TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS allocations ("
                "sequence INTEGER PRIMARY KEY AUTOINCREMENT, allocation_id TEXT NOT NULL UNIQUE, "
                "order_id TEXT NOT NULL UNIQUE, idempotency_key TEXT NOT NULL UNIQUE, "
                "fingerprint TEXT NOT NULL, confirmed_by TEXT NOT NULL, record TEXT NOT NULL)"
            )
            if connection.execute("SELECT payload FROM state WHERE singleton = 1").fetchone() is None:
                state = {
                    "schema_version": 1,
                    "database_id": str(uuid4()),
                    "revision": 0,
                    "as_of": desk.as_of.isoformat(),
                    "sources": desk.source_hashes,
                    "queues": desk.queues,
                }
                connection.execute("INSERT INTO state VALUES (1, ?)", (encode(state),))
            self._state(connection, desk)

    @contextmanager
    def _transaction(self, *, write=False):
        connection = sqlite3.connect(self.path, timeout=5)
        try:
            connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _state(self, connection, desk):
        state = json.loads(connection.execute("SELECT payload FROM state WHERE singleton = 1").fetchone()[0])
        if (
            state["schema_version"] != 1
            or state["as_of"] != desk.as_of.isoformat()
            or state["sources"] != desk.source_hashes
        ):
            raise AllocationError("Workspace sources have changed. Use a separately reviewed workspace migration.")
        return state

    def _preview(self, connection, desk, state, envelope, request, weights):
        desk.queues = dict(state["queues"])
        result = desk.preview(envelope, request, weights)
        order = result.get("order")
        existing = (
            connection.execute(
                "SELECT allocation_id FROM allocations WHERE order_id = ?", (order["order_id"],)
            ).fetchone()
            if order
            else None
        )
        result["storage"] = {
            "database_id": state["database_id"],
            "revision": state["revision"],
            "existing_allocation_id": existing[0] if existing else None,
        }
        result["assumption"] = (
            f"Saved local planning queues, initialized from workshops.csv on {state['as_of']}. "
            "Confirmed expected processing and rework are added; transport is excluded. "
            "The planning date is fixed and queues do not drain with wall-clock time."
        )
        if existing:
            result.update(
                status="ALREADY_ALLOCATED",
                message="This order already has a saved allocation. Review its record before requesting changes.",
                recommendation=None,
                alternative=None,
                decision_basis=None,
            )
        elif result["status"] == "RECOMMEND" and order["status"] != "IN_PROGRESS":
            result.update(status="NEEDS_REVIEW", message="Only an in-progress order can be saved in this workspace.")
        result["commit_allowed"] = result["status"] == "RECOMMEND"
        return result

    def preview(self, envelope: dict, request: DispatchInput, weights: ObjectiveWeights) -> dict:
        desk = DispatchDesk()
        with self._transaction() as connection:
            state = self._state(connection, desk)
            return self._preview(connection, desk, state, envelope, request, weights)

    def _read_tool(self, method: str, payload) -> dict:
        desk = DispatchDesk()
        with self._transaction() as connection:
            state = self._state(connection, desk)
            desk.queues = dict(state["queues"])
            result = getattr(desk, method)(payload)
            result["storage"] = {"database_id": state["database_id"], "revision": state["revision"]}
            result["assumption"] += " Saved planning queues at a fixed date; queues do not drain with wall-clock time."
            return result

    def query_register(self, query: WorkshopQuery) -> dict:
        return self._read_tool("query_register", query)

    def probe_load(self, scenario: LoadScenario) -> dict:
        return self._read_tool("probe_load", scenario)

    def commit_allocation(self, preview: dict, confirmed_by: str, idempotency_key: str, *, confirmed: bool) -> dict:
        if confirmed is not True:
            raise AllocationError("Explicit dispatcher confirmation is required.")
        if not isinstance(confirmed_by, str) or not confirmed_by.strip() or len(confirmed_by) > 100:
            raise AllocationError("Enter a dispatcher name before confirming.")
        if not isinstance(idempotency_key, str) or not idempotency_key.strip() or len(idempotency_key) > 200:
            raise AllocationError("A valid confirmation retry key is required.")
        actor = confirmed_by.strip()
        digest = fingerprint(preview)
        with self._transaction(write=True) as connection:
            saved = connection.execute(
                "SELECT fingerprint, confirmed_by, record FROM allocations WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if saved:
                if saved[:2] != (digest, actor):
                    raise AllocationError(
                        "This confirmation key was already used for different content or a different actor."
                    )
                return json.loads(saved[2])
            desk = DispatchDesk()
            state = self._state(connection, desk)
            try:
                current = self._preview(
                    connection,
                    desk,
                    state,
                    preview["request"],
                    DispatchInput(**preview["input"]),
                    ObjectiveWeights(**preview["configured_weights"]),
                )
            except (KeyError, TypeError, ValueError) as error:
                raise AllocationError("The reviewed preview is invalid. Generate a fresh preview.") from error
            core = {key: value for key, value in preview.items() if key not in INTAKE_FIELDS}
            if fingerprint(core) != fingerprint(current):
                raise AllocationError("The preview is stale or changed. Refresh it and review the decision again.")
            if not current["commit_allowed"]:
                raise AllocationError("This request is not ready for allocation. Resolve it before confirming.")
            chosen = next(
                row for row in current["candidates"] if row["estimate"]["workshop_id"] == current["recommendation"]
            )
            workshop = chosen["estimate"]["workshop_id"]
            estimate = chosen["estimate"]
            increment = estimate["process_days"] * (1 + 0.5 * estimate["defect_risk"])
            queues = dict(state["queues"])
            queues[workshop] += increment
            updated = {**state, "revision": state["revision"] + 1, "queues": queues}
            record = {
                "allocation_id": str(uuid4()),
                "order_id": current["order"]["order_id"],
                "workshop_id": workshop,
                "workshop_name": chosen["name"],
                "confirmed_by": actor,
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "idempotency_key": idempotency_key,
                "preview_fingerprint": digest,
                "planning_date": state["as_of"],
                "database_id": state["database_id"],
                "revision_before": state["revision"],
                "revision_after": updated["revision"],
                "queues_before": state["queues"],
                "queues_after": queues,
                "reserved_processing_days": increment,
                "tool_evidence": current,
                "intake_evidence": {key: preview[key] for key in INTAKE_FIELDS if key in preview},
                "effect": "Saved local planning reservation only; no workshop contacted.",
            }
            connection.execute(
                "INSERT INTO allocations "
                "(allocation_id, order_id, idempotency_key, fingerprint, confirmed_by, record) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (record["allocation_id"], record["order_id"], idempotency_key, digest, actor, encode(record)),
            )
            connection.execute("UPDATE state SET payload = ? WHERE singleton = 1", (encode(updated),))
            return record

    def records(self) -> list[dict]:
        with self._transaction() as connection:
            return [
                json.loads(row[0]) for row in connection.execute("SELECT record FROM allocations ORDER BY sequence")
            ]
