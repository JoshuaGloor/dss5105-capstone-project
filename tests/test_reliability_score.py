"""Synthetic saved-artifact scoring tests; no live model calls."""

import copy
import hashlib
import json
from dataclasses import asdict

import pytest

from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import DispatchDesk, DispatchInput, read_inbox
from dss5105.reliability_score import (
    ROOT,
    STANDARD_QUESTIONS,
    aggregate,
    exact_equal,
    main,
    read_json,
    score_run,
    serialize_outputs,
)


@pytest.fixture
def data():
    benchmark = read_json(ROOT / "examples/reliability_benchmark.json")
    desk = DispatchDesk()
    manifest = {
        "snapshot_date": desk.as_of.isoformat(),
        "source_hashes": desk.source_hashes.copy(),
        "weights": asdict(ObjectiveWeights()),
    }
    inbox = {request["request_id"]: request for request in read_inbox()}

    def record(case_id="R04", **fields):
        case = next(case for case in benchmark["cases"] if case["id"] == case_id)
        request_fields = {key: value for key, value in case["expected_fields"].items() if value is not None}
        request_fields.update(fields)
        result = desk.preview(inbox[case_id], DispatchInput(**request_fields), ObjectiveWeights())
        result["conversation"] = {"needs": [], "deferred_needs": [], "provenance": [], "traces": []}
        return {"request": inbox[case_id].copy(), "status": "completed", "preview": result}

    return benchmark, manifest, record


def run(data, *records, audit=False):
    benchmark, manifest, _ = data
    return score_run(benchmark, list(records), manifest, source_type="synthetic", audit_tools=audit)


def case_result(report, case_id="R04"):
    return next(case for case in report["cases"] if case["case_id"] == case_id)


def checks(report, metric, case_id="R04"):
    return [check for check in case_result(report, case_id)["checks"] if check["metric"] == metric]


def outcome(report, metric, case_id="R04"):
    return checks(report, metric, case_id)[0]["outcome"]


def metric(report, name, basis):
    return next(
        item for item in report["summary"]["metrics"] if item["metric"] == name and item["annotation_basis"] == basis
    )


def test_current_benchmark_has_zero_adjudicated_denominators(data):
    report = run(data, data[2]())
    assert all(
        item["denominator"] == 0 and item["value"] is None
        for item in report["summary"]["metrics"]
        if item["annotation_basis"] == "adjudicated"
    )
    assert metric(report, "status_correctness", "provisional")["denominator"] == 1
    assert outcome(report, "status_correctness") == "PASS"


def test_adjudicated_and_provisional_denominators_never_mix(data):
    benchmark, manifest, make = data
    record_a, record_b = make("R04"), make("R07")
    case = next(case for case in benchmark["cases"] if case["id"] == "R07")
    case["gold_annotation"].update(
        status="independently_adjudicated",
        independent_gold=True,
        annotators=["Reviewer"],
        adjudicator="Human",
        adjudicated_at="2026-10-13",
        pending_adjudication=[],
    )
    report = score_run(benchmark, [record_a, record_b], manifest, source_type="synthetic", audit_tools=False)
    assert metric(report, "status_correctness", "provisional")["denominator"] == 1
    assert metric(report, "status_correctness", "adjudicated")["denominator"] == 1
    assert metric(report, "operational_completion", "integrity_audit")["denominator"] == 2


def test_incomplete_independent_gold_claim_is_rejected(data):
    benchmark, manifest, make = data
    record = make()
    benchmark["cases"][3]["gold_annotation"]["independent_gold"] = True
    with pytest.raises(ValueError, match="gold metadata"):
        score_run(benchmark, [record], manifest)


def test_unresolved_cases_suppress_every_benchmark_check(data):
    record = data[2]("R06")
    report = run(data, record)
    checks_for_case = case_result(report, "R06")["checks"]
    assert all(
        check["outcome"] == "UNRESOLVED_POLICY"
        for check in checks_for_case
        if check["annotation_basis"] != "integrity_audit"
    )
    assert outcome(report, "operational_completion", "R06") == "PASS"
    assert metric(report, "status_correctness", "provisional")["denominator"] == 0


def test_explicit_null_requires_observed_null_and_missing_is_not_scorable(data):
    benchmark, _, make = data
    case = next(case for case in benchmark["cases"] if case["id"] == "R04")
    case["expected_fields"] = {"suggested_workshop": None}
    record = make()
    assert outcome(run(data, record), "request_field_correctness") == "PASS"
    del record["preview"]["input"]["suggested_workshop"]
    report = run(data, record)
    assert outcome(report, "request_field_correctness") == "NOT_SCORABLE"
    assert checks(report, "request_field_correctness")[0]["observed_missing"] is True
    assert outcome(report, "request_exact_match") == "NOT_SCORABLE"


