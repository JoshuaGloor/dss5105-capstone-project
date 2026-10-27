"""Refresh offline Data v3 evidence; never invoke a provider or tune weights."""

import hashlib
import json
from collections import Counter

from dss5105.dispatch import DATA, ROOT, DispatchDesk
from dss5105.evaluate import SPRINT1_PRESETS, run_experiment, run_seed_series
from dss5105.evaluate_chat import check_tool_integrity
from dss5105.harness import HARNESS_PATH
from dss5105.prototype import build_bundle


def main():
    # Sprint 1 configurations, so this record stays comparable; see objective_study.py for Sprint 2.
    normal = run_experiment(configurations=SPRINT1_PRESETS)
    shock = run_seed_series(shock=True, seeds=10, configurations=SPRINT1_PRESETS)
    bundle = build_bundle()
    desk = DispatchDesk()
    rubric = json.loads((ROOT / "examples" / "chat_rubric.json").read_text())
    cases = {}
    for request_id, variants in bundle["previews"].items():
        result = variants["lateness"]
        errors = {name: check_tool_integrity(preview, desk)["errors"] for name, preview in variants.items()}
        if any(errors.values()):
            raise ValueError(f"Tool integrity failed: {request_id}: {errors}")
        cases[request_id] = {
            "course_kind": rubric["cases"][request_id]["course_kind"],
            "input": result["input"],
            "status": result["status"],
            "flags": result["flags"],
            "earliest_option": result["earliest_option"],
            "split_option": result["split_option"],
            "tool_integrity_errors": errors,
        }
    evidence = {
        "course_release": "Data v3; Spec v5; Tracks v4",
        "source_sha256": normal["source_sha256"],
        "course_files_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [HARNESS_PATH, *sorted(DATA.iterdir()), ROOT / "track2" / "CHANGELOG.md"]
            if path.is_file()
        },
        "tool_sha256": {
            name: hashlib.sha256((ROOT / "src" / "dss5105" / name).read_bytes()).hexdigest()
            for name in ("dispatch.py", "prototype.py", "evaluate_chat.py")
        },
        "fixture_sha256": bundle["fixture_sha256"],
        "rubric_sha256": hashlib.sha256((ROOT / "examples" / "chat_rubric.json").read_bytes()).hexdigest(),
        "weights": normal["weights"],
        "scales": normal["scales"],
        "normal_seed": normal["seed"],
        "normal_metrics": normal["metrics"],
        "seeds": shock["seeds"],
        "shock_metrics": shock["metrics"],
        "paired_normal_metrics": shock["normal_metrics"],
        "paired_deltas": shock["paired_deltas"],
        "normal_lateness_guardrail": shock["normal_lateness_guardrail"],
        "per_seed": [
            {"seed": s["seed"], "normal": n["metrics"], "shock": s["metrics"]}
            for s, n in zip(shock["runs"], shock["normal_runs"], strict=True)
        ],
        "fixture_cases": cases,
        "live_language_evaluation": "Pending; fixture replay is not extraction accuracy or held-out evidence.",
    }
    outputs = {
        ROOT / "results" / "allocation-v3-normal.json": normal,
        ROOT / "results" / "allocation-v3-shock.json": shock,
        ROOT / "docs" / "evidence" / "data-v3.json": evidence,
    }
    for path, value in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n")

    def table(metrics):
        keys = ("% late", "late days", "% def pcs", "mean days", "cost", "max share")
        lines = ["| Policy | " + " | ".join(keys) + " |", "|---|" + "---|" * len(keys)]
        for name, row in metrics.items():
            lines.append("| " + name + " | " + " | ".join(f"{row[key]:.3f}" for key in keys) + " |")
        return "\n".join(lines)

    lines = [
        "# Data v3 offline evaluation",
        "",
        "> Sprint 2 note: the scorer now weights the defect term by batch pieces. The Sprint 1",
        "> lateness and defects rows below reproduce unchanged; the 0.7/0.3 hybrid rows were",
        "> produced before that change and reproduce exactly from commit e8c40a5. Current",
        "> presets and results: [OBJECTIVE_STUDY.md](OBJECTIVE_STUDY.md).",
        "",
        "Generated with `uv run python scripts/refresh_v3_evidence.py`. No provider calls.",
        "Source hashes, configurations and per-seed metrics: [retained evidence](evidence/data-v3.json).",
        "Full per-order traces are regenerated in `results/allocation-v3-*.json` (Git-ignored).",
        "Metrics are official per-run metrics; seed summaries average those metrics, including P90.",
        "Displayed percentages use percentage units; calculations retain unrounded values.",
        "This is development evidence on the supplied replay, not held-out performance.",
        "",
        f"## Normal run, seed {normal['seed']}",
        "",
        table(normal["metrics"]),
        "",
        f"## Shock mean over {len(shock['seeds'])} seeds ({shock['seeds'][0]}-{shock['seeds'][-1]})",
        "",
        table(shock["metrics"]),
        "",
        "## Paired normal controls",
        "",
        table(shock["normal_metrics"]),
        "",
        "## Mean shock-minus-normal changes",
        "",
        "| Policy | Late rate change (percentage points) | Late days change | Normal late rate <= random |",
        "|---|---|---|---|",
    ]
    for name, row in shock["paired_deltas"].items():
        guard = "pass" if shock["normal_lateness_guardrail"][name] else "fail"
        lines.append(f"| {name} | {row['% late']:.4f} | {row['late days']:.4f} | {guard} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Lateness beats the shipped baselines on both lateness metrics in these runs.",
            "Earliest finish remains close; the language layer's added value needs separate evidence.",
            "Pure defects fails the random-lateness guardrail. It is a diagnostic comparison,",
            "not a qualifying defects winner. Cheapest wins cost; random has lower load concentration.",
            "A small shock late-rate change alone is insufficient: cheapest has a smaller change",
            "but fails the normal-lateness guardrail. No universal robustness win is claimed.",
            "No weights were tuned and the team has not ratified a primary objective.",
            "",
            "## Structured fixture replay",
            "",
            f"Replayed all {len(cases)} inbox cases across the bundled presets and checked tool fields,",
            "including recomputed split estimates.",
            "These are hand-authored inputs, not model extraction, human gold labels or live chat results.",
            "Course kinds are our labelling; only their counts come from the data dictionary.",
            "",
            "| Course kind | Dictionary count | Labelled | Lateness-preset states |",
            "|---|---|---|---|",
        ]
    )
    for kind, count in rubric["course_kind_counts"].items():
        members = [row for row in cases.values() if row["course_kind"] == kind]
        states = Counter(row["status"] for row in members)
        summary = ", ".join(f"{state} {n}" for state, n in sorted(states.items()))
        lines.append(f"| {kind} | {count} | {len(members)} | {summary} |")
    lines.extend(
        [
            "",
            "R23 asks for a split only if it is faster. The tool estimates the split, but split plans",
            "cannot be saved, so the request stays in review. Every other kind reaches its intended state.",
            "",
            "| Request | Course kind | Lateness-preset state | Flags |",
            "|---|---|---|---|",
        ]
    )
    for request_id, row in cases.items():
        flags = ", ".join(row["flags"]) or "-"
        lines.append(f"| {request_id} | {row['course_kind']} | {row['status']} | {flags} |")
    (ROOT / "docs" / "V3_EVALUATION.md").write_text("\n".join(lines) + "\n")
    print(f"Refreshed offline evidence for {len(cases)} inbox fixtures and {len(shock['seeds'])} paired seeds.")


if __name__ == "__main__":
    main()
