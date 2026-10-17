# 1. Executive summary

This workstream improves the reliability of the Quick-Response Subcontracting
Desk: a chat assistant that identifies an order, checks workshop eligibility,
uses deterministic delivery/ranking tools, and presents a preview for dispatcher
review. The assigned problem was not simply whether a language model could read
a request. Correct extraction could still produce an unhelpful interaction when
the surrounding agent asked for information already available in an order,
repeated the same question, or asked secondary questions before identifying which
order the user meant.

Three production fixes address those problems. Intake reconciles omitted facts
with registered order data while preserving explicit uncertainty. Dispatch avoids
adding the same standard order question twice. Conversation state distinguishes
pending needs from needs deferred until order identity is established. Tests cover
these decisions and their follow-up/UI lifecycle. These runtime changes are
already committed locally; this preparation does not rewrite their history.

The evaluation also needed repair. The first benchmark contained provisional
development expectations, and some AI review material described stale pre-v3
requests. A request-version audit established exact frozen Data v3 inputs, built
a canonical review packet, excluded invalid reviewer-case combinations, and
combined only explicit assertion-level votes. The current scorer can evaluate
approved assertions independently without inheriting unrelated expectations.
Unsupported prose remains unscored rather than being guessed from keywords.

The final AI-consensus canonical-v2 benchmark has 296 accepted assertions. Of
these, 266 have static scorer support, and 247 are actually evaluable in both
frozen runs. BEFORE has 238 PASS and AFTER 239 PASS. R14 status is the one primary
paired improvement; there are no paired regressions. Six duplicate-clarification
integrity violations are separately absent AFTER. Eight persistent shared-assertion
failures comprise four status-policy disagreements (R18/R20/R28/R30) and four
equal-valued quantity integer/string representation mismatches (R05/R11/R14/R24).
The mismatches do not indicate wrong quantity values, and status-policy
disagreements do not by themselves establish production bugs.

These are narrow, useful findings, not comprehensive correctness or general
accuracy. There is one stochastic model run per version, some raw patches differ,
reviewer independence is self-declared, assertions overlap, and baseline deferred
state is missing. The last full offline suite passed 578 tests with one live test
deselected. On 2026-10-17 the user authorized three local commits and local evidence
packaging; those are complete in the revision containing this explanation.
No live call, frozen evaluation rerun, push, PR, upload or sharing occurred.
Teammate review and external delivery approval remain pending. See
PRE_PUSH_READINESS.md for the execution receipt and local package verification.

# 2. Original system architecture

The initial-turn flow is:

```text
user message
  -> LLM structured intake: a DispatchPatch, not a calculated answer
  -> deterministic validation and reconciliation of conversation state
  -> order resolution, eligibility and queue-aware ranking tools
  -> deterministic response text and structured preview fields
  -> saved recorder evidence and separate offline audit/scoring
```

The LLM quotes and extracts fields, exclusions, intent and potential needs. It
does not perform delivery arithmetic or choose a workshop by invented reasoning.
Python validates literal evidence, normalizes supported inputs, preserves prior
constraints and decides which needs block progress. Registered order data can
supply facts that were omitted, but cannot override an explicit amendment.

The course eligibility helper supplies hard workshop membership. Deterministic
tools estimate delivery, rank permitted candidates using configured weights and
build the preview. Response generation here is principally tool-backed templates
and structured fields, not an unrestricted second LLM answer. A preview is not a
booking. Confirmation and saved-plan behavior are separate application features.

The recorder stores model patches, conversation state, tool outputs and source
hashes. The reliability scorer consumes those saved files offline. It does not
replay the agent or feed labels back into the model. Structured consistency audits
cannot establish everything a user sees or every prose claim's faithfulness.

# 3. The three reliability failures

## 3.1 Redundant quantity clarification - R14

Request: "QuickStitch for the scarves on ORD-103?"

The registered ORD-103 row supplies 2000 pieces; QuickStitch makes TOPS, whereas
the scarf order is ACCESSORIES. The model extracted the order, product and
suggested workshop, but also returned needs=["quantity"]. Before reconciliation,
that pending question blocked dispatch and yielded CLARIFY before the unsupported
workshop suggestion could be refused.

