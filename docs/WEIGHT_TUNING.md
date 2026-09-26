# Exploratory weight tuning

Historical pre-v3 experiment. Normal results remain valid; the shock rows below
are superseded and must not be reported as current results. Re-run frozen
configurations over ten paired seeds before drawing new robustness conclusions.
The updated objective guardrails are in EVALUATION_PLAN.md. The follow-up that
adds a deadline buffer, with separate development and course seeds, is
[MARGIN_STUDY.md](MARGIN_STUDY.md).

Run `uv run python -m dss5105.tune` from the source checkout. The script saves all
configurations, selection rules, source hashes, metrics, and per-order outcomes to
`results/weight-search.json`. It does not overwrite `evaluate.PRESETS` or change
allocation logic, course data, or the course simulator.

## Protocol

This is development on the supplied order replay. It is not held-out order
performance: the data and initial results were already inspected during development.
No final primary objective is chosen by this experiment.

Keep `ScoreScales` fixed. Hold the lateness weight at 1.0 and independently vary
both defects and cost weights over `(0, 0.001, 0.01, 0.05, 0.1, 0.3, 1.0)`, giving
49 configurations. These are relative weights; they do not need to sum to one.
Multiplying every weight by the same positive factor preserves ranking in exact
arithmetic. The tiny positive weights also probe the on-time score ties.

Run the grid on the normal scenario with seed 5105. Select candidates using three
rules, before looking at check results:

- Lateness first: least late batches, then lowest cost, then lowest expected batch
  defect exposure, then configuration name.
- Cost at reference lateness: lowest cost among configurations with no more late
  batches than the existing lateness preset; ties use late count, exposure, name.
- Quality at reference lateness: lowest expected batch defect exposure under that
  same late-count limit; ties use late count, cost, name.

The reference guard is a development selection criterion, not an allocator hard
constraint or a guarantee on other scenarios. The quality rule is conservative;
exploring an explicit willingness to accept additional lateness requires a separate,
recorded tolerance. There is no evidence here that these weights are globally optimal.

Freeze the selected candidate IDs. Compare them and all initial reference policies
on additional seeds 5106-5110 under both normal and shock scenarios. Also report
seed 5105 with shock after selection for the shared course comparison. Do not use
check results to choose a different winner or silently update the existing presets.
These are random-seed sensitivity checks on the same orders, not new orders or a
claim to have completed the course's held-out evaluation requirement.

## Metrics

Numeric metrics retain the harness definitions without display rounding, and late
counts are used for selection rather than rounded percentages. `summarize` adds
`expected_batch_defect_pct`: the unweighted average of chosen workshop defect
probabilities across batches, expressed as a percentage. It is not pieces-weighted
exposure, observed defective-batch percentage, or defective garment percentage.
Realized defect percentage and all original metrics remain in the saved results.

Expected exposure removes the immediate defect draw conditional on choices, but
choices depend on queues and earlier random outcomes. This metric can still vary
across seeds. The historical shock rows below used the old coupled RNG. The Data v3 harness
now separates shock selection from defect draws; use the revised evaluation runner.

## Initial result

All three development selection rules picked `grid_d0.05_c0.1`, whose weights are
`ObjectiveWeights(lateness=1.0, defects=0.05, cost=0.1)`. No grid candidate improved
the minimum development late count relative to the existing lateness preset.

The following values come from `tune.print_report`; seed-check rows average metrics
across the five additional seeds. More precise display explains the difference
between the late percentages here and the rounded course report.

| Scenario | Policy | Late % | Mean days | Cost | Expected batch defect % |
|---|---|---|---|---|---|
| Development: normal, 5105 | lateness | 1.67 | 8.10 | 115,360 | 6.65 |
| Development: normal, 5105 | candidate | 1.67 | 14.77 | 100,365 | 5.76 |
| Shared comparison: shock, 5105 | lateness | 1.67 | 8.31 | 115,665 | 6.67 |
| Shared comparison: shock, 5105 | candidate | 3.33 | 14.88 | 100,980 | 5.69 |
| Additional seeds: normal | lateness | 1.67 | 8.21 | 115,662 | 6.72 |
| Additional seeds: normal | candidate | 2.00 | 14.81 | 100,517 | 5.72 |
| Additional seeds: shock | lateness | 1.67 | 8.23 | 115,673 | 6.77 |
| Additional seeds: shock | candidate | 2.00 | 15.17 | 100,899 | 5.71 |

The candidate offers a cost/quality tradeoff, not a strict improvement: mean
turnaround is longer, and the development late-count parity does not hold in every
check scenario. Keep the reference presets and do not describe this as free savings
at unchanged timeliness. Choosing an operational default needs explicit tolerance
for this tradeoff and further evidence on unseen inputs.

## What the search reveals about the current score

Pure lateness clips the expected turnaround at the deadline and breaks ties by
expected turnaround. It therefore selects the earliest expected completion for a
fixed batch, regardless of that batch's deadline. Its effective difference from
`earliest_finish` is the expected rework adjustment.

When secondary weights are nonzero, candidates with no predicted lateness can be
ordered by cost or quality instead of speed. This can use available deadline slack,
but longer queues and future defect events can turn that slack into later failures.
Changing weights explores this behavior; it does not establish that the score is
the best formulation of late-rate risk. Before adding further terms, inspect
specific failures and define any proposed formula and its evaluation in advance.
