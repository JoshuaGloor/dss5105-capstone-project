# Refinement for Spec v5, Tracks v4 and Data v3

Reviewed the complete Spec v5 and the Track 2 requirements in Tracks v4, plus the
official Data v3 changelog, dictionary, inbox and simulator. The source documents
are under `../Week 0/Capstone Project/`. Spec v5 retains the submission dates,
deliverables and grading structure; its evaluation wording now asks for a simple
rule-based comparator. Tracks v4 supplies the objective metrics and guardrails.

The old inbox's widespread March deadlines were a data-generation error, not
intended deadline exceptions. The revised inbox must replace those examples and
their old failure labels. Only the course-declared impossible cases should be
described as intentionally impossible complete requests; other behaviors such as
ship-date handling and split review have separate reasons.

## Changes implemented

- Imported the official simulator, dictionary and inbox without local edits.
  Included the official stage CSVs and changelog. The original orders and workshop
  profiles are unchanged. The course harness is still upstream code, not our fork.
  Compared imported bytes against the supplied folder and checked that normal
  per-order outcomes match the prior harness for every baseline and preset, ignoring
  only the newly added `days_late` field. Git attributes preserve upstream CRLF.
- Updated development fixtures and the draft chat rubric for R04, R06, R07, R16,
  R17, R22, R23, R26 and R27. Regenerated the standalone HTML and its tool evidence.
- Exposed queue days in candidate tables and the April snapshot convention in
  Streamlit and HTML. Streamlit also shows processing, transport, expected rework
  and ETA together. All values are produced by Python tools.
- Added an objective-independent earliest permitted estimate and explicit review
  options for infeasible deadlines. R20, R28 and R30 remain blocked from demo
  confirmation. The second pass below adds numeric split estimates.
- Added `--seeds` to our evaluation runner, retaining official metrics, per-seed
  traces, paired normal controls, robustness changes and the normal-lateness guard.
  Reported shock results use ten seeds. Single-seed shock runs are diagnostic only.
- Refreshed offline results and marked old shock and live-chat evidence historical.
  Source hashes and compact evidence are retained under `docs/evidence/`.

The allocator formula is unchanged. The simulator and chat previews continue to
use the same deterministic ranking and estimation functions, with chat constraints
validated by the dispatch adapter. No LLM is inside the allocation callback.

## Product decisions and limits

Use `workshops.csv` directly as the 2026-04-01 inbox snapshot. The simulator uses
the same queue numbers independently on 2026-01-01. Keep inbox evaluation cases
independent; an evaluation case is not a persisted reservation.

Keep default whole-batch mode. The upstream `--stages` command and supplied files
are available for separate exploration; our product and published comparisons do
not enable stage filtering. Adopting it would require a revised dispatch contract,
stage-aware UI diagnostics and separate comparisons with stage baselines.

### Second pass: aligning behavior with the published request mix

The dictionary gives seven complete, meetable requests. Set aside the six constraint
requests, four workshop suggestions and three impossible dates, and the complete
requests left are exactly R04, R06, R07, R16, R17, R22 and R26. So R06 and R16 must
be among the seven. Both give a "ship date" that
equals the order's recorded due date (ORD-096 on 2026-04-17, ORD-024 on 2026-04-15).
The dispatch tool now uses such a date as the delivery deadline and shows a note
saying so. It still asks when a stated ship date differs from the record. The intake
model no longer raises this question itself (`intake-v2`); Python decides.

R18 asks about movement on ORD-999, which is not in `orders.csv`. A status query
about an unrecorded order is now declined as unanswerable and states that no such
order is recorded. An allocation request naming an unknown order still asks for
the reference.

Splits now have numbers. `assess_split` finds the fastest two-workshop split under
the course eligibility rule and the request's exclusions. It runs for split requests
and whenever no whole batch meets the date, so the three impossible requests (R20,
R28, R30) give the earliest whole-batch date, the split estimate and escalation.
For R23 the split is estimated 1.57 days sooner, and both options meet the date.
R23 stays in review because split plans cannot be confirmed or saved yet. The
integrity audit recomputes every split part.

The chat rubric now tags each request with its course kind, and a test checks those
counts against the dictionary. At the tool level, every kind reaches its intended
state except R23. The per-request assignment is still our own labelling; it has not
been independently annotated.

The dictionary's mix is: seven complete and meetable, three complete but impossible,
six with constraints, four ambiguous, three missing a number/date, four ineligible
suggestions and three unanswerable. Preserve these course categories separately
from overlapping rubric labels such as exclusions, preferences and split requests.

Lateness is the recommended primary candidate for team discussion, with both
late rate and mean late days in the acceptance gate. The pure-defects preset fails
the random-lateness guardrail. It remains useful as an objective tradeoff, not a
successful quality solution. Earliest finish remains a strong simple comparator;
we must demonstrate the language layer's value through extraction, clarification,
constraint handling and faithful explanations. No primary objective has been
formally selected, and no new weights were tuned in this update.

## Reproduce

```bash
uv sync --all-groups
uv run python scripts/refresh_v3_evidence.py
uv run python -m dss5105.prototype
uv run pytest
```

The refresh script runs no provider calls. [V3_EVALUATION.md](V3_EVALUATION.md)
contains the generated tables and all fixture outcomes. The full traces are
regenerated under `results/`; the compact evidence is tracked.

## Remaining acceptance gates

- Run a newly authorized live evaluation on the entire corrected inbox, preserving
  the old run and its rubric. The existing evaluation command spends provider
  tokens and requires an explicit `--live` opt-in; this update did not run it.
- Independently annotate/adjudicate the revised inbox, including the ship-date and
  unknown-order decisions above. Freeze additional held-out cases before using their results.
- Complete the workshop-register query and overload probe contracts/implementation,
  and explicit deadline amendments. Local durable confirmation with stale-state
  rejection is now implemented in a separate saved-plan mode; see
  [the record contract](ALLOCATION_RECORD_CONTRACT.md). Independent previews and
  the HTML reference retain demo confirmation.
- Select the primary objective as a team, justify comparison/hybrid settings, and
  analyze failures individually. The historical weight search is not new v3 shock
  evidence; recheck frozen candidates before reporting robustness.
- Review the regenerated HTML manually in Chrome and test dispatcher tasks with
  teammates. Automated Streamlit checks do not establish human usability.

These remaining gates predate or follow from the course requirements; they are not
claims that the whole Track 2 submission is complete.
