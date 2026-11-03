"""Can a defects-weighted configuration beat greedy_biggest on % def pcs within the lateness guardrail?

Protocol, fixed before the course seeds were run:
1. Grid: lateness weight 1, defects weight 0.05-2, deadline buffer 0/5/10 days.
2. Select on development seeds 6000-6009 (normal run): lowest % def pcs among
   configurations whose % late is no worse than random; ties by % late, then name.
3. Report the frozen choice once on course seeds 5105-5114, normal and shock.

Writes docs/evidence/defects-frontier.json. No provider calls.

    uv run python scripts/defects_frontier.py
"""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from dss5105.allocator import ObjectiveWeights
from dss5105.evaluate import SPRINT1_PRESETS as PRESETS
from dss5105.evaluate import run_seed_series
from dss5105.harness import HARNESS_PATH

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "evidence" / "defects-frontier.json"
DEFECT_WEIGHTS = (0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.0)
BUFFERS = (0.0, 5.0, 10.0)
DEVELOPMENT_SEED, COURSE_SEED, SEEDS = 6000, 5105, 10


def seed_wins(series: dict, name: str, rival: str) -> int:
    """Seeds on which `name` has strictly fewer defective pieces than `rival`."""
    return sum(run["metrics"][name]["% def pcs"] < run["metrics"][rival]["% def pcs"] for run in series["runs"])


def main():
    grid = {}
    for weight in DEFECT_WEIGHTS:
        for buffer in BUFFERS:
            grid[f"defects{weight:g}_buffer{buffer:g}"] = ObjectiveWeights(
                lateness=1.0, defects=weight, deadline_buffer_days=buffer
            )
    development = run_seed_series(False, DEVELOPMENT_SEED, SEEDS, grid)
    metrics = development["metrics"]
    guardrail = metrics["random"]["% late"]
    qualifying = [name for name in grid if metrics[name]["% late"] <= guardrail]
    selected = min(qualifying, key=lambda name: (metrics[name]["% def pcs"], metrics[name]["% late"], name))

    frozen = {"lateness": PRESETS["lateness"], selected: grid[selected]}
    normal = run_seed_series(False, COURSE_SEED, SEEDS, frozen)
    shock = run_seed_series(True, COURSE_SEED, SEEDS, frozen)

    data_dir = HARNESS_PATH.parent.parent / "data"
    sources = [HARNESS_PATH, data_dir / "orders.csv", data_dir / "workshops.csv", Path(__file__)]
    sources.append(ROOT / "src" / "dss5105" / "allocator.py")
    evidence = {
        "question": __doc__.splitlines()[0],
        "selection_rule": "Lowest development % def pcs with % late <= random; ties by % late, then name.",
        "grid": {name: asdict(weights) for name, weights in grid.items()},
        "development": {
            "seeds": development["seeds"],
            "guardrail_pct_late_random": guardrail,
            "configurations_within_guardrail": len(qualifying),
            "metrics": metrics,
        },
        "selected": selected,
        "selected_weights": asdict(grid[selected]),
        "course": {
            "seeds": normal["seeds"],
            "normal": normal["metrics"],
            "shock": shock["metrics"],
            "paired_shock_deltas": shock["paired_deltas"],
            "selected_seed_wins_vs_greedy_biggest_normal": seed_wins(normal, selected, "greedy_biggest"),
            "selected_seed_wins_vs_greedy_biggest_shock": seed_wins(shock, selected, "greedy_biggest"),
        },
        "source_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
    }
    OUTPUT.write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Development: {len(qualifying)} of {len(grid)} settings within the guardrail; selected {selected}.")
    for scenario, rows in (("normal", normal["metrics"]), ("shock", shock["metrics"])):
        print(f"Course seeds, {scenario}:")
        for name in ("random", "greedy_biggest", "cheapest", "earliest_finish", "lateness", selected):
            row = rows[name]
            print(
                f"  {name:22s} % late {row['% late']:6.2f}  % def pcs {row['% def pcs']:5.2f}  cost {row['cost']:9.0f}"
            )
    course = evidence["course"]
    print(f"Seeds where {selected} beats greedy_biggest on % def pcs: ", end="")
    print(f"normal {course['selected_seed_wins_vs_greedy_biggest_normal']}/{SEEDS}, ", end="")
    print(f"shock {course['selected_seed_wins_vs_greedy_biggest_shock']}/{SEEDS}")
    print(f"Saved {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
