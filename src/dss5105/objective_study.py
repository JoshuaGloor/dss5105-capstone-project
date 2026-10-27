"""Objective study: one scorer, one configuration per objective, chosen on development seeds.

Question: with capacity reservation, fairness and robustness added to the scorer, which
configuration best serves each course objective, and our lateness-first, defects-second
priority? Selection uses development seeds 6000-6029 only. The course seeds 5105-5114
run once, after every choice is frozen. Both replay the same 120 orders, so this guards
against tuning to defect and closure draws, not to the order stream.
"""

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from dss5105.allocator import ObjectiveWeights, earliest_finish, make_allocator
from dss5105.harness import HARNESS_PATH, Simulator, cheapest, greedy_biggest, random_choice

DEVELOPMENT_SEED, DEVELOPMENT_SEEDS = 6000, 30
REPORT_SEED, REPORT_SEEDS = 5105, 10
RESERVATIONS = (0.0, 0.5, 1.0, 2.0)
# Design constant, not tuned: missing the date costs one lateness unit (a week), so the
# desk never prefers a late workshop over an on-time one for capacity reservation alone.
DEADLINE_MISS_DAYS = 7.0
HYBRID_DEFECTS = (0.02, 0.05, 0.1, 0.2, 0.3)
HYBRID_BUFFERS = (0.0, 2.0, 4.0, 6.0, 8.0)
DEFECTS_LATENESS = (0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5)
DEFECTS_BUFFERS = (0.0, 5.0)
FAIRNESS = (0.02, 0.05, 0.1, 0.2, 0.5, 1.0)
ROBUSTNESS = (0.05, 0.1, 0.2, 0.5, 1.0)
HYBRID_LATE_TOLERANCE = 0.25  # percentage points of % late the secondary objective may cost
DEFECTS_GUARD_MARGIN = 0.85  # stay well inside "% late no worse than random" on development
FAIRNESS_LATE_TOLERANCE = 1.0  # percentage points: fairness must still deliver on time
METRICS = ("% late", "late days", "% def pcs", "expected % def pcs", "max share", "cost", "mean days")
RULES = {
    "lateness": "Reservation rate with the lowest mean late days over the development normal and shock runs, "
    "then mean % late, then the rate closest to 1 (one day of scarce capacity costs one day of lateness).",
    "hybrid": "Among lateness-first configurations whose development % late (normal and shock) is within "
    f"{HYBRID_LATE_TOLERANCE} points of the lateness preset and whose late days are no higher, the lowest "
    "development expected % def pcs, then % late, then name. The lateness preset wins if none qualifies.",
    "defects": f"Among configurations whose development % late is at most {DEFECTS_GUARD_MARGIN} x random's "
    "(normal and shock), the lowest development expected % def pcs, then % late, then name.",
    "fairness": f"Among configurations within {FAIRNESS_LATE_TOLERANCE} point of the lateness preset's development "
    "% late, the lowest development max share, then % late, then name.",
    "robustness": "The lowest development shock-minus-normal change in % late, then in late days, then the "
    "smaller weight. The lateness preset (weight 0) is a candidate, so 'no change' can win.",
}
REFERENCES = {
    "random": lambda: random_choice,
    "greedy_biggest": lambda: greedy_biggest,
    "cheapest": lambda: cheapest,
    "earliest_finish": lambda: earliest_finish,
}


def expected_defect_pct(outcomes: list[dict], workshops: dict) -> float:
    """Pieces-weighted profile defect rate of the chosen workshops, in percent.

    The same quantity as % def pcs before the defect draw, so it has far less seed noise.
    """
    pieces = sum(row["pieces"] for row in outcomes)
    return 100 * sum(row["pieces"] * workshops[row["workshop"]].defect_rate for row in outcomes) / pieces


def measure(configurations: dict[str, ObjectiveWeights], seed: int, seeds: int) -> dict:
    """Mean official metrics over paired normal and shock runs, plus the per-seed change."""
    policies = dict(REFERENCES)
    policies.update({name: (lambda w=weights: make_allocator(w)) for name, weights in configurations.items()})
    totals = {name: {"normal": {}, "shock": {}} for name in policies}
    for current in range(seed, seed + seeds):
        for scenario in ("normal", "shock"):
            sim = Simulator(shock=scenario == "shock", seed=current)
            for name, factory in policies.items():
                outcomes = sim.run(factory(), name)
                metrics = sim.metrics(outcomes)
                metrics["expected % def pcs"] = expected_defect_pct(outcomes, sim.workshops)
                row = totals[name][scenario]
                for key in METRICS:
                    row[key] = row.get(key, 0.0) + metrics[key] / seeds
    for row in totals.values():
        row["delta"] = {key: row["shock"][key] - row["normal"][key] for key in ("% late", "late days")}
    return {"seeds": list(range(seed, seed + seeds)), "policies": totals}


