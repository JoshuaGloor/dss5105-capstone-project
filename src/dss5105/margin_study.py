"""Deadline-buffer study: select on development seeds, then report on the course seeds.

Question: earliest finish and the lateness preset send every batch to the fastest
workshop, even when it has days of slack. Does "use a cheaper or more careful
workshop that still meets the date with a safety buffer" keep lateness while saving
cost or defects? Selection uses development seeds only; the course seeds are run
once, after the choice is frozen. Both use the same 120 supplied orders, so this
guards against tuning to defect and closure draws, not to the order stream.
"""

import argparse
import hashlib
import json
import random
from dataclasses import asdict
from pathlib import Path

from dss5105.allocator import ObjectiveWeights, make_allocator
from dss5105.evaluate import SPRINT1_PRESETS as PRESETS
from dss5105.evaluate import run_seed_series
from dss5105.harness import HARNESS_PATH, Simulator, eligible_workshops

DEVELOPMENT_SEED = 6000
REPORT_SEED = 5105
SEEDS = 10
SECONDARY_WEIGHT = 0.01
BUFFERS = (0.0, 2.0, 5.0, 7.0, 10.0, 14.0)
SELECTION_RULE = (
    "Lowest mean late days over the development normal and shock runs, then lowest mean % late, "
    "then lowest mean cost, then name. The lateness preset is a candidate, so 'no change' can win."
)
METRICS = ("% late", "late days", "% def pcs", "cost", "max share", "mean days")
# Copied from the course harness for the diagnostic oracle only; never used by a policy.
CLOSURE_START, CLOSURE_END = 30, 44


def closure_oracle(seed: int):
    """Diagnostic upper bound that CHEATS: it knows which workshop --shock closes and when.

    Uses the harness's documented shock draw and closure window. No real detector can
    beat it, so its gap to the lateness preset bounds what stall detection could win.
    """
    workshops = Simulator().workshops
    target = random.Random(seed + 6).choice([w.workshop_id for w in workshops.values() if w.status == "ACTIVE"])
    day0 = Simulator().batches[0]["sent_date"]

    def allocate(batch, workshops, queues):
        day = (batch["sent_date"] - day0).days
        options = []
        for workshop in eligible_workshops(batch, workshops):
            start = day + queues[workshop.workshop_id]
            work = batch["pieces"] / workshop.capacity * (1 + 0.5 * workshop.defect_rate)
            finish = start + work
            if workshop.workshop_id == target:
                if CLOSURE_START <= start < CLOSURE_END:
                    finish = CLOSURE_END + work
                elif start < CLOSURE_START < finish:
                    finish += CLOSURE_END - CLOSURE_START
            options.append((finish + workshop.lead_days, workshop.workshop_id))
        return min(options)[1]

    return allocate


def shock_headroom(seed: int = REPORT_SEED, seeds: int = SEEDS) -> dict:
    """Mean shock % late and late days: lateness preset against the cheating oracle."""
    totals = {"lateness": [0.0, 0.0], "closure_oracle": [0.0, 0.0]}
    for current in range(seed, seed + seeds):
        sim = Simulator(shock=True, seed=current)
        policies = {"lateness": make_allocator(PRESETS["lateness"]), "closure_oracle": closure_oracle(current)}
        for name, policy in policies.items():
            metrics = sim.metrics(sim.run(policy, name))
            totals[name][0] += metrics["% late"] / seeds
            totals[name][1] += metrics["late days"] / seeds
    return {name: {"% late": late, "late days": days} for name, (late, days) in totals.items()}


def grid() -> dict[str, ObjectiveWeights]:
    """Lateness first, a small secondary term to order on-time candidates, and a buffer."""
    candidates = {"lateness": PRESETS["lateness"]}
    for term in ("cost", "defects"):
        for buffer in BUFFERS:
            candidates[f"{term}_buffer{buffer:g}"] = ObjectiveWeights(
                lateness=1.0, **{term: SECONDARY_WEIGHT}, deadline_buffer_days=buffer
            )
    return candidates


def select(series: dict, candidates) -> str:
    """Apply SELECTION_RULE to a shock seed series with its paired normal runs."""

    def mean(name, key):
        return (series["normal_metrics"][name][key] + series["metrics"][name][key]) / 2

    return min(candidates, key=lambda name: (mean(name, "late days"), mean(name, "% late"), mean(name, "cost"), name))


def compact(series: dict) -> dict:
    return {
        "seeds": series["seeds"],
        "normal": {name: {key: row[key] for key in METRICS} for name, row in series["normal_metrics"].items()},
        "shock": {name: {key: row[key] for key in METRICS} for name, row in series["metrics"].items()},
        "paired_deltas": series["paired_deltas"],
        "normal_lateness_guardrail": series["normal_lateness_guardrail"],
    }


def run_study() -> dict:
    candidates = grid()
    development = run_seed_series(shock=True, seed=DEVELOPMENT_SEED, seeds=SEEDS, configurations=candidates)
    winner = select(development, candidates)
    # Frozen before the course seeds run; their results never feed back into the choice.
    frozen = {name: weights for name, weights in PRESETS.items()}
    frozen[f"selected_{winner}"] = candidates[winner]
    report = run_seed_series(shock=True, seed=REPORT_SEED, seeds=SEEDS, configurations=frozen)
    sources = [HARNESS_PATH, HARNESS_PATH.parent.parent / "data" / "orders.csv"]
    sources.append(HARNESS_PATH.parent.parent / "data" / "workshops.csv")
    sources.extend(Path(__file__).with_name(name) for name in ("allocator.py", "evaluate.py", "margin_study.py"))
    return {
        "selection_rule": SELECTION_RULE,
        "grid": {name: asdict(weights) for name, weights in candidates.items()},
        "selected": winner,
        "selected_weights": asdict(candidates[winner]),
        "development": compact(development),
        "report": compact(report),
        "shock_headroom": shock_headroom(),
        "source_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
    }


def table(rows: dict, keys=METRICS) -> str:
    lines = ["| Policy | " + " | ".join(keys) + " |", "|---|" + "---|" * len(keys)]
    for name, row in rows.items():
        lines.append(f"| {name} | " + " | ".join(f"{row[key]:.3f}" for key in keys) + " |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/evidence/margin-study.json"))
    args = parser.parse_args()
    result = run_study()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("Selection rule:", result["selection_rule"])
    print("Selected on development seeds:", result["selected"], result["selected_weights"])
    for stage in ("development", "report"):
        block = result[stage]
        print(f"\n## {stage.capitalize()} seeds {block['seeds'][0]}-{block['seeds'][-1]}")
        for scenario in ("normal", "shock"):
            print(f"\n### {scenario}\n")
            print(table(block[scenario]))
        print("\n### Mean shock-minus-normal change\n")
        print(table(block["paired_deltas"], ("% late", "late days")))
    print("\n## Shock headroom on the course seeds (oracle cheats; diagnostic only)\n")
    print(table(result["shock_headroom"], ("% late", "late days")))
    print(f"\nSaved: {args.output}")


if __name__ == "__main__":
    main()
