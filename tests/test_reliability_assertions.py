"""Assertion approval gates on synthetic saved evidence; no provider calls."""

import copy
import hashlib
import json

import pytest

from dss5105.reliability_assertions import _structured, support_kind, validate_approvals
from dss5105.reliability_score import ROOT, aggregate, read_json, score_case, serialize_outputs, validate_benchmark


@pytest.fixture
def evidence():
    case = copy.deepcopy(read_json(ROOT / "examples/reliability_benchmark.json")["cases"][0])
    record = {
        "status": "completed",
        "preview": {
            "input": {"customer": "Harbor Knits", "exclusions": []},
            "status": "CLARIFY",
            "conversation": {"needs": ["order"], "deferred_needs": []},
            "candidates": [],
            "recommendation": None,
            "alternative": None,
        },
    }
    return case, record


def approval(family="supported_fields", key="customer", value="Harbor Knits", **overrides):
    return {
        "assertion_family": family,
        "assertion_key": key,
        "consensus_value": value,
        "consensus_level": "LIMITED_CONSENSUS",
        "valid_reviewer_count": 2,
        **overrides,
    }


def evaluate(case, record, compatible=True):
    return score_case(case, record, {"compatible": compatible, "audit_source_ok": True}, audit_tools=False)


def semantic(result):
    return [c for c in result["checks"] if c["annotation_basis"] != "integrity_audit"]


def test_legacy_case_still_suppresses_all_and_has_no_assertion_ids(evidence):
    case, record = evidence
    before = evaluate(case, record)
    assert all(c["outcome"] == "UNRESOLVED_POLICY" for c in semantic(before))
    assert all("assertion_id" not in c for c in before["checks"])
    alternate = copy.deepcopy(case)
    alternate["consensus_assertions"] = [approval()]
    assert semantic(evaluate(alternate, record))[0]["outcome"] == "PASS"
    assert evaluate(case, record) == before


def test_policy_case_scores_only_approved_assertion(evidence):
    case, record = evidence
    case["consensus_assertions"] = [approval(), approval(key="product", value="Scarf", score_assertion=False)]
    result = evaluate(case, record)
    a, b = semantic(result)
    assert (a["assertion_id"], a["outcome"]) == ("supported_fields.customer", "PASS")
    assert b["outcome"] == "NOT_SCORABLE" and b["reason_code"] == "assertion_not_approved"
    assert all("assertion_id" in c for c in result["checks"])
    assert not any(c["metric"] == "exclusion_exactness" for c in result["checks"])


def test_unresolved_and_empty_approval_do_not_inherit_legacy_expectations(evidence):
    case, record = evidence
    case["consensus_assertions"] = [approval(consensus_level="UNRESOLVED", valid_reviewer_count=1)]
    assert semantic(evaluate(case, record))[0]["outcome"] == "NOT_SCORABLE"
    case["consensus_assertions"] = []
    assert semantic(evaluate(case, record)) == []


@pytest.mark.parametrize(
    "kind,value,expected",
    [("required", "W1", "PASS"), ("required", "W2", "FAIL"), ("forbidden", "W1", "FAIL"), ("forbidden", "W2", "PASS")],
)
def test_exclusion_membership_does_not_require_exact_set(evidence, kind, value, expected):
    case, record = evidence
    record["preview"]["input"]["exclusions"] = [{"workshop_id": "W1"}, {"workshop_id": "W3"}]
    case["consensus_assertions"] = [approval("exclusions", kind + "." + value, True)]
    checks = semantic(evaluate(case, record))
    assert len(checks) == 1 and checks[0]["outcome"] == expected


def test_explicit_exclusion_exactness_rejects_extra_or_duplicate_members(evidence):
    case, record = evidence
    case["consensus_assertions"] = [approval("supported_fields", "exclusions", ["W1"])]
    for values, expected in [(["W1"], "PASS"), (["W1", "W3"], "FAIL"), (["W1", "W1"], "FAIL")]:
        record["preview"]["input"]["exclusions"] = [{"workshop_id": wid} for wid in values]
        checks = semantic(evaluate(case, record))
        assert len(checks) == 1 and checks[0]["outcome"] == expected
    del record["preview"]["input"]["exclusions"]
    assert semantic(evaluate(case, record))[0]["outcome"] == "NOT_SCORABLE"


@pytest.mark.parametrize(
    "key",
    [
        "no_fabricated_eta",
        "no_fabricated_quote",
        "no_fabricated_history",
        "historical_query_behavior",
        "past_deadline_disclosure",
        "unknown_order_behavior",
    ],
)
def test_prose_assertions_never_pass_from_status_or_absent_claims(evidence, key):
    case, record = evidence
    case["consensus_assertions"] = [approval("operational_predicates", key, True)]
    record["preview"].update(status="DECLINE", message="Everything is supported. ETA tomorrow, quoted price 99.")
    check = semantic(evaluate(case, record))[0]
    assert check["outcome"] == "NOT_SCORABLE"
    assert "no_structured_claim_evidence" in check["reason_code"]


def test_structured_split_review_and_missing_evidence(evidence):
    case, record = evidence
    case["consensus_assertions"] = [approval("operational_predicates", "split_extension_review_path", True)]
    record["preview"]["input"]["split_requested"] = True
    record["preview"].update(flags=["SPLIT_REVIEW"], status="NEEDS_REVIEW", commit_allowed=False)
    assert semantic(evaluate(case, record))[0]["outcome"] == "PASS"
    record["preview"]["commit_allowed"] = True
    assert semantic(evaluate(case, record))[0]["outcome"] == "FAIL"
    del record["preview"]["commit_allowed"]
    assert semantic(evaluate(case, record))[0]["outcome"] == "NOT_SCORABLE"


