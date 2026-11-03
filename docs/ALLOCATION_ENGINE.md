# Allocation engine

This is an offline Python allocator, not the complete chat application. No LLM,
API key, new dependency, or modification to the course harness is needed.

## Run it

From a source checkout, after `uv sync --all-groups`:

```bash
uv run python -m dss5105.evaluate --output results/allocation-normal.json
uv run python -m dss5105.evaluate --shock --seeds 10 --output results/allocation-shock.json
uv run pytest

# Run one preset, without editing Python
uv run python -m dss5105.evaluate --preset defects --output results/defects.json

# Run an arbitrary configured mix; unspecified weights are zero
uv run python -m dss5105.evaluate \
  --lateness-weight 1.0 --defects-weight 0.05 --cost-weight 0.1 \
  --output results/custom.json
```

Single-seed tables use official `Simulator.report()`. `--seeds N` averages
the official per-run metrics and uses the official table formatter. Shock series
also retain paired normal traces, mean late-rate/late-days changes and the normal
random-lateness guardrail. Use `--shock --seeds 10` for course reporting. The JSON saves
the seed, source hashes, weights, scales, per-order choices, queue snapshots and
outcomes. Weighted policies also save all eligible candidate scores. Generated
results are ignored by Git; explicitly select evidence to publish later.

`mean days` and `p90 days` measure turnaround, not days overdue. `% late` counts
late batches; `% defect` counts batches with a simulated defect event. `max share`
measures the largest share of allocated pieces. `late days` is mean positive
overdue days across all batches; `% def pcs` weights defective batches by pieces.
It is not a count of individually inspected defective garments. No combined grade exists.

Without `--preset` or custom weight flags, `evaluate` compares every current preset.
`--preset NAME` runs one configured objective while retaining all four references
(`random`, `greedy_biggest`, `cheapest`, and `earliest_finish`). Supplying any weight
flag runs one configuration named `custom`; omitted weights are zero. The flags cannot
be combined with `--preset`, and at least one supplied weight must be positive. The
printed and saved output records the actual weights and fixed score scales.

## Read the code in this order

1. `allocator.earliest_finish`: filter eligible shops, estimate delivery, pick the
   earliest unadjusted turnaround. This reconstructs the short heuristic described
   in the old notes; the original probe script was not retained, so equivalence to
   that lost implementation is not established. Ties use workshop ID.
2. `allocator.estimate_delivery`: use the current `queues` passed by the harness,
   plus processing and transport. Expected turnaround adds expected rework:
   `process_days * 0.5 * defect_rate`. This uses the course's batch-defect model.
3. `allocator.rank_candidates`: call the course's `eligible_workshops()`, calculate
   component scores and sort the eligible candidates.
4. `allocator.make_allocator`: bind weights to a function taking exactly
   `(batch, workshops, queues)` and returning a workshop ID.
5. `evaluate.run_experiment`: run the course baselines, the short heuristic, and
   the weighted policies through the unmodified simulator.

## Score definition and presets

All objectives use this same formula; a policy name never changes allocation logic:

```text
score = lateness   * (lateness_days + capacity_reservation * reserved_days + miss_charge) / 7
      + defects    * defect_risk / 0.1 * pieces / 750
      + fairness   * projected_share / 0.25
      + robustness * stress_lateness_days / 7
      + cost       * cost_per_piece / 1

lateness_days        = max(0, expected_turnaround_days + deadline_buffer_days - days_until_due)
reserved_days        = pieces / (ACTIVE capacity of each other category this workshop makes)
projected_share      = (pieces this workshop already holds in the ledger + pieces) / (ledger total + pieces)
stress_lateness_days = max(0, expected_turnaround_days + 14 - days_until_due)
miss_charge          = deadline_miss_days if the unbuffered expected turnaround misses the date, else 0
```

