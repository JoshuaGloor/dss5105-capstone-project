# Tool specification

The course requires tools to be specified before they are built (Tracks v3, p. 6).
This document distinguishes implemented Python interfaces from proposed agent
interfaces. The offline functions are not yet registered as LLM-callable tools.

Narrow typed tools are our current design preference, not a Track 2 requirement
to choose a particular SQL interface. They make inputs and failure states explicit,
but the future agent may need to decline questions outside their scope. The course
leaves the allocation mechanism and tool boundaries to the team.

## Implemented offline interfaces

Source: [allocator.py](../src/dss5105/allocator.py). These functions consume valid,
already-resolved simulator batches and workshop profiles. They do not parse chat,
resolve IDs, validate arbitrary user payloads, or persist business decisions.

### `eligible_workshops(batch, workshops)` - course-provided helper

- Input: batch category and pieces, plus the workshop mapping.
- Output: eligible Workshop objects.
- Purpose: enforce ACTIVE status, product capability, and any per-batch limit.
- Non-goals: delivery promises, ranking, capacity reservations, or chat exclusions.
- Failure behavior: no eligible workshops returns an empty list. The allocator
  calls this helper directly; do not duplicate the rule.

### `estimate_delivery(batch, workshop, queues)`

- Input: a resolved batch with pieces, sent date and due date; a Workshop;
  current queue days keyed by workshop ID.
- Output: `DeliveryEstimate` with workshop ID, queue days, process days, transport
  days, unadjusted turnaround days, expected turnaround days, lateness days,
  defect risk, and total batch cost.
- Purpose: provide a common numerical basis for candidate comparison.
- Non-goals: eligibility checks, candidate selection, a guaranteed calendar ETA,
  or prediction of a hidden closure.
- Assumptions: processing is pieces divided by capacity; expected rework follows
  the harness's batch-defect model. The passed queue snapshot is authoritative.
- Failure behavior: missing fields or queue entries raise errors; invalid profile
  data such as zero capacity is not repaired. A late estimate remains a valid
  result, not an exception. User-input validation belongs in the future adapter.

The `lateness_days` field is the positive part of expected turnaround minus time
until due. It is not expected tardiness or late probability. All delivery estimates
in the current allocator come from this function; simulator outcomes are separate
measurements produced by the course harness.

### `rank_candidates(batch, workshops, queues, weights, scales)`

- Input: resolved simulator data, `ObjectiveWeights`, and optional `ScoreScales`.
- Output: sorted `CandidateScore` rows containing a delivery estimate, weighted
  lateness/defects/cost components, and a total score.
- Purpose: rank eligible workshops using the objective configuration.
- Non-goals: chat constraints, eligibility explanations for excluded workshops,
  fairness optimization, split plans, or committing an allocation.
- Failure behavior: an empty candidate set returns an empty list. Weights must
  be finite, nonnegative, and not all zero; scales must be finite and positive.
  Invalid configurations raise `ValueError` when constructed.
- Tie-breaking: expected turnaround, then workshop ID, for every configuration.

The score definition and scale assumptions are in
[ALLOCATION_ENGINE.md](ALLOCATION_ENGINE.md). Changing a policy name does not
change allocation logic; only configuration changes the objective.

### `make_allocator(weights, scales)` and `earliest_finish(...)`

- Input: `make_allocator` binds weights and scales; its returned callback accepts
  `(batch, workshops, queues)`. `earliest_finish` accepts that callback signature
  directly and uses unadjusted turnaround as its criterion.
- Output: a workshop ID for the current batch.
- Purpose: supply a decision to the course simulator.
- Non-goals: language understanding, human confirmation, or modifying queue state.
- Failure behavior: both raise `NoEligibleWorkshop` when no candidate exists. The
  original simulator has no return value for defer, split, or escalate.

## Dispatch adapter increment

The structured preview boundary is specified in
[DISPATCH_CONTRACT.md](DISPATCH_CONTRACT.md). It finalizes resolution, exclusions,
date handling, request preferences, independent queue snapshots, and preview
failure states. It composes the offline tools; it is not free-text extraction or
a durable allocation service. The remaining proposed interfaces below describe
the later agent and persistence layers.

The [Streamlit page](STREAMLIT_APP.md) calls this preview boundary directly. Its
custom sliders change configuration without changing allocation logic. Its demo
confirmation is session-only UI behavior, not an implementation of `commit_allocation`.

