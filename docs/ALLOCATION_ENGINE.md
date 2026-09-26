# Allocation engine: first experiment

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

## Score definition and initial configurations

All objectives use this same formula; a policy name never changes allocation logic:

```text
score = lateness_weight * lateness_days / lateness_scale
      + defects_weight * defect_risk / defects_scale
      + cost_weight * cost_per_piece / cost_scale

lateness_days = max(0, expected_turnaround_days + deadline_buffer_days - days_until_due)
```

`deadline_buffer_days` is part of the configuration and defaults to 0, which is the
original score. A positive buffer penalizes candidates that would use nearly all of
the slack; estimates and the "meets deadline" test do not change. See
[MARGIN_STUDY.md](MARGIN_STUDY.md) for why it exists and what it buys.

The minimum score wins. All configurations break ties by expected turnaround,
then workshop ID. Thus, when every shop can deliver on time, pure lateness chooses
the earliest expected delivery among the tied candidates.

More generally, for a fixed batch, this pure-lateness configuration always has
the same ranking as earliest expected turnaround: clipping at the deadline is
monotone, and the turnaround tie-break orders the zero-penalty candidates. Changing
only that batch's deadline does not change its selected workshop. Compared with
`earliest_finish`, the effective difference is the expected rework adjustment,
not a new deadline-aware scheduling algorithm. Deadlines can affect the tradeoff
when nonzero defect or cost weights are included.

| Preset | Lateness weight | Defects weight | Cost weight |
|---|---|---|---|
| lateness | 1.0 | 0.0 | 0.0 |
| defects | 0.0 | 1.0 | 0.0 |
| hybrid | 0.7 | 0.3 | 0.0 |

Reference scales are 7 days of lateness, 0.1 batch-defect probability, and 1 cost
unit per piece. These fixed units make the tradeoff inspectable across orders;
they do not use future orders or simulator outcomes for normalization. They are
initial design assumptions, not measured optimal scales. The hybrid gives more
weight to lateness while allowing quality to influence the decision. It is an
exploratory configuration, not a justified final business preference or a tuned
winner. Weights and scales both affect the tradeoff; report both.

Cost uses a per-piece reference because batch sizes vary. The candidate estimate
also records total batch cost. Fairness weighting, a dedicated robustness policy,
and chat-imposed constraints are not implemented in this first increment.

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
- No primary objective has been ratified. [DATA_FINDINGS.md](DATA_FINDINGS.md)
  records these runs separately from unverified historical probes. The experiments
  do not validate a weight-sweep frontier or the earlier chat-feasibility labels.
- Chat interpretation, confirmed commitments, and explanation faithfulness remain
  separate work. This experiment is not the complete Track 2 evaluation.

## Exploratory weight search

`uv run python -m dss5105.tune` searches a fixed grid without changing these presets.
See [WEIGHT_TUNING.md](WEIGHT_TUNING.md) for the method, selection rules, sensitivity
checks, and the distinction between development results and unseen-order evaluation.
