# Human labels

Human labelling of the supplied inbox (`track2/data/dispatch_requests.txt`, R01-R30).
Scope is **request kind only**: each request is tagged with one of the data dictionary's
seven kinds. These are not gold answers. Expected fields, replies, recommended workshops
and explanations have no independent human labels.

## Files

| File | What it holds |
|---|---|
| `examples/human_rater_labels_v1.json` | Both raters' independent labels before adjudication, raw and normalised, with the SHA-256 of each source sheet |
| `examples/human_request_kinds_v1.json` | Adjudicated kinds (approved 2026-11-08), the inbox hash and the same sheet hashes. Used by `tests/test_evaluate_chat.py` and `dss5105.reliability_score --kind-labels` |
| `examples/rater_sheets/` | The two original rater sheets, committed byte for byte so their hashes match, plus a CSV copy of each for easier viewing |
| `scripts/rater_agreement.py` | Recomputes every agreement figure below from the two JSON files and `examples/chat_rubric.json` |

## How the labels were made

Two team members (rater A and rater B) each labelled R01-R30 independently against the
raw data, in separate sheets. Neither rater had seen the team's draft rubric
(`examples/chat_rubric.json`) before labelling. Disagreements were discussed only after
both sheets were saved; the adjudicated file was then frozen. The rubric comparisons below
are therefore against labels made without sight of the rubric.

Normalisation before comparison: lower-case, whitespace to underscore, and the one typo
`complete_meltable` mapped to `complete_meetable`. The export keeps the raw labels too.

## Agreement

| Comparison | Agree | Cohen's kappa | Disagreements |
|---|---|---|---|
| Rater A vs rater B | 23/30 | 0.708 | R09, R10, R14, R21, R23, R24, R27 |
| Rater A vs adjudicated | 24/30 | 0.757 | R09, R20, R21, R23, R27, R30 |
| Rater B vs adjudicated | 25/30 | 0.798 | R10, R14, R20, R24, R30 |
| Rater A vs team rubric | 23/30 | 0.717 | R01, R09, R20, R21, R23, R27, R30 |
| Rater B vs team rubric | 24/30 | 0.759 | R01, R10, R14, R20, R24, R30 |
| Adjudicated vs team rubric | 29/30 | 0.960 | R01 |

Label counts:

| Kind | Rater A | Rater B | Adjudicated |
|---|---|---|---|
| complete_meetable | 13 | 9 | 7 |
| complete_impossible | 1 | 3 | 3 |
| constraint | 2 | 6 | 6 |
| ambiguous | 5 | 6 | 5 |
| missing_number_or_date | 2 | 1 | 2 |
| ineligible_suggestion | 4 | 2 | 4 |
| unanswerable | 3 | 3 | 3 |

These figures describe agreement between these two raters on request kinds. They are not
a general measure of labelling reliability, and they say nothing about whether the
desk's recommendations are right.

## Reproduce

```bash
uv run python scripts/rater_agreement.py
```

Offline, no extra packages, no provider calls. It first checks that the export's source
hashes match the adjudicated file, then prints the agreement, counts and an A-by-B
confusion matrix as JSON.

## The original sheets

The rater sheets are committed unchanged in `examples/rater_sheets/`. They hold the inbox
columns (request_id, time, requester, text) plus each rater's `kind` column:

| Rater | File | SHA-256 |
|---|---|---|
| A | `rater_blank2.xlsx` | `495f26f45694b406c76eb0ab72c30cad061d5703ede4e2ca36c63294c18b89ca` |
| B | `human_labelled_cases.numbers` | `93f9f7c0082c1465be31b8b189d09141a5dafb459b15fac8f8a042fb7d80bb73` |

`shasum -a 256 examples/rater_sheets/rater_blank2.xlsx examples/rater_sheets/human_labelled_cases.numbers`
must print the hashes above. To regenerate the
export from the sheets (the readers are not project dependencies):

```bash
uv run --no-project --with openpyxl --with numbers-parser --with "protobuf>=7.36.2" \
    python scripts/rater_agreement.py --sheets examples/rater_sheets/rater_blank2.xlsx \
    examples/rater_sheets/human_labelled_cases.numbers
```

The script refuses a sheet whose hash differs, and reports if the regenerated export
differs from the committed one.

## CSV copies for viewing

The CSV files are added only so the labels are easy to read on GitHub or in any editor
without Excel or Numbers. The original `.xlsx` and `.numbers` files remain the source of
record: their hashes are the ones recorded in the label files, and `--sheets` reads the
originals, not the CSVs.

| Rater | CSV copy | Exported from | SHA-256 of the CSV |
|---|---|---|---|
| A | `rater_a_kinds.csv` | `rater_blank2.xlsx` | `40e9a9b0f3e5483a51bc664fe3bf78513389c415b3e4d72037707956ab44ffcc` |
| B | `rater_b_kinds.csv` | `human_labelled_cases.numbers` | `090c30941e58487eda0f23320f1a1535a373e85b662880e083f4a4c24d0042c2` |

The `kind` column of each CSV matches its original exactly for all 30 requests, including the raw
spelling, so every figure above is the same whichever copy is read. Formatting can differ
from the originals (for example rater A's CSV writes times as `7:53`, not `07:53`).
