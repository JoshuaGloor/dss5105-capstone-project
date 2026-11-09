"""Generate disclosed offline evaluator examples and score them; never call a model."""

import argparse
import copy
import hashlib
import html
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from dss5105.allocator import ObjectiveWeights
from dss5105.dispatch import ROOT, DispatchDesk, DispatchInput, read_inbox
from dss5105.reliability_report import HEADER
from dss5105.reliability_score import json_text, read_json
from dss5105.reliability_score import main as score_main

CASE_IDS = ("R01", "R04", "R14", "R25")
SCENARIOS = (
    ("01-clean", "Unchanged fixture", "PASS"),
    ("02-wrong-cost", "R04 displayed cost changed to 999,999.00", "FAIL"),
    ("03-missing-cost", "R04 displayed cost removed", "NOT_SCORABLE"),
    ("04-failure-and-gap", "Wrong cost plus a missing deadline flag", "FAIL"),
    ("05-incompatible", "Manifest lateness weight changed without changing the preview", "NOT_SCORABLE"),
    ("06-unattempted", "R04 record omitted; planned case remains in the benchmark", "NOT_SCORABLE"),
)


def build_inputs():
    """Build synthetic records from disclosed development fixtures, not model extraction."""
    benchmark = read_json(ROOT / "examples/reliability_benchmark.json")
    benchmark["cases"] = [case for case in benchmark["cases"] if case["id"] in CASE_IDS]
    fixtures_path = ROOT / "examples/dispatch_inputs.json"
    fixtures = read_json(fixtures_path)
    desk = DispatchDesk()
    manifest = {
        "snapshot_date": desk.as_of.isoformat(),
        "source_hashes": desk.source_hashes,
        "weights": asdict(ObjectiveWeights()),
        "model": "none; offline demonstration fixtures",
        "intake_version": "not run; handcrafted fields bypass language extraction",
        "file_hashes": {"dispatch_inputs.json": hashlib.sha256(fixtures_path.read_bytes()).hexdigest()},
    }
    records = []
    for envelope in read_inbox():
        case_id = envelope["request_id"]
        if case_id not in CASE_IDS:
            continue
        preview = desk.preview(envelope, DispatchInput(**fixtures[case_id]), ObjectiveWeights())
        preview["conversation"] = {
            "needs": ["order", "quantity"] if case_id == "R01" else [],
            "deferred_needs": [],
            "provenance": [],
            "traces": [],
        }
        records.append({"request": envelope, "status": "completed", "preview": preview})
    return benchmark, {"manifest": manifest, "records": records}


def scenario_bundle(bundle, name):
    """Mutate copied evidence only; preserve the benchmark's labels and original records."""
    value = copy.deepcopy(bundle)
    preview = next(record["preview"] for record in value["records"] if record["request"]["request_id"] == "R04")
    if name in ("02-wrong-cost", "04-failure-and-gap"):
        preview["candidates"][0]["display"]["cost"] = "999,999.00"
    if name == "03-missing-cost":
        del preview["candidates"][0]["display"]["cost"]
    if name == "04-failure-and-gap":
        del preview["candidates"][0]["meets_deadline"]
    if name == "05-incompatible":
        value["manifest"]["weights"]["lateness"] = 2
    if name == "06-unattempted":
        value["records"] = [record for record in value["records"] if record["request"]["request_id"] != "R04"]
    return value


