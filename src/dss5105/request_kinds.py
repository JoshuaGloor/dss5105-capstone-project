"""Group saved execution evidence by approved human request-kind labels."""

import hashlib
import json
from math import isfinite

from dss5105.dispatch import read_inbox
from dss5105.intake import QUESTIONS

KINDS = {
    "ambiguous",
    "complete_impossible",
    "complete_meetable",
    "constraint",
    "ineligible_suggestion",
    "missing_number_or_date",
    "unanswerable",
}


def load_kind_labels(path, source_root):
    raw = path.read_bytes()
    labels = json.loads(raw)
    inbox_path = source_root / "track2/data/dispatch_requests.txt"
    inbox_sha256 = hashlib.sha256(inbox_path.read_bytes()).hexdigest()
    if labels["scope"] != "request_kind_only" or labels["inbox_sha256"] != inbox_sha256:
        raise ValueError("Request-kind labels must match the course inbox snapshot")
    inbox = {request["request_id"]: request for request in read_inbox(inbox_path)}
    if labels["cases"].keys() != inbox.keys() or any(case["kind"] not in KINDS for case in labels["cases"].values()):
        raise ValueError("Request-kind labels must specify an approved kind for every course request")
    return labels, inbox, hashlib.sha256(raw).hexdigest()


def group_request_kinds(kind_data, records, source_hashes, planned_ids=None):
    labels, inbox, label_sha256 = kind_data
    if source_hashes.get("dispatch_requests.txt") != labels["inbox_sha256"]:
        raise ValueError("Saved run inbox hash does not match the request-kind labels")
    planned_ids = set(inbox if planned_ids is None else planned_ids)
    if not planned_ids <= inbox.keys():
        raise ValueError("Request-kind labels do not cover all planned IDs")
    by_kind = {}
    for case_id in sorted(planned_ids):
        kind = labels["cases"][case_id]["kind"]
        row = by_kind.setdefault(kind, {"planned": 0, "attempted": 0, "completed": 0, "case_ids": []})
        row["planned"] += 1
        row["case_ids"].append(case_id)
    seen = set()
    for record in records:
        request = record["request"]
        case_id = request["request_id"]
        if (
            case_id in seen
            or case_id not in planned_ids
            or any(request.get(field) != inbox[case_id][field] for field in ("text", "requester", "time"))
        ):
            raise ValueError(f"Duplicate, unexpected or changed request in saved run: {case_id}")
        seen.add(case_id)
        row = by_kind[labels["cases"][case_id]["kind"]]
        row["attempted"] += 1
        row["completed"] += record["status"] == "completed"
    return {
        "version": labels["version"],
        "sha256": label_sha256,
        "scope": labels["scope"],
        "by_kind": dict(sorted(by_kind.items())),
    }


def behavior_acceptance(records):
    """Check the three approved Data v3 behaviors against recorded tool output."""
    previews = {
        record["request"]["request_id"]: record.get("preview") for record in records if record["status"] == "completed"
    }
    outcomes = {}
    for case_id in ("R01", "R10", "R23"):
        preview = previews.get(case_id)
        if not preview:
            outcomes[case_id] = {"outcome": "NOT_SCORABLE", "expected": "Completed preview required"}
            continue
        if case_id == "R23":
            outcomes[case_id] = _split_acceptance(preview)
            continue
        needed = ("order", "quantity") if case_id == "R01" else ("product", "quantity", "deadline")
        message = preview.get("message")
        passed = (
            isinstance(message, str)
            and preview.get("status") == "CLARIFY"
            and preview.get("commit_allowed") is False
            and all(QUESTIONS[need] in message for need in needed)
            and (case_id != "R10" or QUESTIONS["order"] not in message)
        )
        outcomes[case_id] = {
            "outcome": "MANUAL_REVIEW" if passed and case_id == "R10" else "PASS" if passed else "FAIL",
            "expected": (
                "Ask for order ID and quantity together"
                if case_id == "R01"
                else "Ask for product, quantity and delivery date without requesting an order ID. "
                "Verify the no-reservation disclosure manually."
            ),
        }
    return outcomes


def _split_acceptance(preview):
    expected = "Use unrounded estimates and suggest a split only if strictly faster"
    try:
        candidates = [row["estimate"] for row in preview["candidates"]]
        parts = [row["estimate"] for row in preview["split_option"]["parts"]]
        times = [row["expected_turnaround_days"] for row in candidates + parts]
        if len(parts) != 2 or not all(type(value) in (int, float) and isfinite(value) for value in times):
            raise ValueError("Invalid estimates")
        fastest = min(times[: len(candidates)])
        split_finish = max(times[len(candidates) :])
        fastest_ids = {row["workshop_id"] for row in candidates if row["expected_turnaround_days"] == fastest}
        if split_finish < fastest:
            passed = preview["status"] == "NEEDS_REVIEW" and "SPLIT_REVIEW" in preview["flags"]
        else:
            passed = (
                preview["status"] == "RECOMMEND"
                and preview["recommendation"] in fastest_ids
                and "SPLIT_REVIEW" not in preview["flags"]
            )
        return {"outcome": "PASS" if passed else "FAIL", "expected": expected}
    except (KeyError, TypeError, ValueError):
        return {"outcome": "NOT_SCORABLE", "expected": expected}