`deadline_buffer_days`, `capacity_reservation` and `deadline_miss_days` are part of the
configuration and default to 0. With both at 0 and only the original weights, the ranking is exactly the
Sprint 1 score. A positive buffer penalizes candidates that would use nearly all of
the slack; reservation charges the lateness objective for scarce shared capacity (a
tops batch at a shop that also makes accessories); the miss charge keeps an on-time
workshop ahead of a late one. Estimates and the "meets deadline" test do not change. See [MARGIN_STUDY.md](MARGIN_STUDY.md) for the buffer and
[OBJECTIVE_STUDY.md](OBJECTIVE_STUDY.md) for the new terms and how the presets were chosen.

The minimum score wins. All configurations break ties by expected turnaround,
then workshop ID. For a fixed batch, pure lateness without reservation has the same
ranking as earliest expected turnaround; with reservation it prefers a tops-only shop
over a shared one whenever both meet the date with the same lateness.

Fairness reads a ledger of pieces already placed: in the simulator the `Allocator`
remembers its own decisions in the current replay; in the desk and the assistant it is
the saved plan's bookings. An empty ledger leaves fairness without effect.

| Preset | Lateness | Defects | Fairness | Robustness | Buffer | Purpose |
|---|---|---|---|---|---|---|
| hybrid (default) | 1.0 | 0.2 | 0 | 0 | 2 days | Our priority: lateness first, then defects |
| lateness | 1.0 | 0 | 0 | 0 | 0 | Primary objective alone |
| defects | 0.2 | 1.0 | 0 | 0 | 5 days | Defects objective within the lateness guardrail |
| fairness | 1.0 | 0 | 1.0 | 0 | 0 | Spread the work while delivering on time |
| robustness | 1.0 | 0 | 0 | 0.5 | 0 | Absorb a two-week closure |

Every preset uses capacity reservation 1 and a one-week deadline miss charge.

Every preset was frozen on development seeds 6000-6029 before the course seeds ran.
The Sprint 1 presets remain in `evaluate.SPRINT1_PRESETS` so the earlier margin,
defects-frontier and tuning studies still reproduce their evidence. (The Sprint 1
0.7/0.3 hybrid now uses the pieces-weighted defect term, so its rows differ slightly
from the archived evidence; its exact numbers are reproducible from commit e8c40a5.)

Reference scales are fixed units: a week of lateness, a 10% batch-defect probability on
a 750-piece batch, a quarter of all pieces, and one cost unit per piece. They make the
tradeoff inspectable across orders and never use future orders or outcomes.

## Limits to keep in the report

- Minimizing the point estimate of tardiness is a greedy heuristic. It is neither
  a global optimum nor direct minimization of the simulator's late-batch fraction.
- A penalty at the expected completion time is not expected tardiness, because
  clipping at the deadline is nonlinear. The simulator also rounds completion
  dates, whereas the scoring penalty uses continuous days.
- No policy reads future orders, the hidden shock target, or future defect draws.
  Shock information can only affect later choices through the queues supplied by
  the harness. A good shock score alone does not prove explicit failure detection.
- Every `Simulator.run` starts fresh queues and its seeded RNG. Data v3 chooses
  the shock target with a separate stream, aligning normal/shock random draws.
  Different allocation paths can still change the probability of a defect event.
  Report shock over ten seeds, with paired normal controls for robustness deltas.
- `rank_candidates` returns an empty list when nobody is eligible. The simulator
  callback raises `NoEligibleWorkshop` because the harness has no deferral protocol.
  The future chat layer must turn this into an explicit escalation, not invent a shop.
- The team's primary objective is minimise lateness, with minimise defects second; the
  default `hybrid` preset encodes that order. [DATA_FINDINGS.md](DATA_FINDINGS.md)
  records the earlier runs separately from unverified historical probes.
- Chat interpretation, confirmed commitments, and explanation faithfulness remain
  separate work. This experiment is not the complete Track 2 evaluation.

## Exploratory weight search

`uv run python -m dss5105.tune` searches a fixed grid without changing these presets.
See [WEIGHT_TUNING.md](WEIGHT_TUNING.md) for the method, selection rules, sensitivity
checks, and the distinction between development results and unseen-order evaluation.