@pytest.mark.parametrize("wrong", [True, 600.0, "600"])
def test_exact_field_comparison_preserves_types(data, wrong):
    record = data[2]()
    record["preview"]["input"]["pieces"] = wrong
    report = run(data, record)
    assert (
        next(check for check in checks(report, "request_field_correctness") if check["id"].endswith("pieces"))[
            "outcome"
        ]
        == "FAIL"
    )
    assert outcome(report, "request_exact_match") == "FAIL"
    assert not exact_equal(True, 1)


@pytest.mark.parametrize("value", [0, False, ""])
def test_nonnull_forbidden_fields_are_violations(data, value):
    record = data[2]()
    record["preview"]["input"]["cost"] = value
    report = run(data, record)
    assert (
        next(check for check in checks(report, "forbidden_field_violation_rate") if check["id"].endswith("cost"))[
            "outcome"
        ]
        == "FAIL"
    )
    assert metric(report, "forbidden_field_violation_rate", "provisional")["numerator"] == 1


def test_request_and_resolved_fields_are_independent(data):
    record = data[2]("R14")
    report = run(data, record)
    assert record["preview"]["input"]["pieces"] is None
    assert record["preview"]["batch"]["pieces"] == 2000
    assert all(check["outcome"] == "PASS" for check in checks(report, "resolved_field_correctness", "R14"))
    assert all(check["outcome"] == "PASS" for check in checks(report, "request_field_correctness", "R14"))


def test_required_forbidden_needs_and_flags(data):
    benchmark, _, make = data
    case = next(case for case in benchmark["cases"] if case["id"] == "R04")
    case.update(required_needs=["deadline"], forbidden_needs=["quantity"], required_flags=["X"], forbidden_flags=["Y"])
    record = make()
    record["preview"]["conversation"]["needs"] = ["quantity"]
    record["preview"]["flags"] = ["Y"]
    report = run(data, record)
    for name in (
        "required_needs_recall",
        "forbidden_needs_violation_rate",
        "required_flags_recall",
        "forbidden_flags_violation_rate",
    ):
        assert outcome(report, name) == "FAIL"
    record["preview"]["conversation"]["needs"] = ["deadline"]
    record["preview"]["flags"] = ["X"]
    report = run(data, record)
    for name in (
        "required_needs_recall",
        "forbidden_needs_violation_rate",
        "required_flags_recall",
        "forbidden_flags_violation_rate",
    ):
        assert outcome(report, name) == "PASS"


@pytest.mark.parametrize(
    "expected,actual,result",
    [
        (None, [], "NOT_APPLICABLE"),
        ([], [], "PASS"),
        ([], ["quantity"], "FAIL"),
        (["quantity", "deadline"], ["deadline", "quantity"], "PASS"),
        (["quantity"], ["quantity", "quantity"], "FAIL"),
    ],
)
def test_deferred_need_sets(data, expected, actual, result):
    benchmark, _, make = data
    next(case for case in benchmark["cases"] if case["id"] == "R04")["expected_deferred_needs"] = expected
    record = make()
    record["preview"]["conversation"]["deferred_needs"] = actual
    assert outcome(run(data, record), "deferred_needs_correctness") == result


def test_missing_legacy_deferred_needs_is_not_scorable(data):
    record = data[2]()
    del record["preview"]["conversation"]["deferred_needs"]
    assert outcome(run(data, record), "deferred_needs_correctness") == "NOT_SCORABLE"


def test_exclusion_omission_invention_and_application(data):
    record = data[2]("R25")
    record["preview"]["input"]["exclusions"] = []
    record["preview"]["recommendation"] = "W3"
    report = run(data, record)
    for name in ("exclusion_recall", "exclusion_exactness", "constraint_application"):
        assert outcome(report, name, "R25") == "FAIL"
    record = data[2]()
    record["preview"]["input"]["exclusions"] = [{"workshop_id": "W3"}]
    assert outcome(run(data, record), "exclusion_exactness") == "FAIL"


