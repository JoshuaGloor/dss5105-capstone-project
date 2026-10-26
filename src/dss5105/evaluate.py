"""Run course baselines and our policies without making any provider calls."""

import argparse
import hashlib
import io
import json
from contextlib import redirect_stdout
from dataclasses import asdict
from pathlib import Path

from dss5105.allocator import OBJECTIVES, ObjectiveWeights, ScoreScales, earliest_finish, make_allocator
from dss5105.harness import HARNESS_PATH, Simulator, cheapest, greedy_biggest, print_table, random_choice

# One configuration per objective, frozen on development seeds by objective_study.py before the
# course seeds were run. See docs/OBJECTIVE_STUDY.md; a test keeps these equal to the evidence.
# "hybrid" is the team's priority: lateness first, then defects.
_LATE = {"capacity_reservation": 1.0, "deadline_miss_days": 7.0}
PRESETS = {
    "hybrid": ObjectiveWeights(lateness=1.0, defects=0.2, deadline_buffer_days=2.0, **_LATE),
    "lateness": ObjectiveWeights(lateness=1.0, **_LATE),
    "defects": ObjectiveWeights(lateness=0.2, defects=1.0, deadline_buffer_days=5.0, **_LATE),
    "fairness": ObjectiveWeights(lateness=1.0, fairness=1.0, **_LATE),
    "robustness": ObjectiveWeights(lateness=1.0, robustness=0.5, **_LATE),
}
DEFAULT_PRESET = "hybrid"
# The exploratory Sprint 1 configurations, kept so the earlier studies reproduce their evidence.
SPRINT1_PRESETS = {
    "lateness": ObjectiveWeights(lateness=1.0),
    "defects": ObjectiveWeights(lateness=0.0, defects=1.0),
    "hybrid": ObjectiveWeights(lateness=0.7, defects=0.3),
}


def run_experiment(
    shock: bool = False,
    seed: int = 5105,
    configurations: dict[str, ObjectiveWeights] | None = None,
) -> dict:
    """Compare configured objectives with the same course baselines and heuristic."""
    configurations = dict(PRESETS if configurations is None else configurations)
    reference_names = {"random", "greedy_biggest", "cheapest", "earliest_finish"}
    if not configurations or reference_names.intersection(configurations):
        raise ValueError("Provide at least one objective configuration without reusing a reference policy name")
    sim = Simulator(shock=shock, seed=seed)
    scales = ScoreScales()
    policies = {"random": random_choice, "greedy_biggest": greedy_biggest, "cheapest": cheapest}
    policies["earliest_finish"] = earliest_finish
    policies.update({name: make_allocator(weights, scales) for name, weights in configurations.items()})
    traces = {}

    for name, policy in policies.items():
        decisions = []

        def record_decision(batch, workshops, queues):
            choice = policy(batch, workshops, queues)
            decision = {
                "order_id": batch["order_id"],
                "sent_date": batch["sent_date"].isoformat(),
                "due_date": batch["due_date"].isoformat(),
                "queues": dict(queues),
                "choice": choice,
            }
            if name in configurations:
                # The policy's own ranking, so fairness sees the same ledger that made the choice.
                decision["candidates"] = [asdict(row) for row in policy.last_ranking]
            decisions.append(decision)
            return choice

        outcomes = sim.run(record_decision, name)
        for decision, outcome in zip(decisions, outcomes, strict=True):
            decision["outcome"] = outcome
        traces[name] = decisions

    # Keep the course's exact metric definitions and rounding in the printed table.
    report = io.StringIO()
    with redirect_stdout(report):
        sim.report()
    data_dir = HARNESS_PATH.parent.parent / "data"
    sources = [HARNESS_PATH, data_dir / "orders.csv", data_dir / "workshops.csv"]
    sources.extend([Path(__file__), Path(__file__).with_name("allocator.py")])
    return {
        "shock": shock,
        "seed": seed,
        "source_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
        "weights": {name: asdict(weights) for name, weights in configurations.items()},
        "scales": asdict(scales),
        "report": report.getvalue(),
        "metrics": {name: sim.metrics(outcomes) for name, outcomes in sim.results.items()},
        "policies": traces,
    }


