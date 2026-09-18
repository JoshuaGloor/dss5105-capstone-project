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
  "today" to the historical replay.
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

## Reproducible initial experiments

The tables below are copied from the current runner's `Simulator.report()` output
using seed 5105. They use the existing course data and unmodified harness. The
saved outputs' source hashes were checked against the current files.

```bash
uv run python -m dss5105.evaluate --output results/allocation-normal.json
uv run python -m dss5105.evaluate --shock --output results/allocation-shock.json
```

Run from a source checkout after `uv sync --all-groups`. JSON records include
source hashes, seed, weights, scales, choices, queue snapshots, and outcomes.
Weighted policies include eligible candidate estimates and score components.
`results/` is generated and Git-ignored; these tables and the runner preserve the
reproduction route. Retain selected raw artifacts with the final evaluation.

See [ALLOCATION_ENGINE.md](ALLOCATION_ENGINE.md) for exact score definitions,
normalization scales, tie-breaking, and exploratory weights. In particular,
`lateness` is a greedy point-estimate penalty, not a proven late-rate optimizer.

### Normal scenario

| Policy | Mean days | P90 days | % late | % defect | Cost | Max share |
|---|---|---|---|---|---|---|
| random | 21.5 | 45.6 | 34% | 4% | 111,780 | 23% |
| greedy_biggest | 49.0 | 80.6 | 84% | 4% | 108,430 | 70% |
| cheapest | 105.1 | 192.9 | 93% | 8% | 85,960 | 70% |
| earliest_finish | 8.1 | 13.7 | 2% | 5% | 115,640 | 26% |
| lateness | 8.1 | 13.7 | 2% | 6% | 115,360 | 25% |
| defects | 162.5 | 282.1 | 95% | 2% | 129,920 | 70% |
| hybrid | 20.1 | 32.8 | 17% | 3% | 109,355 | 42% |

### Shock scenario

| Policy | Mean days | P90 days | % late | % defect | Cost | Max share |
|---|---|---|---|---|---|---|
| random | 23.4 | 48.4 | 39% | 4% | 111,780 | 23% |
| greedy_biggest | 51.0 | 81.2 | 87% | 4% | 108,430 | 70% |
| cheapest | 103.9 | 190.0 | 92% | 5% | 85,960 | 70% |
| earliest_finish | 8.4 | 15.4 | 2% | 5% | 115,805 | 26% |
| lateness | 8.3 | 15.4 | 2% | 6% | 115,665 | 27% |
| defects | 165.0 | 285.1 | 95% | 2% | 129,920 | 70% |
| hybrid | 19.6 | 34.1 | 22% | 3% | 109,165 | 41% |

## What these runs support

- Considering the live queue gives the short earliest-finish heuristic much lower
  turnaround and late rate than the provided baselines in these runs. Its normal
  rounded summary matches the earlier notes; the lost script's exact implementation
  is not established.
- The weighted lateness policy does not show a substantial advantage over that
  short heuristic in the displayed turnaround and late-rate metrics. This is an
  important comparator, not a result to hide.
- Quality-first routing performs poorly on timeliness in this experiment. It is
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
the due date. It does not measure the severity of lateness. `% defect` counts
batch-level defect events, not defective garments. `max share` is the largest
workshop's share of allocated pieces, a concentration proxy rather than a complete
definition of fairness. The printed percentages are rounded.

Defect draws are stochastic but seeded. Decisions change future queues, so one
seed does not establish performance across possible runs. A proposed expected
quality metric can remove the immediate defect-draw noise conditional on a fixed
allocation; allocations themselves can still change across seeds. No such extra
metric is exported by the initial `evaluate` runner. The separate weight-search
runner now reports conditional expected batch-defect exposure; see
[WEIGHT_TUNING.md](WEIGHT_TUNING.md) for its definition and results.

In the shock scenario, the target is selected from ACTIVE workshops. The closure
rule adjusts a chosen batch's start time if it falls in the closure interval; it
does not change the workshop's status to SUSPENDED. Later queue inputs may expose
that delay. Current policies use these queues, not explicit failure detection.
Selecting the shock target also consumes RNG state, so normal/shock differences
include changed defect draws and are not a clean estimate of the closure alone.
A dedicated controlled experiment would need a documented wrapper or variant.

## Questions not yet settled

The read-only dispatch preview now defines an independent inbox snapshot and
conservative date/constraint handling in [DISPATCH_CONTRACT.md](DISPATCH_CONTRACT.md).
Reproduce its development inputs with `uv run python -m dss5105.prototype`; the
generated `results/dispatch-previews.json` retains every preset's tool evidence.
These hand-authored interpretations are not gold chat labels or measured extraction
accuracy. A first live initial-response evaluation now exists in
[CHAT_EVALUATION_RESULTS.md](CHAT_EVALUATION_RESULTS.md). It reports frozen draft
checks and manual findings separately; it is not held-out or full-system validation.

The earlier weight-sweep and cost-frontier claims have no retained reproduction
script and are not included as current results. There is no established optimal
hybrid, proof of incompatible objectives, or verified count of infeasible chat
requests. Do not tune toward those old numbers.

Before computing chat feasibility, establish the intended order, quantities,
requested date, exclusions, and queue-state convention. R12 explicitly excludes
QuickStitch, so an unconstrained fastest estimate via that shop cannot establish
feasibility for that request. A past deadline or infeasible request needs an honest
explanation and options; it does not automatically authorize a late allocation.

Additional data summaries and chat labels should be added only with a recorded
method and evidence. Do not treat preliminary model-generated labels as ground truth.
