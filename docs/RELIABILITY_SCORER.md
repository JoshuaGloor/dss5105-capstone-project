# First offline reliability scorer contract

This scorer reads saved artifacts; it never invokes a model, interprets intake,
replays dispatch, mutates queues, or changes benchmark labels. It is separate from
the live recorder. No current benchmark case is independently adjudicated gold.
READY_FOR_GOLD is provisional readiness for human review, not approval.

## Reporting tracks and eligibility

Each assertion has one annotation basis: `adjudicated`, `provisional`, or
`integrity_audit`. Aggregates are keyed by both metric and basis. A case enters the
adjudicated track only when `gold_annotation.status=independently_adjudicated`,
`independent_gold=true`, nonempty named annotators, adjudicator and adjudication
date, and no pending adjudication items are recorded. Partial or contradictory
gold metadata is rejected, not promoted. An unresolved review overrides either
semantic track; no subfield approvals are inferred.

R01, R03, R06, R10, R15, R16, R19, R23 and R29 currently suppress all
benchmark-dependent assertions as UNRESOLVED_POLICY. Explicit integrity-only
checks (execution completion, observable repeated standard questions, and the
source-compatible tool audit) remain available. No partial approval ledger is
implemented. Held-out authoring templates are rejected as evaluable benchmarks.

## Outcomes and counting

| Outcome | Meaning |
|---|---|
| PASS | An eligible, observable assertion is satisfied |
| FAIL | An eligible assertion is violated, with evidence |
| NOT_APPLICABLE | No requirement or applicable predicate is declared |
| UNRESOLVED_POLICY | Acceptance depends on an unresolved human decision |
| NOT_SCORABLE | Artifact, context, or necessary evidence is absent/incompatible |

Correctness/recall numerators count PASS; violation-rate numerators count FAIL.
Denominators count only PASS plus FAIL. Zero denominator yields JSON null, never
100 percent. Every aggregate reports all five outcome counts and evaluability
coverage. Empty tracks are emitted explicitly, including zero adjudicated
denominators for the current benchmark. There is no combined overall accuracy.
The report lists planned, attempted, and unattempted benchmark cases. Missing
records do not count as attempted. Provider/parsing/validation/tool failures count
against operational completion and are tabulated separately. For a compatible,
attempted, eligible case, execution failure also FAILs status delivery; other
unobservable assertions are NOT_SCORABLE. An attempted record with missing/unknown
execution status fails operational completion and is recorded as unknown; its
semantic status is NOT_SCORABLE.

Partial expected maps assert only listed fields. Explicit null requires an observed
null; missing fields are NOT_SCORABLE and are represented with `observed_missing`,
not silently converted to null. Comparison preserves JSON types, including
bool versus int and int versus float. Forbidden fields allow absence or null;
zero/false/empty string remain non-null violations. Null expected status or null
deferred expectation is NOT_APPLICABLE. An empty deferred list is an exact
empty-set assertion. Required/forbidden empty lists create NOT_APPLICABLE checks.

## Implemented metrics

| Metric | Unit and numerator / denominator |
|---|---|
| operational_completion | completed / attempted records |
| request_field_correctness | matching expected request fields / evaluable declared fields |
| request_exact_match | cases with all expected fields matching / fully evaluable request maps |
| forbidden_field_violation_rate | non-null forbidden keys / observable forbidden-key assertions |
| status_correctness | expected status delivered / compatible attempted eligible cases |
| resolved_field_correctness | matching dotted order/batch values / evaluable declared paths |
| required_needs_recall | required codes present / observable required codes |
| forbidden_needs_violation_rate | forbidden codes present / observable forbidden-code assertions |
| deferred_needs_correctness | exact sets matching / observable specified sets |
| required_flags_recall | required flags present / observable required flags |
| forbidden_flags_violation_rate | forbidden flags present / observable forbidden-flag assertions |
| exclusion_recall | expected workshop IDs present / observable expected exclusions |
| exclusion_exactness | cases with exactly the expected ID set / observable exclusion sets |
| constraint_application | expected exclusions absent from candidates and choices / observable expected-exclusion checks |
| duplicate_standard_clarification_rate | responses repeating a known standard question / responses containing at least one known standard question |
| tool_integrity | source-compatible previews passing the wrapped audit / auditable previews |

Exclusion identity checks deliberately do not grade full evidence/reporter
provenance. Duplicated actual exclusion IDs FAIL exactness. Constraint application
uses benchmark hard exclusions, not merely extracted exclusions, and examines
candidate IDs, recommendation and alternative. Missing selections/candidates are
NOT_SCORABLE rather than assumed empty. Resolved fields never fill extraction.

Duplicate checking only counts exact occurrences of the five standard question
strings in the current recorded message. It does not import the intake module,
infer semantic topics, judge paraphrases, or use unresolved per-case question limits.
No known question yields NOT_APPLICABLE, not a perfect duplicate-free result.

The tool wrapper preserves the existing `check_tool_integrity` contract using
independent assertions and official offline helpers; it never calls the live runner. It
constructs a fresh read-only source desk only after compatibility checks. It also
closes the old checker's empty-candidate completeness gap for resolved ranked
batches. Eligibility is delegated to the official helper. CLARIFY/DECLINE
previews are not required to contain ranked candidates. Wrapper errors caused by
missing legacy fields are NOT_SCORABLE; observed audit errors are FAIL. This is
a partial tool audit, not independent numerical explanation or policy correctness.

### Partial evidence and established failures

Known violations take precedence over unrelated missing evidence. A forbidden
workshop observed in any candidate, recommendation, or alternative FAILs
constraint_application even when other parts are unavailable. Without an observed
violation, incomplete evidence stays NOT_SCORABLE. A separate
constraint_application_evidence assertion records the gap without diluting the
primary per-exclusion denominator.

