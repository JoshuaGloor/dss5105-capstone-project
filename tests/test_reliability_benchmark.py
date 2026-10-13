"""Structural checks only: no production agent imports, model calls, or scoring."""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import pytest
from benchmark_integrity import hash_bytes, source_sha256

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_TYPES = {
    "id": str,
    "raw_text": (str, type(None)),
    "speaker": (str, type(None)),
    "split": str,
    "scenario_family": str,
    "categories": list,
    "expected_status": (str, type(None)),
    "expected_fields": dict,
    "expected_resolved_fields": dict,
    "forbidden_fields": list,
    "required_needs": list,
    "forbidden_needs": list,
    "expected_deferred_needs": (list, type(None)),
    "expected_constraints": dict,
    "expected_workshop_behavior": dict,
    "required_flags": list,
    "forbidden_flags": list,
    "expected_response_behavior": dict,
    "gold_annotation": dict,
    "freeze": dict,
    "notes": list,
}
STRING_LISTS = {
    "categories",
    "forbidden_fields",
    "required_needs",
    "forbidden_needs",
    "required_flags",
    "forbidden_flags",
    "notes",
}
NEEDS = {"order", "quantity", "deadline", "scope", "constraint_change"}
STATUSES = {
    "CLARIFY",
    "DECLINE",
    "RECOMMEND",
    "REFUSE_SUGGESTION",
    "NEEDS_REVIEW",
    "NO_FEASIBLE_OPTION",
    "RECORDED_STATUS",
}
SOURCE_HASH_MODES = {
    "track2/data/dispatch_requests.txt": "raw_bytes_sha256",
    "track2/data/orders.csv": "raw_bytes_sha256",
    "track2/data/workshops.csv": "raw_bytes_sha256",
    "examples/chat_rubric.json": "normalized_text_sha256",
    "examples/dispatch_inputs.json": "normalized_text_sha256",
    "docs/CHAT_EVALUATION_RESULTS.md": "normalized_text_sha256",
    "tests/test_intake.py": "normalized_text_sha256",
    "tests/test_dispatch.py": "normalized_text_sha256",
    "tests/test_chat_ui.py": "normalized_text_sha256",
}


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        assert key not in result, f"Duplicate JSON key: {key}"
        result[key] = value
    return result


