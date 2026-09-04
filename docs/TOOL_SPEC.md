# Tool Specification

The track states that the centre of this project is the tool set, not the chat window,
and that every tool must be specified **before** it is built. This file is that
specification, and it is also a graded deliverable: each tool declares what it takes in,
what it returns, the question it exists to answer, what it deliberately does not do, and
how it fails.

STATUS: proposed. Ratify at the first team meeting, then build against it.

## Design decision: narrow typed tools, not `run_sql`

The track asks us to choose between one flexible `run_sql` tool with full schema access
and a set of narrow typed tools, and to justify the choice against the failure mode we
accept.

We choose **narrow typed tools**. The accepted failure mode is blindness: the agent
cannot answer a question nobody anticipated, and will have to say so. We accept that
because the alternative failure mode is a hallucinated join producing a confident wrong
number, and in this track a fabricated number is the worst possible failure. A refusal
is recoverable; a plausible invented delivery date is not.

Consequence we must live with honestly: when a request needs an unanticipated query, the
right behaviour is to decline, and we count those declines in the evaluation rather than
hiding them.

## Contracts

### 1. `resolve_order`
- **In:** free-text reference (order id, customer name, product, or a vague phrase), optional filters
- **Out:** `{status: RESOLVED | AMBIGUOUS | NOT_FOUND, order_ids: [...], candidates: [...]}`
- **Answers:** which order is this person actually talking about?
- **Non-goals:** does not pick one when several match, and never guesses.
- **Failure mode:** a vague phrase with a large candidate set ("the vests" matches 18).
  Returns AMBIGUOUS with the candidate list so the agent can ask a specific question.

### 2. `get_order`
- **In:** `order_id`
- **Out:** the full order row, or NOT_FOUND
- **Answers:** what are the facts of this order?
- **Non-goals:** no pricing, no quote history, no allocation history. These do not exist
  in the data and the tool must say so rather than return an empty field that reads as zero.
- **Failure mode:** ORD-999 style references to orders that do not exist (see R18).

### 3. `query_register`
- **In:** filters (category, minimum pieces, status, `can_take_by` date)
- **Out:** matching workshops with capability, capacity, queue, status and batch cap
- **Answers:** "who can take 1,500 crewnecks this week?"
- **Non-goals:** does not rank or recommend. Facts only.
- **Failure mode:** empty result when no shop qualifies. Empty is a valid answer and
  must be surfaced as "nobody", not as an error.

### 4. `check_eligibility`
- **In:** `order_id` or `{category, pieces}`, optional `workshop_id`
- **Out:** per workshop `{eligible: bool, exclusion_reason: str | None}`
- **Answers:** can they make it, are they allowed to take it, is the batch within their limit?
- **Non-goals:** says nothing about speed, cost or quality.
- **Failure mode:** none expected. This wraps `eligible_workshops()` from the shared
  harness so our decisions and the simulator can never disagree. **Do not reimplement
  the rule.** The `exclusion_reason` is ours and is what powers refusals and the greyed
  rows in the UI.

### 5. `estimate_delivery`
- **In:** `order_id`, `workshop_id`, `as_of` date
- **Out:** `{queue_days, process_days, transport_days, eta_date, defect_adjusted_eta, cost, slip_vs_due}`
- **Answers:** if we send it there today, when does it come back and what does it cost?
- **Non-goals:** does not decide anything and does not compare workshops.
- **Failure mode:** the estimate is a point value from the profile card. It ignores
  batches allocated later in the same session. State this assumption in the report.
- **This is the only source of delivery numbers in the entire system.**

### 6. `check_feasibility`
- **In:** `order_id`, requested due date
- **Out:** `{feasible: bool, earliest_date, slip_days, best_workshop, per_shop: [...]}`
- **Answers:** can anyone hit this date, and if not, what is the earliest that is real?
- **Non-goals:** does not allocate, and does not choose between late options.
- **Failure mode:** none expected. This is the tool that catches the 12-of-16 infeasible
  requests in [DATA_FINDINGS.md](DATA_FINDINGS.md); it must be called on every
  allocation, not only when something looks wrong.

### 7. `rank_candidates`
- **In:** `order_id`, `objective_weights`, `hard_constraints` (excluded shops and who imposed them)
- **Out:** scored bid table, every row carrying its component numbers and its score
- **Answers:** given what we are optimising for right now, who should get this?
- **Non-goals:** does not commit anything, and does not invent a tie-break rationale.
- **Failure mode:** all candidates excluded by constraints. Must return an empty ranking
  plus the reason, so the agent escalates with options instead of quietly relaxing a
  constraint the boss imposed.
- The objective lives **here**, as data. Never as a branch in allocation logic.

### 8. `evaluate_split`
- **In:** `order_id`, maximum number of shops
- **Out:** candidate split plans with per-shop pieces and a combined completion date
- **Answers:** does splitting the batch actually get it back faster? (see R23)
- **Non-goals:** does not decide whether splitting is acceptable commercially.
- **Failure mode:** splitting often does not help, because `pickup_lead_days` is charged
  per batch. Returning "no, and here is why" is a correct answer.

### 9. `commit_allocation`
- **In:** `order_id`, `workshop_id`, ranked bid table, constraints applied, requester, rationale
- **Out:** the persisted audit record with a timestamp and id
- **Answers:** what did we decide, and how does a human reconstruct it in six weeks?
- **Non-goals:** does not send anything to the workshop and does not modify orders.
- **Failure mode:** this is the only tool with a side effect. **Blast radius:** it writes
  one allocation record. It must be confirmed by the dispatcher before it fires, it is
  append-only, and every record stores the full candidate table, not just the winner.

## Invariants

1. **Arithmetic never happens in the model.** Every numeral shown to a user traces to a
   tool output. We check this automatically; see [EVALUATION_PLAN.md](EVALUATION_PLAN.md).
2. **Eligibility is checked before commitment, always.** Choosing an ineligible workshop
   raises in the simulator. It is an error, not a bad score.
3. **Ambiguity is asked about, never guessed.**
4. **Absent data is declared absent.** There are no prices, no quotes and no allocation
   history in this dataset. Saying so scores higher than inventing a plausible figure.
5. **Constraints record who imposed them.** "No QuickStitch this week" is the boss's
   instruction (R12) and the audit record must say so.