The error was in the agent's handling of extraction, not a missing arithmetic
ability. An identified order already carried the omitted fact. Asking the user
again prevented the system from doing the useful eligibility check.

The fix checks whether the need is retrievable from a uniquely resolved order.
It does not silently replace explicit quantity text, uncertainty, conflicting
values, unclassified legacy blockers or invalid registered data. With the same
recorded raw model patch, AFTER clears the redundant quantity need and reaches
REFUSE_SUGGESTION. Downstream flags also appear, but unsupported semantic flag
concepts are not counted as approved flag successes.

The fix is general reconciliation in intake.py, not an if-R14 rule.

## 3.2 Duplicate clarification

R01, R03, R10, R15, R19 and R29 had observable repeated standard order questions.
Intake had already built a clarification beginning with the order-ID question;
dispatch independently prepended the resolver's identical question. Two correct
local steps produced a poor combined message.

Dispatch now reuses the existing clarification when it starts with that same
resolver question. Otherwise it retains the resolver's question and appends the
distinct clarification. Other needs are preserved. This is a bounded fix for
message assembly; it is not a semantic paraphrase detector.

No six-case list controls production behavior. The rule operates on the resolver
message and request clarification for any matching flow. The six IDs identify
observed evaluation instances, not runtime branches.

## 3.3 Dependency-aware deferred needs

needs contains all pending requirements. deferred_needs identifies only pending
quantity/deadline requirements that may be retrieved after resolving the order.
The questions currently shown are based on:

```text
blocking needs = needs - deferred_needs
```

For example, an ambiguous customer reference may yield needs={order, quantity}
and deferred_needs={quantity}. The user should first identify the order. If the
selected order supplies a valid quantity, Python discharges that need. If the
source field is missing or invalid, quantity becomes a visible blocker instead.

Explicit uncertainty or amendments stay blocking. A later statement can revoke
deferral. Legacy needs without a known deferred classification are not weakened.
Independent needs and exclusions remain intact. Selection, traces and UI reply
rebuilding preserve the state through dataclasses.replace.

Asking everything immediately can burden users with questions the next retrieval
would answer. Deferral improves question order without pretending that unresolved
information is already known.

# 4. Tests and safeguards

Runtime tests cover R14 refusal, explicit/uncertain/conflicting quantities, extra
numerals, missing or ambiguous orders, invalid registered data, order-only
follow-ups, deferred-state invariants and revocation, exclusions and UI state
preservation. These tests matter because an overly broad fallback could suppress
a real amendment or permit dispatch while a genuine blocker remained.

Scorer tests cover legacy behavior, explicitly approved and disabled assertions,
invalid mappings/counts, membership versus exact sets, missing structured evidence,
ranking source binding and refusing to infer unsupported prose correctness.

The final locked offline suite completed with **578 passed, 1 live deselected**.
Ruff check passed; repository-wide format check reported 81 files already
formatted. git diff --check passed. The exact commands and local logs are listed
in PRE_PUSH_READINESS.md. These are newly recorded results, unlike the earlier
handoff's reported test count without a retained terminal log.

# 5. Why the first benchmark was not enough

The provisional benchmark helped find development failures and document expected
behavior. Its expectations were authored during implementation; they were not
independent adjudication. A high agreement count could therefore reflect the
developer's assumptions rather than a broadly accepted interpretation.

Independent review was needed to separate supported facts, policy-sensitive
behavior and unavailable evidence. The original provisional benchmark remains
unchanged. It is retained as a historical diagnostic, not silently promoted into
the final AI-consensus benchmark or a human-adjudicated standard.

# 6. The request-version problem

Some reviewer material described old pre-v3 wording for nine cases:
**R04, R06, R07, R16, R17, R22, R23, R26 and R27**.

An answer to an old request cannot validate a different frozen request, even if
the ID is the same. The forensic audit compared request text and provenance rather
than accepting matching case numbers. It excluded mismatches, corrupted requests
and cases whose exact provenance could not be verified.

