# Final AI-consensus canonical-v2 BEFORE/AFTER evaluation

## Evaluation design

Controlled single-run before/after comparison of the two frozen 30-case recorded_model_run artifacts. The same current scorer and assertion adapter score both runs offline, with tool audit enabled. No live calls, case retries, scorer edits, or benchmark changes occurred. The primary unit is a case-scoped stable assertion ID, approved by consensus and supported and evaluable in both runs. NOT_SCORABLE is excluded, never counted as failure. Supplemental integrity audits are reported separately.

## Frozen artifact identity

Benchmark SHA-256: `c8cc8492a24e1bb7610ae60e2b3ae7f9e1961a222f8184129c3440a6f83e101c`.
Provenance SHA-256: `395604f9c84de3d934cc732f3db56f93166e4d6718bbcd3e9c8e0a442a5b1323`.
Request-set SHA-256 recomputed from exact ordered request texts: `d54a71a8d7c2ef1a53fdcd2ea81f076310fa3d5fef74d85b973febede7f20826`.

- `D:\DESKTOP\dss5105\Capstone_Project\dss5105-baseline-bea5028\results\chat-baseline-bea5028-first`: manifest `5be209b51537d38ec635b2cf428c06c285e484ddefbffd09fbab13363947347d`; consumed source aggregate `e5ece53498c1027de0b3cc2a5fa8eb54b79a4f4f9013117aefb50ba942bee374`.
- `D:\DESKTOP\dss5105\Capstone_Project\dss5105-capstone-project\results\chat-current-reliability-first`: manifest `192a16bcbb47a9f894c861f65a3d5e1f84d0f0c00dec9725095d5daa29a366ba`; consumed source aggregate `9bb0cee3a6fb5d76896fccd2bef6885f7cff1f285d5ee0da511aa5662dcd079c`.

Per-file SHA-256 for all frozen recorder files, old score outputs, reviewer evidence, benchmarks, scorer and adapter are in `results/ai-consensus-v2-freeze-check.json`. Both score manifests match the recorded benchmark and consumed-source aggregate hashes. Both have 30 completed attempts, 30 compatible requests, zero malformed/duplicate/incompatible IDs. All protected files retain their pre-run hashes. Existing working-tree changes predate this task.

## Benchmark/reviewer methodology

Reviewer provenance is taken from the frozen canonical-v2 provenance JSON, joining case ID plus family.key. Only approved HIGH_CONSENSUS, MAJORITY and LIMITED_CONSENSUS rows vote in the primary evaluation. Independence is self-declared. Grok/GPT canonical-v2 reviews and exact-current legacy Gemini/DeepSeek coverage contribute; Claude lacks qualifying provenance. LIMITED_CONSENSUS is two-reviewer agreement. Prose concepts without a deterministic evidence contract remain unsupported. Earlier provenance scoring-disposition labels describe the scorer before its approval adapter; executable coverage here comes from the unchanged current adapter and actual saved outcomes.

## Canonical-v2 coverage

Canonical benchmark assertions: 296; support classification: {'native': 238, 'unsupported': 30, 'structured': 28}. Unresolved provenance assertions: 552; these are excluded from the canonical benchmark or remain disabled. R06/R16 primary status is suppressed and contributes no primary status score.
Excluded canonical assertion instances: 49. Every unsupported accepted assertion remains NOT_SCORABLE in both runs. See the machine artifact for all excluded IDs, reasons and state pairs.

## Shared paired denominator

Primary shared evaluable assertions: 247. {'PASS -> PASS': 238, 'FAIL -> FAIL': 8, 'FAIL -> PASS': 1}. No overall accuracy is claimed. Different assertions can measure the same behavior.

## Metric-family table

