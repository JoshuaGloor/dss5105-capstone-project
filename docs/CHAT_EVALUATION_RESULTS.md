# First live inbox evaluation

All 30 supplied requests completed through the real model and Python tools.
The frozen draft checks passed for 29 requests. R14 failed: an unnecessary
quantity question prevented the required workshop refusal. Manual review also
found problems outside the draft checks, so **29/30 is not overall accuracy**.

This report describes the first run without prompt tuning or paid retries.
The observed issues remain open; this evaluation did not change dispatch behavior.

## Run and evidence

| Setting | Value |
|---|---|
| Started, UTC | 2026-09-18T04:02:02.583973+00:00 |
| Model from existing configuration | `openai:gpt-5.6` |
| Intake | `intake-v1`; current structured patch prompt |
| Requests | All supplied inbox messages, one initial response each |
| State | Independent 2026-04-01 snapshot for every request |
| Objective | Lateness preset, overridden by explicit request preferences |
| Retries / timeout | No automatic retry; 30-second provider timeout |
| Summed case elapsed time | 135.538 seconds |
| Provider-reported tokens | 27,943 input; 6,573 output; 34,516 total |
| Raw artifacts | `results/chat-first/` (Git-ignored) |

The manifest saves the rubric before calls, source and code hashes, exact system
prompt/schema and model settings. Each `Rxx.json` contains the model patch, raw
response content/tool calls, token usage, validated conversation and complete tool
preview. `source_snapshot.json` preserves the evaluated source files and lockfile.
`summary.json` contains machine-computed counts. File and course-data hashes were
verified against the manifest after the run. No course data or queues were changed.

Manifest SHA-256:
`d7d4676fc53a22fd1848e4f9a3e0040b71e3693b435c6c8769881096cb177af9`

Draft rubric SHA-256:
`ff55612f36382ef318d5bc81f37cc5d796253ba9fde3c6fcd5d716749739daba`

See [the run contract and reproduction command](CHAT_EVALUATION.md). A rerun costs
tokens, requires a fresh output directory, and may differ because model output is
not deterministic. Opening the saved JSON files or this report makes no API call.
No currency cost is estimated here; use provider billing for actual charges.

## Automated checks, with denominators

| Check | Result | Meaning |
|---|---|---|
| Model/validation/tool completion | 30/30 | No provider, parser, validation or tool exception |
| Required extraction checks | 30/30 | Only the fields and needs explicitly listed in the draft rubric |
| Expected behavior/flags | 29/30 | R14 asked for quantity instead of refusing QuickStitch |
| Combined draft rubric | 29/30 | Does not cover every semantic error or question-quality issue |
| Tool integrity | 30/30 | Candidate eligibility, hard exclusions, choice membership and display consistency checks |
| Numerical display coverage | 474 fields in 17 requests with candidates | Each formatted value checked against its own candidate/field |

Requests without candidates contribute no numerical display checks. This avoids
interpreting a silent or blocked response as successful numerical explanation.
The integrity audit checks tool fields, not a browser rendering or independent
estimator implementation. The application uses deterministic text and display
fields; there is no free-form LLM explanation to grade in this version.

The categories below are disjoint reporting buckets with overlapping properties
checked separately, such as past deadlines or constraints.

| Category | Draft checks passed / attempted |
|---|---|
| Clarification | 10/10 |
| Deadline exception | 8/8 |
| Explicit exclusion | 2/2 |
| Missing records | 2/2 |
| Objective preference | 3/3 |
| Ineligible suggestion | 3/4 |
| Split request | 1/1 |

## What worked in this run

- R08 refused FreshStart's oversized batch; R11 refused suspended OldMill; R24
  refused Little Loom for an unsupported category. Each provided an eligible alternative.
- R12 retained the QuickStitch exclusion and attributed it to Boss, despite Ravi
  being the speaker. R25 excluded BudgetWorks and attributed that instruction to Mei.
- R21 selected W5 under cheapest-on-time: the permitted candidates were checked
  for the date constraint and minimum cost among on-time options.
- R09 captured fastest turnaround, and R27 captured lowest defects. The latter
  still surfaced its missed deadline instead of presenting an on-time promise.
- R05 requested the unknown revised date. R06 and R16 requested clarification
  of shipping versus delivery. R18 did not invent an unknown order.
- R13 declined to invent a customer quote. R23 recorded the split request and
  explicitly flagged that split planning is unavailable.

These are observed initial responses on supplied development cases, not guarantees
for arbitrary requests or successful multi-turn completion.

## Manual review: failures and weaknesses missed by aggregate counts

### R14: unnecessary clarification blocks a required refusal

Input: "QuickStitch for the scarves on ORD-103?"

The model extracted the correct order, product and suggested workshop, but also
returned `needs=["quantity"]`. The quantity is available in `orders.csv` after
resolving the explicit order ID. The tool treats any pending question as blocking,
so it returned CLARIFY without checking QuickStitch's unsupported category.