The frozen BEFORE/AFTER request envelopes matched each other and current Data v3;
the original benchmark's current-request identity was not the source of this
contamination. Thus the recordings and original evaluation evidence did not need
to be rerun. The affected old reviewer outputs could not be reused without a new
review of the canonical text. Exclusion is not counted as a dissenting vote.

# 7. Canonical review packet v2

Canonical request text comes from the frozen recorder envelopes, not from reviewer
paraphrases. BEFORE and AFTER match for all 30 request envelopes. Each exact UTF-8
request is hashed, and the ordered JSON array of the 30 exact strings has SHA-256:

`d54a71a8d7c2ef1a53fdcd2ea81f076310fa3d5fef74d85b973febede7f20826`

The packet supplies raw order/workshop facts, global rules, exact inputs and blank
review fields. It contains no model responses, scorer results or predetermined
workshop winners. Review instructions prohibit consulting earlier answers or
trying to match the agent. That establishes the intended blind procedure; actual
compliance and reviewer independence remain self-declared.

# 8. AI reviewer pool

| Reviewer | Usable canonical cases | Basis |
|---|---:|---|
| Gemini | 21 | Exact-current legacy request evidence |
| DeepSeek | 5 | Exact-current legacy request evidence |
| Grok | 30 | Canonical-v2 review provenance |
| GPT | 30 | Canonical-v2 review provenance |
| Claude | 0 | Exact request provenance could not be established |

Coverage varies by reviewer and case. Missing, corrupted or mismatched requests
are excluded; they do not become votes against another reviewer. QA documents,
templates and the earlier consensus workbook are not additional reviewers. Model
names, versions and independence declarations are recorded as provided, without
claiming external authentication.

# 9. Assertion-level consensus

A whole-case label is too coarse. Reviewers might agree that status is CLARIFY
yet disagree whether quantity should be asked immediately or deferred. Agreement
on customer or exclusions must not imply agreement on those policies.

Consensus therefore joins explicit votes by case and assertion identity:

- HIGH_CONSENSUS: unanimity for three/four valid votes, or at least 80% for five
  or more.
- MAJORITY: more than half of at least three valid votes, without the higher
  threshold.
- LIMITED_CONSENSUS: both of exactly two valid votes agree.
- UNRESOLVED: insufficient explicit votes or no threshold-reaching agreement.

There are **848 provenance assertions, 296 accepted consensus assertions and
552 unresolved assertions**. Missing votes abstain. Distinct conditional prose is
not equated by guesswork. Two-reviewer agreement is not relabeled high confidence.

# 10. Why the scorer had to change

The original scorer suppressed benchmark-dependent checks for an unresolved case
as a whole. That protected against unapproved policy labels, but also suppressed
independently approved fields. For example, R01 customer can be scoreable even
when its deferred-needs policy is unresolved.

The new path is opt-in: a case with consensus_assertions uses explicit approvals.
Only approved identities are evaluated. The adapter clears inherited expectations
before mapping approved native checks, and uses separate structured evaluators
where supported. Unsupported assertions are NOT_SCORABLE. Stable family.key IDs,
scoped by case, join results to provenance.

Without the new key, legacy behavior remains. Saved regression artifacts reproduce
the original benchmark's cases.jsonl, checks.csv, summary.json and summary.md
byte-identically on both runs. Only scorer_content_hash differs in the manifests,
as expected after a code change. This preparation rechecked saved bytes; it did
not overwrite or rerun historical scoring.

# 11. Canonical-v2 scoreability

There are **296 accepted assertions**, of which **266 are statically
scorer-supported** and 30 unsupported. The supported set contains 238 native
mappings and 28 structured predicates. Only **247 are evaluable in both frozen
runs**. Static scorer support means an evaluator exists; actual evidence
availability and compatibility determine whether an assertion can enter the
shared paired denominator.

The remaining 19 statically supported assertions are excluded as follows, verified
from existing saved checks without rerunning scoring:

