# Dispatch preview contract (first implementation)

This contract is finalized for the first increment, before its implementation.
It implements a structured-input boundary around the existing allocator. The
language layer is specified separately in [INTAKE_CONTRACT.md](INTAKE_CONTRACT.md).
Durable local confirmation is a separate wrapper defined in
[ALLOCATION_RECORD_CONTRACT.md](ALLOCATION_RECORD_CONTRACT.md). This document
continues to specify the independent, read-only preview boundary.

## Source and state

- Load every raw line of `track2/data/dispatch_requests.txt`, retaining its ID,
  timestamp, speaker, and original text. Do not make these IDs policy branches.
- `examples/dispatch_inputs.json` contains hand-authored development interpretations
  of these lines. These are reviewable fixtures, NOT an NLP system or gold labels.
- Every preview independently starts on 2026-04-01, using `current_queue_days`
  directly from `workshops.csv`, the inbox snapshot specified by the v3 dictionary.
  The simulator separately uses those values on 2026-01-01; neither is derived from
  the other. Independent cases remain our evaluation convention: no preceding
  request changes that snapshot.
- A snapshot ID hashes the as-of date, queue values, and source file hashes.
  The tool output includes the source hashes and complete structured input.
- Historical completion/status columns are displayed as recorded facts, but do not
  authorize redispatch or promise current tracking. This is a hypothetical preview.

## `DispatchInput` (JSON)

All unknown keys and invalid types are rejected. Fields:

| Field | Meaning / default |
|---|---|
| `order_id` | Exact ID, or null; an unknown explicit ID never falls back to filters |
| `customer`, `product` | Optional case-insensitive exact CSV filters when ID absent |
| `intent` | `allocate` (default), `quote`, `history`, or `status` |
| `pieces` | Optional positive integer; conflict with CSV requires clarification |
| `due_date` | Optional ISO delivery date; explicit known date overrides CSV, retaining both |
| `date_uncertain` | New date unknown: clarify, never reuse the old deadline silently |
| `date_kind` | `delivery` (default) or `shipping`; a ship date equal to the recorded due date is used as the deadline, any other ship date needs clarification |
| `suggested_workshop` | Optional workshop ID; check and honor if eligible; not a hard exclusion of alternatives |
| `exclusions` | List of `{workshop_id, imposed_by, evidence}`; never relax |
| `preference` | `configured` (default), `fastest`, `lowest_defects`, or `cheapest_on_time` |
| `split_requested` | Boolean; show whole-batch and two-workshop split estimates, then escalate for review |
| `clarification` | Optional unresolved issue extracted from the message; blocks recommendation |

Speaker and raw text come from the inbox envelope, not the interpretation fixture.
Exclusion evidence must be a substring of the raw request and must identify its
imposer. This checks traceability, not the correctness of language interpretation.
Supplied product/category remain authoritative; changed quantities require an
explicit amendment workflow, outside this increment.

## `resolve_order(input)`

Return `RESOLVED`, `AMBIGUOUS`, or `NOT_FOUND`, with source rows. Never choose a
first match. ID plus contradictory customer/product requires clarification.
No ID/filter is ambiguous even if the source happens to contain only one row.

## `DispatchDesk.preview(envelope, input, weights)`

1. Decline quote/history requests because those records are absent. Decline a status
   query whose order is not recorded. Resolve other requests; unknown IDs or ambiguity
   require clarification.
2. Return recorded status only for a resolved status query. State that live movement
   information is unavailable.
3. Clarify unknown/reinterpreted dates and quantity or reference conflicts. A stated
   ship date that equals the order's recorded due date is not ambiguous: use it as the
   delivery deadline and return a `deadline_note` saying so.
4. Reuse course `eligible_workshops` as the authoritative membership rule. A
   diagnostic function explains status/category/cap failures; it does not select
   eligibility. Apply explicit exclusions as separate hard constraints.
5. Use the existing scorer and estimate function. `cheapest_on_time` filters to
   continuous expected turnaround <= days available, THEN minimizes cost. This is
   an estimate criterion, never a delivery guarantee. Other deadline failures require
   review, even if the selected objective prefers that late candidate.
6. Map request preferences to weight configurations outside the scorer. Fastest
   maps to the current pure lateness configuration (whose tie-break minimizes
   expected turnaround); lowest defects to pure defect weight; cheapest-on-time
   to pure cost weight plus a hard date constraint. Record configured and effective
   weights separately. A fixed request preference intentionally overrides the UI.
7. Return candidate estimates/components, considered and excluded workshops,
   deadline feasibility, refusal reasons, and a suggested eligible alternative.
   An ineligible suggestion is refused; an alternative is never auto-committed.