The system did not make an unsafe allocation, but failed to perform a useful,
answerable task. The prompt does not clearly distinguish an omitted field that
can be retrieved from an identified order from an explicitly uncertain quantity.
Fix that distinction while preserving clarification for "usual quantities" and
explicit amendments. Add regression coverage before rerunning affected cases.

### R02: historical time interpreted as a delivery deadline

The final DECLINE is correct because prior workshop allocations are absent.
However, the raw patch assigned "last October" to `due_date` and asked for order,
quantity and date-kind clarification. Python could not normalize the phrase and
set `date_uncertain=true`. These fields are irrelevant to the historical question.

The early history branch prevented a wrong recommendation and hid these questions
from the final tool message. The saved draft is nevertheless semantically wrong;
the original draft rubric did not check these extra fields. This is a concrete
reason not to describe required-field agreement as perfect extraction accuracy.
Future checks should include forbidden extra fields and intent-specific needs.

### Repeated questions and premature requests for details

R01, R03, R10, R15, R19 and R29 repeat the order-ID question: the resolver adds it
and then appends the model's identical pending question. R06 and R16 repeat the
shipping/delivery question in different wording. This is a deterministic response
assembly issue, separate from model extraction.

R03, R15 and R19 also ask for quantity before establishing which existing order
is meant. Retrieving the identified order first could avoid unnecessary questions.
Whether those questions block a later ID-only answer has not been tested with
this live model; it is a follow-up test to perform, not an observed live outcome.

### R10: safe blocking, incomplete new-order workflow

The message explicitly describes a new rush order with details to follow. The
system safely asks for details and reserves nothing, but its standard request for
an existing order ID is not a complete new-order intake workflow. Creation of a
new order is outside the current registered-order preview implementation.

### Exception explanations still need improvement

Late whole-batch options share generic text about agreeing a deadline or split
plan. The UI has separate flags, estimates and exclusion reasons, but those do
not constitute a tailored resolution plan. R23 correctly acknowledges unsupported
splitting; it does not solve the split. R16 asks about date semantics before
surfacing the already-past date. Review these flows with teammates before claiming
the full exception-handling requirement is complete.

These are observations and open limitations, not an invented list of ten distinct
failures. The final course failure-analysis requirement remains unfinished.

## Per-request trace index

Workshop is a preview or refusal alternative, never a committed allocation.
"Pass" refers only to the original automated draft checks.

| Request | Tool status | Workshop | Draft checks |
|---|---|---|---|
| R01 | CLARIFY | - | pass |
| R02 | DECLINE | - | pass; manual extraction issue above |
| R03 | CLARIFY | - | pass |
| R04 | NEEDS_REVIEW | W2 | pass |
| R05 | CLARIFY | - | pass |
| R06 | CLARIFY | - | pass |
| R07 | NEEDS_REVIEW | W1 | pass |
| R08 | REFUSE_SUGGESTION | W6 | pass |
| R09 | RECOMMEND | W6 | pass |
| R10 | CLARIFY | - | pass; new-order workflow gap |
| R11 | REFUSE_SUGGESTION | W6 | pass |
| R12 | RECOMMEND | W6 | pass |
| R13 | DECLINE | - | pass |
| R14 | CLARIFY | - | FAIL |
| R15 | CLARIFY | - | pass |
| R16 | CLARIFY | - | pass |
| R17 | NEEDS_REVIEW | W1 | pass |
| R18 | CLARIFY | - | pass |
| R19 | CLARIFY | - | pass |
| R20 | NEEDS_REVIEW | W2 | pass |
| R21 | RECOMMEND | W5 | pass |
| R22 | NEEDS_REVIEW | W1 | pass |
| R23 | NEEDS_REVIEW | W6 | pass |
| R24 | REFUSE_SUGGESTION | W6 | pass |
| R25 | RECOMMEND | W6 | pass |
| R26 | NEEDS_REVIEW | W1 | pass |
| R27 | NEEDS_REVIEW | W2 | pass |
| R28 | NEEDS_REVIEW | W1 | pass |
| R29 | CLARIFY | - | pass |
| R30 | NEEDS_REVIEW | W1 | pass |

## Next acceptance gates

1. Fix retrieval-versus-clarification semantics and duplicate questions. Preserve
   this first-run evidence; label any subsequent results as post-fix development runs.
2. Have teammates independently review annotations and extend checks for unsupported
   extra fields. Freeze held-out wording before further prompt tuning.
3. Test live follow-ups, including an ID-only clarification and a changed delivery
   date that must preserve an exclusion. No such live result is claimed here.
4. Implement durable confirmation and queue updates only after their contract is
   finalized. Current confirmation is still session-only demonstration behavior.