The tool wrapper accumulates errors and incomplete components separately. It
checks commitment, identities/names, candidate set, choices, deadline, numerical
candidate components, and split components independently. Candidate display checks (ETA, duration, lateness, cost, defects, score, queue,
processing, transport, and expected rework) and deadline consistency are evaluated
independently. Each produces a tool_candidate_integrity assertion; missing evidence
for one cannot erase another failure. Candidate assertion aggregates are separate
from the per-preview tool_integrity aggregate, with no combined score. Selection
membership and cheapest-on-time policy checks are separate from candidate display
validation. Split checks are independent tool_split_integrity assertions for total pieces,
part count, each part identity/membership/eligibility and recomputed estimate,
finish, savings, and each existing summary display field. They preserve the
existing audit contract without adjudicating split policy. Missing summary or
part evidence cannot erase other established violations. Candidate, split and
per-preview aggregates remain separate; there is no combined score. Recorded
observations are never modified.
Errors from completed components survive exceptions in later components.
The primary tool_integrity outcome is FAIL if any error is established, otherwise
NOT_SCORABLE if any component is incomplete, otherwise PASS. Separate
tool_integrity_evidence assertions identify incomplete components as NOT_SCORABLE;
they are not additional per-preview correctness votes.

Forbidden needs inspect both observed needs and deferred_needs. A forbidden code
in either list FAILs even if the other list is missing/invalid. Absence PASSes only
when both lists are observable and valid. The integrity_audit metric
deferred_needs_invariant independently requires deferred_needs to be a subset of
needs. A violated subset is FAIL, missing/invalid state is NOT_SCORABLE, and a valid
subset is PASS. The scorer never repairs inconsistent artifacts. This structural
audit remains available on unresolved cases without approving any semantic needs.

## Compatibility and input shape

Join exclusively on outer `record.request.request_id`; preview.request may use
CHAT. Duplicate record IDs and IDs absent from the benchmark are rejected. Text
and speaker must match the benchmark exactly. A per-case compatibility result
records all problems before any semantic comparison. Incompatible cases are
NOT_SCORABLE (unresolved cases remain UNRESOLVED_POLICY with incompatibility noted).
Operational completion can still describe their execution outcome.

The benchmark's source hashes and modes must match the supplied source checkout.
Normalized UTF-8 text hashes and raw course hashes use the shared portable helper.
Manifest `source_hashes` must include the three benchmark course files with exact
raw hashes, plus the current official simulate.py hash for tool auditing. Manifest
snapshot_date and default objective weights must match benchmark context. When a
preview exists, its snapshot as_of, sources, complete queue map, and configured
weights must match the manifest/context and workshops.csv queue values. Missing
or different snapshot evidence prevents semantic scoring. Case-level explicit
preferences may override effective weights; they do not change configured weights.
Context numeric maps permit equivalent JSON integer/float encodings, while
rejecting booleans/non-finite values. Request/resolved assertions remain type-exact.

Run code/prompt versions may differ intentionally and are retained as provenance;
they are not required to equal current code. The tool wrapper is explicitly a
current-audit-contract diagnostic against verified source data, not reconstruction
of a historical implementation. Unknown legacy display shapes are NOT_SCORABLE.
Recorded estimates/displays are never recomputed into replacement observations.

Inputs can be a recorder directory with manifest.json and Rxx.json files, or a
JSON bundle with `manifest` and `records`. A single saved record requires a separate
--manifest path. Source type is explicitly selected as `recorded_model_run`,
`structured_fixture`, or `synthetic`. Fixture/synthetic scores must not be presented
as model performance. No historical rubric pass/fail is used as the expected answer.

## Outputs and CLI

```
uv run python -m dss5105.reliability_score --input results/saved-run --output results/scored-run
```

Optional arguments: --benchmark, --manifest (single-record input), --source-root,
--source-type, and --no-tool-audit. The output must be a fresh directory inside
the repository, outside input directories, with no existing files overwritten.
All inputs are read before outputs are created. Input validation failures do not
create output files. No credentials/raw provider exceptions are copied into reports.

- cases.jsonl: stable case order, execution, compatibility, and assertion objects.
- summary.json: metric/basis entries, numerators, denominators, values, outcome
  counts, coverage, execution-failure counts, and planned/attempted/unattempted IDs.
- summary.md: human-facing metric and coverage summary, explicitly diagnostic.
- checks.csv: one row per assertion; complex expected/observed values use JSON.
- manifest.json: benchmark content hash, scorer version/content hash, input artifact
  hash, source type, benchmark annotation state, configuration, compatibility, and
  recorded-run provenance. Directory input hashes use sorted relative-path/digest
  pairs for the consumed manifest and case files. Serialization is deterministic:
  sorted JSON keys, UTF-8 ASCII escapes, LF output, no clock or random values.

Each assertion contains id, group, metric, annotation_basis, outcome, expected,
observed, reason_code and evidence_paths; observed_missing distinguishes absent
evidence from observed null. CSV/JSON reasons are stable machine-readable codes.
JSON is the canonical scoring output. No Markdown review prose is parsed.

## Deferred scope

No workshop-policy winner grading beyond the existing integrity audit, full
clarification precision, semantic duplicate detection, numerical prose claims,
unsupported operational prose, rendered UI cards, actual reservation/side effects,
semantic explanation concepts, or multi-turn preservation scoring is implemented.
These require richer captured evidence or independently approved acceptance rules.
No evaluator, prompt, model schema, intake/dispatch/allocator behavior, or official
eligibility rule is modified by this scorer.