Natural-language extraction and multi-turn patch validation are specified in
[INTAKE_CONTRACT.md](INTAKE_CONTRACT.md) and implemented in `intake.py`. The model
extracts quoted fields; deterministic code invokes the preview service. It does
not autonomously choose among registered tool calls or perform numerical work.

The opt-in live evaluation boundary is defined in
[CHAT_EVALUATION.md](CHAT_EVALUATION.md) and implemented by `evaluate_chat.py`.
It checkpoints raw extraction and tool evidence without committing allocations.

## Proposed agent tools and later extensions

These contracts are design proposals for the next increment. Finalize their schemas
and write relevant tests before implementation. Shared inputs should carry a resolved
request, its source text, requester, requested date, constraints with provenance,
and an explicit state snapshot. Do not infer these from simulator replay outcomes.

| Tool | Input | Output | Purpose | Non-goals | Failure behavior |
|---|---|---|---|---|---|
| `resolve_order` | Reference text and optional filters | RESOLVED, AMBIGUOUS, or NOT_FOUND with candidate IDs and supporting fields | Identify the intended order | Choosing an arbitrary match | Return ambiguity or absence for the agent to explain or clarify |
| `get_order` | Order ID | Order fields with source reference, or NOT_FOUND | Retrieve recorded facts | Inventing quotes or past allocations | Distinguish an unknown order from an absent field |
| `query_register` | Capability/status/batch filters and state reference | Matching workshop profiles and queue snapshot | Answer workshop lookup questions | Ranking or interpreting ACTIVE as a delivery guarantee | Empty match is a valid answer; missing state is an explicit failure |
| `check_eligibility` | Resolved batch, workshops, optional workshop ID | Eligibility and reason per workshop | Explain the course helper's exclusions | Soft objective tradeoffs | Reject unresolved inputs; preserve no-eligible as a normal result |
| `estimate_delivery` adapter | Resolved request, workshop ID, as-of date and queue state | Internal estimate plus calendar dates, source references and assumptions | Expose Python estimates to the agent | Silent use of stale state or an unconditional promise | Surface missing state, invalid inputs, and ineligible candidate handling explicitly |
| `check_feasibility` | Resolved request, effective deadline, exclusions, queue state | Whether any permitted candidate meets the estimate criterion, with candidate dates and slips | Explain whether the request can be met under stated assumptions | Automatically committing a late order | Unknown deadline requires clarification; no feasible candidate returns options |
| `rank_candidates` adapter | Resolved request, weights/scales, hard constraints and provenance | Full considered-candidate record, exclusions, ranked scores, and tie-break details | Recommend within the permitted set | Relaxing a hard constraint or committing | All candidates excluded returns a reason and escalation options |
| `evaluate_options` | Resolved request and state, explicitly allowed alternatives | Compared whole-batch/split/load scenarios with assumptions | Examine overload and no-good-option cases | Assuming a split is commercially permitted or simulator-supported | Unsupported scenarios or no improvement must be reported explicitly |
| `commit_allocation` | Confirmed proposed decision, requester, state version and candidate evidence | Persisted allocation ID, timestamp and audit record | Record the approved decision | Contacting workshops or silently changing source orders | Reject stale/unconfirmed decisions; define retry and duplicate handling before building |

The course requires explicit handling of awkward cases; it does not require a
particular split optimizer. The original allocator callback returns one workshop ID,
so split execution needs separate evaluation or a documented harness wrapper.

## Planned behavioral rules and unresolved choices

- Separate hard constraints from objective weights. "Cheapest that still meets the
  date" requires a deadline feasibility constraint; a soft lateness weight alone
  cannot guarantee it. Constraints must record who imposed them.
- Missing or ambiguous requests are clarified, not guessed. Rejecting an ineligible
  suggestion includes a reason and an alternative where one exists.
- Workshop processing cost exists. Customer quoted price and historical allocation
  data do not exist in the supplied files. Do not substitute one for the other.
- An infeasible deadline is explained with supported estimates and options. The
  proposed workflow requires dispatcher confirmation before persisting a decision;
  it must not silently accept lateness or override an instruction.
- Every numerical claim in a chat explanation must trace to a tool result and the
  correct order, workshop, field, and unit. An automated checker is planned.

Before building the chat tools, decide how new requests update queues, whether inbox
cases are independent or sequential, how to handle past deadlines and changed order
quantities, and what confirmation does to state. Current simulation traces are
experiment logs, not confirmed operational allocation records.
