"""Explore a fixed weight grid, then check frozen candidates on additional seeds."""

import argparse
import hashlib
import json
from dataclasses import asdict
from itertools import product
from pathlib import Path
from statistics import mean

from dss5105.allocator import ObjectiveWeights, ScoreScales, earliest_finish, make_allocator
from dss5105.evaluate import SPRINT1_PRESETS as PRESETS
from dss5105.harness import HARNESS_PATH, Simulator, cheapest, greedy_biggest, random_choice

# Fix the search and check scenarios before inspecting their results.
SECONDARY_WEIGHTS = (0.0, 0.001, 0.01, 0.05, 0.1, 0.3, 1.0)
CHECK_SEEDS = (5106, 5107, 5108, 5109, 5110)


def summarize(outcomes, workshops):
    """Unrounded course metrics plus conditional expected batch-defect exposure."""
    n = len(outcomes)
    if not n:
        raise ValueError("Cannot summarize an empty replay")
    days = sorted(row["turnaround"] for row in outcomes)
    total_pieces = sum(row["pieces"] for row in outcomes)
    by_workshop = {}
    for row in outcomes:
        by_workshop[row["workshop"]] = by_workshop.get(row["workshop"], 0) + row["pieces"]
    late_count = sum(row["late"] for row in outcomes)
    return {
        "batch_count": n,
        "late_count": late_count,
        "late_pct": 100 * late_count / n,
        "mean_days": mean(days),
        "p90_days": days[int(0.9 * n)],
        "defect_pct": 100 * sum(row["defective"] for row in outcomes) / n,
        "expected_batch_defect_pct": 100 * mean(workshops[row["workshop"]].defect_rate for row in outcomes),
        "cost": sum(row["cost"] for row in outcomes),
        "max_share_pct": 100 * max(by_workshop.values()) / total_pieces,
    }


def measure(policy, *, seed, shock):
    sim = Simulator(seed=seed, shock=shock)
    outcomes = sim.run(policy, "experiment")
    return {
        "seed": seed,
        "shock": shock,
        "metrics": summarize(outcomes, sim.workshops),
        "outcomes": [
            {"order_id": batch["order_id"], **outcome} for batch, outcome in zip(sim.batches, outcomes, strict=True)
        ],
    }


def select_candidates(development, reference_late_count):
    """Freeze recommendations using development results only, before any checks."""

    def key(name, fields):
        metrics = development[name]["metrics"]
        return (*(metrics[field] for field in fields), name)

    same_lateness = [name for name, run in development.items() if run["metrics"]["late_count"] <= reference_late_count]
    if not same_lateness:
        raise ValueError("The development grid must include a candidate meeting the reference late count")
    return {
        "lateness_first": min(
            development, key=lambda name: key(name, ("late_count", "cost", "expected_batch_defect_pct"))
        ),
        "cost_at_reference_lateness": min(
            same_lateness, key=lambda name: key(name, ("cost", "late_count", "expected_batch_defect_pct"))
        ),
        "quality_at_reference_lateness": min(
            same_lateness, key=lambda name: key(name, ("expected_batch_defect_pct", "late_count", "cost"))
        ),
    }