| Family | Scope | Shared N | BEFORE correct | AFTER correct | BEFORE % | AFTER % | Delta pp | FAIL -> PASS | PASS -> FAIL |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| status | Consensus | 28 | 23 | 24 | 82.14 | 85.71 | 3.57 | 1 | 0 |
| request fields | Consensus | 148 | 148 | 148 | 100.00 | 100.00 | 0.00 | 0 | 0 |
| resolved fields | Consensus | 15 | 11 | 11 | 73.33 | 73.33 | 0.00 | 0 | 0 |
| required needs | Consensus | 12 | 12 | 12 | 100.00 | 100.00 | 0.00 | 0 | 0 |
| forbidden needs | Consensus | 0 | 0 | 0 | N/A | N/A | N/A | 0 | 0 |
| deferred needs | Consensus | 0 | 0 | 0 | N/A | N/A | N/A | 0 | 0 |
| required flags | Consensus | 0 | 0 | 0 | N/A | N/A | N/A | 0 | 0 |
| forbidden flags | Consensus | 0 | 0 | 0 | N/A | N/A | N/A | 0 | 0 |
| exclusions | Consensus | 30 | 30 | 30 | 100.00 | 100.00 | 0.00 | 0 | 0 |
| candidate/workshop eligibility | Consensus | 9 | 9 | 9 | 100.00 | 100.00 | 0.00 | 0 | 0 |
| operational predicates | Consensus | 5 | 5 | 5 | 100.00 | 100.00 | 0.00 | 0 | 0 |
| integrity / duplicate clarification | Audit | 37 | 31 | 37 | 83.78 | 100.00 | 16.22 | 6 | 0 |
| tool integrity | Audit | 1069 | 1069 | 1069 | 100.00 | 100.00 | 0.00 | 0 | 0 |

Zero-denominator families are unsupported or absent from approved executable canonical assertions. Audit counts include individual tool candidate/split checks and must not be pooled with primary consensus metrics. Duplicate integrity checks are observable standard-question duplication checks, not semantic duplicate detection.

## Consensus-strength table

| Strength | Shared N | BEFORE % | AFTER % | Delta pp |
|---|---:|---:|---:|---:|
| HIGH_CONSENSUS | 127 | 97.64 | 98.43 | 0.79 |
| MAJORITY | 3 | 33.33 | 33.33 | 0.00 |
| LIMITED_CONSENSUS | 117 | 96.58 | 96.58 | 0.00 |

## Case-level changed assertions

Only cases with a changed shared scoreable assertion appear below. Audit rows carry no consensus-strength claim.

| Case | Assertion ID | Scope | BEFORE | AFTER | Consensus strength | Identical raw patch | Plausible attribution |
|---|---|---|---|---|---|---|---|
| R14 | primary_status.status | primary | FAIL | PASS | HIGH_CONSENSUS | True | quantity reconciliation fix |
| R01 | integrity.duplicate_standard_clarification_rate.message | supplemental integrity audit | FAIL | PASS | N/A: independent audit | True | duplicate clarification fix |
| R03 | integrity.duplicate_standard_clarification_rate.message | supplemental integrity audit | FAIL | PASS | N/A: independent audit | True | duplicate clarification fix |
| R10 | integrity.duplicate_standard_clarification_rate.message | supplemental integrity audit | FAIL | PASS | N/A: independent audit | False | cannot determine |
| R15 | integrity.duplicate_standard_clarification_rate.message | supplemental integrity audit | FAIL | PASS | N/A: independent audit | False | cannot determine |
| R19 | integrity.duplicate_standard_clarification_rate.message | supplemental integrity audit | FAIL | PASS | N/A: independent audit | True | duplicate clarification fix |
| R29 | integrity.duplicate_standard_clarification_rate.message | supplemental integrity audit | FAIL | PASS | N/A: independent audit | False | cannot determine |

## High-confidence deterministic fix effects and known targets

### R14

