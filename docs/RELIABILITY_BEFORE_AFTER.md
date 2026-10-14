# Controlled reliability BEFORE/AFTER comparison

## Experiment design

~~~json
{
  "before_commit": "bea502865d8255860c32b65c8abdc73d0f2276b6",
  "after_commit": "7a38db938baca919436767773cc7d38eccd9a207",
  "model": "openai:gpt-5.6",
  "runs_per_version": 1,
  "planned_attempted_completed_per_version": 30,
  "snapshot_date": "2026-04-01",
  "weights": {
    "cost": 0.0,
    "deadline_buffer_days": 0.0,
    "defects": 0.0,
    "lateness": 1.0
  },
  "model_parameters": {
    "max_retries": 0,
    "timeout": 30
  },
  "scorer_version": "reliability-score-v1",
  "controls_equal": {
    "model": true,
    "system_prompt": true,
    "schema": true,
    "source_hashes": true,
    "snapshot_date": true,
    "weights": true,
    "model_parameters": true
  }
}
~~~

Identical requests/requesters, course data, snapshot, independent workshop CSV queues, prompt/schema, weights and explicit preference rules. Timeout 30 seconds; zero retries. Code/reconciliation is the treatment. One stochastic run per version.

## Terminology

Provisional development agreement compares unadjudicated expectations. Integrity audit checks observable structural/tool consistency. Independent gold accuracy requires independent adjudication; these results are NOT independent gold accuracy.

## Quantitative results

| Metric / basis | BEFORE | AFTER | Change pp | Directly comparable denominators |
|---|---|---|---|---|
| constraint_application / provisional | 2/2 (100.00%) | 2/2 (100.00%) | +0.00 | True |
| duplicate_standard_clarification_rate / integrity_audit | 6/8 (75.00%) | 0/7 (0.00%) | not comparable | False |
| exclusion_exactness / provisional | 21/21 (100.00%) | 21/21 (100.00%) | +0.00 | True |
| exclusion_recall / provisional | 2/2 (100.00%) | 2/2 (100.00%) | +0.00 | True |
| forbidden_field_violation_rate / provisional | 0/85 (0.00%) | 0/85 (0.00%) | +0.00 | True |
| forbidden_flags_violation_rate / provisional | 0/50 (0.00%) | 0/50 (0.00%) | +0.00 | True |
| operational_completion / integrity_audit | 30/30 (100.00%) | 30/30 (100.00%) | +0.00 | True |
| request_exact_match / provisional | 20/21 (95.24%) | 20/21 (95.24%) | +0.00 | True |
| request_field_correctness / provisional | 97/98 (98.98%) | 97/98 (98.98%) | +0.00 | True |
| required_flags_recall / provisional | 10/12 (83.33%) | 12/12 (100.00%) | +16.67 | True |
| required_needs_recall / provisional | 1/1 (100.00%) | 1/1 (100.00%) | +0.00 | True |
| resolved_field_correctness / provisional | 98/98 (100.00%) | 103/103 (100.00%) | not comparable | False |
| status_correctness / provisional | 20/21 (95.24%) | 21/21 (100.00%) | +4.76 | True |
| tool_candidate_integrity / integrity_audit | 979/979 (100.00%) | 1012/1012 (100.00%) | not comparable | False |
| tool_integrity / integrity_audit | 30/30 (100.00%) | 30/30 (100.00%) | +0.00 | True |
| tool_split_integrity / integrity_audit | 60/60 (100.00%) | 75/75 (100.00%) | not comparable | False |

Lower violation rates are better; higher correctness/recall is better. No weighted accuracy. Resolved fields gain five R14 checks; candidate/split denominators increase when R14 proceeds. Duplicate rates condition on replies containing a known standard question.

Forbidden needs: three shared observable assertions change from three FAILs to two FAILs: R14 quantity clears; R02 order/deadline persist. Baseline-selected observability makes this subset nonrepresentative. Full 3/3 versus 2/100 is not a direct performance improvement. Shared provisional assertions: 406/414 PASS before, 410/414 after; descriptive count, not overall accuracy.

## Coverage

| Metric | BEFORE | AFTER |
|---|---|---|
| Deferred correctness | 0/21 evaluable; 21 NOT_SCORABLE; nine unresolved | 21/21 evaluable/PASS; nine unresolved |
| Deferred invariant | 0/30 evaluable; 30 NOT_SCORABLE | 30/30 evaluable/PASS |
| Forbidden needs | 3 evaluable; 97 NOT_SCORABLE | 100 evaluable; zero NOT_SCORABLE |

Missing baseline deferred_needs is absent evidence, not an empty list or failure. All 30 cases differ in schema evidence.

## Case changes / attribution

