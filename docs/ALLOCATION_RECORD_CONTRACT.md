# Local allocation record contract

Finalized before implementation. This increment adds an explicit saved-plan mode
to Streamlit. Independent inbox previews, the HTML reference and simulator retain
their original semantics. A local record does not contact or book a real workshop.

## State and storage

SQLite lives at `runtime/dispatch.sqlite3` inside the checkout. The directory is
Git-ignored. The first saved-plan use initializes queues directly from the course
April snapshot. Every subsequent preview reads the saved queues and revision.
The planning date stays fixed at the inbox date; elapsed wall-clock time does not
drain queues. Real UTC timestamps identify commits separately from planning time.

A singleton state row contains a database identity, revision, planning date,
source hashes and queue days. An allocations table has unique allocation IDs,
idempotency keys and order IDs. One whole order can be saved only once in this
workspace, even when a second message references it. Partial orders, cancellation,
rescheduling and deletion are outside this increment.

Changing source files after workspace creation rejects use of that workspace.
Do not silently reset, migrate or derive queues from the simulator. A new course
release requires an explicitly chosen new workspace or a later migration tool.

## `AllocationStore.preview(envelope, request, weights)`

- Input: the existing envelope, validated DispatchInput and ObjectiveWeights.
- Output: deterministic dispatch evidence plus a `storage` object containing
  database identity, revision and any existing allocation ID. `commit_allowed`
  is true only for an on-time RECOMMEND on an IN_PROGRESS, unallocated order.
- Purpose: compare candidates against the shared saved plan without reserving work.
- Non-goals: provider invocation, queue mutation, deadline approval, real booking.
- Failure: invalid source state or database error is explicit. Completed orders
  require review; already allocated orders return ALREADY_ALLOCATED. Other existing
  clarification/refusal/infeasibility outcomes remain blocked.

Each preview reads state and existing allocations in one read transaction. It uses
DispatchDesk and the same scorer, preserving eligibility and exclusion checks.
The snapshot note labels saved planning queues rather than pretending they remain
the untouched CSV snapshot.

## `commit_allocation(preview, confirmed_by, idempotency_key, confirmed=True)`

- Input: the exact reviewed preview, nonempty dispatcher name, caller-generated
  retry key and explicit confirmation boolean.
- Output: the persisted record, including allocation ID, UTC time, actor, request,
  order/workshop, weights, constraints, source hashes, reviewed tool evidence,
  queue before/after and revision before/after.
- Purpose: atomically record an approved whole-order decision and reserve capacity
  in the local plan.
- Non-goals: authenticating the dispatcher, sending a message, changing course CSVs,
  approving lateness or executing a split.
- Failure: reject absent confirmation, blank identity/key, forged tool evidence,
  changed source/configuration/queue revision, duplicate order, or blocked state.
  No failed transaction changes queues or creates an allocation.

Within BEGIN IMMEDIATE, check retry identity, read current state, recompute the
preview from its structured input using current sources and compare every tool
field. Never trust a supplied recommendation, ETA or commit flag. UI-only language
traces/interpretation labels may be retained separately as unverified intake
evidence; they cannot replace regenerated tool fields.

A retry with the same key, full preview fingerprint and dispatcher returns the
original record, even after the revision advances. A reused key with different
content or actor is rejected. A new key for an already allocated order is rejected.
Concurrent confirmations serialize; after one succeeds, other old previews fail
the revision check and require renewed review.

Queue reservation adds expected processing occupancy: processing days plus the
existing expected rework allowance. Transport is excluded. This is a planning
convention, not a sampled simulator outcome or measured live workload. Record the
increment explicitly so the queue change can be independently checked.

## UI and evidence

Default to independent preview mode. Saved-plan mode is an explicit sidebar choice
and clearly names its local effect. Review and Confirm remain separate actions.
Changing mode, request, settings or evidence clears pending approval and its retry
key. A dispatcher name is required before saving. A successful save shows a receipt,
refreshes candidates from saved state, and disables a second allocation of that order.
Database failures show an error; they never fall back to a successful demo receipt.

`records()` returns persisted records in commit order for review and JSON export.
The record stores the full source-bound tool evidence and optional intake evidence.
Names are self-declared; this local prototype has no login, authorization layer or
tamper-proof audit store. Multi-user deployment requires those separately.

Explicit deadline amendments remain outside this increment: late or ambiguous
requests cannot be committed. The existing clarification conversation can agree a
new input, which must produce a fresh on-time preview and a fresh confirmation.

## Validation

Offline tests cover restart durability, retries, duplicate order references, stale
and concurrent confirmations, tampering, failed-write rollback, queue occupancy,
source changes and UI confirmation. Provider calls remain outside these tests.