| Exclusion reason | Count | Assertions/cases | Saved states: BEFORE -> AFTER |
|---|---:|---|---|
| BEFORE lacks preview.conversation.deferred_needs | 6 | clarification.deferred_needs_exact: R02/R08/R11/R13/R14/R24 | NOT_SCORABLE -> PASS |
| BEFORE ranking evidence does not satisfy the evaluator's source binding | 12 | operational_predicates.ranking_requires_tool: R04/R06/R07/R09/R12/R16/R20/R21/R25/R26/R27/R30 | NOT_SCORABLE -> PASS |
| Both runs lack preview.order.product | 1 | supported_fields.retrieved.product: R13 | NOT_SCORABLE -> NOT_SCORABLE |

The 12 ranking records contain recommendations, candidates and tool_sources;
their BEFORE dispatch.py hash differs from the current source required by this
evaluator, whereas AFTER matches. They are not cases with no recorded tool output.
Their saved BEFORE reason is structured_evidence_missing; AFTER reports
recorded_ranking_has_audited_tool_evidence. For R13 retrieved product, both saved
reasons are field_missing; both recordings return DECLINE without preview.order.

Exact case/assertion rows and reasons are in
`results/ai-consensus-v2-before-after-comparison.json`, under
`excluded_from_primary`, and in
`results/scored-before-ai-consensus-v2/cases.jsonl` and
`results/scored-after-ai-consensus-v2/cases.jsonl`. Field availability and recorded
tool hashes were cross-checked read-only against the corresponding Rxx.json files
under `../dss5105-baseline-bea5028/results/chat-baseline-bea5028-first/` and
`results/chat-current-reliability-first/`.

Thus 266 - (6 + 12 + 1) = 247. None of these 19 exclusions is a paired FAIL or a
paired improvement: NOT_SCORABLE does not mean FAIL, and AFTER-only evaluability
does not supply comparable BEFORE evidence. The 30 unsupported assertions are a
separate exclusion from the original 296, not part of this 19.

Unsupported is preferable to subjective keyword scoring. A DECLINE status does
not prove the absence of invented history in prose. A clean structured field does
not establish every user-facing claim. Semantic flag concepts, explanations and
other unsupported behaviors remain visible in the ledger without receiving a
manufactured pass/fail label.

# 12. Final BEFORE / AFTER experiment

BEFORE is baseline commit bea5028 in the sibling baseline worktree. AFTER is the
reliability-fixed evaluated state at 7a38db9. Reviewed pre-commit HEAD 705614e includes
later evaluation documentation and is not the source commit of a new live run.

Both runs used the same 30 requests, model name/configuration, prompt/schema,
data, snapshot, weights and zero-retry configuration. Allocator and course data
are unchanged; intake/dispatch differences are the intended treatment. There was
one stochastic run per version. Offline rescoring afterward used the same current
scorer and benchmark for both saved sources.

AFTER's recorded start precedes canonical packet construction. Production does
not import the scorer or canonical labels. Frozen artifact hashes remain intact.
Equal configured model names do not guarantee an identical provider backend or
random sample, so variation remains a confound.

# 13. Final results

| Metric | BEFORE | AFTER |
|---|---:|---:|
| Shared paired assertions | 238/247 | 239/247 |
| Paired semantic improvements | 0 | 1 |
| Paired regressions | 0 | 0 |
| Duplicate clarification violations | 6 | 0 |
| HIGH_CONSENSUS | 124/127 | 125/127 |

The first row counts PASS among the same 247 approved, supported assertions with
evidence in both runs. It is descriptive pooled assertion agreement, not overall
accuracy. There are 238 PASS -> PASS, one FAIL -> PASS, eight FAIL -> FAIL and no
PASS -> FAIL transitions. Improvement/regression rows are relative to BEFORE,
not independent per-run measurements.

Duplicate violations are separate integrity audit checks and are not pooled into
the primary count. HIGH_CONSENSUS is its 127-assertion subset. The remaining
strength groups are MAJORITY 1/3 -> 1/3 and LIMITED_CONSENSUS 113/117 -> 113/117.
Overlapping checks can describe the same underlying behavior.