| Case | Interpretation | Attribution |
|---|---|---|
| R01 | Identical patches; duplicate order question removed; explicit quantity remains blocking. | HIGH-CONFIDENCE CODE EFFECT |
| R03 | Identical patches; duplicate removed and quantity deferred; policy unresolved. | HIGH-CONFIDENCE CODE EFFECT |
| R10 | Duplicate removed and quantity deferred. date_uncertain false to true comes from differing raw patch: LIKELY MODEL VARIATION; policy unresolved. | CONSISTENT WITH CODE EFFECT |
| R14 | Identical patches; quantity blocker removed; CLARIFY to REFUSE_SUGGESTION; two flags and five batch fields restored. | HIGH-CONFIDENCE CODE EFFECT |
| R15 | Equivalent relevant extraction; duplicate removed and quantity deferred; policy unresolved. | HIGH-CONFIDENCE CODE EFFECT |
| R19 | Identical patches; duplicate removed and quantity deferred; policy unresolved. | HIGH-CONFIDENCE CODE EFFECT |
| R29 | Equivalent extracted values; duplicate removed and quantity deferred; deadline retained; policy unresolved. | HIGH-CONFIDENCE CODE EFFECT |
| R05 | AFTER patch already omits quantity; cannot attribute reduced needs solely to reconciliation. | LIKELY MODEL VARIATION |
| R02 | No improvement: historical time misclassified, irrelevant needs retained; final DECLINE reply correct. | UNCLEAR |

Categories: HIGH-CONFIDENCE CODE EFFECT, CONSISTENT WITH CODE EFFECT, LIKELY MODEL VARIATION, UNCLEAR. Identical patches strengthen deterministic attribution. Differing raw extraction weakens it; unresolved cases are not approved semantic successes.

## Failure patterns

BEFORE: eight provisional FAILs in two cases/patterns (R02, R14), plus six duplicate integrity FAILs in six cases (one pattern): 14 assertions, eight affected cases, three grouped patterns. AFTER: four provisional FAILs, one case R02, one pattern. Multiple assertions may measure one underlying failure.

### BEFORE

- R01 / duplicate_standard_clarification_rate.message / integrity_audit
- R02 / request_field_correctness.date_uncertain / provisional
- R02 / request_exact_match.case / provisional
- R02 / forbidden_needs_violation_rate.deadline / provisional
- R02 / forbidden_needs_violation_rate.order / provisional
- R03 / duplicate_standard_clarification_rate.message / integrity_audit
- R10 / duplicate_standard_clarification_rate.message / integrity_audit
- R14 / status_correctness.status / provisional
- R14 / forbidden_needs_violation_rate.quantity / provisional
- R14 / required_flags_recall.NO_ON_TIME_OPTION / provisional
- R14 / required_flags_recall.SUGGESTION_REFUSED / provisional
- R15 / duplicate_standard_clarification_rate.message / integrity_audit
- R19 / duplicate_standard_clarification_rate.message / integrity_audit
- R29 / duplicate_standard_clarification_rate.message / integrity_audit

### AFTER

- R02 / request_field_correctness.date_uncertain / provisional
- R02 / request_exact_match.case / provisional
- R02 / forbidden_needs_violation_rate.deadline / provisional
- R02 / forbidden_needs_violation_rate.order / provisional

R02 final reply correctly declines; incorrect needs are state, not delivered questions. Draft rubric improves 29/30 (R14 failed) to 30/30. Reliability scorer confirms R14, adds duplicates and persistent R02; draft rubric is not authoritative gold.

## Integrity / frozen evidence

Both: 30 compatible cases, zero source issues, tool integrity 30/30 PASS. BEFORE six integrity FAILs are duplicates; 30 NOT_SCORABLE are deferred invariants. AFTER zero integrity FAIL/NOT_SCORABLE.

Both runs and scoring outputs remain unchanged and frozen. Imperfect scores do not justify reruns; no technical comparability defect requires another live run.

## Limitations

- Provisional labels, NOT independent gold accuracy.
- Nine unresolved cases: R01 R03 R06 R10 R15 R16 R19 R23 R29.
- One stochastic run/version; no variance or generalization estimate.
- Baseline deferred_needs absent; coverage gain is not performance improvement.
- Initial-turn only.
- No rendered UI faithfulness.
- No prose claim ledger or numerical-prose grading.

## Evidence hashes

- before_recorder_manifest: 5be209b51537d38ec635b2cf428c06c285e484ddefbffd09fbab13363947347d; D:\DESKTOP\dss5105\Capstone_Project\dss5105-baseline-bea5028\results\chat-baseline-bea5028-first\manifest.json
- after_recorder_manifest: 192a16bcbb47a9f894c861f65a3d5e1f84d0f0c00dec9725095d5daa29a366ba; D:\DESKTOP\dss5105\Capstone_Project\dss5105-capstone-project\results\chat-current-reliability-first\manifest.json
- before_scorer_manifest: cb62ea0684a49849053f724bcac4976ecfb8d4cdab3cfbd37574eef13df85526; D:\DESKTOP\dss5105\Capstone_Project\dss5105-capstone-project\results\scored-before-bea5028-first\manifest.json
- after_scorer_manifest: 5c10153c1c0fb34b8ca8d4cdeba39dfe07144638cfddd54b06fdfc18ca6cd8ff; D:\DESKTOP\dss5105\Capstone_Project\dss5105-capstone-project\results\scored-after-7a38db9-first\manifest.json
- benchmark: bb55a3462c6f8291549f1b956bf14f0c5b7c117fd9b211d4c53a09d0e14be8ee; D:\DESKTOP\dss5105\Capstone_Project\dss5105-capstone-project\examples\reliability_benchmark.json

Machine snapshot: ../results/reliability-before-after-summary.json (Git-ignored). Review preparation: RELIABILITY_INDEPENDENT_REVIEW_PACKET.md.