@pytest.mark.parametrize("failure", ["provider_error", "parsing_error", "validation_error", "tool_error"])
def test_execution_failure_is_not_dispatch_status(data, failure):
    record = data[2]()
    record.update(status=failure)
    del record["preview"]
    report = run(data, record)
    assert outcome(report, "operational_completion") == "FAIL"
    assert outcome(report, "status_correctness") == "FAIL"
    assert outcome(report, "request_field_correctness") == "NOT_SCORABLE"
    assert report["summary"]["execution_outcomes"][failure] == 1


def test_completed_clarification_is_execution_success_even_if_semantically_wrong(data):
    record = data[2]()
    record["preview"]["status"] = "CLARIFY"
    report = run(data, record)
    assert outcome(report, "operational_completion") == "PASS"
    assert outcome(report, "status_correctness") == "FAIL"


def test_tool_audit_detects_empty_ranked_candidates_without_model_or_preview_calls(data, monkeypatch):
    from dss5105 import llm

    def forbidden(*args, **kwargs):
        pytest.fail("Scorer must not invoke a model or replay dispatch")

    record = data[2]()
    record["preview"].update(candidates=[], recommendation=None)
    monkeypatch.setattr(llm, "get_model", forbidden)
    monkeypatch.setattr(DispatchDesk, "preview", forbidden)
    report = run(data, record, audit=True)
    assert outcome(report, "tool_integrity") == "FAIL"
    assert checks(report, "tool_integrity")[0]["annotation_basis"] == "integrity_audit"
    assert any("empty set" in error for error in checks(report, "tool_integrity")[0]["observed"])


def test_tool_audit_passes_valid_preview_and_does_not_mutate_record(data):
    record = data[2]()
    before = copy.deepcopy(record)
    assert outcome(run(data, record, audit=True), "tool_integrity") == "PASS"
    assert record == before


def test_missing_ranked_batch_is_not_a_successful_tool_audit(data):
    record = data[2]()
    del record["preview"]["batch"]
    assert outcome(run(data, record, audit=True), "tool_integrity") == "NOT_SCORABLE"


def test_unknown_candidate_identity_is_a_tool_integrity_failure(data):
    record = data[2]()
    record["preview"]["candidates"][0]["estimate"]["workshop_id"] = "W99"
    assert outcome(run(data, record, audit=True), "tool_integrity") == "FAIL"


def test_outer_request_id_is_used_even_when_preview_id_is_chat(data):
    record = data[2]()
    record["preview"]["request"]["request_id"] = "CHAT"
    assert outcome(run(data, record), "status_correctness") == "PASS"


def test_missing_execution_status_counts_as_attempted_not_completed(data):
    record = data[2]()
    del record["status"]
    report = run(data, record)
    assert metric(report, "operational_completion", "integrity_audit")["denominator"] == 1
    assert outcome(report, "operational_completion") == "FAIL"
    assert outcome(report, "status_correctness") == "NOT_SCORABLE"
    assert report["summary"]["execution_outcomes"] == {"unknown": 1}


def test_known_failures_do_not_drop_from_execution_denominator(data):
    good, failed = data[2]("R04"), data[2]("R07")
    failed["status"] = "provider_error"
    del failed["preview"]
    completion = metric(run(data, good, failed), "operational_completion", "integrity_audit")
    assert (completion["numerator"], completion["denominator"], completion["value"]) == (1, 2, 0.5)


def test_manifest_int_float_weights_are_compatible_but_bools_are_not(data):
    _, manifest, make = data
    record = make()
    manifest["weights"] = {key: int(value) for key, value in manifest["weights"].items()}
    assert outcome(run(data, record), "status_correctness") == "PASS"
    manifest["weights"]["lateness"] = True
    assert outcome(run(data, record), "status_correctness") == "NOT_SCORABLE"


def test_duplicate_standard_question_detection_is_exact_only(data):
    record = data[2]()
    record["preview"]["message"] = STANDARD_QUESTIONS["order"] + " " + STANDARD_QUESTIONS["order"]
    assert outcome(run(data, record), "duplicate_standard_clarification_rate") == "FAIL"
    record["preview"]["message"] = "Which order? Please identify the order."
    assert outcome(run(data, record), "duplicate_standard_clarification_rate") == "NOT_APPLICABLE"


def test_duplicate_record_ids_are_rejected(data):
    record = data[2]()
    with pytest.raises(ValueError, match="Duplicate case record ID"):
        run(data, record, copy.deepcopy(record))


def test_request_text_mismatch_prevents_semantic_scoring(data):
    record = data[2]()
    record["request"]["text"] = "different wording"
    report = run(data, record)
    assert outcome(report, "status_correctness") == "NOT_SCORABLE"
    assert "request_text_mismatch" in case_result(report)["compatibility"]["issues"]


