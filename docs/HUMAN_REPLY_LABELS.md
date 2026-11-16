# Human reply labels

Two team members independently judged the 30 saved first replies of the Sprint 3 live
inbox run (`results/sprint3-live-01f2524/supplied`, commit `01f2524`, 9 November 2026).
This is the only human judgement of the replies themselves; the earlier human labels
(`docs/HUMAN_LABELS.md`) cover request kinds only.

## Questions

Each rater answered two questions per reply, Yes / No / Unsure:

1. **Decision correct?** Given the request and the data, is the desk's state, and the
   workshop or action it offers, what a careful dispatcher should do?
2. **Explanation faithful?** Does everything the desk shows (reply message, reasons,
   options, exclusions) agree with the tool output and the request?

## How the labels were made

- A blind sheet was built from the saved replies: request text, the desk's reading of it,
  the order record, state, reply, recommended workshop, reasons, options, exclusions, every
  candidate estimate, and the course data. Rubric results, request kinds and categories
  were left out.
- Each rater labelled alone and returned the sheet before any comparison (15 November 2026).
  The run-output columns of both returned sheets are identical to the blank sheet.
- Both raters are on the team and had seen the system. These are not external labels.

## Files

| File | What it holds |
|---|---|
| `examples/human_reply_labels_v1.json` | Both raters' labels and notes before adjudication, the run's artifact hashes and the SHA-256 of each returned sheet |
| `examples/rater_sheets/reply/` | The two returned sheets, byte for byte |
| `scripts/reply_label_agreement.py` | Recomputes every figure below from the JSON with no extra packages; `--sheets` also checks the sheets against their hashes (needs openpyxl) |

## Agreement (before adjudication)

| Question | Agree | Chance agreement | Cohen's kappa | Disagreements |
|---|---|---|---|---|
| Decision correct? | 28/30 | 0.871 | 0.48 | R01, R29 (A: Unsure, B: Yes) |
| Explanation faithful? | 29/30 | 0.967 | 0.00 | R10 (A: Yes, B: No) |

Label counts:

| | Rater A Yes / No / Unsure | Rater B Yes / No / Unsure |
|---|---|---|
| Decision | 27 / 1 / 2 | 29 / 1 / 0 |
| Explanation | 30 / 0 / 0 | 29 / 1 / 0 |

Kappa is low although raw agreement is high because almost every label is "Yes": with
rater A marking all 30 explanations faithful, chance agreement equals observed agreement
and kappa is 0. Read the raw agreement and the disagreement list, not kappa alone.

## What the labels show

- **R10 is the only reply either rater judged wrong.** Both marked the decision wrong
  (a new order should be asked for product, quantity and date, not an existing order ID);
  rater B also marked the explanation unfaithful. This matches the R10 human behaviour
  check in `docs/SPRINT3_LIVE_EVALUATION.md`.
- **R01 and R29: rater A unsure.** Rater A noted that the order ID should be enough to
  identify the order, i.e. once the order is known, the record could supply what else is
  asked. Rater B judged both correct. This is a policy question, not a clear error.
- **The raters did not flag the wording issues found by reading the replies**, for
  example the shared "Agree a deadline or split plan" headline on R23 when the deadline is
  safe, or the "delivery deadline" question on R29 when the message gives a ship date. A
  yes/no judgement of the whole reply is a lenient check of explanation wording.

## Limits

- Two raters from the team, one run, first replies only, inbox (development) set only.
- Decisions were judged against the data shown, not against a written policy, so the
  raters could differ on policy cases (R01, R29).
- Adjudicated labels are not yet recorded; this file holds the independent labels only.

## Reproduce

```bash
uv run python scripts/reply_label_agreement.py
# also re-read the two sheets and check their hashes (openpyxl is not a project dependency)
uv run --no-project --with openpyxl python scripts/reply_label_agreement.py --sheets
```
