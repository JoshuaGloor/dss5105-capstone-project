"""Opt-in paid development evaluation; preserve outputs before judging them."""

import argparse
import hashlib
import json
import os
import time
from collections import Counter
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from datetime import time as day_time
from math import ceil
from pathlib import Path

from dss5105 import llm
from dss5105.allocator import ObjectiveWeights, estimate_delivery
from dss5105.dispatch import DATA, ROOT, DispatchDesk, read_inbox
from dss5105.harness import eligible_workshops
from dss5105.intake import (
    SCHEMA,
    SYSTEM_PROMPT,
    VERSION,
    Conversation,
    IntakeError,
    interpret_turn,
    preview_conversation,
)

RUBRIC = ROOT / "examples" / "chat_rubric.json"
GENERATED = ROOT / "examples" / "eval_sets"
SETS = {
    "supplied": (DATA / "dispatch_requests.txt", RUBRIC),
    "train_extra": (GENERATED / "train_extra_requests.txt", GENERATED / "train_extra_rubric.json"),
    "test_extra": (GENERATED / "test_extra_requests.txt", GENERATED / "test_extra_rubric.json"),
}
SET_LIMITATIONS = {
    "supplied": "Development set; draft checks are not independent human gold annotations.",
    "train_extra": "Generated development split; labels come from construction and tools, not humans.",
    "test_extra": "Generated test split with unseen templates; held out only if never used for tuning.",
}


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, payload):
    with path.open("x", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=True, indent=2, sort_keys=True)
        file.write("\n")


def output_path(path: Path) -> Path:
    path = path.resolve()
    if not path.is_relative_to(ROOT.resolve()) or path == ROOT.resolve():
        raise ValueError("Evaluation output must be a new directory inside the repository.")
    if path.exists():
        raise ValueError("Output already exists. Choose a fresh directory; paid runs are never overwritten.")
    return path


class RecordedModel:
    """Keep provider response fields, never transport metadata or exception messages."""

    def __init__(self, model, name):
        self.model = model
        self.audit_model_name = name
        self.record = {}

    def with_structured_output(self, schema):
        self.runnable = self.model.with_structured_output(schema, include_raw=True)
        return self

    def invoke(self, messages):
        self.record["messages"] = [{"role": item.type, "content": item.content} for item in messages]
        response = self.runnable.invoke(messages)
        raw = response.get("raw")
        self.record.update(
            patch=response.get("parsed"),
            content=getattr(raw, "content", None),
            tool_calls=getattr(raw, "tool_calls", None),
            usage=getattr(raw, "usage_metadata", None),
            parsing_error_type=(type(response["parsing_error"]).__name__ if response.get("parsing_error") else None),
        )
        if response.get("parsing_error"):
            raise ValueError("Structured output parsing failed")
        return response.get("parsed")


def check_rubric(result: dict, rule: dict) -> dict:
    request = result["input"]
    extraction = [
        f"{key}: expected {expected!r}, got {request.get(key)!r}"
        for key, expected in rule["fields"].items()
        if request.get(key) != expected
    ]
    actual_exclusions = {item["workshop_id"]: item["imposed_by"] for item in request["exclusions"]}
    if actual_exclusions != rule.get("exclusions", {}):
        extraction.append(f"Exclusions/imposers differ: {actual_exclusions!r}")
    for need in rule.get("needs", []):
        if need not in result["conversation"]["needs"]:
            extraction.append(f"Missing clarification need: {need}")
    behavior = []
    if result["status"] not in rule["statuses"]:
        behavior.append(f"Expected state in {rule['statuses']!r}, got {result['status']}")
    for flag in rule.get("flags", []):
        if flag not in result["flags"]:
            behavior.append(f"Missing flag: {flag}")
    return {"extraction_errors": extraction, "behavior_errors": behavior}