@pytest.mark.parametrize("change", ["sources", "date", "weights", "queue"])
def test_context_incompatibility_is_not_model_failure(data, change):
    _, manifest, make = data
    record = make()
    if change == "sources":
        manifest["source_hashes"]["orders.csv"] = "0" * 64
    elif change == "date":
        manifest["snapshot_date"] = "2026-04-02"
    elif change == "weights":
        manifest["weights"]["cost"] = 1
    else:
        record["preview"]["snapshot"]["queues"]["W1"] += 1
    report = run(data, record, audit=True)
    assert outcome(report, "status_correctness") == "NOT_SCORABLE"
    assert outcome(report, "tool_integrity") == "NOT_SCORABLE"
    assert outcome(report, "operational_completion") == "PASS"


def test_missing_record_is_unattempted_and_zero_denominator_is_null(data):
    report = run(data)
    assert report["summary"]["attempted"] == 0
    assert len(report["summary"]["unattempted_ids"]) == 30
    assert all(item["denominator"] == 0 and item["value"] is None for item in report["summary"]["metrics"])
    assert all(item["value"] is None for item in aggregate([])["metrics"])


def test_templates_cannot_be_scored(data):
    with pytest.raises(ValueError, match="Templates"):
        score_run(read_json(ROOT / "examples/reliability_heldout_template.json"), [], data[1])


def test_serialization_is_deterministic_and_record_order_independent(data):
    a, b = data[2]("R04"), data[2]("R07")
    manifest = {"test": "synthetic"}
    first = serialize_outputs(run(data, a, b), manifest)
    second = serialize_outputs(run(data, b, a), manifest)
    assert first == second
    assert set(first) == {"cases.jsonl", "summary.json", "summary.md", "checks.csv", "manifest.json"}
    assert all("\r\n" not in value for value in first.values())


def test_cli_writes_five_files_and_never_overwrites_input(data, tmp_path):
    benchmark, manifest, make = data
    benchmark_path = tmp_path / "benchmark.json"
    input_path = tmp_path / "input.json"
    benchmark_path.write_text(json.dumps(benchmark), encoding="utf-8")
    input_path.write_text(json.dumps({"manifest": manifest, "records": [make()]}), encoding="utf-8")
    before = hashlib.sha256(input_path.read_bytes()).hexdigest()
    output = tmp_path / "output"
    args = [
        "--input",
        str(input_path),
        "--benchmark",
        str(benchmark_path),
        "--output",
        str(output),
        "--source-type",
        "synthetic",
        "--no-tool-audit",
    ]
    assert main(args) == 0
    assert len(list(output.iterdir())) == 5
    saved = read_json(output / "manifest.json")
    assert saved["benchmark_annotation_state"]["case_bases"] == {"provisional": 30}
    assert saved["source_type"] == "synthetic"
    assert hashlib.sha256(input_path.read_bytes()).hexdigest() == before
    with pytest.raises(SystemExit):
        main(args)


def test_regression_known_exclusion_missing_alternative(data):
    record = data[2]("R25")
    record["preview"]["recommendation"] = "W3"
    del record["preview"]["alternative"]
    report = run(data, record)
    assert outcome(report, "constraint_application", "R25") == "FAIL"
    result = metric(report, "constraint_application", "provisional")
    assert result["denominator"] == 1
    assert result["outcome_counts"]["FAIL"] == 1


def test_regression_tool_failure_missing_alternative(data):
    record = data[2]()
    record["preview"]["commit_allowed"] = True
    del record["preview"]["alternative"]
    report = run(data, record, audit=True)
    assert outcome(report, "tool_integrity") == "FAIL"
    assert "Preview allowed a commitment" in checks(report, "tool_integrity")[0]["observed"]
    assert metric(report, "tool_integrity", "integrity_audit")["denominator"] == 1


def test_regression_forbidden_deferred_need_only(data):
    benchmark, _, make = data
    next(case for case in benchmark["cases"] if case["id"] == "R04")["forbidden_needs"] = ["quantity"]
    record = make()
    record["preview"]["conversation"].update(needs=[], deferred_needs=["quantity"])
    report = run(data, record)
    assert outcome(report, "forbidden_needs_violation_rate") == "FAIL"
    assert any(
        check["annotation_basis"] == "integrity_audit"
        and check["outcome"] == "FAIL"
        and check["reason_code"] == "deferred_needs_not_subset_of_needs"
        for check in case_result(report)["checks"]
    )


