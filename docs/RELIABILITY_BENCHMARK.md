# Reliability benchmark data contract

This is a data layer only. It does not implement scoring or invoke a model.
`examples/reliability_benchmark.json` contains R01-R30, all development-exposed,
with provisional expectations pending independent adjudication. Neither the
existing rubric, fixtures, historical run, nor this representation is independent
gold. No independently authored or frozen held-out dataset is included.

## Envelope and context

The benchmark uses `schema_version = reliability-case-v1` and a `cases` array.
The envelope records artifact kind, annotation status, independent-gold status,
creation date, freeze status, limitations, and a shared context. Context identifies
the independent 2026-04-01 workshop queue snapshot, registered-order preview scope,
default objective weights, explicit preference overrides, and SHA-256 hashes of
the source data, provisional labels, historical report, and regression knowledge.
Hashes identify the source context; they do not mean annotations are frozen.

### Portable source-integrity hashes

`context.source_sha256` maps each source path to its SHA-256 digest.
The additive `context.source_hash_modes` map uses exactly the same paths and
declares how each digest is computed. There is no implicit mode or automatic
file-extension/binary detection. The shared offline helper is
`src/dss5105/benchmark_integrity.py`. It reads bytes, not newline-translated text.

- `normalized_text_sha256`: explicitly declared UTF-8 text only. Validate UTF-8,
  replace CRLF with LF, then remaining lone CR with LF, and hash the resulting
  bytes. LF, CRLF, and lone-CR checkouts have the same hash. Do not change Unicode,
  BOMs, other whitespace, or the presence/absence of a final newline.
- `raw_bytes_sha256`: hash the original bytes without decoding or normalization.
  Use this for byte-exact course sources and any future binary source. LF and
  CRLF versions intentionally differ. Unknown modes are rejected.

| Source | Hash mode |
|---|---|
| `examples/chat_rubric.json` | `normalized_text_sha256` |
| `examples/dispatch_inputs.json` | `normalized_text_sha256` |
| `docs/CHAT_EVALUATION_RESULTS.md` | `normalized_text_sha256` |
| `tests/test_intake.py` | `normalized_text_sha256` |
| `tests/test_dispatch.py` | `normalized_text_sha256` |
| `tests/test_chat_ui.py` | `normalized_text_sha256` |
| `track2/data/dispatch_requests.txt` | `raw_bytes_sha256` |
| `track2/data/orders.csv` | `raw_bytes_sha256` |
| `track2/data/workshops.csv` | `raw_bytes_sha256` |

The six normalized-text sources are ordinary Git-normalized text; their previous
Windows-working-tree CRLF digests were replaced by LF-normalized digests. The three course-source digests are unchanged. `.gitattributes` keeps
`track2/**` byte-exact with `-text`; do not normalize those files to make a test pass.
No arbitrary binary data is normalized. Synthetic and real-source checkout tests
exercise the explicit modes without changing tracked source files.

## Case fields

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Unique case ID |
| `raw_text` | string or null | Exact request text; required for scoring |
| `speaker` | string or null | Requester, not necessarily the constraint imposer |
| `split` | enum | `development` or independently authored `held_out` |
| `scenario_family` | string | Semantic family for later leakage-aware partitioning |
| `categories` | string array | Overlapping behavior labels, not disjoint counts |
| `expected_status` | string or null | Expected top-level initial-response status |
| `expected_fields` | object | Partial assertions on normalized request fields, not raw model patches |
| `expected_resolved_fields` | object | Partial assertions on retrieved `order.*` and constructed `batch.*` fields |
| `forbidden_fields` | string array | Request keys that must be absent or null; defaults are not forbidden |
| `required_needs` | string array | Needs required in reconciled pending state |
| `forbidden_needs` | string array | Needs forbidden even when deferred |
| `expected_deferred_needs` | string array or null | Exact deferred state if specified; null leaves it unasserted |
| `expected_constraints` | object | Exact exclusion identities/provenance and recorded split intent |
| `expected_workshop_behavior` | object | Declarative candidate, refusal, alternative, and selection predicates |
| `required_flags` / `forbidden_flags` | string arrays | Positive/negative flag requirements |
| `expected_response_behavior` | object | Preview safety, question scope/count, required explanation concepts |
| `turns` | object array, optional | Future follow-ups/selections, each with its own expectations |
| `gold_annotation` | object | Status, independent-gold boolean, annotators, adjudication, exposure, evidence |
| `freeze` | object | Freeze status, timestamp, content hash, and development exposure |
| `notes` | string array | Source conflicts, interpretation limitations, pending policy choices |
| `adjudication_review` | object, development only | Review state, unresolved questions, proposed decision, evidence, blank human sign-off, and pre-review case digest |

Development cases also retain `source_time`, `course_kind`, and a separate
`historical_observation`. Historical status/workshop fields are pre-v3 report
observations, not current expected answers or post-fix model evidence. Raw historical
artifacts are absent from this checkout. Source text is preserved exactly, with
non-ASCII punctuation escaped in JSON.