Raw model patches identical: True. Status: CLARIFY -> REFUSE_SUGGESTION. Flags: `[]` -> `['NO_ON_TIME_OPTION', 'SUGGESTION_REFUSED']`.
Conversation BEFORE: `{"needs": ["quantity"], "deferred_needs": "<absent>"}`.
Conversation AFTER: `{"needs": [], "deferred_needs": []}`.
Changed primary IDs: primary_status.status. Shared primary failures AFTER: supported_fields.retrieved.quantity.
Identical extraction plus changed deterministic downstream state supports a quantity-reconciliation effect on the status/clarification path. Required flag concepts are unsupported; observed flags are not counted as approved flag successes. Resolved/eligibility evidence that exists only AFTER is coverage, not a paired win. Batch/order details and every excluded ID are retained in the machine artifact.

### R01

Raw model patches identical: True. Status: CLARIFY -> CLARIFY. Flags: `[]` -> `[]`.
Conversation BEFORE: `{"needs": ["order", "quantity"], "deferred_needs": "<absent>"}`.
Conversation AFTER: `{"needs": ["order", "quantity"], "deferred_needs": []}`.
Changed primary IDs: none. Shared primary failures AFTER: none.

### R03

Raw model patches identical: True. Status: CLARIFY -> CLARIFY. Flags: `[]` -> `[]`.
Conversation BEFORE: `{"needs": ["order", "quantity"], "deferred_needs": "<absent>"}`.
Conversation AFTER: `{"needs": ["order", "quantity"], "deferred_needs": ["quantity"]}`.
Changed primary IDs: none. Shared primary failures AFTER: none.
Quantity deferral is visible AFTER. Missing BEFORE deferred_needs prevents paired deferred correctness; approved required-needs checks can independently remain scoreable. Do not count schema evidence as a FAIL -> PASS.

### R10

Raw model patches identical: False. Status: CLARIFY -> CLARIFY. Flags: `[]` -> `[]`.
Conversation BEFORE: `{"needs": ["order", "quantity", "deadline"], "deferred_needs": "<absent>"}`.
Conversation AFTER: `{"needs": ["order", "quantity", "deadline"], "deferred_needs": ["quantity"]}`.
Changed primary IDs: none. Shared primary failures AFTER: none.

### R15

Raw model patches identical: False. Status: CLARIFY -> CLARIFY. Flags: `[]` -> `[]`.
Conversation BEFORE: `{"needs": ["order", "quantity"], "deferred_needs": "<absent>"}`.
Conversation AFTER: `{"needs": ["order", "quantity"], "deferred_needs": ["quantity"]}`.
Changed primary IDs: none. Shared primary failures AFTER: none.
Quantity deferral is visible AFTER. Missing BEFORE deferred_needs prevents paired deferred correctness; approved required-needs checks can independently remain scoreable. Do not count schema evidence as a FAIL -> PASS.

### R19

Raw model patches identical: True. Status: CLARIFY -> CLARIFY. Flags: `[]` -> `[]`.
Conversation BEFORE: `{"needs": ["order", "quantity"], "deferred_needs": "<absent>"}`.
Conversation AFTER: `{"needs": ["order", "quantity"], "deferred_needs": ["quantity"]}`.
Changed primary IDs: none. Shared primary failures AFTER: none.
Quantity deferral is visible AFTER. Missing BEFORE deferred_needs prevents paired deferred correctness; approved required-needs checks can independently remain scoreable. Do not count schema evidence as a FAIL -> PASS.

### R29

Raw model patches identical: False. Status: CLARIFY -> CLARIFY. Flags: `[]` -> `[]`.
Conversation BEFORE: `{"needs": ["order", "quantity", "deadline"], "deferred_needs": "<absent>"}`.
Conversation AFTER: `{"needs": ["order", "quantity", "deadline"], "deferred_needs": ["quantity"]}`.
Changed primary IDs: none. Shared primary failures AFTER: none.
Quantity deferral is visible AFTER. Missing BEFORE deferred_needs prevents paired deferred correctness; approved required-needs checks can independently remain scoreable. Do not count schema evidence as a FAIL -> PASS.