# 14. R14: strongest evidence for the deterministic mechanism

The recorded raw extraction patches are identical. BEFORE returns CLARIFY;
AFTER returns REFUSE_SUGGESTION after reconciling the quantity need with the order.

The identical recorded extraction patches, together with the reconciliation code
path, provide strong mechanism-level evidence that the fix explains the observed
R14 status change. The frozen comparison alone is not a fixed-patch replay
experiment and does not establish a general causal effect.

The regression tests separately validate the reconciliation guards and R14 refusal
behavior described in section 4; this qualification does not weaken those test
results. Required flag concepts and AFTER-only evidence do not become additional
paired successes. A statistical or general causal claim about future requests or
model samples would require further controlled evaluation.

# 15. Duplicate clarification results

The six observable standard-question violations disappear: **6 -> 0**. This is an
interaction-integrity improvement: users receive fewer repeated questions.
It does not measure semantic extraction accuracy or all possible paraphrases.

R01/R03/R19 have identical patches, supporting a deterministic interpretation.
R10/R15/R29 patches differ, so their individual causal attribution remains more
limited even though the audit transition is unambiguous.

# 16. Deferred-needs result

The implementation and structural tests validate the lifecycle, including
retrieval, explicit uncertainty, invalid registered fields and UI preservation.
AFTER captures deferred_needs; BEFORE does not supply comparable evidence.

Missing evidence is NOT_SCORABLE, not an empty list or failure. Consequently there
is no paired numerical deferral gain to headline. Approved independent needs can
still be scored, and newly captured state is a coverage improvement rather than
a FAIL -> PASS transition.

# 17. Remaining failures

Eight persistent shared-assertion failures comprise four status-policy
disagreements and four equal-valued quantity integer/string representation
mismatches. They are not eight established business errors.

## A. Semantic/policy disagreements

R18 expects CLARIFY under majority consensus but records DECLINE, which is the
production behavior for unknown-order status lookup. Gemini also voted DECLINE.
R20/R28/R30 expect RECOMMEND_ALLOCATE but record NEEDS_REVIEW because production
does not silently accept infeasible deadlines. These are preserved disagreements
under the declared mapping, with real policy questions behind the coarse labels.
These four status-policy disagreements are not all established production bugs.

## B. Unresolved primary statuses

R06/R16 status has no resolved consensus and is excluded. Independently approved
fields or predicates may still be scored.

## C. Representation issues

R05/R11/R14/R24 retrieved quantities are expected integers but recorded CSV strings
with the same values. Arithmetic uses integer batch quantities correctly. The
type-strict scorer produces four shared-assertion failures. These do not show that the
quantity values are wrong. Normalization would change the current scoring contract
and must be a separately specified/versioned decision, not metric cleanup.

## D. Unsupported assertions

Thirty accepted assertions lack an executable evidence contract. These include
prose/semantic concepts and some field expectations, not solely prose. They remain
NOT_SCORABLE rather than being included among the eight persistent shared-assertion
failures.

# 18. What we can claim

"The AI-consensus canonical-v2 benchmark records one primary paired semantic
improvement and no paired regressions in the controlled single-run before/after
comparison."

"Six duplicate-clarification integrity violations present in the baseline are
absent after the reliability fixes."

"The evaluation uses canonical requests and assertion-level AI consensus;
unresolved assertions and unavailable evidence are excluded from the paired
denominator rather than forced into success or failure labels."

Attach the single-run, self-declared reviewer independence, type-mismatch and
coverage qualifications to these statements.

# 19. What we cannot claim

- Human gold or independently human-adjudicated truth.
- True accuracy, comprehensive correctness or complete explanation faithfulness.
- A major accuracy gain from 238/247 -> 239/247.
- Statistical significance or a general causal improvement.
- Independent samples merely because there are many assertions.
- High-confidence gold from LIMITED_CONSENSUS.
- A paired numerical deferred-needs improvement without baseline evidence.
- Success on unsupported assertions, or failure merely from NOT_SCORABLE.

