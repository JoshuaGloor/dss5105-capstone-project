import copy
import json
import re
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

from dss5105 import evaluate_chat
from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import DispatchDesk, DispatchInput, read_inbox
from dss5105.evaluate_chat import RecordedModel, check_rubric, check_tool_integrity, evaluate_case, summarize


class Provider:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def with_structured_output(self, schema, *, include_raw):
        assert include_raw
        return self

    def invoke(self, messages):
        self.calls += 1
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_live_opt_in_is_required_before_model_construction(monkeypatch):
    monkeypatch.setattr("sys.argv", ["evaluate_chat", "--output", "results/test-unused"])
    monkeypatch.setattr(evaluate_chat.llm, "get_model", lambda **kwargs: pytest.fail("Unexpected provider"))
    with pytest.raises(SystemExit, match="2"):
        evaluate_chat.main()


def test_output_stays_in_repo_and_existing_runs_are_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluate_chat, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="inside"):
        evaluate_chat.output_path(tmp_path.parent / "outside-chat-run")
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(ValueError, match="exists"):
        evaluate_chat.output_path(existing)
    assert evaluate_chat.output_path(tmp_path / "new") == (tmp_path / "new").resolve()


def test_provider_failure_is_safe_and_counted_as_uncompleted():
    model = RecordedModel(Provider(RuntimeError("secret-token-never-log")), "fake")
    envelope = read_inbox()[0]
    record = evaluate_case(envelope, {"category": "clarification"}, DispatchDesk(), model)
    assert record["status"] == "provider_error"
    assert "secret-token" not in json.dumps(record)
    summary = summarize([record], 30)
    assert summary["draft_rubric_passed"] == 0
    assert summary["unattempted"] == 29
    assert model.model.calls == 1


def test_rejected_patch_is_saved_without_returning_a_preview():
    patch = {"updates": [{"field": "pieces", "value": "999", "evidence": "invented"}], "exclusions": [], "needs": []}
    model = RecordedModel(Provider({"parsed": patch, "raw": None, "parsing_error": None}), "fake")
    record = evaluate_case(read_inbox()[0], {"category": "clarification"}, DispatchDesk(), model)
    assert record["status"] == "validation_error"
    assert record["model_output"]["patch"] == patch
    assert "preview" not in record


def test_recorded_model_preserves_actual_model_label_and_usage():
    envelope = read_inbox()[17]
    patch = {
        "updates": [
            {"field": "order_id", "value": "ORD-999", "evidence": "ORD-999"},
            {"field": "intent", "value": "status", "evidence": "Any movement"},
        ],
        "exclusions": [],
        "needs": [],
    }
    raw = SimpleNamespace(content=[], tool_calls=[], usage_metadata={"input_tokens": 10, "output_tokens": 3})
    model = RecordedModel(Provider({"parsed": patch, "raw": raw, "parsing_error": None}), "configured-eval-model")
    rule = json.loads(evaluate_chat.RUBRIC.read_text())["cases"]["R18"]
    record = evaluate_case(envelope, rule, DispatchDesk(), model)
    assert record["status"] == "completed"
    assert record["preview"]["conversation"]["traces"][0]["model"] == "configured-eval-model"
    assert summarize([record], 1)["usage"] == {"input_tokens": 10, "output_tokens": 3}


def test_omitted_exclusion_fails_even_when_response_state_matches():
    rule = json.loads(evaluate_chat.RUBRIC.read_text())["cases"]["R25"]
    result = {
        "input": {**rule["fields"], "exclusions": []},
        "status": "RECOMMEND",
        "flags": [],
        "conversation": {"needs": []},
    }
    checks = check_rubric(result, rule)
    assert checks["extraction_errors"]
    assert not checks["behavior_errors"]


def test_candidate_bound_audit_detects_wrong_workshop_values_and_ineligible_choice():
    desk = DispatchDesk()
    result = desk.preview(read_inbox()[24], DispatchInput(order_id="ORD-109"), ObjectiveWeights())
    assert not check_tool_integrity(result, desk)["errors"]
    changed = copy.deepcopy(result)
    changed["candidates"][0]["display"]["cost"] = changed["candidates"][1]["display"]["cost"]
    changed["recommendation"] = "W7"
    errors = check_tool_integrity(changed, desk)["errors"]
    assert any("display.cost" in error for error in errors)
    assert any("not a permitted" in error for error in errors)


def test_rubric_labelling_matches_the_published_request_mix():
    rubric = json.loads(evaluate_chat.RUBRIC.read_text())
    labelled = Counter(case["course_kind"] for case in rubric["cases"].values())
    assert labelled == rubric["course_kind_counts"]
    dictionary = (evaluate_chat.ROOT / "track2" / "data" / "data_dictionary.md").read_text()
    mix = dictionary[dictionary.index("| Kind | How many |") :]
    published = [int(count) for count in re.findall(r"^\| [^|]+ \| (\d+) \| ", mix, re.MULTILINE)]
    assert published == list(rubric["course_kind_counts"].values())


def test_split_audit_recomputes_parts_and_summary():
    desk = DispatchDesk()
    request = DispatchInput(order_id="ORD-005", split_requested=True)
    result = desk.preview(read_inbox()[22], request, ObjectiveWeights())
    assert not check_tool_integrity(result, desk)["errors"]
    changed = copy.deepcopy(result)
    changed["split_option"]["parts"][0]["pieces"] += 1
    changed["split_option"]["summary"] = changed["split_option"]["summary"].replace(
        changed["split_option"]["display"]["eta"], "2026-04-02 00:00"
    )
    errors = check_tool_integrity(changed, desk)["errors"]
    assert any("cover the batch" in error for error in errors)
    assert any("does not recompute" in error for error in errors)
    assert any("omits tool field eta" in error for error in errors)


def test_rubric_covers_raw_inbox_without_importing_demo_fixtures():
    rubric = json.loads(evaluate_chat.RUBRIC.read_text())["cases"]
    assert set(rubric) == {item["request_id"] for item in read_inbox()}
    assert "dispatch_inputs.json" not in Path(evaluate_chat.__file__).read_text()