@pytest.mark.parametrize("violation,result", [(False, "NOT_SCORABLE"), (True, "FAIL")])
def test_partial_constraint_evidence_does_not_erase_known_selection(data, violation, result):
    record = data[2]("R25")
    record["preview"]["candidates"] = []
    record["preview"]["recommendation"] = "W3" if violation else None
    del record["preview"]["alternative"]
    report = run(data, record)
    assert outcome(report, "constraint_application", "R25") == result
    assert outcome(report, "constraint_application_evidence", "R25") == "NOT_SCORABLE"


@pytest.mark.parametrize("violation,result", [(False, "NOT_SCORABLE"), (True, "FAIL")])
def test_partial_tool_evidence_preserves_failure_and_records_incomplete_component(data, violation, result):
    record = data[2]()
    record["preview"]["commit_allowed"] = violation
    del record["preview"]["alternative"]
    report = run(data, record, audit=True)
    assert outcome(report, "tool_integrity") == result
    partial = checks(report, "tool_integrity_evidence")
    assert any(check["id"].endswith("alternative") and check["outcome"] == "NOT_SCORABLE" for check in partial)


def test_legacy_candidate_error_is_retained_when_other_candidate_evidence_is_missing(data):
    record = data[2]()
    assert len(record["preview"]["candidates"]) >= 2
    del record["preview"]["candidates"][0]["estimate"]["queue_days"]
    record["preview"]["candidates"][1]["display"]["cost"] = "incorrect"
    del record["preview"]["alternative"]
    report = run(data, record, audit=True)
    assert outcome(report, "tool_integrity") == "FAIL"
    assert any("display.cost" in error for error in checks(report, "tool_integrity")[0]["observed"])
    assert any(check["outcome"] == "NOT_SCORABLE" for check in checks(report, "tool_integrity_evidence"))


def test_valid_deferred_subset_has_no_invariant_error(data):
    record = data[2]()
    record["preview"]["conversation"].update(needs=["quantity", "deadline"], deferred_needs=["quantity"])
    assert outcome(run(data, record), "deferred_needs_invariant") == "PASS"


def test_missing_need_list_cannot_hide_known_forbidden_deferred_code(data):
    record = data[2]()
    del record["preview"]["conversation"]["needs"]
    record["preview"]["conversation"]["deferred_needs"] = ["quantity"]
    report = run(data, record)
    quantity = next(
        check for check in checks(report, "forbidden_needs_violation_rate") if check["id"].endswith("quantity")
    )
    assert quantity["outcome"] == "FAIL"
    assert outcome(report, "deferred_needs_invariant") == "NOT_SCORABLE"


def test_missing_deferred_state_does_not_claim_forbidden_need_absence(data):
    record = data[2]()
    del record["preview"]["conversation"]["deferred_needs"]
    report = run(data, record)
    assert all(check["outcome"] == "NOT_SCORABLE" for check in checks(report, "forbidden_needs_violation_rate"))
    assert outcome(report, "deferred_needs_invariant") == "NOT_SCORABLE"


def test_partial_constraint_observations_serialize_without_repairing_record(data):
    record = data[2]("R25")
    record["preview"]["candidates"] = [{"estimate": {}}]
    record["preview"]["recommendation"] = "W3"
    del record["preview"]["alternative"]
    before = copy.deepcopy(record)
    report = run(data, record)
    assert outcome(report, "constraint_application", "R25") == "FAIL"
    observation = checks(report, "constraint_application", "R25")[0]["observed"]
    assert "preview.alternative" in observation["unavailable_evidence_paths"]
    assert "preview.candidates[0].estimate.workshop_id" in observation["unavailable_evidence_paths"]
    serialize_outputs(report, {"test": "synthetic"})
    assert record == before


def test_regression_candidate_cost_failure_survives_missing_deadline(data):
    record = data[2]()
    row = record["preview"]["candidates"][0]
    row["display"]["cost"] = "incorrect"
    del row["meets_deadline"]
    report = run(data, record, audit=True)
    assert outcome(report, "tool_integrity") == "FAIL"
    assert any("display.cost" in error for error in checks(report, "tool_integrity")[0]["observed"])
    assert metric(report, "tool_integrity", "integrity_audit")["denominator"] == 1