def run_seed_series(shock=False, seed=5105, seeds=10, configurations=None):
    """Average official per-run metrics; retain paired controls and every trace."""
    if type(seeds) is not int or seeds < 1:
        raise ValueError("seeds must be a positive integer")
    runs = [run_experiment(shock, current, configurations) for current in range(seed, seed + seeds)]

    def average(records):
        return {
            name: {key: sum(run["metrics"][name][key] for run in records) / len(records) for key in metrics}
            for name, metrics in records[0]["metrics"].items()
        }

    metrics = average(runs)
    report = io.StringIO()
    with redirect_stdout(report):
        print_table(metrics)
    result = {
        "shock": shock,
        "seeds": [run["seed"] for run in runs],
        "weights": runs[0]["weights"],
        "scales": runs[0]["scales"],
        "source_sha256": runs[0]["source_sha256"],
        "metrics": metrics,
        "report": report.getvalue(),
        "runs": runs,
    }
    if shock:
        normal = [run_experiment(False, current, configurations) for current in range(seed, seed + seeds)]
        result["normal_runs"] = normal
        result["normal_metrics"] = average(normal)
        result["paired_deltas"] = {
            name: {
                key: sum(s["metrics"][name][key] - n["metrics"][name][key] for s, n in zip(runs, normal, strict=True))
                / seeds
                for key in ("% late", "late days")
            }
            for name in metrics
        }
        result["normal_lateness_guardrail"] = {
            name: row["% late"] <= result["normal_metrics"]["random"]["% late"]
            for name, row in result["normal_metrics"].items()
        }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=PRESETS, help="Choose one preset; otherwise compare all presets")
    for objective in OBJECTIVES:
        parser.add_argument(
            f"--{objective}-weight",
            type=float,
            help="Custom nonnegative weight; unspecified custom weights are zero; cannot combine with --preset",
        )
    parser.add_argument(
        "--deadline-buffer-days",
        type=float,
        help="Safety buffer for a custom configuration; needs at least one custom weight",
    )
    parser.add_argument(
        "--deadline-miss-days",
        type=float,
        help="Lateness charge for missing the date in a custom configuration; needs a custom weight",
    )
    parser.add_argument(
        "--capacity-reservation",
        type=float,
        help="Lateness charge for scarce shared capacity in a custom configuration; needs a custom weight",
    )
    parser.add_argument("--shock", action="store_true", help="Use the course's hidden workshop closure")
    parser.add_argument("--seed", type=int, default=5105)
    parser.add_argument("--seeds", type=int, help="Average N consecutive seeds; use 10 for reported shock results")
    parser.add_argument("--output", type=Path, help="Save configuration, report, and per-order traces as JSON")
    args = parser.parse_args(argv)
    if args.seeds is not None and args.seeds < 1:
        parser.error("--seeds must be positive")
    requested_weights = {objective: getattr(args, f"{objective}_weight") for objective in OBJECTIVES}
    custom = any(value is not None for value in requested_weights.values())
    if args.preset and custom:
        parser.error("--preset cannot be combined with custom weight arguments")
    if args.deadline_buffer_days is not None and not custom:
        parser.error("--deadline-buffer-days needs at least one custom weight argument")
    if args.capacity_reservation is not None and not custom:
        parser.error("--capacity-reservation needs at least one custom weight argument")
    if args.deadline_miss_days is not None and not custom:
        parser.error("--deadline-miss-days needs at least one custom weight argument")
    configurations = None
    if args.preset:
        configurations = {args.preset: PRESETS[args.preset]}
    elif custom:
        try:
            weights = ObjectiveWeights(
                **{key: 0.0 if value is None else value for key, value in requested_weights.items()},
                deadline_buffer_days=args.deadline_buffer_days or 0.0,
                capacity_reservation=args.capacity_reservation or 0.0,
                deadline_miss_days=args.deadline_miss_days or 0.0,
            )
        except ValueError as exc:
            parser.error(str(exc))
        configurations = {"custom": weights}
    if args.seeds is not None:
        result = run_seed_series(args.shock, args.seed, args.seeds, configurations)
    else:
        result = run_experiment(shock=args.shock, seed=args.seed, configurations=configurations)
    print(f"Scenario: {'shock' if args.shock else 'normal'}; seed: {args.seed}")
    if args.seeds:
        print(f"Averaged over seeds: {result['seeds']}")
    if args.shock and args.seeds != 10:
        print("Diagnostic run only: course shock reporting requires --seeds 10.")
    print(f"Objective weights: {json.dumps(result['weights'], sort_keys=True)}")
    print(f"Score scales: {json.dumps(result['scales'], sort_keys=True)}")
    print(result["report"], end="")
    if "paired_deltas" in result:
        print("Paired shock-minus-normal changes (% late in percentage points; late days in days):")
        print(json.dumps(result["paired_deltas"], indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"Saved experiment: {args.output}")


if __name__ == "__main__":
    main()
