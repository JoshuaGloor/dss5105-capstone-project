# Data v3 offline evaluation

Generated with `uv run python scripts/refresh_v3_evidence.py`. No provider calls.
Source hashes, configurations and per-seed metrics: [retained evidence](evidence/data-v3.json).
Full per-order traces are regenerated in `results/allocation-v3-*.json` (Git-ignored).
Metrics are official per-run metrics; seed summaries average those metrics, including P90.
Displayed percentages use percentage units; calculations retain unrounded values.
This is development evidence on the supplied replay, not held-out performance.

## Normal run, seed 5105

| Policy | % late | late days | % def pcs | mean days | cost | max share |
|---|---|---|---|---|---|---|
| random | 34.167 | 5.867 | 3.102 | 21.523 | 111780.000 | 22.620 |
| greedy_biggest | 84.167 | 25.283 | 2.032 | 49.024 | 108430.000 | 70.160 |
| cheapest | 93.333 | 80.808 | 5.348 | 105.126 | 85960.000 | 70.160 |
| earliest_finish | 1.667 | 0.167 | 4.064 | 8.055 | 115640.000 | 25.561 |
| lateness | 1.667 | 0.167 | 5.348 | 8.099 | 115360.000 | 25.455 |
| defects | 95.000 | 138.008 | 0.642 | 162.514 | 129920.000 | 70.160 |
| hybrid | 16.667 | 1.533 | 2.246 | 20.068 | 109355.000 | 41.818 |

## Shock mean over 10 seeds (5105-5114)

| Policy | % late | late days | % def pcs | mean days | cost | max share |
|---|---|---|---|---|---|---|
| random | 38.167 | 7.166 | 5.599 | 23.275 | 111780.000 | 22.620 |
| greedy_biggest | 84.917 | 28.047 | 5.278 | 51.843 | 108430.000 | 70.160 |
| cheapest | 91.833 | 84.120 | 8.241 | 108.405 | 85960.000 | 70.160 |
| earliest_finish | 1.917 | 0.191 | 7.118 | 8.509 | 115459.500 | 26.524 |
| lateness | 1.917 | 0.181 | 7.374 | 8.456 | 115283.500 | 26.380 |
| defects | 95.083 | 142.482 | 2.914 | 166.978 | 129920.000 | 70.160 |
| hybrid | 20.500 | 1.868 | 6.160 | 20.226 | 109185.000 | 40.385 |

## Paired normal controls

| Policy | % late | late days | % def pcs | mean days | cost | max share |
|---|---|---|---|---|---|---|
| random | 34.167 | 6.133 | 5.599 | 21.866 | 111780.000 | 22.620 |
| greedy_biggest | 84.250 | 26.528 | 5.278 | 50.303 | 108430.000 | 70.160 |
| cheapest | 91.833 | 81.916 | 8.241 | 106.200 | 85960.000 | 70.160 |
| earliest_finish | 1.667 | 0.178 | 7.182 | 8.260 | 115566.500 | 26.283 |
| lateness | 1.667 | 0.180 | 7.492 | 8.235 | 115591.500 | 26.209 |
| defects | 95.083 | 139.868 | 2.914 | 164.365 | 129920.000 | 70.160 |
| hybrid | 18.833 | 1.801 | 5.754 | 20.331 | 109456.000 | 40.866 |

## Mean shock-minus-normal changes

| Policy | Late rate change (percentage points) | Late days change | Normal late rate <= random |
|---|---|---|---|
| random | 4.0000 | 1.0333 | pass |
| greedy_biggest | 0.6667 | 1.5183 | fail |
| cheapest | 0.0000 | 2.2042 | fail |
| earliest_finish | 0.2500 | 0.0125 | pass |
| lateness | 0.2500 | 0.0008 | pass |
| defects | 0.0000 | 2.6133 | fail |
| hybrid | 1.6667 | 0.0667 | pass |

## Interpretation

Lateness beats the shipped baselines on both lateness metrics in these runs.
Earliest finish remains close; the language layer's added value needs separate evidence.
Pure defects fails the random-lateness guardrail. It is a diagnostic comparison,
not a qualifying defects winner. Cheapest wins cost; random has lower load concentration.
A small shock late-rate change alone is insufficient: cheapest has a smaller change
but fails the normal-lateness guardrail. No universal robustness win is claimed.
No weights were tuned and the team has not ratified a primary objective.

## Structured fixture replay

Replayed all 30 inbox cases across the bundled presets and checked tool fields,
including recomputed split estimates.
These are hand-authored inputs, not model extraction, human gold labels or live chat results.
Course kinds are our labelling; only their counts come from the data dictionary.

| Course kind | Dictionary count | Labelled | Lateness-preset states |
|---|---|---|---|
| complete_meetable | 7 | 7 | RECOMMEND 7 |
| complete_impossible | 3 | 3 | NEEDS_REVIEW 3 |
| constraint | 6 | 6 | NEEDS_REVIEW 1, RECOMMEND 5 |
| ambiguous | 4 | 4 | CLARIFY 4 |
| missing_number_or_date | 3 | 3 | CLARIFY 3 |
| ineligible_suggestion | 4 | 4 | REFUSE_SUGGESTION 4 |
| unanswerable | 3 | 3 | DECLINE 3 |

R23 asks for a split only if it is faster. The tool estimates the split, but split plans
cannot be saved, so the request stays in review. Every other kind reaches its intended state.

| Request | Course kind | Lateness-preset state | Flags |
|---|---|---|---|
| R01 | missing_number_or_date | CLARIFY | - |
| R02 | unanswerable | DECLINE | - |
| R03 | ambiguous | CLARIFY | - |
| R04 | complete_meetable | RECOMMEND | - |
| R05 | missing_number_or_date | CLARIFY | - |
| R06 | complete_meetable | RECOMMEND | - |
| R07 | complete_meetable | RECOMMEND | - |
| R08 | ineligible_suggestion | REFUSE_SUGGESTION | SUGGESTION_REFUSED |
| R09 | constraint | RECOMMEND | - |
| R10 | missing_number_or_date | CLARIFY | - |
| R11 | ineligible_suggestion | REFUSE_SUGGESTION | SUGGESTION_REFUSED |
| R12 | constraint | RECOMMEND | - |
| R13 | unanswerable | DECLINE | - |
| R14 | ineligible_suggestion | REFUSE_SUGGESTION | NO_ON_TIME_OPTION, SUGGESTION_REFUSED |
| R15 | ambiguous | CLARIFY | - |
| R16 | complete_meetable | RECOMMEND | - |
| R17 | complete_meetable | RECOMMEND | - |
| R18 | unanswerable | DECLINE | - |
| R19 | ambiguous | CLARIFY | - |
| R20 | complete_impossible | NEEDS_REVIEW | NO_ON_TIME_OPTION, SELECTED_OPTION_LATE |
| R21 | constraint | RECOMMEND | - |
| R22 | complete_meetable | RECOMMEND | - |
| R23 | constraint | NEEDS_REVIEW | SPLIT_REVIEW |
| R24 | ineligible_suggestion | REFUSE_SUGGESTION | SUGGESTION_REFUSED |
| R25 | constraint | RECOMMEND | - |
| R26 | complete_meetable | RECOMMEND | - |
| R27 | constraint | RECOMMEND | - |
| R28 | complete_impossible | NEEDS_REVIEW | PAST_DEADLINE, NO_ON_TIME_OPTION, SELECTED_OPTION_LATE |
| R29 | ambiguous | CLARIFY | - |
| R30 | complete_impossible | NEEDS_REVIEW | NO_ON_TIME_OPTION, SELECTED_OPTION_LATE |