def run_tuning(development_seed=5105, check_seeds=CHECK_SEEDS, secondary_weights=SECONDARY_WEIGHTS):
    if not check_seeds or development_seed in check_seeds or len(set(check_seeds)) != len(check_seeds):
        raise ValueError("Check seeds must be nonempty, unique, and distinct from the development seed")
    scales = ScoreScales()
    grid = {
        f"grid_d{defects:g}_c{cost:g}": ObjectiveWeights(lateness=1.0, defects=defects, cost=cost)
        for defects, cost in product(secondary_weights, repeat=2)
    }
    development = {
        name: measure(make_allocator(weights, scales), seed=development_seed, shock=False)
        for name, weights in grid.items()
    }
    references = {"random": random_choice, "greedy_biggest": greedy_biggest, "cheapest": cheapest}
    references["earliest_finish"] = earliest_finish
    references.update({name: make_allocator(weights, scales) for name, weights in PRESETS.items()})
    reference_runs = {name: measure(policy, seed=development_seed, shock=False) for name, policy in references.items()}
    selected = select_candidates(development, reference_runs["lateness"]["metrics"]["late_count"])

    # Do not use check results to reselect candidates or rewrite the product presets.
    frozen = {name: make_allocator(grid[name], scales) for name in sorted(set(selected.values()))}
    checks = {
        name: [measure(policy, seed=seed, shock=shock) for shock in (False, True) for seed in check_seeds]
        for name, policy in (references | frozen).items()
    }
    shared_shock = {
        name: measure(policy, seed=development_seed, shock=True) for name, policy in (references | frozen).items()
    }
    sources = [HARNESS_PATH, HARNESS_PATH.parent.parent / "data" / "orders.csv"]
    sources.append(HARNESS_PATH.parent.parent / "data" / "workshops.csv")
    sources.extend(Path(__file__).with_name(name) for name in ("allocator.py", "evaluate.py", "tune.py"))
    return {
        "scope": "Exploratory tuning on supplied orders; additional seeds are sensitivity checks, not unseen orders",
        "development_seed": development_seed,
        "check_seeds": list(check_seeds),
        "secondary_weights": list(secondary_weights),
        "scales": asdict(scales),
        "grid": {name: asdict(weights) for name, weights in grid.items()},
        "reference_weights": {name: asdict(weights) for name, weights in PRESETS.items()},
        "source_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
        "development": development,
        "references": reference_runs,
        "selection_rules": {
            "lateness_first": "late_count, then cost, then expected batch defect exposure, then name",
            "cost_at_reference_lateness": "Within reference late count: cost, late_count, expected exposure, name",
            "quality_at_reference_lateness": "Within reference late count: expected exposure, late_count, cost, name",
        },
        "selected": selected,
        "checks": checks,
        "shared_shock": shared_shock,
    }


def print_report(result):
    print(f"Development seed: {result['development_seed']}; grid configurations: {len(result['grid'])}")
    for rule, name in result["selected"].items():
        print(f"{rule}: {name}; weights={result['grid'][name]}")
    print("\nDevelopment results (supplied orders, normal scenario):")
    header = f"{'policy':<24}{'late %':>9}{'mean days':>11}{'cost':>12}{'expected defect %':>19}"
    print(header)
    rows = result["references"] | {name: result["development"][name] for name in result["selected"].values()}
    for name, row in rows.items():
        m = row["metrics"]
        print(
            f"{name:<24}{m['late_pct']:>9.2f}{m['mean_days']:>11.2f}{m['cost']:>12,.0f}"
            f"{m['expected_batch_defect_pct']:>19.2f}"
        )
    print("\nShared-seed shock comparison (after candidate selection):")
    print(header)
    for name, row in result["shared_shock"].items():
        m = row["metrics"]
        print(
            f"{name:<24}{m['late_pct']:>9.2f}{m['mean_days']:>11.2f}{m['cost']:>12,.0f}"
            f"{m['expected_batch_defect_pct']:>19.2f}"
        )
    print(f"\nSensitivity checks: seeds {result['check_seeds']}; averages across seeds, same supplied orders")
    for shock in (False, True):
        print(f"\nScenario: {'shock' if shock else 'normal'}")
        print(header)
        for name, runs in result["checks"].items():
            metrics = [run["metrics"] for run in runs if run["shock"] == shock]
            m = {field: mean(row[field] for row in metrics) for field in metrics[0]}
            print(
                f"{name:<24}{m['late_pct']:>9.2f}{m['mean_days']:>11.2f}{m['cost']:>12,.0f}"
                f"{m['expected_batch_defect_pct']:>19.2f}"
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/weight-search.json"))
    args = parser.parse_args()
    result = run_tuning()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print_report(result)
    print(f"\nSaved all configurations, selection rules, and outcomes: {args.output}")
    print("Existing presets were not changed. This is not held-out order evaluation.")


if __name__ == "__main__":
    main()