def check_tool_integrity(result: dict, desk: DispatchDesk) -> dict:
    """Audit candidate-bound fields; not a semantic or complete UI faithfulness score."""
    errors = []
    claims = 0
    candidates = result["candidates"]
    by_id = {row["estimate"]["workshop_id"]: row for row in candidates}
    if len(by_id) != len(candidates):
        errors.append("Duplicate workshop candidates")
    if result["commit_allowed"]:
        errors.append("Preview allowed a commitment")
    if candidates:
        eligible = {w.workshop_id for w in eligible_workshops(result["batch"], desk.workshops)}
        forbidden = {item["workshop_id"] for item in result["input"]["exclusions"]}
        if set(by_id) != eligible - forbidden:
            errors.append("Candidate set differs from eligible, permitted workshops")
    for row in candidates:
        estimate = row["estimate"]
        workshop_id = estimate["workshop_id"]
        if row["name"] != desk.workshops[workshop_id].name:
            errors.append(f"{workshop_id}: workshop name mismatch")
        eta = datetime.combine(date.fromisoformat(result["snapshot"]["as_of"]), day_time()) + timedelta(
            minutes=ceil(estimate["expected_turnaround_days"] * 1440)
        )
        expected = {
            "eta": eta.isoformat(sep=" ", timespec="minutes"),
            "turnaround": f"{estimate['expected_turnaround_days']:.2f} days",
            "lateness": f"{estimate['lateness_days']:.2f} days",
            "cost": f"{estimate['cost']:,.2f}",
            "defects": f"{estimate['defect_risk']:.1%}",
            "score": f"{row['score']:.4f}",
            "queue": f"{estimate['queue_days']:.2f} days",
            "processing": f"{estimate['process_days']:.2f} days",
            "transport": f"{estimate['transport_days']:.2f} days",
            "expected_rework": f"{estimate['expected_turnaround_days'] - estimate['turnaround_days']:.2f} days",
        }
        for field, value in expected.items():
            claims += 1
            if row["display"].get(field) != value:
                errors.append(f"{workshop_id}: display.{field} does not match its own estimate")
        if row["meets_deadline"] != (estimate["lateness_days"] == 0):
            errors.append(f"{workshop_id}: deadline flag mismatch")
    for field in ("recommendation", "alternative"):
        chosen = result[field]
        if chosen and chosen not in by_id:
            errors.append(f"{field} is not a permitted candidate")
        elif chosen and result["input"]["preference"] == "cheapest_on_time":
            on_time = [row for row in candidates if row["meets_deadline"]]
            if not by_id[chosen]["meets_deadline"] or by_id[chosen]["estimate"]["cost"] != min(
                (row["estimate"]["cost"] for row in on_time), default=None
            ):
                errors.append("Cheapest-on-time selection violates the date or minimum cost")
    split = result.get("split_option")
    if split:
        parts = split["parts"]
        if sum(part["pieces"] for part in parts) != result["batch"]["pieces"] or len(parts) != 2:
            errors.append("Split parts do not cover the batch")
        for part in parts:
            workshop = desk.workshops[part["workshop_id"]]
            batch = {
                **result["batch"],
                "pieces": part["pieces"],
                "sent_date": date.fromisoformat(result["batch"]["sent_date"]),
                "due_date": date.fromisoformat(result["batch"]["due_date"]),
            }
            if part["workshop_id"] not in by_id or workshop not in eligible_workshops(batch, desk.workshops):
                errors.append(f"Split part {part['workshop_id']} is not permitted at its size")
            if asdict(estimate_delivery(batch, workshop, result["snapshot"]["queues"])) != part["estimate"]:
                errors.append(f"Split part {part['workshop_id']} estimate does not recompute")
        finish = max(part["estimate"]["expected_turnaround_days"] for part in parts)
        earliest = result["earliest_option"]["estimate"]["expected_turnaround_days"]
        if split["expected_turnaround_days"] != finish or split["days_saved"] != earliest - finish:
            errors.append("Split finish or saving does not match its parts")
        for field in ("eta", "cost", "days_saved"):
            claims += 1
            if split["display"][field] not in split["summary"]:
                errors.append(f"Split summary omits tool field {field}")
    if result["status"] in ("CLARIFY", "DECLINE") and (candidates or result["recommendation"]):
        errors.append("Unresolved request received an allocation")
    if result["status"] == "RECOMMEND":
        chosen = by_id.get(result["recommendation"])
        if chosen is None or not chosen["meets_deadline"]:
            errors.append("Ready recommendation is missing or late")
    return {"errors": errors, "candidate_count": len(candidates), "display_fields_checked": claims}


def evaluate_case(envelope: dict, rule: dict, desk: DispatchDesk, model: RecordedModel) -> dict:
    started = time.monotonic()
    record = {
        "request": envelope,
        "course_kind": rule.get("course_kind", "unlabelled"),
        "category": rule["category"],
        "template": rule.get("template", "supplied"),
        "status": "not_completed",
    }
    try:
        conversation = interpret_turn(
            Conversation(), envelope["text"], desk, speaker=envelope["requester"], model=model
        )
        result = preview_conversation(conversation, desk, ObjectiveWeights())
        record.update(
            status="completed",
            preview=result,
            rubric=check_rubric(result, rule),
            tool_integrity=check_tool_integrity(result, desk),
        )
    except IntakeError as error:
        failure = "validation_error"
        if "patch" not in model.record:
            failure = "provider_error"
        elif model.record.get("parsing_error_type"):
            failure = "parsing_error"
        record.update(status=failure, safe_error=str(error))
        if error.__cause__:
            record["error_type"] = type(error.__cause__).__name__
    except Exception as error:
        record.update(status="tool_error", error_type=type(error).__name__)
    record.update(elapsed_seconds=round(time.monotonic() - started, 3), model_output=model.record)
    return record