def lateness_grid() -> dict[str, ObjectiveWeights]:
    return {
        f"lateness_r{rate:g}": ObjectiveWeights(capacity_reservation=rate, deadline_miss_days=DEADLINE_MISS_DAYS)
        for rate in RESERVATIONS
    }


def objective_grids(reservation: float) -> dict[str, dict[str, ObjectiveWeights]]:
    """Every objective keeps the chosen reservation; each grid varies only its own terms."""
    late = {"capacity_reservation": reservation, "deadline_miss_days": DEADLINE_MISS_DAYS}
    return {
        "hybrid": {
            f"hybrid_d{defects:g}_b{buffer:g}": ObjectiveWeights(defects=defects, deadline_buffer_days=buffer, **late)
            for defects in HYBRID_DEFECTS
            for buffer in HYBRID_BUFFERS
        },
        "defects": {
            f"defects_l{lateness:g}_b{buffer:g}": ObjectiveWeights(
                lateness=lateness, defects=1.0, deadline_buffer_days=buffer, **late
            )
            for lateness in DEFECTS_LATENESS
            for buffer in DEFECTS_BUFFERS
        },
        "fairness": {f"fairness_{weight:g}": ObjectiveWeights(fairness=weight, **late) for weight in FAIRNESS},
        "robustness": {f"robustness_{weight:g}": ObjectiveWeights(robustness=weight, **late) for weight in ROBUSTNESS},
    }


def _mean(row: dict, key: str) -> float:
    return (row["normal"][key] + row["shock"][key]) / 2


def select_lateness(dev: dict, grid: dict[str, ObjectiveWeights]) -> str:
    rows = dev["policies"]
    return min(
        grid,
        key=lambda name: (
            _mean(rows[name], "late days"),
            _mean(rows[name], "% late"),
            abs(grid[name].capacity_reservation - 1.0),
            name,
        ),
    )


def select_hybrid(dev: dict, grid: dict, reference: str) -> str:
    rows = dev["policies"]
    ref = rows[reference]
    eligible = [
        name
        for name in grid
        if all(
            rows[name][scenario]["% late"] <= ref[scenario]["% late"] + HYBRID_LATE_TOLERANCE
            and rows[name][scenario]["late days"] <= ref[scenario]["late days"]
            for scenario in ("normal", "shock")
        )
    ]
    if not eligible:
        return reference
    return min(
        eligible,
        key=lambda name: (rows[name]["normal"]["expected % def pcs"], rows[name]["normal"]["% late"], name),
    )


def select_defects(dev: dict, grid: dict) -> str | None:
    rows = dev["policies"]
    eligible = [
        name
        for name in grid
        if all(
            rows[name][scenario]["% late"] <= DEFECTS_GUARD_MARGIN * rows["random"][scenario]["% late"]
            for scenario in ("normal", "shock")
        )
    ]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda name: (rows[name]["normal"]["expected % def pcs"], rows[name]["normal"]["% late"], name),
    )


def select_fairness(dev: dict, grid: dict, reference: str) -> str:
    rows = dev["policies"]
    limit = rows[reference]["normal"]["% late"] + FAIRNESS_LATE_TOLERANCE
    eligible = [name for name in grid if rows[name]["normal"]["% late"] <= limit] or [reference]
    return min(eligible, key=lambda name: (rows[name]["normal"]["max share"], rows[name]["normal"]["% late"], name))


def select_robustness(dev: dict, grid: dict[str, ObjectiveWeights]) -> str:
    rows = dev["policies"]
    return min(
        grid,
        key=lambda name: (
            rows[name]["delta"]["% late"],
            rows[name]["delta"]["late days"],
            grid[name].robustness,
            name,
        ),
    )


