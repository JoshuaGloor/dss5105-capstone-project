"""Long-term assistant memory: standing rules, conversation episodes and the dispatcher profile.

Memory never invents a constraint or a number. A standing rule is created only from an
exclusion that a dispatcher confirmed with a saved booking; it keeps the original quote,
who imposed it and which booking taught it. Python applies active rules as exclusions,
and only an explicit dispatcher action pauses or resumes one. Episodes are an audit
trail of what was said and decided. Allocation records and queues stay in records.py.
"""

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, fields
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import DispatchDesk
from dss5105.records import RUNTIME

DEFAULT_MEMORY_PATH = RUNTIME / "memory.sqlite3"
PROFILE_DEFAULTS = {"dispatcher": "", "preset": "hybrid", "weights": None, "speak_replies": True}
WEIGHT_FIELDS = {field.name for field in fields(ObjectiveWeights)}
MAX_TEXT = 600


class MemoryUpdateError(ValueError):
    """A rejected memory change, safe to show to the dispatcher."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value, name: str, *, optional=False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_TEXT:
        raise MemoryUpdateError(f"{name} must be a nonempty string of at most {MAX_TEXT} characters")
    return value.strip()


class MemoryStore:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else DEFAULT_MEMORY_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        desk = DispatchDesk()
        self.workshops = {key: workshop.name for key, workshop in desk.workshops.items()}
        self.customers = {row["customer"] for row in desk.orders}
        with self._transaction(write=True) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS rules ("
                "rule_id TEXT PRIMARY KEY, workshop_id TEXT NOT NULL, customer TEXT, imposed_by TEXT NOT NULL, "
                "evidence TEXT NOT NULL, created_on TEXT NOT NULL, created_by TEXT NOT NULL, "
                "created_at_utc TEXT NOT NULL, source_allocation_id TEXT, active INTEGER NOT NULL, "
                "changed_by TEXT, changed_at_utc TEXT)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS episodes ("
                "sequence INTEGER PRIMARY KEY AUTOINCREMENT, episode_id TEXT NOT NULL UNIQUE, "
                "created_at_utc TEXT NOT NULL, payload TEXT NOT NULL)"
            )
            connection.execute("CREATE TABLE IF NOT EXISTS profile (key TEXT PRIMARY KEY, value TEXT NOT NULL)")

    @contextmanager
    def _transaction(self, *, write=False):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    # Standing rules -------------------------------------------------------------------------

    def remember_rule(
        self,
        *,
        workshop_id: str,
        customer: str | None,
        imposed_by: str,
        evidence: str,
        created_on: str,
        created_by: str,
        source_allocation_id: str | None = None,
    ) -> dict:
        """Keep a confirmed exclusion for later requests; an identical active rule is reused."""
        if workshop_id not in self.workshops:
            raise MemoryUpdateError("Unknown workshop for a standing rule")
        if customer is not None and customer not in self.customers:
            raise MemoryUpdateError("A standing rule can only name a recorded customer")
        values = {
            "workshop_id": workshop_id,
            "customer": customer,
            "imposed_by": _text(imposed_by, "imposed_by"),
            "evidence": _text(evidence, "evidence"),
            "created_on": _text(created_on, "created_on"),
            "created_by": _text(created_by, "created_by"),
            "source_allocation_id": _text(source_allocation_id, "source_allocation_id", optional=True),
        }
        with self._transaction(write=True) as connection:
            existing = connection.execute(
                "SELECT * FROM rules WHERE workshop_id = ? AND customer IS ? AND active = 1",
                (workshop_id, customer),
            ).fetchone()
            if existing:
                return self._rule(existing)
            rule = {"rule_id": "rule-" + uuid4().hex[:10], **values, "created_at_utc": _now(), "active": 1}
            connection.execute(
                "INSERT INTO rules (rule_id, workshop_id, customer, imposed_by, evidence, created_on, created_by, "
                "created_at_utc, source_allocation_id, active) VALUES (:rule_id, :workshop_id, :customer, "
                ":imposed_by, :evidence, :created_on, :created_by, :created_at_utc, :source_allocation_id, :active)",
                rule,
            )
            return self._rule(
                connection.execute("SELECT * FROM rules WHERE rule_id = ?", (rule["rule_id"],)).fetchone()
            )

    def _rule(self, row) -> dict:
        rule = dict(row)
        rule["active"] = bool(rule["active"])
        rule["workshop_name"] = self.workshops[rule["workshop_id"]]
        scope = f"{rule['customer']} orders" if rule["customer"] else "every order"
        rule["summary"] = f"Avoid {rule['workshop_name']} for {scope}"
        return rule

    def rules(self, *, active_only: bool = False) -> list[dict]:
        query = "SELECT * FROM rules" + (" WHERE active = 1" if active_only else "") + " ORDER BY created_at_utc"
        with self._transaction() as connection:
            return [self._rule(row) for row in connection.execute(query)]

    def rule_payloads(self) -> list[dict]:
        """Active rules in the exact shape DispatchDesk.preview validates and applies."""
        keys = ("rule_id", "workshop_id", "customer", "imposed_by", "evidence", "created_on")
        return [{key: rule[key] for key in keys} for rule in self.rules(active_only=True)]

    def set_rule_active(self, rule_id: str, active: bool, changed_by: str) -> dict:
        if type(active) is not bool:
            raise MemoryUpdateError("active must be a boolean")
        actor = _text(changed_by, "changed_by")
        with self._transaction(write=True) as connection:
            row = connection.execute("SELECT * FROM rules WHERE rule_id = ?", (rule_id,)).fetchone()
            if row is None:
                raise MemoryUpdateError("Unknown standing rule")
            if (
                active
                and connection.execute(
                    "SELECT 1 FROM rules WHERE workshop_id = ? AND customer IS ? AND active = 1 AND rule_id != ?",
                    (row["workshop_id"], row["customer"], rule_id),
                ).fetchone()
            ):
                raise MemoryUpdateError("An identical rule is already active")
            connection.execute(
                "UPDATE rules SET active = ?, changed_by = ?, changed_at_utc = ? WHERE rule_id = ?",
                (int(active), actor, _now(), rule_id),
            )
            return self._rule(connection.execute("SELECT * FROM rules WHERE rule_id = ?", (rule_id,)).fetchone())

    # Episodes ---------------------------------------------------------------------------------

    def log_episode(self, payload: dict) -> dict:
        """Append what was said and what the tools answered; never edited afterwards."""
        if not isinstance(payload, dict):
            raise MemoryUpdateError("An episode must be a JSON object")
        episode = {"episode_id": "ep-" + uuid4().hex[:12], "created_at_utc": _now(), **payload}
        encoded = json.dumps(episode, sort_keys=True, ensure_ascii=True, allow_nan=False)
        with self._transaction(write=True) as connection:
            connection.execute(
                "INSERT INTO episodes (episode_id, created_at_utc, payload) VALUES (?, ?, ?)",
                (episode["episode_id"], episode["created_at_utc"], encoded),
            )
        return episode

    def episodes(self, limit: int = 100) -> list[dict]:
        with self._transaction() as connection:
            rows = connection.execute("SELECT payload FROM episodes ORDER BY sequence DESC LIMIT ?", (limit,))
            return [json.loads(row["payload"]) for row in rows]

    # Profile ----------------------------------------------------------------------------------

    def profile(self) -> dict:
        with self._transaction() as connection:
            stored = {row["key"]: json.loads(row["value"]) for row in connection.execute("SELECT * FROM profile")}
        profile = {**PROFILE_DEFAULTS, **stored}
        return profile

    def update_profile(self, **values) -> dict:
        unknown = set(values) - set(PROFILE_DEFAULTS)
        if unknown:
            raise MemoryUpdateError("Unknown profile setting: " + ", ".join(sorted(unknown)))
        if "dispatcher" in values and values["dispatcher"]:
            values["dispatcher"] = _text(values["dispatcher"], "dispatcher")[:60]
        if "speak_replies" in values and type(values["speak_replies"]) is not bool:
            raise MemoryUpdateError("speak_replies must be a boolean")
        if values.get("weights") is not None:
            weights = values["weights"]
            if not isinstance(weights, dict) or not set(weights) <= WEIGHT_FIELDS:
                raise MemoryUpdateError("Unknown objective weight")
            try:
                values["weights"] = asdict(ObjectiveWeights(**weights))
            except (TypeError, ValueError) as error:
                raise MemoryUpdateError(str(error)) from error
        with self._transaction(write=True) as connection:
            for key, value in values.items():
                connection.execute(
                    "INSERT INTO profile (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, json.dumps(value, sort_keys=True, allow_nan=False)),
                )
        return self.profile()

    def export(self) -> dict:
        return {"rules": self.rules(), "episodes": self.episodes(limit=10_000), "profile": self.profile()}


def rule_suggestions(record: dict, memory: MemoryStore) -> list[dict]:
    """Exclusions from a just-confirmed booking that are not yet remembered for its customer."""
    evidence = record["tool_evidence"]
    customer = evidence["order"]["customer"]
    remembered = {(rule["workshop_id"], rule["customer"]) for rule in memory.rules(active_only=True)}
    applied = {rule["workshop_id"] for rule in evidence.get("applied_rules", [])}
    suggestions = []
    for item in evidence["input"]["exclusions"]:
        if (item["workshop_id"], customer) in remembered or item["workshop_id"] in applied:
            continue
        suggestions.append(
            {
                "workshop_id": item["workshop_id"],
                "workshop_name": memory.workshops[item["workshop_id"]],
                "customer": customer,
                "imposed_by": item["imposed_by"],
                "evidence": item["evidence"],
                "source_allocation_id": record["allocation_id"],
            }
        )
    return suggestions
