# Data and experiment findings

This file separates facts in the course data from observations produced by the
current experiment runner. Earlier chat notes contained unretained probe results;
those are not evidence for the current implementation.

## Data and simulator facts

Sources: [data dictionary](../track2/data/data_dictionary.md),
[workshops.csv](../track2/data/workshops.csv), and the
[unmodified simulator](../track2/harness/simulate.py).

- The course supplies 120 orders, 8 workshop profiles, and 30 chat requests.
- The chat inbox is dated 2026-04-01. The simulator instead replays all orders in
  `order_date` order, starting at the first order's date. Do not apply the inbox's
  "today" to the historical replay. Use workshop queue values directly as the
  April inbox snapshot; the replay separately reuses them as its January start.
- The simulator uses order ID, category, pieces, order date, and due date. It
  simulates new outcomes rather than scoring the historical `completed_date` or
  `days_late` columns. It does not restrict replay to IN_PROGRESS orders.
- Eligibility requires ACTIVE status, a supported category, and compliance with
  a batch cap if present. A blank cap means no cap. It does not mean ineligible.
- W7 OldMill is SUSPENDED and is never reactivated by the simulator. W8 FreshStart
  has a 300-piece cap; the other profiles have no batch cap.
- Eligibility does not guarantee timely delivery. Current queue, processing,
  and transport determine the delivery estimate.
- `workshops.csv` contains subcontracting `cost_per_piece`. The supplied files do
  not contain customer selling prices, historical quotes, or past allocations.
  Workshop cost cannot answer a question about a customer quote.
- `simulate.py` does not read `dispatch_requests.txt`. Language evaluation is a
  separate task.

## Current Data v3 experiments

The official data release replaces the inbox and fixes shock execution. Original
orders and workshop profiles remain unchanged. Normal-run results remain valid;
pre-v3 shock results are superseded.

```bash
uv run python scripts/refresh_v3_evidence.py
uv run python -m dss5105.prototype
```

See [V3_EVALUATION.md](V3_EVALUATION.md) for generated normal, ten-seed shock,
paired controls and robustness changes. [The retained evidence](evidence/data-v3.json)
includes source hashes, weights, scales, per-seed metrics and fixture outcomes.
Full per-order traces are regenerated in `results/allocation-v3-*.json`.
No weights were changed for this rerun and no provider was called.

The course now explicitly declares R20, R28 and R30 impossible. The nine corrected
requests are listed in [the official changelog](../track2/CHANGELOG.md). This is
source information, not an inferred infeasibility count from an old probe.

## What these runs support

- Considering the live queue gives the short earliest-finish heuristic much lower
  turnaround and late rate than the provided baselines in these runs. Its normal
  rounded summary matches the earlier notes; the lost script's exact implementation
  is not established.
- The weighted lateness policy does not show a substantial advantage over that
  short heuristic in the displayed turnaround and late-rate metrics. This is an
  important comparator, not a result to hide.
- Quality-first routing fails the new random-lateness guardrail and cannot
  qualify as a primary defects win. It performs poorly on timeliness. It is
  evidence of a tradeoff for this policy and dataset, not proof that fast and
  low-defect allocation is mathematically impossible.
- The hybrid changes the tradeoff: in the normal run it costs less and has fewer
  simulated defective batches than the lateness policy, but more late batches.
  It has not been selected as the product default or shown to be Pareto-optimal.
- Baselines still win on some metrics: cheapest has lower cost than our current
  policies, and random has lower load concentration than our current policies.
  A primary-objective win does not imply superiority on every metric.

## Metric definitions and inference limits

`mean days` and `p90 days` measure turnaround from dispatch to delivery, not days
past the deadline. `% late` counts batches whose rounded completion date exceeds
the due date. The new `late days` metric is mean positive rounded overdue days over all
batches, with on-time batches counting as zero. `% defect` counts
batch-level defect events, not defective garments. `% def pcs` weights those
batch events by their pieces; it is not an inspection count of defective garments.
`max share` is the largest workshop's share of allocated pieces, a concentration
proxy rather than a complete definition of fairness. Printed percentages are rounded.

Defect draws are stochastic but seeded. Decisions change future queues, so one
seed does not establish performance across possible runs. A proposed expected
quality metric can remove the immediate defect-draw noise conditional on a fixed
allocation; allocations themselves can still change across seeds. The `evaluate`
runner now exports all official metrics without display rounding. The separate
weight-search runner reports conditional expected batch-defect exposure; see
[WEIGHT_TUNING.md](WEIGHT_TUNING.md) for its definition and results.

In Data v3, a separate random stream chooses the shock target from ACTIVE
workshops. Work in progress pauses across the closure, and work arriving during it
waits. The workshop is not marked SUSPENDED. Later queue inputs expose the delay;
our policies adapt to queues without explicit failure detection. Paired normal and
shock runs align random draws, although changed workshop choices can change defect
probabilities and realized events. Robustness reporting averages per-seed changes
over the required ten seeds.

## Questions not yet settled

The read-only dispatch preview now defines an independent inbox snapshot and
conservative date/constraint handling in [DISPATCH_CONTRACT.md](DISPATCH_CONTRACT.md).
Reproduce its development inputs with `uv run python -m dss5105.prototype`; the
generated `results/dispatch-previews.json` retains every preset's tool evidence.
These hand-authored interpretations are not gold chat labels or measured extraction
accuracy. A first live initial-response evaluation now exists in
[CHAT_EVALUATION_RESULTS.md](CHAT_EVALUATION_RESULTS.md). That run is historical
pre-v3 evidence; a new paid live rerun is pending.
The refreshed fixture replay is not language accuracy or full-system validation.

The earlier weight-sweep and cost-frontier claims have no retained reproduction
script and are not included as current results. There is no established optimal
hybrid or proof of incompatible objectives. The v3 impossible-request IDs now
come from the course announcement. Do not tune toward old inferred counts.

Before computing chat feasibility, establish the intended order, quantities,
requested date, exclusions, and queue-state convention. R12 explicitly excludes
QuickStitch, so an unconstrained fastest estimate via that shop cannot establish
feasibility for that request. A past deadline or infeasible request needs an honest
explanation and options; it does not automatically authorize a late allocation.

Additional data summaries and chat labels should be added only with a recorded
method and evidence. Do not treat preliminary model-generated labels as ground truth.
