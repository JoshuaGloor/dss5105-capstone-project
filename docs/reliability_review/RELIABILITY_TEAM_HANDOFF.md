# Reliability workstream: team handoff

## What changed and why

Three deterministic fixes make clarification more useful: retrieve an omitted
quantity from an identified order without hiding explicit uncertainty; avoid
repeating the standard order question; defer retrievable quantity/deadline needs
until order identity is known. These fixes are already committed locally.

Pending scorer support evaluates only explicitly approved consensus assertions,
while retaining legacy benchmark behavior. Exact current requests were reviewed
after stale pre-v3 reviewer inputs were excluded. Unsupported prose remains
NOT_SCORABLE. Production does not import the scorer or benchmark labels.

## Final results

| Measure | BEFORE | AFTER |
|---|---:|---:|
| Shared AI-consensus assertions | 238/247 PASS | 239/247 PASS |
| Primary paired improvements | 0 | 1: R14 status |
| Paired regressions | 0 | 0 |
| Duplicate-clarification violations, separate integrity audit | 6 | 0 |
| HIGH_CONSENSUS subset | 124/127 | 125/127 |

The benchmark has 296 accepted assertions, 266 statically scorer-supported, and
247 evaluable in both frozen runs. The other 19 supported assertions comprise
six missing BEFORE deferred-state checks, twelve BEFORE ranking checks whose
recorded dispatch.py hash does not satisfy the current evaluator's source binding,
and one R13 retrieved-product check missing in both runs. The ranking recordings
contain tool outputs; this is an evidence-binding limitation, not their absence.
See section 11 of RELIABILITY_WORKSTREAM_EXPLAINED.md and
`results/ai-consensus-v2-before-after-comparison.json` (`excluded_from_primary`).
Static support is distinct from actual evidence availability; these exclusions
are neither paired failures nor paired improvements.

R14's recorded raw extraction patches are identical: BEFORE returns CLARIFY and
AFTER REFUSE_SUGGESTION. Together with the reconciliation code path, this is strong
mechanism-level evidence explaining the observed change. The frozen comparison
alone is not a fixed-patch replay experiment and establishes no general causal
effect; the existing regression-test conclusions remain intact.

One stochastic model run per version; all later scoring is offline. The latest
offline suite passes 578 tests, with one live test deselected. Ruff lint and format
checks passed. The approved three local commits and local evidence package are
complete in the revision containing this handoff. The package was extracted and
hash-verified locally; no push, PR, upload or sharing occurred. See
PRE_PUSH_READINESS.md for execution details. No full tests or evaluations were
rerun for committing and packaging.

## Read these files

1. RELIABILITY_WORKSTREAM_EXPLAINED.md: full explanation from architecture to claims.
2. PRE_PUSH_QUALITY_AUDIT.md: skeptical findings, quantity representation and policy
   disagreements.
3. AI_CONSENSUS_V2_BEFORE_AFTER.md: full metric-family and assertion-change evidence.
4. PRE_PUSH_COMMIT_PLAN.md: exact proposed file groups and evidence decisions.
5. PRE_PUSH_READINESS.md: checks completed and approvals still pending.

These files are in docs/reliability_review/. Review the implementation in
src/dss5105/intake.py, dispatch.py, reliability_score.py and
reliability_assertions.py, plus their tests. Benchmark/provenance are under
examples/ with the reliability_benchmark_ai_consensus_v2 prefix.

## Known limitations

Eight persistent shared-assertion failures comprise four status-policy
disagreements (R18/R20/R28/R30) and four equal-valued quantity integer/string
representation mismatches (R05/R11/R14/R24). These are not eight established
business errors: the mismatches do not indicate wrong quantity values, and the
status disagreements do not by themselves establish production bugs. R06/R16
primary status is unresolved. Thirty accepted assertions remain unsupported.
BEFORE lacks deferred-state evidence, so there is no paired numerical deferral
claim. NOT_SCORABLE does not mean FAIL.

AI reviewer independence is self-declared. Counts are overlapping assertions,
not independent statistical samples or overall accuracy. AI consensus is not human
gold. Structured tool audits do not establish comprehensive explanation faithfulness.
A single stochastic run does not establish statistical significance or a general
causal effect.

## What needs approval

- Confirm the guarded production behavior and review remaining policy choices.
- Agree whether raw reviewer responses belong in Git or a hash-verified companion
  archive. Do not distribute a provenance bundle with inaccessible evidence.
- Agree how teammates receive ignored results/, including recordings, scores and
  comparison JSON. Existing repository policy intentionally ignores that tree.
- Review presentation wording; exact commit files and local packaging were
  approved by the user and completed.
- Teammate review and external privacy/delivery approval remain pending. No push,
  PR, upload or sharing is authorized by the local execution approval.
