# Can we beat greedy_biggest on defects?

> Sprint 2 note: superseded by [OBJECTIVE_STUDY.md](OBJECTIVE_STUDY.md), where a
> defects configuration now beats greedy_biggest. The scorer weights the defect term by
> batch pieces since Sprint 2, so this grid reproduces exactly only from commit e8c40a5.

Tracks v4 asks for at least one objective besides the primary one. For "minimise
defects" the metric is `% def pcs` and the guardrail is `% late` no worse than random.
This study asks whether any defects-weighted configuration of our scorer clears both.

Reproduce with `uv run python scripts/defects_frontier.py` (under a minute, no provider
calls). It writes [the evidence](evidence/defects-frontier.json) with source hashes, the
grid, the selection rule and every metric.

## Protocol, fixed before the course seeds were run

- Grid: lateness weight 1, defects weight 0.05, 0.1, 0.2, 0.3, 0.5, 1 or 2, deadline
  buffer 0, 5 or 10 days (21 configurations).
- Selection on development seeds 6000-6009, normal run: lowest `% def pcs` among
  configurations whose `% late` is no worse than random; ties by `% late`, then name.
- Report the frozen choice once on course seeds 5105-5114, normal and `--shock`.

## Result: greedy_biggest still wins on defects

Development selected `defects0.5_buffer0`: 5.107 % def pcs at 19.333 % late, against
5.235 for greedy_biggest. The edge did not hold on the course seeds:

| Scenario | Policy | % late | late days | % def pcs | cost | max share |
|---|---|---|---|---|---|---|
| Normal | random | 34.167 | 6.133 | 5.599 | 111,780 | 22.6 |
| Normal | greedy_biggest | 84.250 | 26.528 | 5.278 | 108,430 | 70.2 |
| Normal | cheapest | 91.833 | 81.916 | 8.241 | 85,960 | 70.2 |
| Normal | lateness | 1.667 | 0.180 | 7.492 | 115,592 | 26.2 |
| Normal | defects0.5_buffer0 | 18.417 | 1.759 | 5.540 | 109,399 | 40.9 |
| Shock | greedy_biggest | 84.917 | 28.047 | 5.278 | 108,430 | 70.2 |
| Shock | lateness | 1.917 | 0.181 | 7.374 | 115,284 | 26.4 |
| Shock | defects0.5_buffer0 | 21.000 | 1.886 | 6.160 | 109,098 | 40.4 |

The selected setting beats random and cheapest on defective pieces and passes the
lateness guardrail, but it beats greedy_biggest on only 2 of 10 course seeds in each
scenario. We report this as a case where a baseline still wins.

## Why

The three lowest-defect workshops (Little Loom, SteadyHands, FreshStart) are small:
together they hold 340 of the 1400 pieces per day of active capacity, and FreshStart
caps batches at 300 pieces. Pushing more work to them builds queues and lateness faster than
it removes defects. greedy_biggest sends most tops to GiantWeave, whose 6 % defect rate is
already below the capacity-weighted average of the active workshops (7.0 %), so it is a hard target on this one
metric while failing every lateness metric.

## Limits

- `% def pcs` is a realized count from random defect draws; ten runs is a small sample,
  and the development edge (0.13 points) was within that noise.
- Development and course seeds replay the same 120 orders. This guards against tuning to
  defect and closure draws, not to the order stream.
- The hybrid for the final report is still to be frozen; this study only rules out a
  clean defects win for the configurations tried.
