"""Run course baselines and our policies without making any provider calls."""

import argparse
import hashlib
import io
import json
from contextlib import redirect_stdout
from dataclasses import asdict
from pathlib import Path

from dss5105.allocator import ObjectiveWeights, ScoreScales, earliest_finish, make_allocator, rank_candidates
from dss5105.harness import HARNESS_PATH, Simulator, cheapest, greedy_biggest, random_choice

# Exploratory configurations, chosen before running experiments, not tuned winners.
PRESETS = {
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
                decision["candidates"] = [
                    asdict(row) for row in rank_candidates(batch, workshops, queues, configurations[name], scales)
                ]
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
        "policies": traces,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=PRESETS, help="Choose one preset; otherwise compare all presets")
    for objective in ("lateness", "defects", "cost"):
        parser.add_argument(
            f"--{objective}-weight",
            type=float,
            help="Custom nonnegative weight; unspecified custom weights are zero; cannot combine with --preset",
        )
    parser.add_argument("--shock", action="store_true", help="Use the course's hidden workshop closure")
    parser.add_argument("--seed", type=int, default=5105)
    parser.add_argument("--output", type=Path, help="Save configuration, report, and per-order traces as JSON")
    args = parser.parse_args(argv)
    requested_weights = {
        "lateness": args.lateness_weight,
        "defects": args.defects_weight,
        "cost": args.cost_weight,
    }
    custom = any(value is not None for value in requested_weights.values())
    if args.preset and custom:
        parser.error("--preset cannot be combined with custom weight arguments")
    configurations = None
    if args.preset:
        configurations = {args.preset: PRESETS[args.preset]}
    elif custom:
        try:
            weights = ObjectiveWeights(
                **{key: 0.0 if value is None else value for key, value in requested_weights.items()}
            )
        except ValueError as exc:
            parser.error(str(exc))
        configurations = {"custom": weights}
    result = run_experiment(shock=args.shock, seed=args.seed, configurations=configurations)
    print(f"Scenario: {'shock' if args.shock else 'normal'}; seed: {args.seed}")
    print(f"Objective weights: {json.dumps(result['weights'], sort_keys=True)}")
    print(f"Score scales: {json.dumps(result['scales'], sort_keys=True)}")
    print(result["report"], end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"Saved experiment: {args.output}")


if __name__ == "__main__":
    main()
