"""Score saved artifacts offline; never invoke intake, a provider, or dispatch previews."""

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from dataclasses import asdict
from datetime import date, datetime, time, timedelta
from math import ceil, isfinite
from pathlib import Path

from dss5105.benchmark_integrity import source_sha256

VERSION = "reliability-score-v1"
ROOT = Path(__file__).resolve().parents[2]
MISSING = object()
OUTCOMES = ("PASS", "FAIL", "NOT_APPLICABLE", "UNRESOLVED_POLICY", "NOT_SCORABLE")
BASES = ("adjudicated", "provisional", "integrity_audit")
FAILURES = ("provider_error", "parsing_error", "validation_error", "tool_error", "not_completed")
UNRESOLVED = {"R01", "R03", "R06", "R10", "R15", "R16", "R19", "R23", "R29"}
SOURCE_TYPES = ("recorded_model_run", "structured_fixture", "synthetic")
COURSE_FILES = ("orders.csv", "workshops.csv", "dispatch_requests.txt")
STANDARD_QUESTIONS = {
    "order": "Which order do you mean? Please confirm its order ID.",
    "quantity": "Please confirm the quantity using digits.",
    "deadline": "Please confirm the delivery deadline using an explicit date, preferably YYYY-MM-DD.",
    "scope": "This request needs a new, fully specified order request. Please start a new request.",
    "constraint_change": (
        "Existing exclusions cannot be relaxed here. Start a new request with the agreed constraints."
    ),
}
METRICS = {
    "operational_completion": "execution",
    "request_field_correctness": "extraction",
    "request_exact_match": "extraction",
    "forbidden_field_violation_rate": "extraction",
    "status_correctness": "behavior",
    "resolved_field_correctness": "behavior",
    "required_needs_recall": "clarification",
    "forbidden_needs_violation_rate": "clarification",
    "deferred_needs_correctness": "clarification",
    "required_flags_recall": "behavior",
    "forbidden_flags_violation_rate": "behavior",
    "exclusion_recall": "constraints",
    "exclusion_exactness": "constraints",
    "constraint_application": "constraints",
    "constraint_application_evidence": "constraints",
    "deferred_needs_invariant": "integrity",
    "duplicate_standard_clarification_rate": "clarification",
    "tool_integrity": "integrity",
    "tool_integrity_evidence": "integrity",
    "tool_candidate_integrity": "integrity",
    "tool_split_integrity": "integrity",
}
VIOLATIONS = {name for name in METRICS if name.endswith("violation_rate")} | {"duplicate_standard_clarification_rate"}


def json_text(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, indent=2) + "\n"


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError(f"Non-finite JSON value: {value}")


def read_json(path):
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_unique_keys, parse_constant=_invalid_constant
    )


def get_path(value, path):
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return MISSING
        value = value[part]
    return value


