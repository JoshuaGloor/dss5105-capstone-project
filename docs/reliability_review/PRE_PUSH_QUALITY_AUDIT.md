# Final local quality audit

Audit date: 2026-10-15 (Asia/Shanghai). Scope: current working tree on
`TangZheling/agent-reliability`, HEAD `705614e655ef7b838f87dcb77a8866b1b6a3ae7e`.
The branch is six commits ahead of the cached origin branch. No fetch was made;
this is not a statement about the current remote server. The index is empty.

This is a second, skeptical review pass over source and saved evidence by the
same local assistant, not another independent reviewer vote. No production,
benchmark, assertion adapter or test semantics changed during this task.

## Findings and disposition

| Severity | Finding | Disposition |
|---|---|---|
| BLOCKER | No production defect or invalid paired result established by this audit | None outstanding within the audited scope |
| IMPORTANT | Scorer contract opening described whole-case suppression as universal, contradicting its opt-in adapter section | Corrected to scope suppression to legacy benchmarks |
| IMPORTANT | Ignored recordings/results and raw reviewer responses will not all accompany an ordinary commit | Evidence distribution and reviewer-file inclusion need user/team approval before sharing; no evidence deleted or force-added |
| MINOR | Four quantity checks fail on equal-valued integer/string representations | Leave type-strict semantics and historical outputs unchanged; distinguish these from wrong quantity values |
| MINOR | R18/R20/R28/R30 are policy/behavior status disagreements | Preserve failures; do not tune production or relabel benchmark |
| MINOR | Earlier consensus reports contain construction-time scorer limitations and old test evidence | Treat these as dated snapshots; current coverage is 266 supported, 247 paired. This audit and PRE_PUSH_READINESS.md are the current status |
| MINOR | Historical manifests/provenance include local absolute audit paths | No credentials detected; new teaching/handoff documents use relative paths. Keep old machine inventories local and preserve provenance hashes |

## Source review

| Change | Original problem and current behavior | Safeguards and compatibility |
|---|---|---|
| Intake quantity reconciliation, b5c327c then generalized in 9af09ff | A model quantity need blocked a refusal even when a uniquely resolved order supplied quantity | Explicit uncertainty, amendments, extra digits and invalid registered data remain blockers; no R14 condition exists in intake |
| Dispatch deduplication, 6e562b6 | Resolver and intake both emitted the same standard order question | Reuse the existing clarification only when it starts with the resolver question; retain other questions; exact standard-question scope |
| Deferred lifecycle, 9af09ff | Secondary needs were treated as independent blockers before order identity | Deferred values are a subset of pending quantity/deadline needs; explicit evidence revokes deferral; invalid retrieved fields become blockers; legacy needs stay blocking |
| Trace/selection/UI reconstruction | Rebuilding Conversation could lose the new state | dataclasses.replace preserves deferred state; immutable tuple defaults avoid new shared-default state |
| Scorer opt-in adapter | Whole-case suppression discarded independently approved fields | Only consensus_assertions enables the new path; clear cloned expectations prevent accidental inheritance; legacy suppression remains for old benchmarks |
| Structured predicates | Accepted prose could otherwise be mistaken for executable evidence | Exact sets, exact dispatch reason contracts and source-bound audited ranking evidence; missing/incompatible evidence is NOT_SCORABLE |
| Stable IDs/serialization | Case-local checks needed a provenance join | family.key scoped by case, separate integrity IDs, conditional CSV column, adapter hash and dynamic metric aggregation |

Reviewed tests cover uncertain/explicit quantities, order-only follow-ups, malformed
registered values, exclusions, deferred-state revocation, UI preservation, legacy
approval absence, disabled approvals, mappings, exact/member exclusions, missing
evidence, source-bound rankings and non-scoring of unsupported prose.

No new model schema field was required: deferred_needs is internal conversation
state, not a request to the provider. Its default is empty for legacy callers.
JSON recorder output gains that evidence only AFTER; absence BEFORE is preserved.

No dead production branch, new cross-conversation state leakage or case-specific
runtime workaround was identified. Legacy scorer unresolved IDs remain explicitly
case-specific evaluation policy; they are not imported by production. The existing
web UI R25 default is unrelated pre-existing example selection. The adapter reuses
legacy check generation and filters its results; this is some extra computation,
not a second production decision path. Narrow evidence-reading exceptions become
NOT_SCORABLE rather than PASS. Standard-question ordering and case-sensitive
prefix matching are intentional bounded contracts, not semantic deduplication.

## Quantity representation review

DispatchDesk loads orders with csv.DictReader, retaining string columns. The
recorded preview.order is that source row. The executable batch converts pieces
to int before tool arithmetic. Recorder JSON preserves these types faithfully.
Consensus retrieved.quantity is an integer; the adapter maps it to order.pieces;
the legacy comparator deliberately requires exact JSON types. Thus R05/R11/R14/R24
compare 1000/600/2000/300 with equal-valued strings and FAIL in both runs.

The smallest prospective alternative would normalize only a declared retrieved
positive-integer field, accept ASCII digit strings, reject bool/float/invalid
values, and leave every legacy benchmark comparison untouched. That could preserve
legacy outputs, but would change the explicitly type-strict consensus comparison
contract and final counts. There is no approved typed-equivalence contract here.
It is therefore a versioned future option, not a safe silent correction in this
freeze. No normalization was implemented and no scoring was rerun.

