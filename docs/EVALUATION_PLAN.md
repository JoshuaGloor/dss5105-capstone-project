# Evaluation plan

Source of mandatory requirements: Spec v4 p. 6 and Tracks v3 pp. 6-7. Evaluation
quality carries 15% of the project rubric; the simulator does not produce a final
course grade. This document is a plan, not a claim that the complete system has
already been evaluated.

## Course requirements and current evidence

| Requirement | Current status |
|---|---|
| Use the shared simulator against all three provided baselines | Initial offline runs complete; reproducible runner and traces available |
| Declare a primary objective at Sprint 1 | Not selected; current presets do not constitute a team declaration |
| Report primary, another objective, and a justified weighted hybrid | Lateness, defects, and hybrid experiments available; final choice and weight rationale pending |
| Include at least one shock run | Initial shock run complete; broader robustness analysis pending |
| Beat all three baselines on the primary objective and report where baselines win | Initial late-rate results are favorable; primary not declared; metric tradeoffs recorded in DATA_FINDINGS.md |
| Compare with a short heuristic and explain the system's added value | earliest_finish implemented; full-system added value not yet measured |
| Evaluate all 30 supplied chat requests by behavior | First live initial-response run complete; independent gold annotations and held-out evaluation pending |
| Judge decisions and explanation faithfulness separately | Behavior and tool-field integrity checked separately; full explanation/UX review still pending |
| Explain metrics, evaluation-set construction, per-category results, and limitations | Initial simulator method documented; full report pending |
| Analyze at least 10 failure cases individually | Pending; collect cases as features are built |
| State what would be measured with more time | Planned in final report |
| If development used the evaluation set, disclose it and provide a held-out result | Supplied data has already been inspected and used in development; held-out evaluation pending |

A tool specification, usable interface, and auditable output are also core Track 2
capabilities. Completing the simulator rows does not complete the project.

## Allocation experiments

Use the commands and definitions in [ALLOCATION_ENGINE.md](ALLOCATION_ENGINE.md).
Current observations and both scenario tables are in [DATA_FINDINGS.md](DATA_FINDINGS.md).
Each policy run starts fresh queues. Preserve the seed, configuration, scales,
source versions, and raw per-order evidence when reporting results.

| Metric | Meaning | Important limit |
|---|---|---|
| Mean turnaround | Average dispatch-to-delivery duration | Not mean days overdue |
| P90 turnaround | The course report's upper-quantile statistic | Retain the course indexing convention |
| Late fraction | Fraction of batches delivered after their due date | Does not measure lateness severity |
| Defect fraction | Fraction of batches with a simulated defect event | Not the fraction of garments defective |
| Total cost | Sum of pieces times chosen workshop unit cost | Not customer selling price or profit |
| Maximum workshop share | Largest share of assigned pieces | Concentration proxy; eligibility and capacity differ |

Report the original metrics even if adding better-suited ones. The separate
[weight-search runner](WEIGHT_TUNING.md) adds batch-average expected defect probability.
Actual overdue duration and pieces-weighted defect exposure remain proposed additions.
Distinguish these definitions:
weighting workshop defect probabilities by pieces does not measure actual defective
garment counts in the harness. Conditional expected exposure avoids immediate defect
sampling noise, but allocation paths still depend on past random events.

The scoring penalty is not the evaluator: it uses a continuous point estimate of
lateness, while the simulator uses sampled outcomes and rounded completion dates.
A good internal score does not establish a good realized result or global optimum.

Next experiments should inspect changed allocations, baseline wins, and sensitivity
to scales and additional scenarios. Initial weight and seed sensitivity results are
documented in [WEIGHT_TUNING.md](WEIGHT_TUNING.md). Avoid presenting tuning on this supplied replay as
held-out performance. Use documented additional data/scenarios and freeze any held-out
set before tuning against it. Preserve the shared run for cross-team comparison.

For shock analysis, disclose that target selection consumes RNG state and changes
subsequent defect draws. Current queue-aware policies do not explicitly detect a
closure. A causal estimate of closure impact or a claim of failure detection needs
additional controlled evidence, not just the normal/shock table difference.

## Chat evaluation: define the rubric before implementing language intake

The [dispatch preview](DISPATCH_PREVIEW.md) now supports structured inputs and an
independent snapshot convention specified in [DISPATCH_CONTRACT.md](DISPATCH_CONTRACT.md).
Its draft fixtures are implementation examples, not gold labels or evidence of
language understanding. The generated prototype bundles their tool outcomes.
Generate a blank independent annotation sheet with
`uv run python -m dss5105.prototype --annotations results/annotations-rater-a.csv`.
The generator never copies predicted outcomes into expected-label columns.

The [Streamlit page](STREAMLIT_APP.md) now has offline AppTest coverage for request
selection, live custom weights, exception states, preference precedence, and demo
confirmation invalidation. These are application behavior checks using draft
structured inputs, not NLP accuracy, human usability results, or durable commitment
tests. Browser layout still needs manual review in Chrome.

