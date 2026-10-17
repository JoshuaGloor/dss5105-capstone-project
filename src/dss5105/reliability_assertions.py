"""Opt-in assertion approvals for saved artifacts. No prose classification or live calls."""

import copy
import csv
import hashlib

LEVELS = {"HIGH_CONSENSUS", "MAJORITY", "LIMITED_CONSENSUS"}


def assertion_id(row):
    return f"{row['assertion_family']}.{row['assertion_key']}"


def approved(row):
    return row.get("score_assertion", True) and row["consensus_level"] in LEVELS


def native_mapping(row):
    """Derive allowed mappings from assertion identity, never trust arbitrary paths."""
    family, key = row["assertion_family"], row["assertion_key"]
    if family == "primary_status" and key == "status":
        return "expected_status"
    if family == "supported_fields":
        if key == "exclusions":
            return "expected_constraints.exclusions"
        if key.startswith("retrieved."):
            field = key.removeprefix("retrieved.")
            if field in {"order_id", "customer", "product", "quantity", "due_date"}:
                return "expected_resolved_fields.order." + ("pieces" if field == "quantity" else field)
        if key in {"order_id", "customer", "product", "quantity", "due_date", "suggested_workshop", "preference"}:
            if key == "preference" and row["consensus_value"] is None:
                return None  # Absence of a stated preference is not runtime configured/default.
            return "expected_fields." + ("pieces" if key == "quantity" else key)
    if family == "clarification":
        if key == "deferred_needs_exact":
            return "expected_deferred_needs"
        for prefix in ("required_needs.", "forbidden_needs."):
            if key.startswith(prefix):
                return key
    return None


def validate_approvals(rows):
    if not isinstance(rows, list):
        raise ValueError("consensus_assertions must be a list")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or any(
            not isinstance(row.get(k), str) or not row[k] for k in ("assertion_family", "assertion_key")
        ):
            raise ValueError("Invalid assertion identity")
        aid = assertion_id(row)
        if aid in seen:
            raise ValueError("Duplicate assertion approval")
        seen.add(aid)
        if row.get("consensus_level") not in LEVELS | {"UNRESOLVED"} or "consensus_value" not in row:
            raise ValueError("Invalid consensus approval")
        if "score_assertion" in row and type(row["score_assertion"]) is not bool:
            raise ValueError("score_assertion must be boolean")
        n = row.get("valid_reviewer_count")
        if type(n) is not int or n < 0:
            raise ValueError("Invalid reviewer count")
        if row["consensus_level"] in LEVELS and (
            n < 2
            or (row["consensus_level"] == "LIMITED_CONSENSUS" and n != 2)
            or (row["consensus_level"] != "LIMITED_CONSENSUS" and n < 3)
        ):
            raise ValueError("Consensus level conflicts with reviewer count")
        mapping = native_mapping(row)
        if row.get("scorer_mapping") is not None and row["scorer_mapping"] != mapping:
            raise ValueError("Assertion identity and scorer mapping disagree")
        if not approved(row):
            continue
        value = row["consensus_value"]
        if mapping in {"expected_deferred_needs", "expected_constraints.exclusions"} and (
            not isinstance(value, list) or any(not isinstance(v, str) for v in value) or len(set(value)) != len(value)
        ):
            raise ValueError("Invalid approved exact set")
        if mapping and mapping.startswith(("required_needs.", "forbidden_needs.")) and value is not True:
            raise ValueError("Need membership approval must be true")


def support_kind(row):
    """Static coverage classification; no records or score execution needed."""
    if not approved(row):
        return "unresolved"
    if native_mapping(row):
        return "native"
    family, key = row["assertion_family"], row["assertion_key"]
    if family == "exclusions" and key.startswith(("required.", "forbidden.")):
        return "structured"
    if family == "clarification" and key == "required_needs_exact":
        return "structured"
    if family == "operational_predicates" and key in {
        "workshop_hard_eligibility_ids",
        "explicit_exclusion_workshop_ids",
        "named_workshop_refusal_reason_code",
        "ranking_requires_tool",
        "split_extension_review_path",
    }:
        return "structured"
    return "unsupported"