## Remaining status disagreements

| Case | Consensus | Recorded | Classification |
|---|---|---|---|
| R18 | CLARIFY, MAJORITY | DECLINE | Policy/behavior disagreement: production declines status lookup for an unknown order; Gemini also voted DECLINE |
| R20 | RECOMMEND_ALLOCATE, HIGH_CONSENSUS | NEEDS_REVIEW | Coarse recommendation label versus production infeasibility review gate; mapping RECOMMEND_ALLOCATE to RECOMMEND is explicit, not a serialization bug |
| R28 | RECOMMEND_ALLOCATE, MAJORITY | NEEDS_REVIEW | Same status-policy boundary; GPT dissented with CLARIFY |
| R30 | RECOMMEND_ALLOCATE, HIGH_CONSENSUS | NEEDS_REVIEW | Same infeasibility review boundary; not missing evidence |

These are genuine disagreements under the approved executable status mapping.
They do not prove that accepting infeasible work would be better behavior.
R06/R16 primary statuses are unresolved and absent from the paired status set.

## Benchmark and reviewer audit

Recomputed exact R01-R30 identities, per-request SHA-256 and whole-set SHA-256:
`d54a71a8d7c2ef1a53fdcd2ea81f076310fa3d5fef74d85b973febede7f20826`.
Packet, benchmark and provenance agree on text identity. Consensus vote thresholds,
case-scoped assertion identities, accepted values and reviewer source hashes were
checked directly. All vote sources exist; invalid reviewer-case entries do not
vote. Claude contributes zero; Gemini 21, DeepSeek 5, Grok 30 and GPT 30 cases.
QA and the prior consensus workbook are non-voting files, not additional reviewers.

Packet policy_sensitive is editorial routing before review. Consensus legitimately
adds R05/R18/R20/R21/R28/R30 based on disagreement or tool-dependent policy; these
changes are explicitly listed in provenance.new_policy_sensitive_cases and are
not request-version contamination. The nine stale reviewer cases are
R04/R06/R07/R16/R17/R22/R23/R26/R27. Their old labels are not transferred to the
current canonical requests. No human-adjudicated claim is made.

The canonical packet contains raw facts and blank review templates rather than
model outputs or scorer decisions. Blindness is requested and self-declared;
actual reviewer compliance and identity cannot be independently authenticated.

## Leakage and fairness

Production modules have no import of reliability_score or reliability_assertions.
The model prompt/schema is equal across runs and does not load canonical labels.
AFTER began on 2026-10-14 at 09:47:41 UTC; the canonical packet manifest was created
on 2026-10-15 at 05:38:18 UTC. This supports the recorded chronology; it is not
externally authenticated proof of all reviewer conduct.

Both saved manifests and request envelopes confirm the same 30 requests, speakers,
model/settings, prompt/schema, snapshot, weights, course CSVs and simulator hashes.
Allocator code is unchanged. Intake and dispatch deliberately differ as the
treatment, so it would be inaccurate to claim all deterministic code is identical.
There is one run per version. Backend model revisions and stochastic patch
variation remain confounds. Identical R14 patches support its local mechanism;
they do not establish a general population effect.

## Results independently reconstructed from saved checks

247 shared evaluable approved assertions; BEFORE 238 PASS, AFTER 239 PASS;
one FAIL -> PASS; zero PASS -> FAIL; eight FAIL -> FAIL. Strength counts are
124/127 -> 125/127 HIGH_CONSENSUS, 1/3 -> 1/3 MAJORITY and 113/117 -> 113/117
LIMITED_CONSENSUS. Observable duplicate violations are separately 6 -> 0.
The case/assertion/state set matches the saved comparison JSON exactly.

No score_run, scorer CLI, model evaluation or dispatch replay was used to obtain
these checks: this audit reads existing files and reconstructs the denominator.
NOT_SCORABLE is excluded, integrity audits are separate, overlapping assertions
are not independent samples, and missing baseline deferral evidence is not a FAIL.

## Validation and protection

- Full locked offline suite: 578 passed, 1 live deselected, 43.25 seconds.
- First attempt: 523 passed, 55 setup errors because this task omitted the parent
  of its new pytest basetemp. Parent creation fixed the invocation; no code edit
  or frozen evaluation rerun was needed.
- Ruff check: passed. Ruff format check over src/tests/scripts: 36 files already
  formatted. Repository-wide format check is recorded in the final readiness file.
- git diff --check: passed.
- Source, tests, benchmarks, reviewer responses, both recorder directories and
  historical/final scoring files retain their audit hashes. Only the listed
  documentation clarification is an intentional pre-existing-file edit.
- Narrow secret/private-key pattern scan found no matches in intended source,
  test, benchmark and documentation text. No .env was opened or copied. This is
  a scoped check, not an assurance about unreviewed private material.

New test logs/caches are isolated under ignored results/pre-push-validation/.
Useful local reproduction helpers and old evidence were retained. No cache cleanup
was necessary for commit isolation; no evidence was deleted. Exact per-file A-I
classification and hash checks are in the local audit JSON and commit plan.
