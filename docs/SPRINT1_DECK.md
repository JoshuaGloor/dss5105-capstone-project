# Sprint 1 deck: content draft

Working draft of `Presentation_Group11_Sprint1` (.pptx or .pdf, upload by 15:00 on
Fri 16 Oct 2026; live 5 minutes + 2 minutes Q&A, hard stop). Slide order follows
Spec v5 p. 3. Every number on a slide comes from a retained evidence file named
under that slide; do not type a number into the deck that is not listed here.

Status: the primary objective below is a **proposal for team sign-off**. Once the
team agrees, update the architecture SVG caption and the objective rows in
PLAN.md and EVALUATION_PLAN.md in the same change.

Evidence files:

- `V3` = [V3_EVALUATION.md](V3_EVALUATION.md) / [evidence/data-v3.json](evidence/data-v3.json)
  (ten course seeds 5105-5114, normal paired controls and shock).
- `MS` = [MARGIN_STUDY.md](MARGIN_STUDY.md) / [evidence/margin-study.json](evidence/margin-study.json)
  (development seeds 6000-6009, course seeds 5105-5114).
- `CHAT` = [CHAT_EVALUATION_RESULTS.md](CHAT_EVALUATION_RESULTS.md) (pre-v3, historical).

Timing budget: 8 slides, 5:00 total.

---

## Slide 1 - Title (0:15)

**Quick-Response Subcontracting Desk**
Group 11 / Track 2 / Sprint 1
Members: _names to fill in_

One line: *Understand the request. Calculate with tools. Confirm with evidence.*

Speaker: name the track and the one-line idea, move on.

---

## Slide 2 - Problem and proposed solution (0:40)

**Problem.** Today one chat message is the whole decision:
"@Chen - order 042, 1,500 crewnecks. Send it to QuickStitch, need it back by the 19th."
Three questions live in one dispatcher's head:

1. Can they make it? (product category)
2. Can they take it now? (queue + capacity)
3. Are they allowed to? (suspended shop, trial batch cap)

Get one wrong and the batch bounces back a day later; in a 10-day cycle that is
the margin gone. Nothing is written down.

**Solution.** A dispatch desk that reads the chat request, asks when something is
missing, checks eligibility and delivery with Python tools, recommends a workshop,
and saves the decision with its evidence after a human confirms.

Speaker: the chat is the interface we replace, so the language layer is not
optional. The LLM reads and asks; it never calculates.

---

## Slide 3 - Architecture (0:40)

Image: [sprint1-architecture.svg](sprint1-architecture.svg) (update caption to the
declared objective before export).

Three boundaries to say out loud:

- **Language boundary**: LLM extracts intent, references and constraints with
  quoted source spans; Python validates every field. Malformed output fails closed.
- **Deterministic boundary**: course `eligible_workshops()`, delivery estimate
  (queue + processing + transport + expected rework), one configurable scorer.
  Every numeral shown to the user is formatted by a tool.
- **Confirmation boundary**: a preview is not a reservation. Confirm revalidates
  the queue state, writes one SQLite record and updates queues atomically.

The same scorer runs inside the shared simulator (no LLM in the allocator).

---

## Slide 4 - Primary objective: minimise lateness (1:00)

**Declaration: minimise lateness**, measured by `% late` and `late days`.

Why this objective:

- **Business**: quick response sells speed. A reorder due in ten days that comes
  back late loses the sale; a defect can be reworked, a missed date cannot.
- **Evidence**: it is the only objective where we clearly beat all three baselines
  on the course metric without an asterisk.

| Candidate | What we measured (10 course seeds) | Verdict |
|---|---|---|
| Lateness | 1.7% late, 0.18 late days vs random 34.2% / 6.13 | Beats all three, normal and shock |
| Defects | Pure-defects: 2.9% def pcs but 95.1% late | Fails the "late no worse than random" guardrail |
| Robustness | Our shock change +0.25 pp late; cheapest +0.00 pp | Cheapest is already 92% late, so it cannot get worse; metric ceiling |
| Fairness | Max share 26.2% vs random 22.6% | Not implemented; random already sits near the floor |

Sources: V3 paired normal controls and shock-minus-normal table; defects row from
V3 normal controls.

**Other objective (required)**: minimise defects, run as a comparison. Finding to
report: chasing quality sends work to small, slow shops whose queues explode.

**Hybrid (required)**: lateness first, defects second, with a deadline safety
buffer. Weights frozen by a pre-registered protocol on development seeds before
course seeds are run (Sprint 2). The current 0.7/0.3 preset is **retired**: it is
18.8% late on the course seeds (V3), which no dispatcher would accept.

Speaker: we chose the objective the business is paying for, and we say where it is
weak (next slide and Q&A).

---

## Slide 5 - Business value (0:30)

- **No bounced batches**: eligibility is checked before any recommendation, using
  the course's own rule, so an ineligible allocation cannot be proposed.
- **Fewer late batches**: in the shared simulator, checking queue + processing +
  transport first gives 1.7% late against 34.2% for a random eligible shop
  (V3, normal controls). This is simulator evidence, not a field result.