def _native_case(case, rows):
    clone = copy.deepcopy(case)
    clone.pop("consensus_assertions")
    clone.update(
        expected_fields={},
        expected_resolved_fields={},
        expected_status=None,
        expected_deferred_needs=None,
        expected_constraints={"exclusions": []},
        required_needs=[],
        forbidden_needs=[],
        required_flags=[],
        forbidden_flags=[],
        forbidden_fields=[],
    )
    ids = {}
    for row in rows:
        mapping, value = native_mapping(row), row["consensus_value"]
        if mapping == "expected_status":
            clone[mapping] = {"RECOMMEND_ALLOCATE": "RECOMMEND", "NEEDS_REVIEW_ESCALATE": "NEEDS_REVIEW"}.get(
                value, value
            )
            key = "status_correctness.status"
        elif mapping == "expected_deferred_needs":
            clone[mapping] = value
            key = "deferred_needs_correctness.set"
        elif mapping == "expected_constraints.exclusions":
            clone["expected_constraints"]["exclusions"] = [{"workshop_id": wid} for wid in value]
            key = "exclusion_exactness.set"
        elif mapping:
            name, field = mapping.split(".", 1)
            if name in {"expected_fields", "expected_resolved_fields"}:
                clone[name][field] = value
                key = (
                    "request_field_correctness." if name == "expected_fields" else "resolved_field_correctness."
                ) + field
            else:
                clone[name].append(field)
                key = (
                    "required_needs_recall." if name == "required_needs" else "forbidden_needs_violation_rate."
                ) + field
        else:
            continue
        ids[assertion_id(row)] = key
    return clone, ids


def _structured(row, preview, compatibility, source_root, legacy_checks):
    from dss5105.reliability_score import MISSING, get_path

    family, key, expected = row["assertion_family"], row["assertion_key"], row["consensus_value"]

    def result(value, paths, reason="structured_evidence_comparison"):
        if value is MISSING:
            return "NOT_SCORABLE", None, True, "structured_evidence_missing", paths
        return "PASS" if value else "FAIL", value, False, reason, paths

    def ids(path):
        rows = get_path(preview, path)
        if not isinstance(rows, list):
            return None
        values = [get_path(r, "estimate.workshop_id" if path == "candidates" else "workshop_id") for r in rows]
        return values if all(isinstance(v, str) for v in values) else None

    if family == "exclusions" and key.startswith(("required.", "forbidden.")):
        actual = ids("input.exclusions")
        kind, wid = key.split(".", 1)
        value = MISSING if actual is None else (wid in actual if kind == "required" else wid not in actual)
        return result(value if expected is True else MISSING, ["preview.input.exclusions"])
    if family == "clarification" and key == "required_needs_exact":
        actual = get_path(preview, "conversation.needs")
        valid = isinstance(actual, list) and all(isinstance(v, str) for v in actual)
        valid = valid and isinstance(expected, list) and all(isinstance(v, str) for v in expected)
        return result(
            set(actual) == set(expected) and len(actual) == len(set(actual)) if valid else MISSING,
            ["preview.conversation.needs"],
        )
    if family != "operational_predicates":
        return "NOT_SCORABLE", None, True, "unsupported_assertion", []
    if key == "workshop_hard_eligibility_ids":
        actual = ids("candidates")
        valid = actual is not None and isinstance(get_path(preview, "batch"), dict)
        valid = valid and isinstance(expected, list) and all(isinstance(v, str) for v in expected)
        return result(
            set(actual) == set(expected) and len(actual) == len(set(actual)) if valid else MISSING,
            ["preview.batch", "preview.candidates"],
        )
    if key == "explicit_exclusion_workshop_ids":
        actual, candidates = ids("input.exclusions"), ids("candidates")
        choices = [get_path(preview, k) for k in ("recommendation", "alternative")]
        valid_expected = isinstance(expected, list) and all(isinstance(v, str) for v in expected)
        if not valid_expected:
            return result(MISSING, [])
        if any(w in (candidates or []) or w in choices for w in expected):
            return result(False, ["preview.candidates", "preview.recommendation", "preview.alternative"])
        valid = actual is not None and candidates is not None and all(v is None or isinstance(v, str) for v in choices)
        return result(
            all(w in actual for w in expected) if valid else MISSING,
            ["preview.input.exclusions", "preview.candidates", "preview.recommendation", "preview.alternative"],
        )
    if key == "named_workshop_refusal_reason_code":
        # These are exact structured reason-array values emitted by dispatch.py,
        # not keyword searches over the user-facing message.
        if not compatibility.get("audit_source_ok"):
            return result(MISSING, [])
        wid = get_path(preview, "input.suggested_workshop")
        batch = get_path(preview, "batch")
        excluded = get_path(preview, "excluded")
        if not isinstance(batch, dict) or not isinstance(excluded, list):
            return result(MISSING, ["preview.batch", "preview.excluded"])
        try:
            with (source_root / "track2/data/workshops.csv").open(encoding="utf-8", newline="") as stream:
                workshop = next(w for w in csv.DictReader(stream) if w["workshop_id"] == wid)
            if expected == "batch_cap":
                cap = int(workshop["max_batch_pieces"])
                condition = type(batch["pieces"]) is int and batch["pieces"] > cap
                reason = f"Batch exceeds the {cap}-piece limit."
            elif expected == "suspended":
                condition = workshop["status"] == "SUSPENDED"
                reason = "Status is SUSPENDED."
            elif expected == "category_unsupported":
                condition = batch["category"] not in workshop["makes"].split("+")
                reason = f"Cannot make {batch['category']}."
            else:
                return result(MISSING, [])
            entry = next(e for e in excluded if e.get("workshop_id") == wid)
            if not isinstance(entry.get("reasons"), list):
                return result(MISSING, ["preview.excluded"])
            value = condition and reason in entry["reasons"] and preview.get("status") == "REFUSE_SUGGESTION"
            return result(value, ["preview.input.suggested_workshop", "preview.excluded", "preview.status"])
        except (OSError, StopIteration, KeyError, TypeError, ValueError):
            return result(MISSING, ["preview.excluded"])
    if key == "split_extension_review_path" and expected is True:
        fields = [get_path(preview, k) for k in ("input.split_requested", "flags", "status", "commit_allowed")]
        if any(v is MISSING for v in fields) or not isinstance(fields[1], list):
            return result(MISSING, ["preview.input.split_requested", "preview.flags", "preview.commit_allowed"])
        return result(
            fields[0] is True and "SPLIT_REVIEW" in fields[1] and fields[2] == "NEEDS_REVIEW" and fields[3] is False,
            ["preview.input.split_requested", "preview.flags", "preview.status", "preview.commit_allowed"],
        )
    if key == "ranking_requires_tool" and expected is True:
        choices = [get_path(preview, k) for k in ("recommendation", "alternative")]
        candidates = ids("candidates")
        source = get_path(preview, "tool_sources")
        paths = ["preview.recommendation", "preview.alternative", "preview.candidates", "preview.tool_sources"]
        if not isinstance(source, dict) or candidates is None or not any(isinstance(v, str) for v in choices):
            return result(MISSING, paths)
        if any(isinstance(v, str) and v not in candidates for v in choices):
            return result(False, paths)
        if any(v is not None and not isinstance(v, str) for v in choices):
            return result(MISSING, paths)
        try:
            if any(
                source.get(name) != hashlib.sha256((source_root / "src/dss5105" / name).read_bytes()).hexdigest()
                for name in ("allocator.py", "dispatch.py")
            ):
                return result(MISSING, paths, "tool_source_unavailable")
        except OSError:
            return result(MISSING, paths)
        audit = next(c for c in legacy_checks if c["metric"] == "tool_integrity")
        return result(
            True if audit["outcome"] == "PASS" else MISSING, paths, "recorded_ranking_has_audited_tool_evidence"
        )
    # Clean structured values do not establish absence of fabricated prose claims.
    # No ETA/quote/history claim ledger exists in the recorder contract.
    return "NOT_SCORABLE", None, True, "unsupported_assertion_no_structured_claim_evidence", []