def read(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"), object_pairs_hook=unique_keys)


DEVELOPMENT = read("reliability_benchmark.json")
TEMPLATES = read("reliability_heldout_template.json")
ALL_CASES = DEVELOPMENT["cases"] + TEMPLATES["cases"]


@pytest.mark.parametrize("artifact", [DEVELOPMENT, TEMPLATES], ids=["development", "templates"])
def test_envelope_and_context_are_explicit(artifact):
    assert artifact["schema_version"] == "reliability-case-v1"
    assert artifact["annotation_status"] == "pending_independent_adjudication"
    assert artifact["independent_gold"] is False
    assert artifact["freeze_status"] == "not_frozen"
    assert artifact["limitations"]
    assert (ROOT / artifact["schema_document"]).is_file()
    context = artifact["context"]
    assert context["as_of"] == "2026-04-01"
    assert context["queue_mode"] == "independent_workshops_csv_snapshot"
    assert context["scope"] == "registered_order_preview"
    assert set(context["objective_weights"]) == {"lateness", "defects", "cost", "deadline_buffer_days"}
    assert context["source_hash_modes"] == SOURCE_HASH_MODES
    assert set(context["source_sha256"]) == set(context["source_hash_modes"])
    for path, digest in context["source_sha256"].items():
        assert re.fullmatch(r"[0-9a-f]{64}", digest)
        assert source_sha256(ROOT / path, mode=context["source_hash_modes"][path]) == digest


def test_development_ids_exist_exactly_once_and_are_not_held_out():
    assert Counter(case["id"] for case in DEVELOPMENT["cases"]) == Counter(f"R{i:02d}" for i in range(1, 31))
    assert all(case["split"] == "development" for case in DEVELOPMENT["cases"])
    assert all(case["split"] != "held_out" for case in ALL_CASES)


@pytest.mark.parametrize("case", ALL_CASES, ids=lambda case: case["id"])
def test_case_required_fields_and_types(case):
    for key, expected_type in REQUIRED_TYPES.items():
        assert key in case, (case["id"], key)
        assert isinstance(case[key], expected_type), (case["id"], key)
    assert case["expected_status"] in STATUSES
    assert case["scenario_family"]
    assert case["categories"]
    for key in STRING_LISTS:
        assert all(isinstance(item, str) and item for item in case[key])
        assert len(case[key]) == len(set(case[key]))
    assert set(case["required_needs"]) <= NEEDS
    assert set(case["forbidden_needs"]) <= NEEDS
    assert not set(case["required_needs"]) & set(case["forbidden_needs"])
    assert not set(case["required_flags"]) & set(case["forbidden_flags"])
    deferred = case["expected_deferred_needs"]
    if deferred is not None:
        assert set(deferred) <= {"quantity", "deadline"}
        assert set(deferred) <= set(case["required_needs"])
        assert len(deferred) == len(set(deferred))
    if "turns" in case:
        assert isinstance(case["turns"], list)
        assert all(isinstance(turn, dict) for turn in case["turns"])


@pytest.mark.parametrize("case", ALL_CASES, ids=lambda case: case["id"])
def test_nested_metadata_and_field_namespaces(case):
    request_fields = {
        "order_id",
        "customer",
        "product",
        "pieces",
        "due_date",
        "suggested_workshop",
        "intent",
        "date_kind",
        "preference",
        "date_uncertain",
        "split_requested",
    }
    assert set(case["expected_fields"]) <= request_fields
    assert all(key.startswith(("order.", "batch.")) for key in case["expected_resolved_fields"])
    for key in case["forbidden_fields"]:
        assert key not in case["expected_fields"] or case["expected_fields"][key] is None
    constraints = case["expected_constraints"]
    assert isinstance(constraints["exclusions"], list)
    assert isinstance(constraints["split_requested"], bool)
    excluded = []
    for exclusion in constraints["exclusions"]:
        assert {"workshop_id", "imposed_by", "reported_by", "evidence"} <= exclusion.keys()
        assert all(isinstance(value, str) and value for value in exclusion.values())
        assert exclusion["evidence"] in case["raw_text"]
        excluded.append(exclusion["workshop_id"])
    assert len(excluded) == len(set(excluded))
    annotation = case["gold_annotation"]
    assert annotation["independent_gold"] is False
    assert annotation["annotators"] == []
    assert annotation["adjudicator"] is None
    assert annotation["adjudicated_at"] is None
    assert isinstance(annotation["pending_adjudication"], list) and annotation["pending_adjudication"]
    assert isinstance(annotation["supporting_evidence"], list)
    freeze = case["freeze"]
    assert freeze["freeze_status"] == "not_frozen"
    assert freeze["frozen_at"] is None
    assert freeze["content_sha256"] is None
    assert isinstance(freeze["development_exposed"], bool)


def test_raw_requests_and_speakers_match_inbox_exactly():
    text = (ROOT / "track2/data/dispatch_requests.txt").read_text(encoding="utf-8")
    source = {
        case_id: (time, speaker, raw)
        for case_id, time, speaker, raw in re.findall(r"^(R\d{2}) \[(\d\d:\d\d)\] ([^:]+): (.+)$", text, re.MULTILINE)
    }
    assert len(source) == 30
    for case in DEVELOPMENT["cases"]:
        assert (case["source_time"], case["speaker"], case["raw_text"]) == source[case["id"]]
        assert case["gold_annotation"]["status"] == "provisional_pending_independent_adjudication"
        assert case["gold_annotation"]["prior_exposure"] == "development_material"
        assert case["freeze"]["development_exposed"] is True


def test_rubric_fields_are_carried_over_without_using_historical_answers():
    rubric = read("chat_rubric.json")["cases"]
    for case in DEVELOPMENT["cases"]:
        rule = rubric[case["id"]]
        assert case["expected_status"] in rule["statuses"]
        assert all(case["expected_fields"].get(key) == value for key, value in rule["fields"].items())
        assert set(rule.get("needs", [])) <= set(case["required_needs"])
        assert set(rule.get("flags", [])) <= set(case["required_flags"])
        historical = case["historical_observation"]
        assert historical["scope"] == "historical_pre_v3_not_current_wording_or_post_fix_evidence"
        assert historical["raw_artifacts_available_in_checkout"] is False


def test_retrieved_quantity_is_not_request_extraction_and_winners_are_not_hardcoded():
    cases = {case["id"]: case for case in DEVELOPMENT["cases"]}
    assert cases["R14"]["expected_fields"]["pieces"] is None
    assert cases["R14"]["expected_resolved_fields"]["batch.pieces"] == 2000
    assert "quantity" in cases["R14"]["forbidden_needs"]
    assert cases["R12"]["expected_constraints"]["exclusions"][0]["imposed_by"] == "Boss"
    assert cases["R12"]["speaker"] == "Ravi"
    for case in DEVELOPMENT["cases"]:
        workshop = case["expected_workshop_behavior"]
        assert "recommendation" not in workshop
        assert "winner" not in workshop
        if case["expected_status"] in {"RECOMMEND", "REFUSE_SUGGESTION", "NEEDS_REVIEW"}:
            assert isinstance(workshop["selection_predicate"], str)


def test_held_out_slots_are_exactly_ten_unfrozen_authoring_templates():
    assert Counter(case["id"] for case in TEMPLATES["cases"]) == Counter(f"H{i:02d}" for i in range(1, 11))
    for case in TEMPLATES["cases"]:
        assert case["split"] == "held_out_template"
        assert case["raw_text"] is None
        assert case["speaker"] is None
        assert case["turns"] == []
        assert case["freeze_status"] == case["freeze"]["freeze_status"] == "not_frozen"
        assert case["gold_annotation"]["status"] == "authoring_template_pending_independent_authoring_and_adjudication"
        assert case["freeze"]["development_exposed"] is False
        specification = case["authoring_specification"]
        assert specification["requirements"]
        assert specification["final_wording_location"] is None
        assert specification["follow_up_wording_finalized"] is False


@pytest.mark.parametrize("case", DEVELOPMENT["cases"], ids=lambda case: case["id"])
def test_development_adjudication_state_is_explicit_and_not_final_gold(case):
    assert "adjudication_review" in case
    review = case["adjudication_review"]
    assert review["state"] in {
        "READY_FOR_GOLD",
        "NEEDS_POLICY_DECISION",
        "NEEDS_SOURCE_VERIFICATION",
        "NEEDS_WORDING/EXPECTATION_REFINEMENT",
    }
    assert review["unresolved"] is (review["state"] != "READY_FOR_GOLD")
    assert isinstance(review["questions"], list)
    assert all(isinstance(question, str) and question for question in review["questions"])
    assert bool(review["questions"]) == review["unresolved"]
    assert review["confidence"] in {"high", "medium", "low"}
    assert review["confidence_scope"] == "provisional_semantics_not_model_accuracy_or_independent_agreement"
    assert review["recommended_decision"]
    assert review["evidence"]
    assert review["reviewer"] is None
    assert review["adjudicator"] is None
    assert review["human_decision"] is None
    assert case["gold_annotation"]["status"] == "provisional_pending_independent_adjudication"
    assert case["gold_annotation"]["independent_gold"] is False
    assert case["gold_annotation"]["adjudicated_at"] is None
    assert case["freeze"]["freeze_status"] == "not_frozen"
    original_case = {key: value for key, value in case.items() if key != "adjudication_review"}
    encoded = json.dumps(original_case, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    assert hashlib.sha256(encoded).hexdigest() == review["reviewed_case_sha256"]
    # JSON is canonical. Markdown is a human-facing worksheet, not a second data schema.
    assert (ROOT / review["review_document"]).is_file()


def test_known_unresolved_review_cases_are_not_marked_ready():
    cases = {case["id"]: case for case in DEVELOPMENT["cases"]}
    policy = {"R01", "R06", "R10", "R16", "R23"}
    refinement = {"R03", "R15", "R19", "R29"}
    unresolved = {case_id for case_id, case in cases.items() if case["adjudication_review"]["unresolved"]}
    assert unresolved == policy | refinement
    for case_id in policy:
        assert cases[case_id]["adjudication_review"]["state"] == "NEEDS_POLICY_DECISION"
    for case_id in refinement:
        assert cases[case_id]["adjudication_review"]["state"] == "NEEDS_WORDING/EXPECTATION_REFINEMENT"
    for case in TEMPLATES["cases"]:
        assert "adjudication_review" not in case


def test_normalized_text_hash_is_identical_for_lf_crlf_and_lone_cr():
    lf = "first line\nsecond line: \u00e9\n".encode("utf-8")
    expected = hashlib.sha256(lf).hexdigest()
    for data in (lf, lf.replace(b"\n", b"\r\n"), lf.replace(b"\n", b"\r")):
        assert hash_bytes(data, mode="normalized_text_sha256") == expected


def test_raw_bytes_hash_preserves_line_endings_and_binary_data(tmp_path):
    lf, crlf = b"first\nsecond\n", b"first\r\nsecond\r\n"
    assert hash_bytes(lf, mode="raw_bytes_sha256") != hash_bytes(crlf, mode="raw_bytes_sha256")
    binary = b"\x00\xff\r\n\r\x80"
    source = tmp_path / "binary.dat"
    source.write_bytes(binary)
    assert source_sha256(source, mode="raw_bytes_sha256") == hashlib.sha256(binary).hexdigest()
    with pytest.raises(UnicodeDecodeError):
        hash_bytes(binary, mode="normalized_text_sha256")


def test_unknown_hash_mode_is_rejected():
    with pytest.raises(ValueError, match="Unknown source hash mode"):
        hash_bytes(b"text", mode="guess_from_extension")


@pytest.mark.parametrize(
    "path", [path for path, mode in SOURCE_HASH_MODES.items() if mode == "normalized_text_sha256"]
)
def test_real_text_source_metadata_survives_checkout_line_endings(path, tmp_path):
    data = (ROOT / path).read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    source = tmp_path / "checkout.txt"
    for artifact in (DEVELOPMENT, TEMPLATES):
        expected = artifact["context"]["source_sha256"][path]
        for checkout in (data, data.replace(b"\n", b"\r\n"), data.replace(b"\n", b"\r")):
            source.write_bytes(checkout)
            assert source_sha256(source, mode="normalized_text_sha256") == expected