@pytest.mark.parametrize(
    "wrong,missing,result", [(True, True, "FAIL"), (False, True, "NOT_SCORABLE"), (True, False, "FAIL")]
)
def test_independent_candidate_assertions(data, wrong, missing, result):
    record = data[2]()
    row = record["preview"]["candidates"][0]
    if wrong:
        row["display"]["cost"] = "incorrect"
        row["display"]["eta"] = "incorrect"
    if missing:
        del row["meets_deadline"]
    report = run(data, record, audit=True)
    assert outcome(report, "tool_integrity") == result
    detail = {check["id"].split(".")[-1]: check for check in checks(report, "tool_candidate_integrity")}
    assert detail["candidate_0_display_cost"]["outcome"] == ("FAIL" if wrong else "PASS")
    assert detail["candidate_0_display_eta"]["outcome"] == ("FAIL" if wrong else "PASS")
    assert detail["candidate_0_deadline"]["outcome"] == ("NOT_SCORABLE" if missing else "PASS")
    summary = metric(report, "tool_candidate_integrity", "integrity_audit")
    assert summary["outcome_counts"]["FAIL"] == (2 if wrong else 0)
    assert summary["outcome_counts"]["NOT_SCORABLE"] == (1 if missing else 0)
    outputs = serialize_outputs(report, {"test": "synthetic"})
    assert outputs == serialize_outputs(report, {"test": "synthetic"})
    assert len({check["id"] for check in case_result(report)["checks"]}) == len(case_result(report)["checks"])


def test_regression_split_total_failure_survives_missing_summary(data):
    record = data[2]("R23")
    assert record["preview"]["batch"]["pieces"] == 500
    split = record["preview"]["split_option"]
    split["parts"][0]["pieces"] += 1
    del split["summary"]
    report = run(data, record, audit=True)
    assert outcome(report, "tool_integrity", "R23") == "FAIL"
    assert any("cover the batch" in error for error in checks(report, "tool_integrity", "R23")[0]["observed"])
    assert metric(report, "tool_integrity", "integrity_audit")["denominator"] == 1


@pytest.mark.parametrize("wrong,missing", [(True, True), (False, True), (True, False), (False, False)])
def test_split_assertions_keep_failure_and_incomplete_states(data, wrong, missing):
    import csv
    import io

    record = data[2]("R23")
    split = record["preview"]["split_option"]
    if wrong:
        split["parts"][0]["pieces"] += 1
        split["expected_turnaround_days"] += 1
    if missing:
        del split["summary"]
    before = copy.deepcopy(record)
    report = run(data, record, audit=True)
    detail = {check["id"]: check for check in checks(report, "tool_split_integrity", "R23")}
    assert detail["tool_split_integrity.split.total_pieces"]["outcome"] == ("FAIL" if wrong else "PASS")
    assert detail["tool_split_integrity.split.finish"]["outcome"] == ("FAIL" if wrong else "PASS")
    assert all(
        detail[f"tool_split_integrity.split.summary_{field}"]["outcome"] == ("NOT_SCORABLE" if missing else "PASS")
        for field in ("eta", "cost", "days_saved")
    )
    assert outcome(report, "tool_integrity", "R23") == ("FAIL" if wrong else "NOT_SCORABLE" if missing else "PASS")
    summary = metric(report, "tool_split_integrity", "integrity_audit")
    assert summary["denominator"] == sum(check["outcome"] in ("PASS", "FAIL") for check in detail.values())
    assert summary["outcome_counts"]["NOT_SCORABLE"] == (3 if missing else 0)
    if wrong:
        assert summary["outcome_counts"]["FAIL"] >= 2
    case = case_result(report, "R23")
    assert all(
        check["outcome"] == "UNRESOLVED_POLICY"
        for check in case["checks"]
        if check["annotation_basis"] != "integrity_audit"
    )
    assert len({check["id"] for check in case["checks"]}) == len(case["checks"])
    assert not any(check["observed"] in detail for check in checks(report, "tool_integrity_evidence", "R23"))
    outputs = serialize_outputs(report, {"test": "synthetic"})
    csv_rows = list(csv.DictReader(io.StringIO(outputs["checks.csv"])))
    for check in detail.values():
        row = next(row for row in csv_rows if row["case_id"] == "R23" and row["id"] == check["id"])
        assert row["outcome"] == check["outcome"]
    saved = json.loads(outputs["summary.json"])
    assert saved == report["summary"]
    assert (
        f"| tool_split_integrity | integrity_audit | {summary['numerator']} | {summary['denominator']} |"
        in outputs["summary.md"]
    )
    assert outputs == serialize_outputs(report, {"test": "synthetic"})
    assert record == before