# 20. Reproducibility map

All paths are relative to this repository unless a sibling worktree is shown.

| Artifact | Purpose |
|---|---|
| src/dss5105/intake.py | Validation, reconciliation and deferred lifecycle |
| src/dss5105/dispatch.py; chat_ui.py in the same directory | Deduplication, deterministic preview and state preservation |
| src/dss5105/reliability_score.py; reliability_assertions.py in the same directory | Offline scorer and opt-in approval adapter |
| tests/test_intake.py; tests/test_dispatch.py; tests/test_chat_ui.py | Production regression safeguards |
| tests/test_reliability_score.py; tests/test_reliability_assertions.py; tests/test_reliability_benchmark.py | Scorer and benchmark safeguards |
| examples/reliability_benchmark.json | Preserved provisional benchmark |
| examples/reliability_benchmark_ai_consensus_v2.json | Accepted canonical assertions |
| examples/reliability_benchmark_ai_consensus_v2_provenance.json | Votes, exclusions, unresolved assertions and provenance |
| examples/canonical_ai_review_packet_v2.json | Exact requests, facts and hashes |
| docs/reliability_review/CANONICAL_AI_REVIEW_PACKET_V2.md | Reviewer-facing packet |
| docs/reliability_review/Part_A_Claude.docx; Part_A_DeepSeek.docx; Part_A_Gemini.pdf | Original reviewer sources; eligibility varies |
| docs/reliability_review/Reviewer_D_Grok_4.5_Canonical_V2.md; AI_REVIEW_RESPONSE_COMPLETED_V2.md | Canonical-v2 reviewer sources |
| ../dss5105-baseline-bea5028/results/chat-baseline-bea5028-first/ | Frozen BEFORE recording |
| results/chat-current-reliability-first/ | Frozen AFTER recording |
| results/scored-before-ai-consensus-v2/; results/scored-after-ai-consensus-v2/ | Final saved scoring outputs |
| results/ai-consensus-v2-before-after-comparison.json | Exact paired assertions and transitions |
| docs/reliability_review/AI_CONSENSUS_V2_BEFORE_AFTER.md | Full family/strength report |
| docs/reliability_review/PRE_PUSH_QUALITY_AUDIT.md | Current skeptical audit and corrections |
| docs/reliability_review/PRE_PUSH_COMMIT_PLAN.md | Exact proposed files and distribution decisions |
| docs/reliability_review/PRE_PUSH_READINESS.md | Current validation and pending approvals |
| results/pre-push-validation/ | New local test logs, classification, hashes and audit reproduction helper |

results/ is intentionally ignored. Do not assume those evidence paths will be
available to teammates after a normal commit. Preserve a companion archive or
choose an explicit repository location with the team. Historical reports and
manifests are snapshots; their construction-time coverage statements are not the
current adapter's coverage. Read this audit/readiness set for current status.

# 21. What teammates should review

- Production guards: which needs may be retrieved, deferred or kept blocking.
- Scorer adapter: explicit approvals, evidence contracts and legacy compatibility.
- Canonical methodology: exact requests, reviewer exclusions, vote thresholds and
  self-declared independence.
- Policy choices: unknown-order status, infeasible deadlines and unresolved date
  semantics; avoid tuning labels simply to agree with production.
- Git contents and evidence distribution: raw reviews, historical artifacts,
  ignored recordings/results and local machine manifests.
- Presentation wording: one primary paired change, separate duplicate integrity,
  and visible limitations.

# 22. Next steps

The exact file selection, three local commits and local evidence packaging were
authorized and completed; see PRE_PUSH_READINESS.md. Still required before push:
teammate review, external privacy/delivery approval and separate authorization.
Cached origin state should be rechecked when remote access is later authorized.
No push, PR, upload or sharing is authorized now.

Optional future upgrades: human adjudication of policy disagreements, a richer
claim/faithfulness evidence contract, repeated stochastic evaluations, additional
held-out requests and typed/versioned scorer support. Each would produce a new
evaluation revision while retaining these frozen artifacts.
