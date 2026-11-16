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
| `examples/human_reply_labels_adjudicated_v1.json` | Final labels after adjudication, each decision with both raters' labels and the reason, and the SHA-256 of the independent labels file |
| `examples/rater_sheets/reply/` | The two returned sheets, byte for byte |
| `scripts/reply_label_agreement.py` | Recomputes every figure below from the two JSON files with no extra packages, and checks that every disagreement has a recorded decision; `--sheets` also checks the sheets against their hashes (needs openpyxl) |

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

## After adjudication

The team decided the three disagreements on 16 November 2026, after both sheets had been
returned and compared. Every other label is the label both raters gave.

| Case | Question | Rater A | Rater B | Final | Reason |
|---|---|---|---|---|---|
| R01 | Decision | Unsure | Yes | Yes | Asking for the order ID and the quantity is acceptable under the current clarification policy, which is still open |
| R29 | Decision | Unsure | Yes | Yes | Same as R01; the "delivery deadline" wording is a separate known wording failure, not a decision error |
| R10 | Explanation | Yes | No | Yes | The reply text matches the tool output; the wrong question is already counted as a decision error, so it is not counted twice |

Final labels: **decision correct 29/30** (R10 wrong) and **explanation faithful 30/30**.
The agreement figures above are from before adjudication and do not change.

## What the labels show

- **R10 is the only reply either rater judged wrong.** Both marked the decision wrong
  (a new order should be asked for product, quantity and date, not an existing order ID);
  rater B also marked the explanation unfaithful. This matches the R10 human behaviour
  check in `docs/SPRINT3_LIVE_EVALUATION.md`.
- **R01 and R29: rater A unsure.** Rater A noted that the order ID should be enough to
  identify the order, i.e. once the order is known, the record could supply what else is
  asked. Rater B judged both correct. This is a policy question, not a clear error; the
  team recorded both as Yes (see "After adjudication").
- **The raters did not flag the wording issues found by reading the replies**, for
  example the shared "Agree a deadline or split plan" headline on R23 when the deadline is
  safe, or the "delivery deadline" question on R29 when the message gives a ship date. A
  yes/no judgement of the whole reply is a lenient check of explanation wording.

## Limits

- Two raters from the team, one run, first replies only, inbox (development) set only.
- Decisions were judged against the data shown, not against a written policy, so the
  raters could differ on policy cases (R01, R29).
- R01 and R29 were decided by the team, not by an outside adjudicator, and the clarification
  policy behind them is still open.

## Reproduce

```bash
uv run python scripts/reply_label_agreement.py
# also re-read the two sheets and check their hashes (openpyxl is not a project dependency)
uv run --no-project --with openpyxl python scripts/reply_label_agreement.py --sheets
```
