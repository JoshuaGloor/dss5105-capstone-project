# Dispatch preview contract (first implementation)

This contract is finalized for the first increment, before its implementation.
It implements a structured-input boundary around the existing allocator. The
language layer is specified separately in [INTAKE_CONTRACT.md](INTAKE_CONTRACT.md).
Durable confirmation remains a later increment.

## Source and state

- Load every raw line of `track2/data/dispatch_requests.txt`, retaining its ID,
  timestamp, speaker, and original text. Do not make these IDs policy branches.
- `examples/dispatch_inputs.json` contains hand-authored development interpretations
  of these lines. These are reviewable fixtures, NOT an NLP system or gold labels.
- Every preview independently starts on 2026-04-01, with `current_queue_days` from
  the workshop CSV. This is our explicit experimental convention, not a claim about
  real historical queue state. No preceding request changes that snapshot.
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
| `date_kind` | `delivery` (default) or `shipping`; shipping needs clarification |
| `suggested_workshop` | Optional workshop ID; check and honor if eligible; not a hard exclusion of alternatives |
| `exclusions` | List of `{workshop_id, imposed_by, evidence}`; never relax |
| `preference` | `configured` (default), `fastest`, `lowest_defects`, or `cheapest_on_time` |
| `split_requested` | Boolean; expose whole-batch evidence, but escalate split planning |
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

1. Decline quote/history requests because those records are absent. Resolve other
   requests; unknown IDs or ambiguity require clarification.
2. Return recorded status only for a resolved status query. State that live movement
   information is unavailable.
3. Clarify unknown/reinterpreted dates and quantity or reference conflicts.
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

## Side effects and failures

Preview never changes queues or source CSVs, sends messages, or records a business
allocation. Invalid JSON/types, unknown workshops, missing/invalid queues, and bad
weights fail explicitly. Clarification and infeasibility are normal tool results.
Local demo confirmation is clearly labeled, does not persist, and is cleared on
request/configuration changes. Durable commit needs a separate approved contract
covering state versions, transactions, retries, and duplicate allocation prevention.

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

## Reproduction and evaluation boundary

The CLI runs reviewed structured JSON or the supplied draft fixtures without an
API key. The prototype bundles all preset previews generated by this same service.
Tests establish deterministic tool behavior; they do NOT establish extraction
accuracy or explanation faithfulness of an LLM. Human annotation and a frozen
held-out chat set remain required before reporting full-system performance.
