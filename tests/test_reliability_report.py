"""Report projections and disclosed fault injection; all tests are offline."""

import copy
import json
import tempfile
from pathlib import Path

import pytest

from dss5105 import llm
from dss5105.evaluator_demo import SCENARIOS, build_demo, build_inputs, scenario_bundle
from dss5105.reliability_report import render_html_report
from dss5105.reliability_score import ROOT, main, score_run, serialize_outputs


@pytest.fixture
def saved():
    benchmark, bundle = build_inputs()
    report = score_run(benchmark, bundle["records"], bundle["manifest"], source_type="synthetic")
    return benchmark, bundle, report


@pytest.fixture
def repository_tmp_path():
    cache = ROOT / ".cache/report-tests"
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache) as directory:
        yield Path(directory)


def test_html_preserves_scoring_determinism_and_evidence_values(saved):
    _, _, report = saved
    before = copy.deepcopy(report)
    outputs = serialize_outputs(report, {})
    rendered = render_html_report(report, {})
    assert rendered == render_html_report(report, {})
    assert report == before and serialize_outputs(report, {}) == outputs
    assert "synthetic" in rendered and "not independent human gold" in rendered
    assert "UNRESOLVED_POLICY" in rendered and "Coverage" in rendered
    assert "provisional" in rendered and "integrity_audit" in rendered
    assert "<script src=" not in rendered and 'href="https://' not in rendered


def test_artifact_strings_are_escaped_in_text_attributes_and_provenance(saved):
    _, _, report = saved
    payload = '"><script>alert("artifact")</script><img src=x onerror=alert(1)>'
    report["cases"][0]["case_id"] = payload
    check = report["cases"][0]["checks"][0]
    check.update(expected=payload, observed=payload, reason_code=payload, evidence_paths=[payload])
    rendered = render_html_report(report, {"run_provenance": {"model": payload}})
    assert payload not in rendered
    assert "&lt;script&gt;" in rendered and "&lt;img" in rendered
    assert rendered.count("<script>") == 1


def test_missing_evidence_and_observed_null_are_not_conflated(saved):
    _, _, report = saved
    checks = report["cases"][0]["checks"]
    checks[0].update(observed=None, observed_missing=True)
    checks[1].update(observed=None, observed_missing=False)
    rendered = render_html_report(report, {})
    assert "Missing evidence (not JSON null)" in rendered and "<pre>null</pre>" in rendered


@pytest.mark.parametrize("name,description,expected", SCENARIOS)
def test_injected_faults_have_distinct_outcomes_without_mutating_labels(saved, name, description, expected):
    benchmark, bundle, _ = saved
    original = copy.deepcopy((benchmark, bundle))
    variant = scenario_bundle(bundle, name)
    report = score_run(benchmark, variant["records"], variant["manifest"], source_type="synthetic")
    case = next(case for case in report["cases"] if case["case_id"] == "R04")
    audit = next(check for check in case["checks"] if check["metric"] == "tool_integrity")
    assert audit["outcome"] == expected
    assert (benchmark, bundle) == original
    if name == "04-failure-and-gap":
        assert any(check["outcome"] == "NOT_SCORABLE" for check in case["checks"])
    if name == "05-incompatible":
        assert "configured_weights_mismatch" in case["compatibility"]["issues"]
    if name == "06-unattempted":
        assert report["summary"]["attempted"] == 3 and "R04" in report["summary"]["unattempted_ids"]


def test_cli_html_is_opt_in_and_preserves_the_canonical_five_files(repository_tmp_path, saved):
    tmp_path = repository_tmp_path
    benchmark, bundle, _ = saved
    source, labels = tmp_path / "input.json", tmp_path / "benchmark.json"
    source.write_text(json.dumps(bundle), encoding="utf-8")
    labels.write_text(json.dumps(benchmark), encoding="utf-8")
    common = [
        "--input",
        str(source),
        "--benchmark",
        str(labels),
        "--source-root",
        str(ROOT),
        "--source-type",
        "synthetic",
    ]
    plain, enhanced = tmp_path / "plain", tmp_path / "enhanced"
    assert main([*common, "--output", str(plain)]) == 0
    assert main([*common, "--output", str(enhanced), "--html-report"]) == 0
    assert len(list(plain.iterdir())) == 5 and len(list(enhanced.iterdir())) == 6
    for name in ("cases.jsonl", "summary.json", "summary.md", "checks.csv"):
        assert (plain / name).read_bytes() == (enhanced / name).read_bytes()
    manifest = json.loads((enhanced / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["report_renderer_content_hash"]) == 64
    with pytest.raises(SystemExit):
        main([*common, "--output", str(enhanced), "--html-report"])


def test_full_demo_never_calls_a_model_or_overwrites_output(repository_tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "get_model", lambda **kwargs: pytest.fail("demo must not call a model"))
    output = build_demo(repository_tmp_path / "demo")
    assert (output / "index.html").is_file()
    manifest = json.loads((output / "demo_manifest.json").read_text(encoding="utf-8"))
    assert manifest["no_model_calls"] and manifest["source_type"] == "synthetic"
    for name, _, _ in SCENARIOS:
        assert (output / name / "report.html").is_file()
    with pytest.raises(ValueError, match="NEW directory"):
        build_demo(output)
