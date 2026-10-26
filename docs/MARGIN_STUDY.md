# What the allocator adds over earliest finish

Tracks v4 asks what the full system adds over the best simple rule, such as
"earliest estimated finish". This study answers that for the allocation policy.
The language layer's value is a separate question, measured on the chat inbox.

Reproduce with `uv run python -m dss5105.margin_study` (a few seconds, no provider
calls). It writes [the compact evidence](evidence/margin-study.json) with source
hashes, the grid, the selection rule and every metric.

## Finding 1: no room left under shock

The simulator only reveals a closure through the queues: once a batch is stuck at
the closed workshop, its queue jumps. Earliest finish and the lateness preset
already read those queues, so they route around the closure after that first batch.

To bound what any "stalled workshop" detector could win, the study runs a
diagnostic oracle that cheats: it knows which workshop closes and when. On the
course seeds 5105-5114 with `--shock`:

| Policy | % late | late days |
|---|---|---|
| lateness preset | 1.917 | 0.181 |
| closure oracle (cheats) | 1.833 | 0.183 |

The gap is 0.083 percentage points, about one late batch over ten runs. No
detector can beat the oracle, so stall detection is not worth building for this
simulator. The oracle is diagnostic only and is never offered as a policy.

## Finding 2: lateness is near its floor

In the normal run, the lateness preset has two late batches: ORD-062 and ORD-108,
both 2,000 accessories in a 17-day window. Only three active workshops make
accessories, and earlier jobs have already filled the fastest of them. No rule we
tried lowers the late rate meaningfully below 1.667%.

## Finding 3: a deadline buffer buys cost and late days

Earliest finish sends every batch to the fastest workshop, even with days of slack.
The configurable alternative uses the slack: pick the cheapest (or lowest-defect)
workshop whose expected turnaround plus a safety buffer still fits the due date,
and fall back to the fastest when none fits. This is configuration, not a new
policy: `ObjectiveWeights(lateness=1, cost=0.01, deadline_buffer_days=B)`. The
buffer only changes the lateness term of the score; estimates are unchanged.

Protocol, fixed in `margin_study.py` before the course seeds were run:

- Grid: buffer 0, 2, 5, 7, 10 or 14 days, with a secondary weight of 0.01 on
  either cost or defects, plus the unchanged lateness preset (13 candidates).
- Development: seeds 6000-6009, normal and shock.
- Selection: lowest mean late days over the development runs, then % late, then
  cost, then name. The lateness preset could win, meaning "no change".
- Report: the frozen choice against every reference on course seeds 5105-5114.

Development selected `cost_buffer10`. Course-seed results:

| Scenario | Policy | % late | late days | cost | % def pcs | mean days | max share |
|---|---|---|---|---|---|---|---|
| Normal | earliest_finish | 1.667 | 0.178 | 115,567 | 7.18 | 8.26 | 26.3 |
| Normal | lateness | 1.667 | 0.180 | 115,592 | 7.49 | 8.24 | 26.2 |
| Normal | cost_buffer10 | 1.750 | 0.138 | 106,668 | 6.48 | 10.99 | 29.7 |
| Shock | earliest_finish | 1.917 | 0.191 | 115,460 | 7.12 | 8.51 | 26.5 |
| Shock | lateness | 1.917 | 0.181 | 115,284 | 7.37 | 8.46 | 26.4 |
| Shock | cost_buffer10 | 2.250 | 0.155 | 107,047 | 6.35 | 11.24 | 29.7 |

Shock-minus-normal change: +0.500 percentage points and +0.017 late days for
`cost_buffer10`, against +0.250 and +0.001 for the lateness preset.

It is a tradeoff, not a strict win:

- Better: 14-23% fewer late days, 7-8% lower cost, about one point fewer defective
  pieces, and far better than every shipped baseline on every lateness metric.
- Worse: slightly more late batches (about one more over ten normal runs and four
  more over ten shock runs), longer mean turnaround, more load concentration, and
  a larger shock penalty.

Defect-first buffers never came close: the low-defect workshops are slow, their
queues grow, and lateness rose to 3-18% in development.

## What this means for the report

- Earliest finish is a strong comparator. On the lateness objective alone our
  preset only matches it; say so.
- What the allocator adds is configuration: the same code expresses the lateness
  preset, the buffered cost tradeoff and the other objectives, and the dispatcher
  sees why each option won. A single fixed rule cannot move along this tradeoff.
- `cost_buffer10` is a useful tradeoff to report, but cost is not one of the four course
  objectives, so it is unlikely to count as the required hybrid on its own. See
  [DEFECTS_FRONTIER.md](DEFECTS_FRONTIER.md) for the lateness + defects frontier.
  Whether to prefer it is a team decision about how many extra late batches a lower
  cost is worth.

## Limits

- Development and course seeds replay the same 120 orders, so this guards against
  tuning to defect and closure draws, not to the order stream. It is not held-out
  order evaluation.
- The development exploration was run before this protocol was written into code,
  with a prototype of the same rule on the same development seeds. The course seeds
  were not used until the choice was frozen.
- The oracle copies the harness's closure window and shock draw; if the harness
  changes, rerun the study.