Natural-language intake now has fake-model and AppTest coverage for typed extraction,
literal evidence validation, clarification state, preserved constraints, explicit
retry, and absence of provider calls on ordinary reruns. These do not measure real
extraction accuracy. The [intake contract](INTAKE_CONTRACT.md) distinguishes those
checks from semantic correctness/completeness. The first live run is documented in
[CHAT_EVALUATION_RESULTS.md](CHAT_EVALUATION_RESULTS.md), with a frozen draft rubric,
raw outputs and manual review of errors that the automated checks missed.

The simulator never reads `dispatch_requests.txt`. Run these requests through the
chat application and retain the conversation, tool inputs/outputs, structured
request, decision, and explanation for each case.

| Behavior | What to judge |
|---|---|
| Complete request | Correct extraction, resolution, constraints, objective interpretation, eligibility and justified recommendation |
| Ambiguous or incomplete request | Targeted clarification; no guessed order, quantity, or deadline |
| Ineligible suggestion | Correct refusal reason and an eligible alternative where possible |
| Unanswerable question | Explicit limitation tied to missing records or fields; no invented answer |

Overlay labels should capture deadline infeasibility, exclusion provenance, objective
preferences, and split requests. Behaviors need not be mutually exclusive: a request
may be resolvable but infeasible, or need clarification before a recommendation.

Do not assume a single gold workshop for every valid request. Some outcomes admit
several defensible choices; a rubric should check constraints and evidence as well
as any reference policy. For a requested deadline, feasibility must use the permitted
candidate set. An instruction such as R21's "cheapest shop that can still make" the
date is a constrained request, not merely a different soft weight vector.

The first increment records conservative choices below in the dispatch contract.
Review them as a team before freezing annotations:

- Whether each inbox case starts from the same 2026-04-01 snapshot or earlier cases
  update shared queues. The data does not itself define a commitment sequence.
- How message fields override CSV fields, and which conflicts require clarification.
- How past deadlines, unknown dates, and infeasible requests should be handled.
- When the agent may recommend alternatives and when a human must confirm a decision.

Do not pre-label every impossible deadline as "allocate anyway". The system must
explain the conflict and offer permitted options without silently changing the task.

## Proposed annotation protocol

The following is a team methodology proposal, not an extra literal course minimum.
Earlier model-generated label counts and feasibility tables are not ground truth
and are excluded from the rubric.

Have multiple team members independently label the requests against the raw data,
recording supporting rows and acceptable behaviors. Record prior exposure to earlier
labels rather than claiming annotators are blind if they have already seen them.
Discuss disagreements only after independent labels are saved, then freeze an
adjudicated rubric and document the reasoning.

Report agreement before adjudication. Cohen's kappa applies to two raters; use
pairwise Cohen's kappa or an appropriate multi-rater measure such as Fleiss' kappa
if more raters participate. Define how multi-label behaviors are encoded before
calculating agreement. These statistics are planned, not already measured.

Prepare additional labeled requests that are held out from prompt and tool tuning.
Set their size and category coverage explicitly in the evaluation design; the
course does not prescribe an additional set of exactly 30 chat requests.

## Explanation faithfulness

The live runner now checks candidate-bound numerical display fields and selected
workshop eligibility. This is a partial tool-integrity audit, not a complete
explanation-faithfulness checker. The full checker should link claims to the right tool field,
request, workshop, units, and state snapshot. Merely finding the same number anywhere
in a tool-output log is insufficient: the right value attached to the wrong workshop
is still false. Check non-numerical claims such as eligibility and imposed constraints
as well. Specify permitted rounding and date formatting, and inspect violations.

Report decision correctness and explanation faithfulness separately, including cases
where a correct recommendation has an unsupported explanation. The course treats a
right allocation with an invented justification as a failure. Report both coverage
and errors; an agent that omits all numerical claims has not necessarily explained
the decision well.

## What does the language layer add?

Compare the short heuristic with the weighted allocator on structured simulator
inputs. Then evaluate the complete chat system on extraction, clarification,
constraint handling, refusal, and faithful explanation. Where useful, compare its
structured requests with manually verified structured inputs passed to the same
allocator; this helps isolate language errors from allocation errors.

A Python heuristic does not parse chat by itself, but ordinary code can enforce
constraints once supplied in structured form. Do not claim that only an LLM can
handle exclusions or refuse an ineligible workshop. If the full system uses the
same allocator and receives identical inputs, do not attribute its numerical policy
performance to the LLM.

The previous proposal to let an LLM do arithmetic is not part of the implementation
or default tests. All product arithmetic remains in tools. Any provider-based
experiment must be explicitly planned and authorized; `uv run pytest` stays offline
and live tests remain opt-in.

## Failure analysis and final reporting

For each analyzed failure, record the input, expected behavior and evidence, observed
behavior, failure category, consequence, and possible fix. Categories can include
extraction, resolution, constraints, estimation, scoring, explanation, state handling,
and UX. Include baseline wins and policy tradeoffs separately from software bugs.
If too few genuine failures are observed, design meaningful stress cases and disclose
that construction; do not fabricate failures to fill a quota.

The final report should distinguish implemented behavior, observed results, proposed
improvements, and untested assumptions. Do not mark required evaluation complete
merely because the corresponding code or plan exists.
