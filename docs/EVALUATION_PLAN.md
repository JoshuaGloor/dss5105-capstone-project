# Evaluation Plan

`Evaluation.pdf` carries 15% of the grade on its own and feeds the 35% problem-solving
score. The spec says plainly that inflated numbers cost more marks than low ones, and
that teams presenting only successes score poorly. Plan accordingly: we are optimising
for defensible evidence, not for a good-looking table.

Write this evaluation set **before** the system. It defines what "working" means.

## Required checklist

Every line below is a literal requirement. Tick them off.

- [ ] Run the shared simulator `track2/harness/simulate.py`
- [ ] Report our **primary** objective
- [ ] Report at least **one other** objective
- [ ] Report **one hybrid** (weighted mix), with the weights justified
- [ ] All of the above against **all three** baselines
- [ ] At least one `--shock` run
- [ ] Report **the cases where a baseline still wins**
- [ ] State what our system adds over a **ten-line heuristic** (or honestly, that it adds nothing yet)
- [ ] Results on **all 30** requests in `dispatch_requests.txt`, broken down by behaviour
- [ ] Judge **decision** and **explanation faithfulness** separately
- [ ] **At least 10** failure cases analysed individually (we target 15)
- [ ] What we measured and why that metric
- [ ] How the evaluation set was built, and why it is not rigged in our favour
- [ ] Per-category breakdown
- [ ] What we would measure with more time
- [ ] If we tuned on the evaluation set, say so and report a held-out result too

## Metrics

From the harness: mean turnaround, p90 turnaround, % late, % defect, total cost, max
workshop share (our fairness proxy).

Added by us: **pieces-weighted expected defect rate** of the chosen shops. The harness
draws defects stochastically per batch, so its `% defect` is partly RNG rather than
allocation quality. We report both and explain why. The track explicitly invites arguing
with the harness given evidence.

Also added: **slip against the requested date**, because 12 of the 16 allocatable chat
requests cannot hit the date they ask for (see [DATA_FINDINGS.md](DATA_FINDINGS.md)).
An allocation that is on the efficient frontier but silently 25 days late is not a good
answer.

## Explanation faithfulness, measured automatically

This is our strongest differentiator and it directly targets the failure the track marks
hardest. The requirement is that every number in an explanation traces back to a tool
output.

Method: log every tool call and its outputs for a request. Extract every numeral and
date from the agent's user-facing explanation. Assert each one appears in that request's
tool-output set (with tolerance for rounding and formatting).

Report: percentage of numerals that trace to a tool call, plus every violation
individually. A right allocation with an invented justification counts as a **failure**,
so decision correctness and faithfulness are scored on separate axes and reported in a
two-by-two table.

## The 30-request behaviour taxonomy

PROPOSED, NOT RATIFIED. These labels are one person's reading. Do **not** treat them as
ground truth, and do not show them to the other labellers before independent labelling
(see the protocol below), or we lose the inter-rater evidence.

| Behaviour | Count | Requests |
|---|---|---|
| ALLOCATE | 16 | R04 R06 R07 R09 R12 R16 R17 R20 R21 R22 R23 R25 R26 R27 R28 R30 |
| CLARIFY | 7 | R01 R03 R05 R10 R15 R19 R29 |
| REFUSE | 4 | R08 R11 R14 R24 |
| DECLINE | 3 | R02 R13 R18 |

### The four refusals, each a different rule

| Req | Asked for | Correct refusal |
|---|---|---|
| R08 | ORD-073 (400 hoodies) to FreshStart | 400 exceeds the 300-piece trial cap |
| R11 | ORD-008 to OldMill | OldMill status is SUSPENDED |
| R14 | ORD-103 scarves to QuickStitch | QuickStitch makes TOPS only |
| R24 | ORD-015 to Little Loom | ORD-015 is vests (TOPS); Little Loom makes ACCESSORIES only |

Each refusal must carry the reason **and** an alternative.

### The three declines, each failing differently

| Req | Asked for | Why we cannot answer |
|---|---|---|
| R02 | Which workshop handled Harbor Knits last October | No allocation history exists in this data |
| R13 | The price quoted to TrendCart on ORD-120 | No price or quote column exists |
| R18 | Movement on ORD-999 | No such order in the dataset |

Three distinct messages, not one generic "I do not know".

### Sub-labels that overlay ALLOCATE

- **INFEASIBLE_DEADLINE** (12 of 16): must allocate *and* report the slip with the
  earliest achievable date.
- **Hard constraint:** R12 (no QuickStitch this week, imposed by Boss), R25 (not
  BudgetWorks, imposed by Mei). The record must name who imposed it.
- **Objective override in natural language:** R09 (fastest, cost no object), R21
  (cheapest that still makes Apr 13), R27 (lowest defect rate). These are three
  different weight vectors stated in English, and they are the bridge between the chat
  surface and the allocation engine.
- **Split request:** R23.

## How we show the set is not rigged

1. **Independent labelling.** Three team members label all requests separately, without
   discussion and without reading the table above.
2. **Report raw agreement and Cohen's kappa before adjudication.** Publish the
   disagreements. Requests where humans disagreed are exactly where the system should be
   allowed partial credit, and saying so is worth more than a clean 100%.
3. **Adjudicate** disagreements in a recorded meeting, then freeze the labels.
4. **Held-out set.** Write 30 new chat requests in the same style, labelled by the same
   protocol, and never look at them during development. Report both numbers. The data is
   explicitly extensible provided we document what we changed.

## Ablation: what does the LLM actually add?

The direct answer to the spec's question. Four systems, same 120 orders and same 30
requests:

| System | Simulator | 30 requests |
|---|---|---|
| A. Ten-line heuristic | yes | cannot run: no language surface |
| B. Tools + scorer, no LLM | yes | cannot run |
| C. LLM, no tools (model does its own arithmetic) | yes | yes |
| D. Full system | yes | yes |

Expected and acceptable outcome: A and D score similarly on the simulator, because
allocation quality comes from the scorer. C should be visibly worse on faithfulness and
probably on allocation too. If A matches D on the simulator, **say so plainly** and
locate our contribution in the chat surface, the refusals, the constraint handling and
the audit record, which A cannot do at all.

## Failure analysis

At least 10 cases, individually analysed; target 15. Assign each to a category
(extraction, resolution, eligibility, estimation, objective interpretation, faithfulness,
UX) and record what went wrong, why, and what would fix it. Start collecting these from
the first working prototype. Do not leave this to the final week; it is the section that
most visibly separates a strong report from a weak one.