Partial maps assert only listed keys. Missing keys are unspecified; an explicit
null is an asserted null. Empty required/forbidden lists impose no requirements
of that kind, not a blanket assertion that the corresponding output is empty.
`expected_deferred_needs = []` is different: it asserts no deferred needs.
For ambiguous R03/R15/R19/R29, null allows optional omitted quantity/deadline needs
to be deferred. Their response rules still prohibit premature questions about
those retrievable details. R01's explicit quantity uncertainty remains blocking.

For example, R14 has `expected_fields.pieces = null`, while
`expected_resolved_fields["batch.pieces"] = 2000`. Retrieval must not be scored
as model extraction. R05 asserts only an identified order in resolved fields:
an unknown revised deadline blocks construction/ranking of a dispatch batch.
Quote/history declines do not require a resolved allocation batch.

## Workshop and response predicates

Selection uses declarative predicates, not hardcoded recommendation winners:
minimum configured score, minimum expected turnaround, minimum defect risk, or
minimum cost among permitted on-time candidates. Current tie ordering is expected
turnaround then workshop ID. All candidates must satisfy batch eligibility and
hard exclusions. Refusal targets/reasons may name a workshop; that is different
from hardcoding a recommendation winner. `recommendation_must_be_on_time` applies
to RECOMMEND. Review/refusal alternatives can be late and must disclose it.

Response rules describe required concepts rather than exact prose. Numerical claims
must trace to the matching tool field, workshop, and snapshot. Preview commitment
and capacity reservation are disallowed. `max_questions_per_topic` limits duplicate
questions without prescribing the wording. No predicate is executed in this layer.

## Held-out authoring and adjudication

Create held-out cases independently with final request text, speaker, expectations,
source context, and `split = held_out`. Record exposure and adjudication before
freezing the dataset. Do not tune on it. Unauthored templates are rejected by the
scorer; an empty scaffold does not establish held-out coverage.

For development, all expected statuses, fields, negative assertions, needs,
constraints, workshop predicates, flags, response concepts, and category labels
still need independent adjudication. Supporting evidence pointers are provenance,
not signatures from independent annotators. Shipping dates matching recorded due
dates (R06/R16), incomplete new-order scope (R10), and conditional split semantics
(R23) explicitly retain policy caveats. Historical weaknesses inform provisional
negative checks but do not override current Data v3 expectations.

Lightweight tests validate the structure, source fidelity, separation of request
and resolved fields, provisional labeling, and absence of frozen held-out claims.
They do not establish semantic correctness, independent agreement, or model accuracy.

## Development review metadata

`docs/RELIABILITY_GOLD_REVIEW.md` is the R01-R30 review worksheet.
The canonical review record is each case's JSON `adjudication_review` object in
`examples/reliability_benchmark.json`, including questions, confidence, evidence,
recommended decision, and blank human sign-off. Markdown is a human-facing
documentation view of that record, not a second machine-readable schema. Tests
validate JSON and the worksheet's existence; they do not parse prose or require
exact Markdown rows. Keep the worksheet current when review metadata changes;
documentation drift is handled by human review, not a brittle Markdown parser.
`adjudication_review.state` is one of `READY_FOR_GOLD`, `NEEDS_POLICY_DECISION`,
`NEEDS_SOURCE_VERIFICATION`, or `NEEDS_WORDING/EXPECTATION_REFINEMENT`.
`unresolved` is false only for READY_FOR_GOLD; all other states have explicit
`questions`. READY means ready for independent annotation under the shared scope,
not finalized gold. Confidence concerns provisional semantics, not measured accuracy.
`recommended_decision` is a proposal; `reviewer`, `adjudicator`, and `human_decision`
remain null until humans supply them. The existing `gold_annotation` and freeze
metadata retain their provisional/not-frozen meanings regardless of review state.

`reviewed_case_sha256` identifies the exact pre-review case values. It is SHA-256
of UTF-8 JSON with sorted keys, ASCII escaping, and compact separators, excluding
only `adjudication_review`. It is a review-integrity marker, not a freeze hash.
Any later semantic refinement requires a new review rather than silently changing
the values covered by the marker.

## Alternate assertion-consensus benchmarks

The scorer accepts optional per-case `consensus_assertions` without changing the
original provisional benchmark. Each row contains `assertion_family`,
`assertion_key`, `consensus_value`, `consensus_level`, and `valid_reviewer_count`.
Accepted levels are HIGH_CONSENSUS or MAJORITY with at least three valid reviewers,
and LIMITED_CONSENSUS with exactly two. UNRESOLVED is disabled. Optional
`score_assertion: false` disables an accepted row; a supplied `scorer_mapping`
must match the mapping derived from its identity. Duplicate identities are invalid.

Approval is specific to the assertion; it does not approve other expectations in
the case or make this independently adjudicated gold. Policy-sensitive metadata
is retained. Rows absent from the approval list are not synthesized from legacy
expectations. Unresolved assertions retained only in provenance remain outside
scoring denominators. Unsupported approved rows are reported NOT_SCORABLE.
See RELIABILITY_SCORER.md for deterministic evidence requirements and output IDs.
