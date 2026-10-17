# A. Problem statement - slide 1

Correct extraction can still produce unreliable clarification: asking for a retrievable quantity, repeating an order question, or asking secondary questions too early. Evaluation also needs exact-current requests and defensible reviewed expectations. Structured tool checks do not establish complete explanation faithfulness.

# B. Fixes - slide 2

- Reconcile omitted quantity against a uniquely identified order while preserving explicit uncertainty and amendments.
- Reuse the standard order question instead of appending it twice.
- Defer retrievable quantity/deadline needs until order identification; preserve state through selections and UI replies.
- Add assertion-level scorer approvals and deterministic evidence checks; leave unsupported prose unscored.

# C. Evaluation design - slide 3

Same 30 canonical Data v3 requests, model/configuration and course data. One frozen stochastic BEFORE run and one AFTER run; subsequent scoring is offline. Independent AI reviews are filtered by exact request provenance, with self-declared independence. Unresolved assertions are excluded. This is a controlled single-run comparison, with no repeated-run causal or significance claim.

# D. Final results - slide 4

| Metric | BEFORE | AFTER |
|---|---:|---:|
| Shared AI-consensus assertions | 238/247 | 239/247 |
| Primary paired semantic improvements | 0 | 1 |
| Paired regressions | 0 | 0 |
| Duplicate clarification violations | 6 | 0 |

HIGH_CONSENSUS: 124/127 -> 125/127 PASS. The primary improvement is R14 status. Improvement/regression rows describe transitions relative to BEFORE; they are not independent per-run measures. Duplicate violations are supplemental integrity checks outside the primary consensus denominator. The pooled assertion row is descriptive agreement, not overall accuracy.

# E. Limitations / takeaway - slide 5

- One stochastic run per version; no general causal or statistical claim.
- Eight persistent FAILs: four status disagreements and four equal-valued quantity type mismatches.
- R06/R16 primary status unresolved; 30 accepted assertions unsupported.
- BEFORE lacks deferred-state evidence; no paired numerical deferral gain.
- Reviewer independence is self-declared; this is AI consensus, not human adjudication.

Takeaway: one primary paired semantic improvement, no paired regressions, and six fewer duplicate-clarification violations, within explicit evidence and coverage limits.