def score_approved_case(case, record, compatibility, *, source_root, audit_tools):
    from dss5105.reliability_score import _score_legacy_case, annotation_basis

    rows = case["consensus_assertions"]
    validate_approvals(rows)
    selected = [r for r in rows if approved(r)]
    clone, native_ids = _native_case(case, selected)
    legacy = _score_legacy_case(
        clone, record, compatibility, source_root=source_root, audit_tools=audit_tools, assertion_mode=True
    )
    by_id = {c["id"]: c for c in legacy["checks"]}
    checks = []
    for check in legacy["checks"]:
        if check["annotation_basis"] == "integrity_audit":
            checks.append({**check, "assertion_id": "integrity." + check["id"]})
    preview = record.get("preview") if isinstance(record, dict) else None
    preview = preview if isinstance(preview, dict) else {}
    for row in rows:
        aid = assertion_id(row)
        if approved(row) and aid in native_ids:
            check = {**by_id[native_ids[aid]], "assertion_id": aid}
        else:
            check = {
                "id": aid,
                "assertion_id": aid,
                "group": "behavior",
                "metric": "consensus_assertion",
                "annotation_basis": annotation_basis(case),
                "outcome": "NOT_SCORABLE",
                "expected": row["consensus_value"],
                "observed": None,
                "observed_missing": True,
                "reason_code": "assertion_not_approved",
                "evidence_paths": [],
            }
            if approved(row):
                if not compatibility["compatible"]:
                    check["reason_code"] = "artifact_benchmark_incompatible"
                elif not record or record.get("status") != "completed":
                    check["reason_code"] = "completed_record_required"
                else:
                    outcome, observed, missing, reason, paths = _structured(
                        row, preview, compatibility, source_root, legacy["checks"]
                    )
                    check.update(
                        outcome=outcome,
                        observed=observed,
                        observed_missing=missing,
                        reason_code=reason,
                        evidence_paths=paths,
                    )
        checks.append(check)
    return {**legacy, "checks": checks}