### R02

Raw model patches identical: True. Status: DECLINE -> DECLINE. Flags: `[]` -> `[]`.
Conversation BEFORE: `{"needs": ["order", "deadline"], "deferred_needs": "<absent>"}`.
Conversation AFTER: `{"needs": ["order", "deadline"], "deferred_needs": []}`.
Changed primary IDs: none. Shared primary failures AFTER: none.
Canonical-v2 supports DECLINE and unsupported-history predicates; the prior date_uncertain/forbidden order/deadline failure labels are not automatically inherited. Inspect the paired failures and unsupported predicates rather than carrying provisional failures forward.

### R06

Raw model patches identical: False. Status: RECOMMEND -> RECOMMEND. Flags: `[]` -> `[]`.
Conversation BEFORE: `{"needs": [], "deferred_needs": "<absent>"}`.
Conversation AFTER: `{"needs": [], "deferred_needs": []}`.
Changed primary IDs: none. Shared primary failures AFTER: none.
Primary status remains unresolved and is not scored or used as a headline. Only independently approved assertions are evaluated.

### R16

Raw model patches identical: False. Status: RECOMMEND -> RECOMMEND. Flags: `[]` -> `[]`.
Conversation BEFORE: `{"needs": [], "deferred_needs": "<absent>"}`.
Conversation AFTER: `{"needs": [], "deferred_needs": []}`.
Changed primary IDs: none. Shared primary failures AFTER: none.
Primary status remains unresolved and is not scored or used as a headline. Only independently approved assertions are evaluated.

## Model-variation cases

A differing raw patch prevents a high-confidence deterministic attribution even if some extracted values are equivalent. R05/R10 and every other differing patch are enumerated below; none establishes a causal effect from one sample.
- R04: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R05: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R06: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R10: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R11: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R13: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R15: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R16: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R20: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R21: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R22: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R23: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R24: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R28: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R29: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.
- R30: raw patch differs; model stochastic variation or interaction with deterministic processing cannot be separated here.

## Remaining failures

- R05 / supported_fields.retrieved.quantity (LIMITED_CONSENSUS): FAIL -> FAIL; expected `1000`, AFTER observed `1000`.
- R11 / supported_fields.retrieved.quantity (LIMITED_CONSENSUS): FAIL -> FAIL; expected `600`, AFTER observed `600`.
- R14 / supported_fields.retrieved.quantity (LIMITED_CONSENSUS): FAIL -> FAIL; expected `2000`, AFTER observed `2000`.
- R18 / primary_status.status (MAJORITY): FAIL -> FAIL; expected `CLARIFY`, AFTER observed `DECLINE`.
- R20 / primary_status.status (HIGH_CONSENSUS): FAIL -> FAIL; expected `RECOMMEND`, AFTER observed `NEEDS_REVIEW`.
- R24 / supported_fields.retrieved.quantity (LIMITED_CONSENSUS): FAIL -> FAIL; expected `300`, AFTER observed `300`.
- R28 / primary_status.status (MAJORITY): FAIL -> FAIL; expected `RECOMMEND`, AFTER observed `NEEDS_REVIEW`.
- R30 / primary_status.status (HIGH_CONSENSUS): FAIL -> FAIL; expected `RECOMMEND`, AFTER observed `NEEDS_REVIEW`.

Four resolved quantity FAILs (R05/R11/R14/R24) are exact-type mismatches: numeric expected quantities versus equal-valued CSV strings in recorded order.pieces. They are retained exactly as emitted by the frozen scorer, but do not establish incorrect quantity values. The other four FAILs are status disagreements: R18 CLARIFY vs DECLINE; R20/R28/R30 RECOMMEND vs NEEDS_REVIEW. These failures occur in both runs.

## Unsupported / unresolved assertions