Possible outcomes: `RECOMMEND`, `CLARIFY`, `REFUSE_SUGGESTION`, `NEEDS_REVIEW`,
`NO_FEASIBLE_OPTION`, `DECLINE`, `RECORDED_STATUS`. Reasons may overlap; preserve
all relevant flags (e.g. a refused suggestion and late alternative).

Expected ETA is as-of midnight plus fractional expected days, rounded UP to the
next minute for display. Deadline feasibility uses unrounded day values. This is
not the simulator's rounded sampled completion date. Cost has no asserted currency
because the source does not specify one. Defect risk is per batch, not per garment.

Output includes preformatted display strings generated by Python. The prototype
only selects/displays results; it does not recompute estimates or scores.

### Data v3 refinement

Candidate display fields include queue, processing, transport and expected rework
days, alongside the expected ETA. The visible snapshot note names workshops.csv
and its as-of date. This makes queue-dependent decisions inspectable.

`earliest_option` is the permitted candidate with the smallest expected turnaround
(workshop ID breaks ties), independent of objective weights. `review_options`
contains tool-authored explanations for deadline amendment, split assessment and
human escalation. If no candidate meets the date, show the earliest estimated
whole-batch delivery and its lateness even when the cost constraint selects nobody.
An exception never enables confirmation. These are estimates under the supplied
snapshot, not guaranteed earliest achievable dates.

`decision_basis` explains the chosen workshop (the recommendation, or the alternative
after a refusal) and is `null` when nothing is chosen. It never chooses or reorders.
Its tool-authored `reasons` name any metric on which the choice is best among the
permitted workshops (or among those that meet the deadline, when the choice is on time
and others are not), its slack or lateness against the deadline, and its differences
from the next-ranked workshop (or the first-ranked one, when a hard date or a suggestion
moved the choice). Differences are taken between the displayed values, so they agree
with the comparison table. The raw differences are stored beside the sentences.

### Two-workshop split assessment

`split_option` is computed when the request asks for a split or no permitted whole
batch meets the date. `assess_split` (in `allocator.py`) tries every pair of permitted
workshops and every integer division of the pieces. Each part must pass the course
`eligible_workshops` rule at its own size, and chat exclusions still apply. Each part
is estimated with `estimate_delivery` on the same queue snapshot. The plan finishes
when its slower part does; ties prefer lower total cost, then workshop IDs.

The output lists both parts with their estimates and display strings, the plan's
expected turnaround, lateness, total cost, `days_saved` against `earliest_option`,
and a tool-authored `summary` that is added to `review_options`. A split request sets
the `SPLIT_REVIEW` flag and returns `NEEDS_REVIEW`. Split plans cannot be confirmed or
saved yet, and the course simulator never evaluates them: it sends one batch to one
workshop. The split never changes the recommended whole-batch workshop.

## Side effects and failures

Preview never changes queues or source CSVs, sends messages, or records a business
allocation. Invalid JSON/types, unknown workshops, missing/invalid queues, and bad
weights fail explicitly. Clarification and infeasibility are normal tool results.
Local demo confirmation is clearly labeled, does not persist, and is cleared on
request/configuration changes. The saved-plan wrapper's separate finalized contract
covers state versions, transactions, retries, and duplicate allocation prevention.

## Streamlit adapter contract

The web page calls `DispatchDesk.preview` directly on each request or configuration
change. Its offline mode loads the same draft inputs as the CLI; selecting a message
there does not invoke a language model. Natural language uses the intake contract.
Native controls select a preset or nonnegative
custom weights. All-zero weights block the result and confirmation. An explicit
request preference keeps precedence over global weights. The page explains when
global settings are retained but do not change the effective configuration.

Store selected request, settings, and demo confirmation in Streamlit session state
only. A fingerprint of the full tool result binds review/receipt to the exact input,
effective/configured weights, and source snapshot. Any changed preview or error
clears both. Only `RECOMMEND` can enter the demo confirmation flow. A second explicit
button acknowledges the demo; no durable allocation, file write, or queue mutation
occurs. Other states show clarification, refusal, or escalation guidance.

The page displays tool-provided numerical strings and exposes the complete JSON
evidence for download. Downloads are initiated by the user. The application never
opens a browser automatically. Streamlit's telemetry is disabled in project config.
The HTML remains a separate portable design reference.

Saved local plan is an explicit alternative workspace in Streamlit. It reads
persisted queues and adds storage revision and commit eligibility to the tool result.
Its separate confirmation flow writes a durable record; see the record contract.
It does not change the CLI, fixture evaluation or HTML snapshot behavior above.

## Reproduction and evaluation boundary

The CLI runs reviewed structured JSON or the supplied draft fixtures without an
API key. The prototype bundles all preset previews generated by this same service.
Tests establish deterministic tool behavior; they do NOT establish extraction
accuracy or explanation faithfulness of an LLM. Human annotation and a frozen
held-out chat set remain required before reporting full-system performance.