def summarize(records: list[dict], planned: int, evaluation_set: str = "supplied") -> dict:
    completed = [record for record in records if record["status"] == "completed"]

    def passed(record):
        return record["status"] == "completed" and not any(record["rubric"].values())

    def breakdown(key):
        return {
            value: {
                "attempted": sum(record.get(key, "unlabelled") == value for record in records),
                "draft_rubric_passed": sum(
                    passed(record) for record in records if record.get(key, "unlabelled") == value
                ),
            }
            for value in sorted({record.get(key, "unlabelled") for record in records})
        }

    return {
        "evaluation_set": evaluation_set,
        "planned": planned,
        "attempted": len(records),
        "unattempted": planned - len(records),
        "completed": len(completed),
        "outcomes": dict(Counter(record["status"] for record in records)),
        "draft_rubric_passed": sum(passed(record) for record in records),
        "extraction_passed": sum(not record["rubric"]["extraction_errors"] for record in completed),
        "behavior_passed": sum(not record["rubric"]["behavior_errors"] for record in completed),
        "tool_integrity_passed": sum(not record["tool_integrity"]["errors"] for record in completed),
        "display_fields_checked": sum(record["tool_integrity"]["display_fields_checked"] for record in completed),
        "cases_with_candidates": sum(bool(record["preview"]["candidates"]) for record in completed),
        "by_course_kind": breakdown("course_kind"),
        "by_category": breakdown("category"),
        "by_template": breakdown("template"),
        "failed_case_ids": [record["request"]["request_id"] for record in records if not passed(record)],
        "usage": dict(
            sum(
                (
                    Counter(
                        {
                            key: value
                            for key, value in (record["model_output"].get("usage") or {}).items()
                            if isinstance(value, int)
                        }
                    )
                    for record in records
                ),
                Counter(),
            )
        ),
        "limitations": [
            SET_LIMITATIONS[evaluation_set],
            "Single initial response per request; no multi-turn evaluation.",
            "Tool field integrity is not complete UI or explanation-faithfulness evaluation.",
            "No automatic retries; no API price estimate; source queues never change.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Explicitly opt in to paid provider calls")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--set", choices=SETS, default="supplied", dest="evaluation_set")
    args = parser.parse_args()
    if not args.live:
        parser.error("Pass --live to authorize this paid evaluation. No model was called.")
    try:
        output = output_path(args.output)
    except ValueError as error:
        parser.error(str(error))
    inbox_path, rubric_path = SETS[args.evaluation_set]
    desk, inbox = DispatchDesk(), read_inbox(inbox_path)
    rubric = json.loads(rubric_path.read_text())
    if set(rubric["cases"]) != {row["request_id"] for row in inbox}:
        parser.error("Rubric IDs must match the complete inbox")
    output.mkdir(parents=True)
    paths = [
        rubric_path,
        inbox_path,
        ROOT / "uv.lock",
        ROOT / "pyproject.toml",
        *(
            Path(__file__).with_name(name)
            for name in (
                "evaluate_chat.py",
                "intake.py",
                "dispatch.py",
                "allocator.py",
                "harness.py",
                "llm.py",
                "web_app.py",
            )
        ),
    ]
    manifest = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_set": args.evaluation_set,
        "planned_requests": len(inbox),
        "snapshot_date": desk.as_of.isoformat(),
        "source_hashes": desk.source_hashes,
        "file_hashes": {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in paths},
        "rubric": rubric,
        "intake_version": VERSION,
        "system_prompt": SYSTEM_PROMPT,
        "schema": SCHEMA,
        "weights": asdict(ObjectiveWeights()),
        "model_parameters": {"timeout": 30, "max_retries": 0},
        "model": "configuration unavailable",
    }
    try:
        provider = llm.get_model(timeout=30, max_retries=0)
        manifest["model"] = os.getenv("LLM_MODEL", "configured model")
    except Exception as error:
        manifest["configuration_error_type"] = type(error).__name__
        write_json(output / "manifest.json", manifest)
        print("Model configuration failed. Only a safe error type was saved; no request was sent.")
        return 1
    write_json(output / "manifest.json", manifest)
    write_json(output / "source_snapshot.json", {str(path.relative_to(ROOT)): path.read_text() for path in paths})
    records = []
    for envelope in inbox:
        model = RecordedModel(provider, manifest["model"])
        record = evaluate_case(envelope, rubric["cases"][envelope["request_id"]], desk, model)
        write_json(output / (envelope["request_id"] + ".json"), record)
        records.append(record)
        print(f"{envelope['request_id']}: {record['status']} ({record['elapsed_seconds']}s)", flush=True)
        if record["status"] in ("provider_error", "tool_error"):
            print("Stopped without retry. Saved cases remain available.", flush=True)
            break
    summary = summarize(records, len(inbox), args.evaluation_set)
    write_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return int(len(records) != len(inbox))


if __name__ == "__main__":
    raise SystemExit(main())