def exact_equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(exact_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(exact_equal(a, b) for a, b in zip(left, right, strict=True))
    return left == right


def _string_list(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def numeric_map_equal(left, right):
    """Context weights/queues are numbers; JSON int/float encoding is immaterial."""
    return (
        isinstance(left, dict)
        and isinstance(right, dict)
        and left.keys() == right.keys()
        and all(
            type(left[key]) in (int, float)
            and type(right[key]) in (int, float)
            and isfinite(left[key])
            and isfinite(right[key])
            and left[key] == right[key]
            for key in left
        )
    )


def annotation_basis(case):
    annotation = case["gold_annotation"]
    independent = annotation.get("independent_gold")
    finalized = annotation.get("status") == "independently_adjudicated"
    if independent is not False and independent is not True:
        raise ValueError("independent_gold must be an explicit boolean")
    if independent or finalized:
        if not (
            independent is True
            and finalized
            and _string_list(annotation.get("annotators"))
            and annotation["annotators"]
            and all(name.strip() for name in annotation["annotators"])
            and isinstance(annotation.get("adjudicator"), str)
            and annotation["adjudicator"].strip()
            and isinstance(annotation.get("adjudicated_at"), str)
            and annotation["adjudicated_at"].strip()
            and annotation.get("pending_adjudication") == []
        ):
            raise ValueError("Incomplete or contradictory independent gold metadata")
        return "adjudicated"
    return "provisional"


def validate_benchmark(benchmark):
    if benchmark.get("schema_version") != "reliability-case-v1":
        raise ValueError("Unsupported benchmark schema")
    cases = benchmark.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Benchmark must contain cases")
    ids = []
    for case in cases:
        if "consensus_assertions" in case:
            from dss5105.reliability_assertions import validate_approvals

            validate_approvals(case["consensus_assertions"])
        if case.get("split") not in ("development", "held_out") or not isinstance(case.get("raw_text"), str):
            raise ValueError("Templates or un-authored cases cannot be scored")
        ids.append(case["id"])
        if not isinstance(case["id"], str) or not case["id"] or not isinstance(case.get("speaker"), str):
            raise ValueError("Case ID and speaker must be strings")
        annotation_basis(case)
        for key in ("expected_fields", "expected_resolved_fields", "expected_constraints", "adjudication_review"):
            if not isinstance(case.get(key), dict):
                raise ValueError(f"Missing benchmark object: {key}")
        for key in ("forbidden_fields", "required_needs", "forbidden_needs", "required_flags", "forbidden_flags"):
            if not _string_list(case.get(key)):
                raise ValueError(f"Invalid benchmark list: {key}")
        if case.get("expected_deferred_needs") is not None and not _string_list(case["expected_deferred_needs"]):
            raise ValueError("Invalid deferred expectation")
        if "expected_deferred_needs" not in case or "expected_status" not in case:
            raise ValueError("Missing status or deferred expectation")
        exclusions = case["expected_constraints"].get("exclusions")
        if not isinstance(exclusions, list) or any(
            not isinstance(item, dict) or not isinstance(item.get("workshop_id"), str) for item in exclusions
        ):
            raise ValueError("Invalid benchmark exclusions")
        if len({item["workshop_id"] for item in exclusions}) != len(exclusions):
            raise ValueError("Duplicate benchmark exclusions")
        review = case["adjudication_review"]
        if review.get("state") not in {
            "READY_FOR_GOLD",
            "NEEDS_POLICY_DECISION",
            "NEEDS_SOURCE_VERIFICATION",
            "NEEDS_WORDING/EXPECTATION_REFINEMENT",
        } or review.get("unresolved") is not (review.get("state") != "READY_FOR_GOLD"):
            raise ValueError("Inconsistent adjudication review state")
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate benchmark case IDs")


def verify_context(benchmark, manifest, source_root):
    """Return issues and immutable queue data; no agent replay or state changes."""
    context = benchmark["context"]
    issues = []
    hashes = context.get("source_sha256", {})
    modes = context.get("source_hash_modes", {})
    if not hashes or set(hashes) != set(modes):
        issues.append("benchmark_hash_modes_missing_or_inconsistent")
    for name, digest in hashes.items():
        path = (source_root / name).resolve()
        if not path.is_relative_to(source_root.resolve()):
            raise ValueError("Benchmark source path escapes source root")
        try:
            actual = source_sha256(path, mode=modes.get(name, ""))
        except (OSError, ValueError):
            issues.append(f"benchmark_source_unavailable:{name}")
            continue
        if actual != digest:
            issues.append(f"benchmark_source_hash_mismatch:{name}")
    recorded_sources = manifest.get("source_hashes")
    if not isinstance(recorded_sources, dict):
        issues.append("manifest_source_hashes_missing")
        recorded_sources = {}
    for name in COURSE_FILES:
        relative = f"track2/data/{name}"
        if modes.get(relative) != "raw_bytes_sha256":
            issues.append(f"course_source_not_byte_exact:{name}")
        if recorded_sources.get(name) != hashes.get(relative) or relative not in hashes:
            issues.append(f"run_source_hash_mismatch:{name}")
    if manifest.get("snapshot_date") != context.get("as_of"):
        issues.append("snapshot_date_mismatch")
    if context.get("queue_mode") != "independent_workshops_csv_snapshot":
        issues.append("unsupported_queue_mode")
    if context.get("scope") != "registered_order_preview":
        issues.append("unsupported_scope")
    if not numeric_map_equal(manifest.get("weights"), context.get("objective_weights")):
        issues.append("configured_weights_mismatch")
    queues = {}
    try:
        with (source_root / "track2/data/workshops.csv").open(encoding="utf-8", newline="") as file:
            queues = {row["workshop_id"]: float(row["current_queue_days"]) for row in csv.DictReader(file)}
    except (OSError, KeyError, ValueError):
        issues.append("workshop_snapshot_unavailable")
    harness = source_root / "track2/harness/simulate.py"
    try:
        audit_source_ok = recorded_sources.get("simulate.py") == source_sha256(harness, mode="raw_bytes_sha256")
    except OSError:
        audit_source_ok = False
    return {"compatible": not issues, "issues": issues, "audit_source_ok": audit_source_ok}, queues


def case_compatibility(case, record, manifest, common, queues, context):
    issues = list(common["issues"])
    if record is None:
        issues.append("record_missing")
    else:
        request = record.get("request", {})
        if request.get("text") != case["raw_text"]:
            issues.append("request_text_mismatch")
        if request.get("requester") != case["speaker"]:
            issues.append("request_speaker_mismatch")
        preview = record.get("preview")
        if isinstance(preview, dict):
            if get_path(preview, "snapshot.as_of") != context["as_of"]:
                issues.append("preview_snapshot_date_mismatch")
            if not exact_equal(get_path(preview, "snapshot.sources"), manifest.get("source_hashes")):
                issues.append("preview_source_hashes_mismatch")
            if not numeric_map_equal(get_path(preview, "snapshot.queues"), queues):
                issues.append("preview_queue_snapshot_mismatch")
            if not numeric_map_equal(preview.get("configured_weights"), context["objective_weights"]):
                issues.append("preview_configured_weights_mismatch")
        elif record.get("status") == "completed":
            issues.append("completed_preview_missing")
    return {"compatible": not issues, "issues": issues, "audit_source_ok": common["audit_source_ok"]}


def tool_audit(preview, compatibility, source_root):
    if not compatibility["compatible"] or not compatibility["audit_source_ok"]:
        return "NOT_SCORABLE", "tool_source_snapshot_not_verified", [], [], []
    if source_root.resolve() != ROOT.resolve():
        return "NOT_SCORABLE", "tool_wrapper_requires_current_source_checkout", [], [], []
    if not isinstance(preview, dict):
        return "NOT_SCORABLE", "preview_missing", [], [], []
    # Imports do not invoke providers; source data and official offline helpers only.
    from dss5105.allocator import estimate_delivery
    from dss5105.dispatch import DispatchDesk
    from dss5105.harness import eligible_workshops

    errors, incomplete, assertions = [], [], []

    def audit_assertion(key, check, error):
        try:
            passed = check()
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
            assertions.append((key, "NOT_SCORABLE", "candidate_evidence_missing_or_invalid"))
            incomplete.append(key)
        else:
            assertions.append((key, "PASS" if passed else "FAIL", error))
            if not passed:
                errors.append(error)

    def section(name, check):
        try:
            errors.extend(check())
        except (KeyError, TypeError, ValueError, AttributeError, OSError, OverflowError):
            incomplete.append(name)

    try:
        desk = DispatchDesk()
        if desk.source_hashes != preview["snapshot"]["sources"]:
            return "NOT_SCORABLE", "tool_desk_sources_mismatch", [], [], []
    except (KeyError, TypeError, ValueError, AttributeError, OSError):
        return "NOT_SCORABLE", "tool_desk_unavailable", [], ["source_desk"], []

    commitment = get_path(preview, "commit_allowed")
    if commitment is True:
        errors.append("Preview allowed a commitment")
    elif commitment is not False:
        incomplete.append("commit_allowed")
    candidates = get_path(preview, "candidates")
    candidate_ids = []
    if not isinstance(candidates, list):
        incomplete.append("candidates")
        candidates = []  # Local iteration only; the missing source value is retained in preview.
    for index, row in enumerate(candidates):
        workshop_id = get_path(row, "estimate.workshop_id")
        if not isinstance(workshop_id, str):
            incomplete.append(f"candidate_{index}_identity")
            continue
        candidate_ids.append(workshop_id)
        if workshop_id not in desk.workshops:
            errors.append("Candidate has missing or unknown workshop identity")
            continue
        name = get_path(row, "name")
        if name is MISSING:
            incomplete.append(f"candidate_{index}_name")
        elif name != desk.workshops[workshop_id].name:
            errors.append(f"{workshop_id}: workshop name mismatch")

        estimate = row["estimate"]
        formats = {
            "eta": lambda: (
                datetime.combine(date.fromisoformat(preview["snapshot"]["as_of"]), time())
                + timedelta(minutes=ceil(estimate["expected_turnaround_days"] * 1440))
            ).isoformat(sep=" ", timespec="minutes"),
            "turnaround": lambda: f"{estimate['expected_turnaround_days']:.2f} days",
            "lateness": lambda: f"{estimate['lateness_days']:.2f} days",
            "cost": lambda: f"{estimate['cost']:,.2f}",
            "defects": lambda: f"{estimate['defect_risk']:.1%}",
            "score": lambda: f"{row['score']:.4f}",
            "queue": lambda: f"{estimate['queue_days']:.2f} days",
            "processing": lambda: f"{estimate['process_days']:.2f} days",
            "transport": lambda: f"{estimate['transport_days']:.2f} days",
            "expected_rework": lambda: (
                f"{estimate['expected_turnaround_days'] - estimate['turnaround_days']:.2f} days"
            ),
        }
        for field, formatted in formats.items():
            audit_assertion(
                f"candidate_{index}_display_{field}",
                lambda: row["display"][field] == formatted(),
                f"{workshop_id}: display.{field} does not match its own estimate",
            )
        audit_assertion(
            f"candidate_{index}_deadline",
            lambda: row["meets_deadline"] == (estimate["lateness_days"] == 0),
            f"{workshop_id}: deadline flag mismatch",
        )
    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append("Duplicate workshop candidates")
    complete_candidates = isinstance(get_path(preview, "candidates"), list) and len(candidate_ids) == len(candidates)

    def candidate_set():
        if not complete_candidates:
            raise ValueError("Incomplete candidate identities")
        eligible = {workshop.workshop_id for workshop in eligible_workshops(preview["batch"], desk.workshops)}
        excluded = {item["workshop_id"] for item in preview["input"]["exclusions"]}
        return (
            []
            if set(candidate_ids) == eligible - excluded
            else ["Ranked candidate set incomplete or incorrect, including empty set"]
        )

    status = get_path(preview, "status")
    if status is MISSING:
        incomplete.append("status")
    elif status not in ("CLARIFY", "DECLINE", "RECORDED_STATUS"):
        section("ranked_candidate_set", candidate_set)
    for field in ("recommendation", "alternative"):
        choice = get_path(preview, field)
        if choice is MISSING or (choice is not None and not isinstance(choice, str)):
            incomplete.append(field)
            continue
        if choice is not None:
            if complete_candidates:
                if choice not in candidate_ids:
                    errors.append(f"{field} is not a permitted candidate")
            else:
                incomplete.append(f"{field}_membership")

            def selection_policy():
                if preview["input"]["preference"] != "cheapest_on_time":
                    return []
                by_id = {row["estimate"]["workshop_id"]: row for row in candidates}
                selected = by_id[choice]
                if selected["meets_deadline"] is False:
                    return ["Cheapest-on-time selection violates the date or minimum cost"]
                on_time = [row for row in candidates if row["meets_deadline"]]
                return (
                    []
                    if selected["estimate"]["cost"] == min((row["estimate"]["cost"] for row in on_time), default=None)
                    else ["Cheapest-on-time selection violates the date or minimum cost"]
                )

            section(f"{field}_policy", selection_policy)
    if status in ("CLARIFY", "DECLINE"):
        if candidates or isinstance(get_path(preview, "recommendation"), str):
            errors.append("Unresolved request received an allocation")
    elif status == "RECOMMEND":
        choice = get_path(preview, "recommendation")
        if choice is None:
            errors.append("Ready recommendation is missing or late")
        elif isinstance(choice, str):
            row = next((row for row in candidates if get_path(row, "estimate.workshop_id") == choice), None)
            if row is not None:
                on_time = get_path(row, "meets_deadline")
                if on_time is False:
                    errors.append("Ready recommendation is missing or late")
                elif on_time is not True:
                    incomplete.append("recommendation_deadline")
    if preview.get("split_option"):
        split = preview["split_option"]
        audit_assertion(
            "split.total_pieces",
            lambda: sum(part["pieces"] for part in split["parts"]) == preview["batch"]["pieces"],
            "Split parts do not cover the batch",
        )
        audit_assertion("split.part_count", lambda: len(split["parts"]) == 2, "Split must contain two parts")
        parts = get_path(split, "parts")
        if isinstance(parts, list):
            for index, part in enumerate(parts):

                def part_batch():
                    return {
                        **preview["batch"],
                        "pieces": part["pieces"],
                        "sent_date": date.fromisoformat(preview["batch"]["sent_date"]),
                        "due_date": date.fromisoformat(preview["batch"]["due_date"]),
                    }

                audit_assertion(
                    f"split.part_{index}.identity",
                    lambda: part["workshop_id"] in desk.workshops,
                    f"Split part {index} has unknown workshop identity",
                )

                def membership():
                    workshop_id = part["workshop_id"]
                    if workshop_id in candidate_ids:
                        return True
                    if not complete_candidates:
                        raise ValueError("Incomplete candidate membership evidence")
                    return False

                audit_assertion(
                    f"split.part_{index}.membership",
                    membership,
                    f"Split part {index} is not a permitted candidate",
                )
                audit_assertion(
                    f"split.part_{index}.eligibility",
                    lambda: desk.workshops[part["workshop_id"]] in eligible_workshops(part_batch(), desk.workshops),
                    f"Split part {index} is not permitted at its size",
                )
                audit_assertion(
                    f"split.part_{index}.estimate",
                    lambda: (
                        asdict(
                            estimate_delivery(
                                part_batch(), desk.workshops[part["workshop_id"]], preview["snapshot"]["queues"]
                            )
                        )
                        == part["estimate"]
                    ),
                    f"Split part {index} estimate does not recompute",
                )

        def finish():
            return max(part["estimate"]["expected_turnaround_days"] for part in split["parts"])

        audit_assertion(
            "split.finish",
            lambda: split["expected_turnaround_days"] == finish(),
            "Split finish does not match its parts",
        )
        audit_assertion(
            "split.days_saved",
            lambda: (
                split["days_saved"] == preview["earliest_option"]["estimate"]["expected_turnaround_days"] - finish()
            ),
            "Split saving does not match its parts",
        )
        for field in ("eta", "cost", "days_saved"):
            audit_assertion(
                f"split.summary_{field}",
                lambda: split["display"][field] in split["summary"],
                f"Split summary omits tool field {field}",
            )
    errors = list(dict.fromkeys(errors))
    incomplete = list(dict.fromkeys(incomplete))
    return (
        "FAIL" if errors else "NOT_SCORABLE" if incomplete else "PASS",
        "tool_integrity_violations"
        if errors
        else "tool_audit_evidence_incomplete"
        if incomplete
        else "tool_integrity_verified",
        errors,
        incomplete,
        assertions,
    )


def score_case(case, record, compatibility, *, source_root=ROOT, audit_tools=True):
    if "consensus_assertions" in case:
        from dss5105.reliability_assertions import score_approved_case

        return score_approved_case(case, record, compatibility, source_root=source_root, audit_tools=audit_tools)
    return _score_legacy_case(case, record, compatibility, source_root=source_root, audit_tools=audit_tools)


def _score_legacy_case(case, record, compatibility, *, source_root=ROOT, audit_tools=True, assertion_mode=False):
    basis = annotation_basis(case)
    review = case["adjudication_review"]
    unresolved = not assertion_mode and (
        case["id"] in UNRESOLVED or review.get("unresolved") is not False or review.get("state") != "READY_FOR_GOLD"
    )
    preview = record.get("preview", {}) if record else {}
    if not isinstance(preview, dict):
        preview = {}
    execution = record.get("status", MISSING) if record else MISSING
    checks = []

    def add(metric, suffix, outcome, expected=None, observed=MISSING, reason="", paths=(), *, integrity=False):
        if not integrity:
            if unresolved:
                outcome, reason = "UNRESOLVED_POLICY", "case_policy_or_expectation_unresolved"
            elif outcome != "NOT_APPLICABLE" and not compatibility["compatible"]:
                outcome, reason = "NOT_SCORABLE", "artifact_benchmark_incompatible"
        check = {
            "id": f"{metric}.{suffix}",
            "group": METRICS[metric],
            "metric": metric,
            "annotation_basis": "integrity_audit" if integrity else basis,
            "outcome": outcome,
            "expected": expected,
            "observed": None if observed is MISSING else observed,
            "observed_missing": observed is MISSING,
            "reason_code": reason,
            "evidence_paths": list(paths),
        }
        checks.append(check)
        return check

    def compare(metric, suffix, expected, path):
        actual = get_path(preview, path)
        outcome = "NOT_SCORABLE" if actual is MISSING else "PASS" if exact_equal(actual, expected) else "FAIL"
        return add(
            metric,
            suffix,
            outcome,
            expected,
            actual,
            "field_missing" if actual is MISSING else "value_comparison",
            [f"preview.{path}"],
        )

    completion = "NOT_APPLICABLE" if record is None else "PASS" if execution == "completed" else "FAIL"
    add(
        "operational_completion",
        "record",
        completion,
        "completed",
        execution,
        "execution_outcome",
        ["status"],
        integrity=True,
    )
    fields = case["expected_fields"]
    field_checks = [compare("request_field_correctness", key, fields[key], f"input.{key}") for key in sorted(fields)]
    if not fields:
        add("request_field_correctness", "none", "NOT_APPLICABLE", reason="no_expected_fields")
    evaluable = bool(field_checks) and all(check["outcome"] in ("PASS", "FAIL") for check in field_checks)
    exact = (
        "PASS"
        if evaluable and all(check["outcome"] == "PASS" for check in field_checks)
        else "FAIL"
        if evaluable
        else "NOT_SCORABLE"
        if fields
        else "NOT_APPLICABLE"
    )
    add("request_exact_match", "case", exact, fields, get_path(preview, "input"), "complete_request_map_comparison")
    forbidden = case["forbidden_fields"]
    if not forbidden:
        add("forbidden_field_violation_rate", "none", "NOT_APPLICABLE", reason="no_forbidden_fields")
    for key in sorted(forbidden):
        request = get_path(preview, "input")
        actual = get_path(preview, f"input.{key}")
        outcome = (
            "NOT_SCORABLE"
            if not isinstance(request, dict)
            else "PASS"
            if actual is MISSING or actual is None
            else "FAIL"
        )
        add(
            "forbidden_field_violation_rate",
            key,
            outcome,
            "absent_or_null",
            actual,
            "forbidden_field_check",
            [f"preview.input.{key}"],
        )
    expected_status = case.get("expected_status")
    actual_status = get_path(preview, "status")
    status_outcome = (
        "NOT_APPLICABLE"
        if expected_status is None
        else "FAIL"
        if execution in FAILURES
        else "NOT_SCORABLE"
        if actual_status is MISSING or execution != "completed"
        else "PASS"
        if exact_equal(actual_status, expected_status)
        else "FAIL"
    )
    add(
        "status_correctness",
        "status",
        status_outcome,
        expected_status,
        actual_status,
        "execution_failure" if execution in FAILURES else "dispatch_status_comparison",
        ["status", "preview.status"],
    )
    resolved = case["expected_resolved_fields"]
    for path in sorted(resolved):
        compare("resolved_field_correctness", path, resolved[path], path)
    if not resolved:
        add("resolved_field_correctness", "none", "NOT_APPLICABLE", reason="no_resolved_expectations")

    for metric, key, actual_path, forbidden_mode in (
        ("required_needs_recall", "required_needs", "conversation.needs", False),
        ("forbidden_needs_violation_rate", "forbidden_needs", "conversation.needs", True),
        ("required_flags_recall", "required_flags", "flags", False),
        ("forbidden_flags_violation_rate", "forbidden_flags", "flags", True),
    ):
        actual = get_path(preview, actual_path)
        if not case[key]:
            add(metric, "none", "NOT_APPLICABLE", reason="no_item_requirements")
        for item in sorted(case[key]):
            deferred_actual = get_path(preview, "conversation.deferred_needs")
            observed = actual
            paths = [f"preview.{actual_path}"]
            outcome = (
                "NOT_SCORABLE"
                if not _string_list(actual)
                else "PASS"
                if (item not in actual if forbidden_mode else item in actual)
                else "FAIL"
            )
            if metric == "forbidden_needs_violation_rate":
                observed = {
                    "needs": None if actual is MISSING else actual,
                    "deferred_needs": None if deferred_actual is MISSING else deferred_actual,
                }
                paths.append("preview.conversation.deferred_needs")
                present = any(isinstance(values, list) and item in values for values in (actual, deferred_actual))
                outcome = (
                    "FAIL"
                    if present
                    else "PASS"
                    if _string_list(actual) and _string_list(deferred_actual)
                    else "NOT_SCORABLE"
                )
            add(
                metric,
                item,
                outcome,
                {item: "absent" if forbidden_mode else "present"},
                observed,
                "set_membership",
                paths,
            )
    needs_actual = get_path(preview, "conversation.needs")
    deferred_actual = get_path(preview, "conversation.deferred_needs")
    invariant = (
        "NOT_SCORABLE"
        if not _string_list(needs_actual) or not _string_list(deferred_actual)
        else "PASS"
        if set(deferred_actual) <= set(needs_actual)
        else "FAIL"
    )
    add(
        "deferred_needs_invariant",
        "subset",
        invariant,
        "deferred_needs_subset_of_needs",
        {
            "needs": None if needs_actual is MISSING else needs_actual,
            "deferred_needs": None if deferred_actual is MISSING else deferred_actual,
        },
        "deferred_needs_not_subset_of_needs"
        if invariant == "FAIL"
        else "deferred_needs_invariant_verified"
        if invariant == "PASS"
        else "need_state_evidence_missing_or_invalid",
        ["preview.conversation.needs", "preview.conversation.deferred_needs"],
        integrity=True,
    )
    deferred = case["expected_deferred_needs"]
    actual = get_path(preview, "conversation.deferred_needs")
    deferred_outcome = (
        "NOT_APPLICABLE"
        if deferred is None
        else "NOT_SCORABLE"
        if not _string_list(actual)
        else "PASS"
        if set(actual) == set(deferred) and len(actual) == len(set(actual))
        else "FAIL"
    )
    add(
        "deferred_needs_correctness",
        "set",
        deferred_outcome,
        deferred,
        actual,
        "deferred_set_comparison",
        ["preview.conversation.deferred_needs"],
    )
    expected_exclusions = {item["workshop_id"] for item in case["expected_constraints"]["exclusions"]}
    actual_exclusions = get_path(preview, "input.exclusions")
    valid_exclusions = isinstance(actual_exclusions, list) and all(
        isinstance(item, dict) and isinstance(item.get("workshop_id"), str) for item in actual_exclusions
    )
    actual_ids = [item["workshop_id"] for item in actual_exclusions] if valid_exclusions else MISSING
    if not expected_exclusions:
        add("exclusion_recall", "none", "NOT_APPLICABLE", reason="no_expected_exclusions")
    for workshop in sorted(expected_exclusions):
        outcome = "NOT_SCORABLE" if actual_ids is MISSING else "PASS" if workshop in actual_ids else "FAIL"
        add(
            "exclusion_recall",
            workshop,
            outcome,
            workshop,
            actual_ids,
            "exclusion_membership",
            ["preview.input.exclusions"],
        )
    outcome = (
        "NOT_SCORABLE"
        if actual_ids is MISSING
        else "PASS"
        if set(actual_ids) == expected_exclusions and len(actual_ids) == len(set(actual_ids))
        else "FAIL"
    )
    add(
        "exclusion_exactness",
        "set",
        outcome,
        sorted(expected_exclusions),
        actual_ids,
        "exclusion_exact_set",
        ["preview.input.exclusions"],
    )
    candidates = get_path(preview, "candidates")
    candidate_ids = (
        [get_path(item, "estimate.workshop_id") for item in candidates] if isinstance(candidates, list) else MISSING
    )
    choices = [get_path(preview, field) for field in ("recommendation", "alternative")]
    valid_choices = all(choice is None or isinstance(choice, str) for choice in choices)
    if not expected_exclusions:
        add("constraint_application", "none", "NOT_APPLICABLE", reason="no_expected_hard_exclusions")
    for workshop in sorted(expected_exclusions):
        valid = (
            candidate_ids is not MISSING and all(isinstance(value, str) for value in candidate_ids) and valid_choices
        )
        violation = (candidate_ids is not MISSING and workshop in candidate_ids) or workshop in choices
        outcome = "FAIL" if violation else "PASS" if valid else "NOT_SCORABLE"
        add(
            "constraint_application",
            workshop,
            outcome,
            "excluded_from_candidates_and_choices",
            {
                "candidates": [None if value is MISSING else value for value in candidate_ids]
                if candidate_ids is not MISSING
                else None,
                "choices": [None if value is MISSING else value for value in choices],
                "unavailable_evidence_paths": (
                    ["preview.candidates"]
                    if candidate_ids is MISSING
                    else [
                        f"preview.candidates[{index}].estimate.workshop_id"
                        for index, value in enumerate(candidate_ids)
                        if value is MISSING
                    ]
                )
                + [
                    f"preview.{field}"
                    for field, value in zip(("recommendation", "alternative"), choices, strict=True)
                    if value is MISSING
                ],
            },
            "hard_exclusion_application",
            ["preview.candidates", "preview.recommendation", "preview.alternative"],
        )
        if not valid:
            add(
                "constraint_application_evidence",
                workshop,
                "NOT_SCORABLE",
                "complete_candidates_and_choices",
                reason="constraint_evidence_incomplete",
                paths=["preview.candidates", "preview.recommendation", "preview.alternative"],
            )
    message = get_path(preview, "message")
    counts = (
        {key: message.count(text) for key, text in STANDARD_QUESTIONS.items()} if isinstance(message, str) else MISSING
    )
    duplicate_outcome = (
        "NOT_SCORABLE"
        if counts is MISSING
        else "NOT_APPLICABLE"
        if not any(counts.values())
        else "FAIL"
        if any(count > 1 for count in counts.values())
        else "PASS"
    )
    add(
        "duplicate_standard_clarification_rate",
        "message",
        duplicate_outcome,
        "at_most_one_exact_occurrence_per_standard_question",
        counts,
        "exact_standard_question_counts",
        ["preview.message"],
        integrity=True,
    )
    audit_outcome, reason, errors, incomplete, assertions = (
        tool_audit(preview, compatibility, source_root)
        if audit_tools
        else ("NOT_SCORABLE", "tool_audit_disabled", [], [], [])
    )
    add(
        "tool_integrity",
        "preview",
        audit_outcome,
        "no_tool_integrity_errors",
        errors,
        reason,
        ["preview"],
        integrity=True,
    )
    for key, outcome, assertion_reason in assertions:
        add(
            "tool_split_integrity" if key.startswith("split.") else "tool_candidate_integrity",
            key,
            outcome,
            True,
            MISSING if outcome == "NOT_SCORABLE" else outcome == "PASS",
            reason="candidate_evidence_missing_or_invalid"
            if outcome == "NOT_SCORABLE"
            else "candidate_integrity_verified"
            if outcome == "PASS"
            else "candidate_integrity_violation",
            paths=["preview.split_option" if key.startswith("split.") else "preview.candidates"],
            integrity=True,
        )
    assertion_keys = {key for key, _, _ in assertions}
    for component in incomplete:
        if component in assertion_keys:
            continue
        add(
            "tool_integrity_evidence",
            component,
            "NOT_SCORABLE",
            "complete_component_evidence",
            component,
            "tool_component_evidence_incomplete",
            ["preview"],
            integrity=True,
        )
    return {
        "case_id": case["id"],
        "split": case["split"],
        "annotation_basis": basis,
        "adjudication_state": review["state"],
        "execution": {"attempted": record is not None, "outcome": None if execution is MISSING else execution},
        "compatibility": compatibility,
        "checks": checks,
    }


def aggregate(cases):
    metrics = []
    for metric in sorted(set(METRICS) | {check["metric"] for case in cases for check in case["checks"]}):
        for basis in BASES:
            counts = Counter(
                check["outcome"]
                for case in cases
                for check in case["checks"]
                if check["metric"] == metric and check["annotation_basis"] == basis
            )
            denominator = counts["PASS"] + counts["FAIL"]
            numerator = counts["FAIL"] if metric in VIOLATIONS else counts["PASS"]
            eligible = denominator + counts["NOT_SCORABLE"]
            metrics.append(
                {
                    "metric": metric,
                    "annotation_basis": basis,
                    "numerator": numerator,
                    "denominator": denominator,
                    "value": numerator / denominator if denominator else None,
                    "outcome_counts": {outcome: counts[outcome] for outcome in OUTCOMES},
                    "coverage": {
                        "declared_checks": sum(counts.values()),
                        "eligible_assertions": eligible,
                        "evaluable_assertions": denominator,
                        "value": denominator / eligible if eligible else None,
                    },
                }
            )
    attempted = [case for case in cases if case["execution"]["attempted"]]
    return {
        "schema_version": VERSION,
        "planned": len(cases),
        "attempted": len(attempted),
        "unattempted_ids": [case["case_id"] for case in cases if not case["execution"]["attempted"]],
        "execution_outcomes": dict(
            sorted(Counter(case["execution"]["outcome"] or "unknown" for case in attempted).items())
        ),
        "metrics": metrics,
        "limitations": [
            "Provisional diagnostics are not independent gold accuracy.",
            "Integrity audits are partial and do not establish rendered explanation faithfulness.",
            "Unresolved cases have no inferred approved subfields.",
        ],
    }


def score_run(
    benchmark, records, run_manifest, *, source_root=ROOT, source_type="recorded_model_run", audit_tools=True
):
    validate_benchmark(benchmark)
    if source_type not in SOURCE_TYPES:
        raise ValueError("Unsupported source type")
    by_id = {}
    known = {case["id"] for case in benchmark["cases"]}
    for record in records:
        record_id = get_path(record, "request.request_id")
        if not isinstance(record_id, str) or record_id not in known:
            raise ValueError("Artifact case ID missing or absent from benchmark")
        if record_id in by_id:
            raise ValueError(f"Duplicate case record ID: {record_id}")
        by_id[record_id] = record
    common, queues = verify_context(benchmark, run_manifest, source_root)
    results = []
    for case in sorted(benchmark["cases"], key=lambda case: case["id"]):
        record = by_id.get(case["id"])
        compatible = case_compatibility(case, record, run_manifest, common, queues, benchmark["context"])
        results.append(score_case(case, record, compatible, source_root=source_root, audit_tools=audit_tools))
    summary = aggregate(results)
    summary["source_type"] = source_type
    compatibility = {
        "context": common,
        "compatible_attempted_cases": sum(case["compatibility"]["compatible"] for case in results),
        "incompatible_attempted_ids": [
            case["case_id"]
            for case in results
            if case["execution"]["attempted"] and not case["compatibility"]["compatible"]
        ],
    }
    return {"cases": results, "summary": summary, "compatibility": compatibility}


def load_artifact(path, manifest_path=None):
    if path.is_dir():
        if manifest_path is not None:
            raise ValueError("Directory inputs already contain manifest.json")
        manifest_path = path / "manifest.json"
        metadata = {"manifest.json", "source_snapshot.json", "summary.json"}
        files = sorted(file for file in path.glob("*.json") if file.name not in metadata)
        manifest = read_json(manifest_path)
        records = [read_json(file) for file in files]
        consumed = [manifest_path, *files]
    else:
        value = read_json(path)
        if isinstance(value, dict) and "records" in value and "manifest" in value:
            if manifest_path is not None:
                raise ValueError("Bundle already contains its manifest")
            manifest, records = value["manifest"], value["records"]
            consumed = [path]
        else:
            if manifest_path is None:
                raise ValueError("A single record requires --manifest")
            manifest, records = read_json(manifest_path), [value]
            consumed = [path, manifest_path]
    if not isinstance(records, list) or not isinstance(manifest, dict):
        raise ValueError("Artifact must contain a manifest object and records array")
    digests = {file.name: hashlib.sha256(file.read_bytes()).hexdigest() for file in consumed}
    if len(digests) != len(consumed):
        raise ValueError("Consumed artifact filenames collide")
    digest = hashlib.sha256(json_text(digests).encode("utf-8")).hexdigest()
    return records, manifest, digest, consumed


def serialize_outputs(report, manifest):
    checks_buffer = io.StringIO(newline="")
    columns = [
        "case_id",
        "id",
        "group",
        "metric",
        "annotation_basis",
        "outcome",
        "expected",
        "observed",
        "observed_missing",
        "reason_code",
        "evidence_paths",
    ]
    if any("assertion_id" in check for case in report["cases"] for check in case["checks"]):
        columns.append("assertion_id")
    writer = csv.DictWriter(checks_buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for case in report["cases"]:
        for check in case["checks"]:
            row = {"case_id": case["case_id"], **check}
            for key in ("expected", "observed", "evidence_paths"):
                row[key] = json.dumps(row[key], sort_keys=True, ensure_ascii=True, allow_nan=False)
            writer.writerow(row)
    summary = report["summary"]
    markdown = [
        "# Offline reliability scoring",
        "",
        f"Source type: {summary['source_type']}. Provisional results are diagnostics, not gold accuracy.",
        "",
        f"Planned: {summary['planned']}; attempted: {summary['attempted']}; "
        f"unattempted: {len(summary['unattempted_ids'])}.",
        "",
        "| Metric | Basis | Numerator | Denominator | Value | Unresolved | Not scorable |",
        "|---|---|---|---|---|---|---|",
    ]
    for metric in summary["metrics"]:
        value = "null" if metric["value"] is None else f"{metric['value']:.6f}"
        markdown.append(
            f"| {metric['metric']} | {metric['annotation_basis']} | {metric['numerator']} | "
            f"{metric['denominator']} | {value} | {metric['outcome_counts']['UNRESOLVED_POLICY']} | "
            f"{metric['outcome_counts']['NOT_SCORABLE']} |"
        )
    return {
        "cases.jsonl": "".join(
            json.dumps(case, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n" for case in report["cases"]
        ),
        "summary.json": json_text(summary),
        "summary.md": "\n".join(markdown) + "\n",
        "checks.csv": checks_buffer.getvalue(),
        "manifest.json": json_text(manifest),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--benchmark", type=Path, default=ROOT / "examples/reliability_benchmark.json")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--source-type", choices=SOURCE_TYPES, default="recorded_model_run")
    parser.add_argument("--no-tool-audit", action="store_true")
    args = parser.parse_args(argv)
    try:
        output = args.output.resolve()
        input_path = args.input.resolve()
        if output.exists() or not output.is_relative_to(ROOT.resolve()) or output == ROOT.resolve():
            raise ValueError("Output must be a new directory inside the repository")
        if input_path.is_dir() and output.is_relative_to(input_path):
            raise ValueError("Output must not be inside the input artifact directory")
        records, run_manifest, input_digest, consumed = load_artifact(input_path, args.manifest)
        if any(path.resolve().is_relative_to(output) for path in [args.benchmark, *consumed]):
            raise ValueError("Output would contain input artifacts")
        benchmark = read_json(args.benchmark)
        report = score_run(
            benchmark,
            records,
            run_manifest,
            source_root=args.source_root.resolve(),
            source_type=args.source_type,
            audit_tools=not args.no_tool_audit,
        )
        manifest = {
            "scorer_version": VERSION,
            "scorer_content_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "benchmark_content_hash": hashlib.sha256(args.benchmark.read_bytes()).hexdigest(),
            "input_artifact_hash": input_digest,
            "source_type": args.source_type,
            "benchmark_annotation_state": {
                "status": benchmark.get("annotation_status"),
                "independent_gold": benchmark.get("independent_gold"),
                "case_bases": dict(sorted(Counter(case["annotation_basis"] for case in report["cases"]).items())),
            },
            "scorer_configuration": {
                "tool_audit": not args.no_tool_audit,
                "unresolved_policy": "suppress_all_benchmark_assertions",
                "source_hash_modes": benchmark["context"].get("source_hash_modes"),
            },
            "compatibility": report["compatibility"],
            "run_provenance": {
                key: run_manifest[key] for key in ("model", "intake_version", "file_hashes") if key in run_manifest
            },
        }
        if any("consensus_assertions" in case for case in benchmark["cases"]):
            manifest["scorer_configuration"]["unresolved_policy"] = "explicit_assertion_approval"
            manifest["assertion_adapter_content_hash"] = hashlib.sha256(
                Path(__file__).with_name("reliability_assertions.py").read_bytes()
            ).hexdigest()
        outputs = serialize_outputs(report, manifest)
        output.mkdir(parents=True, exist_ok=False)
        for name, content in outputs.items():
            with (output / name).open("x", encoding="utf-8", newline="\n") as file:
                file.write(content)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(f"Scored {report['summary']['attempted']} attempted records offline; provisional diagnostics are not gold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