- **Decision on record**: every confirmed allocation stores the request, candidates,
  estimates, constraints, who imposed them, and who confirmed.
- **Explicit bad news**: impossible dates get the earliest achievable date and the
  options (split, accept lateness, escalate), not a silent allocation.

Honest cost: speed is not free. The lateness policy spends 115,592 per replay vs
85,960 for cheapest (V3 normal controls, cost column).

---

## Slide 6 - Sprint 1 progress (0:45)

| Policy (10 course seeds) | % late normal | late days normal | % late shock | late days shock |
|---|---|---|---|---|
| random | 34.2 | 6.13 | 38.2 | 7.17 |
| greedy_biggest | 84.3 | 26.53 | 84.9 | 28.05 |
| cheapest | 91.8 | 81.92 | 91.8 | 84.12 |
| earliest finish (simple rule) | 1.7 | 0.18 | 1.9 | 0.19 |
| **ours: lateness** | **1.7** | **0.18** | **1.9** | **0.18** |

Source: V3 paired normal controls and shock tables.

Two honest findings:

- A ten-second rule (earliest finish) **ties** us on lateness. Our value is not a
  smarter lateness formula; lateness is near its floor (two batches of 2,000
  accessories cannot be made in their window; MS finding 2).
- What the configurable scorer adds: a deadline buffer that spends slack on price
  cuts cost 7.7% and late days 23% for about one extra late batch per ten normal
  runs, four under shock (MS, `cost_buffer10`: 106,668 vs 115,592; 0.138 vs 0.180
  late days).

Also working today: Streamlit desk, all 30 inbox requests reach their intended
state on hand-authored inputs (V3 fixture replay), saved-plan confirmation with
SQLite, 278 offline tests.

Speaker: fixture replay is not language accuracy; the live chat rerun is Sprint 2.

---

## Slide 7 - Risks and key assumptions (0:40)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM states a number no tool produced | Medium | High | LLM extracts only; tools format every numeral; automated check binds each value to its candidate and field |
| Misread request: guessed order, wrong clarification (first live run: one refusal blocked by an unneeded question, R14) | High | High | Independent gold labels, held-out requests written before tuning, fail-closed validation |
| Tuning to the 120 supplied orders | Medium | Medium | Separate development seeds; freeze choices before course seeds; disclose reuse |
| Simulator is simpler than a factory (one unit of work, no stages, fixed capacity) | Certain | Medium | State it; keep the default run as yardstick; argue with evidence where it matters |

| Assumption | How we check it |
|---|---|
| Inbox requests are judged on the 1 April queue snapshot, independently | Dispatch contract; same snapshot for every comparison |
| A defect costs rework time (half the processing time), as in the harness | Taken from `simulate.py`; revisit if harness changes |
| `cost_per_piece` is subcontract cost, not customer price | Quote questions are declined as unanswerable |
| A human confirms every allocation; nothing is auto-sent | Confirmation revalidates state before saving |

---

## Slide 8 - Sprint 2 roadmap and success criteria (0:30)

| Work (owner) | Priority | Success criterion by 30 Oct |
|---|---|---|
| Live chat rerun on Data v3 inbox + fix clarification defects (_owner_) | High | 30/30 run end to end; behaviour judged against independently labelled answers, reported per kind |
| Evaluation set (_owner_) | High | >= 30 questions verified against data files, including ambiguous, unanswerable and feasibility cases; >= 10 held-out, written before tuning |
| Register query + overload probe tools (_owner_) | High | "Who can take 1,500 crewnecks this week?" answered from tools only |
| Hybrid freeze (_owner_) | Medium | Weights and scales fixed on dev seeds, then one course-seed run; rationale on one slide |
| Faithfulness check (_owner_) | Medium | 0 displayed numerals without a matching tool field |
| Demo video (_owner_) | Medium | Recorded flow: request, clarification, refusal, impossible date, confirm |

Primary-objective success criterion (final): beat random, greedy_biggest and
cheapest on both `% late` and `late days`, normal and ten-seed shock, and report
where earliest finish and cheapest still win.

---

## Q&A preparation

- *"The track headline is the shock test. Why not robustness?"* Our queue-aware
  policy already routes around the closure: an oracle that knows which shop closes
  and when improves shock late rate by only 0.08 points (MS finding 1). And the
  metric rewards policies that are already late: cheapest changes by 0.00 points.
  We report robustness anyway, over ten seeds.
- *"If earliest finish ties you, what does your system add?"* Three things the rule
  cannot do: read the chat and ask, respect request constraints and refuse bad
  suggestions, and move along the cost/late-days tradeoff by configuration. We say
  plainly that on lateness alone it adds nothing yet.
- *"Why is your hybrid not in between the other two?"* It does not have to be; the
  first one used slack greedily and ran late. The Sprint 2 hybrid adds a deadline
  buffer and is chosen on development seeds before the course seeds are used.
- *"How do you know a number was not invented?"* The LLM never writes numbers.
  Displayed values are tool fields, checked per candidate and per field.
- *"Why is the fixture replay 30/30?"* Because the inputs are hand-authored. It
  tests the tools, not language understanding; the live run is the real test.