def test_eligibility_set_is_structured_not_inferred_from_status(evidence):
    case, record = evidence
    case["consensus_assertions"] = [approval("operational_predicates", "workshop_hard_eligibility_ids", ["W2", "W4"])]
    assert semantic(evaluate(case, record))[0]["outcome"] == "NOT_SCORABLE"
    record["preview"]["batch"] = {"pieces": 500, "category": "ACCESSORIES"}
    record["preview"]["candidates"] = [{"estimate": {"workshop_id": wid}} for wid in ["W2", "W4"]]
    assert semantic(evaluate(case, record))[0]["outcome"] == "PASS"
    record["preview"]["candidates"].append({"estimate": {"workshop_id": "W8"}})
    assert semantic(evaluate(case, record))[0]["outcome"] == "FAIL"


def test_exact_refusal_reason_contract_not_keyword_match(evidence):
    case, record = evidence
    case["consensus_assertions"] = [
        approval("operational_predicates", "named_workshop_refusal_reason_code", "batch_cap")
    ]
    record["preview"]["input"]["suggested_workshop"] = "W8"
    record["preview"].update(
        batch={"category": "TOPS", "pieces": 400},
        status="REFUSE_SUGGESTION",
        excluded=[{"workshop_id": "W8", "reasons": ["Batch exceeds the 300-piece limit."]}],
    )
    assert semantic(evaluate(case, record))[0]["outcome"] == "PASS"
    record["preview"]["excluded"][0]["reasons"] = ["This is probably a batch cap issue"]
    assert semantic(evaluate(case, record))[0]["outcome"] == "FAIL"


def test_explicit_exclusion_application_known_failure_beats_missing(evidence):
    case, record = evidence
    case["consensus_assertions"] = [approval("operational_predicates", "explicit_exclusion_workshop_ids", ["W1"])]
    record["preview"]["input"]["exclusions"] = [{"workshop_id": "W1"}]
    assert semantic(evaluate(case, record))[0]["outcome"] == "PASS"
    del record["preview"]["candidates"]
    assert semantic(evaluate(case, record))[0]["outcome"] == "NOT_SCORABLE"
    record["preview"]["recommendation"] = "W1"
    assert semantic(evaluate(case, record))[0]["outcome"] == "FAIL"


def test_approved_assertions_still_require_compatible_evidence(evidence):
    case, record = evidence
    case["consensus_assertions"] = [approval()]
    assert semantic(evaluate(case, record, compatible=False))[0]["outcome"] == "NOT_SCORABLE"


def test_ranking_requires_bound_sources_and_audited_candidates(evidence):
    _, record = evidence
    preview = record["preview"]
    row = approval("operational_predicates", "ranking_requires_tool", True)
    preview.update(
        recommendation="W2",
        candidates=[{"estimate": {"workshop_id": "W2"}}],
        tool_sources={
            name: hashlib.sha256((ROOT / "src/dss5105" / name).read_bytes()).hexdigest()
            for name in ("allocator.py", "dispatch.py")
        },
    )
    audit = [{"metric": "tool_integrity", "outcome": "PASS"}]
    assert _structured(row, preview, {}, ROOT, audit)[0] == "PASS"
    audit[0]["outcome"] = "FAIL"
    assert _structured(row, preview, {}, ROOT, audit)[0] == "NOT_SCORABLE"
    audit[0]["outcome"] = "PASS"
    preview["tool_sources"]["dispatch.py"] = "tampered"
    assert _structured(row, preview, {}, ROOT, audit)[0] == "NOT_SCORABLE"
    preview["recommendation"] = "W8"
    assert _structured(row, preview, {}, ROOT, audit)[0] == "FAIL"


def test_approval_validation_rejects_duplicate_ids_and_mapping_substitution():
    with pytest.raises(ValueError, match="Duplicate"):
        validate_approvals([approval(), approval()])
    with pytest.raises(ValueError, match="mapping"):
        validate_approvals([approval(scorer_mapping="expected_status")])
    with pytest.raises(ValueError, match="reviewer count"):
        validate_approvals([approval(valid_reviewer_count=1)])


def test_v2_csv_has_assertion_ids_and_dynamic_metric(evidence):
    case, record = evidence
    case["consensus_assertions"] = [approval(), approval("operational_predicates", "no_fabricated_quote", True)]
    result = evaluate(case, record)
    report = {"cases": [result], "summary": {**aggregate([result]), "source_type": "synthetic"}}
    outputs = serialize_outputs(report, {})
    assert "assertion_id" in outputs["checks.csv"].splitlines()[0]
    assert "supported_fields.customer" in outputs["checks.csv"]
    assert any(m["metric"] == "consensus_assertion" for m in report["summary"]["metrics"])


def test_canonical_v2_load_and_static_coverage_when_present():
    path = ROOT / "examples/reliability_benchmark_ai_consensus_v2.json"
    if not path.exists():
        pytest.skip("Local reviewer benchmark is not committed")
    benchmark = json.loads(path.read_text(encoding="utf-8"))
    validate_benchmark(benchmark)
    kinds = [support_kind(r) for c in benchmark["cases"] for r in c["consensus_assertions"]]
    assert "native" in kinds and "structured" in kinds and "unsupported" in kinds