All canonical exclusions, reason codes, observations and NOT_SCORABLE transitions are in the machine artifact. Required/forbidden semantic flags and unsupported history/quote/prose claims do not become executable through consensus alone. Baseline missing deferred-needs evidence blocks pairing. R06/R16 unresolved primary statuses are excluded. Newly available AFTER-only evidence is reported as coverage.
Excluded transitions: {'NOT_SCORABLE -> NOT_SCORABLE': 31, 'NOT_SCORABLE -> PASS': 18}. AFTER-only PASS checks are coverage gains, not paired wins. Ranking evidence is unavailable BEFORE under the current tool-source evidence contract; no negative performance inference is made.

## Comparison with original provisional results

- Qualitatively unchanged: recorded execution completes 30/30 per version; observable duplicate clarifications decrease; R14 refusal path changes with identical raw extraction.
- Stronger: assertion approval allows independently supported assertions in formerly whole-case suppressed policy-sensitive cases. The shared denominator and consensus-strength split make the permitted claims explicit.
- Weaker: provisional R14 required-flag gains cannot be restated as consensus-scored gains because flag concepts lack executable coverage. Equivalent rather than identical model patches do not justify high-confidence deterministic attribution.
- No longer scoreable: provisional R02 date_uncertain and blanket forbidden-needs expectations are not inherited without canonical approval; R06/R16 primary statuses remain unresolved.
- Newly scoreable: approved fields/status/needs and structured operational predicates can now be assessed independently in formerly suppressed cases, including approved assertions in R03/R15/R19/R29. Deferred-needs AFTER evidence is a coverage gain only when BEFORE lacks it.
- Original provisional comparison used 414 shared provisional checks with 406 -> 410 PASS, plus separate integrity audits. Its labels and denominator differ from this consensus benchmark, so numerical deltas across benchmarks are not performance trends.
- Newly visible disagreements include R18/R20/R28/R30 status and four retrieved-quantity type mismatches. These do not represent newly introduced AFTER regressions.

## Limitations

- One stochastic run per version; no variance or generalization estimate.
- Assertions overlap and are not independent observations.
- No full prose claim ledger or rendered UI faithfulness grading.
- Baseline deferred state is absent; coverage gains are not paired performance improvements.
- Integrity audits are separate from consensus-approved primary assertions.
- Provenance scoring dispositions predate the assertion adapter; current support_kind and actual outcomes determine executability.

## Defensible headline results

On 247 shared evaluable assertions approved under the AI-consensus canonical-v2 benchmark, BEFORE has 238 PASS and AFTER 239 PASS; 1 FAIL -> PASS and 0 PASS -> FAIL. This is a controlled single-run before/after comparison, conditional on frozen evidence and executable coverage.
Supplemental shared integrity audits: 6 FAIL -> PASS, 0 PASS -> FAIL. These are outside the primary consensus denominator.

## Freeze decision

Safe to freeze as reproducible final outputs from the specified unchanged scorer, with the quantity type-mismatch qualification attached. An unqualified semantic correctness claim is not supported. No technical execution failure required a scoring rerun. All protected inputs and old outputs are unchanged. No staging, commit, push or PR occurred.

## Final protection check

All 95 protected file hashes and all new score output hashes match. `git diff --check` passes. Full before/after Git status is in `results/ai-consensus-v2-final-protection-check.json`.

```text
 M docs/RELIABILITY_BENCHMARK.md
 M docs/RELIABILITY_SCORER.md
 M src/dss5105/reliability_score.py
?? docs/reliability_review/
?? examples/canonical_ai_review_packet_v2.json
?? examples/reliability_ai_consensus_status_v1.json
?? examples/reliability_benchmark_ai_consensus_v1.json
?? examples/reliability_benchmark_ai_consensus_v1_provenance.json
?? examples/reliability_benchmark_ai_consensus_v2.json
?? examples/reliability_benchmark_ai_consensus_v2_provenance.json
?? src/dss5105/reliability_assertions.py
?? tests/test_reliability_assertions.py
```