def build_demo(output):
    output = Path(output).resolve()
    if output.exists() or output == ROOT.resolve() or not output.is_relative_to(ROOT.resolve()):
        raise ValueError("Demo output must be a NEW directory inside the repository")
    benchmark, bundle = build_inputs()
    output.mkdir(parents=True, exist_ok=False)
    inputs = output / "inputs"
    inputs.mkdir()
    benchmark_path = output / "benchmark.json"
    benchmark_path.write_text(json_text(benchmark), encoding="utf-8", newline="\n")
    rows, results = [], []
    for name, description, expected in SCENARIOS:
        value = scenario_bundle(bundle, name)
        input_path = inputs / f"{name}.json"
        input_path.write_text(json_text(value), encoding="utf-8", newline="\n")
        run_dir = output / name
        score_main(
            [
                "--input",
                str(input_path),
                "--output",
                str(run_dir),
                "--benchmark",
                str(benchmark_path),
                "--source-type",
                "synthetic",
                "--html-report",
            ]
        )
        cases = [json.loads(line) for line in (run_dir / "cases.jsonl").read_text(encoding="utf-8").splitlines()]
        scored = next(case for case in cases if case["case_id"] == "R04")
        outcome = next(check["outcome"] for check in scored["checks"] if check["metric"] == "tool_integrity")
        if outcome != expected:
            raise ValueError(f"Demo expectation changed for {name}: expected {expected}, observed {outcome}")
        summary = read_json(run_dir / "summary.json")
        audit_metric = next(
            metric
            for metric in summary["metrics"]
            if metric["metric"] == "tool_integrity" and metric["annotation_basis"] == "integrity_audit"
        )
        coverage = audit_metric["coverage"]
        results.append(
            {"scenario": name, "description": description, "r04_tool_integrity": outcome, "expected": expected}
        )
        rows.append(
            f'<tr><td><a href="{name}/report.html">{html.escape(name)}</a></td>'
            f'<td>{html.escape(description)}</td><td><span class="badge {outcome}">{outcome}</span></td>'
            f"<td>{summary['attempted']} / {summary['planned']}</td>"
            f"<td>{audit_metric['numerator']} / {audit_metric['denominator']}</td>"
            f"<td>{coverage['evaluable_assertions']} / {coverage['eligible_assertions']}</td>"
            f'<td><a href="inputs/{name}.json">Input JSON</a></td></tr>'
        )
        print(f"{name}: R04 tool_integrity = {outcome}")
    (output / "demo_manifest.json").write_text(
        json_text(
            {
                "source_type": "synthetic",
                "case_ids": list(CASE_IDS),
                "no_model_calls": True,
                "description": "Disclosed fixture and evidence mutations; not model or held-out performance.",
                "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "scenarios": results,
            }
        ),
        encoding="utf-8",
        newline="\n",
    )
    index = (
        HEADER
        + '<main><p class="eyebrow">STITCHFLOW / LOCAL DEMONSTRATION</p>'
        + "<h1>One evaluator. Six evidence conditions.</h1>"
        + '<p class="notice"><strong>Synthetic demonstration, no model calls.</strong> '
        + "R01, R04, R14 and R25 come from disclosed development fixtures. The same provisional "
        + "benchmark labels are kept for every scenario. Injected faults are not observed model failures.</p>"
        + "<p>The generator creates read-only Python previews first. The evaluator then reads saved "
        + "JSON only; it does not rerun the dispatcher or use a model. Reports are local files.</p>"
        + "<h2>Open a scenario</h2><table><thead><tr><th>Report</th><th>Evidence change</th>"
        + "<th>Observed R04 tool integrity</th><th>Attempted / planned</th>"
        + "<th>Tool pass count</th><th>Tool coverage count</th><th>Evidence</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table><p>Tool pass and coverage counts above are for the tool_integrity metric only, "
        + "across all four planned cases. Compare their denominators: missing evidence can leave a "
        + "perfect observed pass rate with reduced coverage. They are not model accuracy.</p>"
        + "<h2>Recording walkthrough</h2><ol>"
        + "<li>Start with the unchanged fixture: inspect compatibility and PASS assertions for R04.</li>"
        + "<li>Open wrong cost: filter R04 and FAIL, then expand tool_integrity and the cost assertion.</li>"
        + "<li>Open missing cost: NOT_SCORABLE means evidence is missing, not that a value is wrong.</li>"
        + "<li>Open failure and gap: the known wrong cost stays FAIL despite the missing deadline flag.</li>"
        + "<li>Open incompatible: inspect configured_weights_mismatch before interpreting scores.</li>"
        + "<li>Open unattempted: all four cases remain planned but only three were attempted.</li></ol>"
        + "<p>In every report, select R01 and UNRESOLVED_POLICY to see policy-sensitive labels withheld "
        + "from semantic grading. No aggregate model accuracy is claimed.</p>"
        + "<p>Limit: the new HTML improves review and evidence navigation; the existing scoring "
        + "rules detect these faults. It does not improve the language model or add a full "
        + "free-text explanation judge.</p></main></body></html>\n"
    )
    (output / "index.html").write_text(index, encoding="utf-8", newline="\n")
    print(f"\nOpen in Chrome: {output / 'index.html'}")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Fresh repository-local directory; never overwritten")
    args = parser.parse_args(argv)
    output = args.output or ROOT / "results/evaluator-demo" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    try:
        build_demo(output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