def course_checks(report: dict) -> dict:
    """Tracks v4 acceptance criteria, computed from the course-seed report."""
    rows = report["policies"]
    baselines = ("random", "greedy_biggest", "cheapest")

    def beats(name, key, scenario="normal"):
        return all(rows[name][scenario][key] < rows[base][scenario][key] for base in baselines)

    def guard(name):
        return rows[name]["normal"]["% late"] <= rows["random"]["normal"]["% late"]

    def steadier(name, references):
        return all(
            rows[name]["delta"][key] <= rows[base]["delta"][key]
            for base in references
            for key in ("% late", "late days")
        )

    # A baseline that is already late most of the time cannot get much later under a closure,
    # so the robustness comparison also reports the baselines that pass the lateness guardrail.
    qualified = [base for base in baselines if guard(base)]
    checks = {"guardrail_qualified_baselines": qualified}
    for name in rows:
        if name in REFERENCES:
            continue
        checks[name] = {
            "lateness_beats_all_baselines": beats(name, "% late") and beats(name, "late days"),
            "defects_beats_all_baselines": beats(name, "% def pcs"),
            "fairness_matches_random_share": rows[name]["normal"]["max share"]
            <= rows["random"]["normal"]["max share"],
            "robustness_steadier_than_all_baselines": steadier(name, baselines),
            "robustness_steadier_than_qualified_baselines": steadier(name, qualified),
            "normal_late_no_worse_than_random": guard(name),
            "beats_earliest_finish_on_late_days": rows[name]["normal"]["late days"]
            < rows["earliest_finish"]["normal"]["late days"],
        }
    return checks


def run_study() -> dict:
    stage_one = lateness_grid()
    first = measure(stage_one, DEVELOPMENT_SEED, DEVELOPMENT_SEEDS)
    lateness = select_lateness(first, stage_one)
    reservation = stage_one[lateness].capacity_reservation
    grids = objective_grids(reservation)
    candidates = {"lateness": stage_one[lateness]}
    for grid in grids.values():
        candidates.update(grid)
    second = measure(candidates, DEVELOPMENT_SEED, DEVELOPMENT_SEEDS)
    selected = {
        "lateness": "lateness",
        "hybrid": select_hybrid(second, grids["hybrid"], "lateness"),
        "defects": select_defects(second, grids["defects"]),
        "fairness": select_fairness(second, grids["fairness"], "lateness"),
        "robustness": select_robustness(second, {"lateness": candidates["lateness"], **grids["robustness"]}),
    }
    # Frozen before the course seeds run; their results never feed back into any choice.
    frozen = {objective: candidates[name] for objective, name in selected.items() if name is not None}
    frozen["sprint1_lateness"] = ObjectiveWeights(lateness=1.0)
    report = measure(frozen, REPORT_SEED, REPORT_SEEDS)
    data = HARNESS_PATH.parent.parent / "data"
    sources = [HARNESS_PATH, data / "orders.csv", data / "workshops.csv"]
    sources.extend(Path(__file__).with_name(name) for name in ("allocator.py", "objective_study.py"))
    return {
        "rules": RULES,
        "lateness_grid": {name: asdict(weights) for name, weights in stage_one.items()},
        "grids": {objective: {n: asdict(w) for n, w in grid.items()} for objective, grid in grids.items()},
        "selected": selected,
        "frozen_weights": {name: asdict(weights) for name, weights in frozen.items()},
        "development": {"lateness_stage": first, "objective_stage": second},
        "report": report,
        "course_checks": course_checks(report),
        "source_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
    }


def table(rows: dict, scenario: str, keys=METRICS) -> str:
    lines = ["| Policy | " + " | ".join(keys) + " |", "|---|" + "---|" * len(keys)]
    for name, row in rows.items():
        lines.append(f"| {name} | " + " | ".join(f"{row[scenario][key]:,.3f}" for key in keys) + " |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/evidence/objective-study.json"))
    args = parser.parse_args()
    result = run_study()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("Selected on development seeds:", json.dumps(result["selected"], indent=2))
    rows = result["report"]["policies"]
    for scenario in ("normal", "shock", "delta"):
        keys = ("% late", "late days") if scenario == "delta" else METRICS
        print(f"\n## Course seeds 5105-5114: {scenario}\n")
        print(table(rows, scenario, keys))
    print("\n## Course checks\n")
    print(json.dumps(result["course_checks"], indent=2))
    print(f"\nSaved: {args.output}")


if __name__ == "__main__":
    main()
