# Exact proposed local commit contents

The user authorized this exact three-group plan for local execution on 2026-10-17.
Branch: TangZheling/agent-reliability. Reviewed starting HEAD: 705614e.
A is 596a31c30ccb3bfb41fe1927192b9859511ae851; B is bfed436b8163402e1bb6c91b1e7d77d2e067d95f; C is the commit containing this
revision. The local execution receipt resolves all three final hashes. No network
refresh of the project remote, push, PR, upload or sharing was performed.

## Already committed: leave history untouched

- b5c327c: quantity reconciliation in intake and its regression tests.
- 6e562b6: dispatch clarification deduplication and tests.
- 9af09ff: dependency-aware deferred needs, UI state preservation and tests.
- 34af86e: initial benchmark framework.
- 7a38db9: original offline scorer.
- 705614e: provisional comparison and review packet.

Do not recreate these commits or stage unchanged intake/dispatch/UI files.

## Approved local commit A: scorer support

Message: `Add opt-in assertion-level reliability scoring`

These files implement and test one opt-in contract, including the documentation
correction made in this preparation:

- src/dss5105/reliability_score.py
- src/dss5105/reliability_assertions.py
- tests/test_reliability_assertions.py
- docs/RELIABILITY_SCORER.md
- docs/RELIABILITY_BENCHMARK.md

## Approved local commit B: canonical benchmark and evaluation

Message: `Add canonical-v2 AI consensus benchmark and paired evaluation`

These files connect exact requests, approved assertions, their provenance and the
qualified final comparison:

- examples/canonical_ai_review_packet_v2.json
- examples/reliability_benchmark_ai_consensus_v2.json
- examples/reliability_benchmark_ai_consensus_v2_provenance.json
- docs/reliability_review/CANONICAL_AI_REVIEW_PACKET_V2.md
- docs/reliability_review/CANONICAL_REVIEW_PACKET_V2_MANIFEST.json
- docs/reliability_review/AI_REVIEW_RESPONSE_TEMPLATE_V2.md
- docs/reliability_review/AI_CONSENSUS_CANONICAL_V2_REPORT.md
- docs/reliability_review/AI_CONSENSUS_V2_BEFORE_AFTER.md

The consensus report's scorer-compatibility section is a historical
construction-time snapshot. Current adapter support and scoreability are documented
in the final comparison and PRE_PUSH_QUALITY_AUDIT.md. Preserve historical hashes
and methodology rather than rewriting the snapshot.

The selected proposal puts raw reviewer sources in a separate evidence package,
not Git. The exact reviewer files in that package inventory are:

- docs/reliability_review/Part_A_Claude.docx
- docs/reliability_review/Part_A_DeepSeek.docx
- docs/reliability_review/Part_A_Gemini.pdf
- docs/reliability_review/Reviewer_D_Grok_4.5_Canonical_V2.md
- docs/reliability_review/AI_REVIEW_RESPONSE_COMPLETED_V2.md
- docs/reliability_review/Reviewer_D_Grok_4.5_QA.md (non-voting context)

These files are not selected for commit B. Their relative destinations, byte sizes
and SHA-256 values are in EVIDENCE_PACKAGE_MANIFEST.json. The user approved local packaging; the archive is now created and verified locally.
It has not been delivered. Teammate and external privacy/delivery approval remain
pending. EVIDENCE_REFERENCE_MAP.json maps old absolute references to Git or package
paths so critical evidence does not require the original machine's directories.

## Approved local commit C: explanation and handoff

Message: `Document reliability interpretation and evidence handoff plan`

These files provide the current explanation, audit, decisions and validation:

- docs/reliability_review/RELIABILITY_WORKSTREAM_EXPLAINED.md
- docs/reliability_review/RELIABILITY_TEAM_HANDOFF.md
- docs/reliability_review/RELIABILITY_PRESENTATION_SUMMARY.md
- docs/reliability_review/PRE_PUSH_QUALITY_AUDIT.md
- docs/reliability_review/PRE_PUSH_COMMIT_PLAN.md
- docs/reliability_review/PRE_PUSH_READINESS.md
- docs/reliability_review/COMMIT_SELECTION.json
- docs/reliability_review/EVIDENCE_PACKAGE_MANIFEST.json
- docs/reliability_review/EVIDENCE_REFERENCE_MAP.json
- docs/reliability_review/EVIDENCE_DELIVERY_PLAN.md

COMMIT_SELECTION.json is the machine-readable exact selection: A has five files,
B eight and C ten (23 total). Every selected file exists. The three modified
tracked files belong to A; the other 20 files are untracked. These were the reviewed pre-execution states. The user approved the selection,
and the exact three groups are now locally committed in the revision containing
this plan; no group-outside file was staged. A retains the legacy benchmark contract; B
depends on A for opt-in scoring; C explains B and its evidence handoff. No extra
commit is needed for already committed production fixes.

PRE_PUSH_EVIDENCE_MANIFEST.json is no longer selected for Git. Its hashes of
RELIABILITY_WORKSTREAM_EXPLAINED.md and RELIABILITY_TEAM_HANDOFF.md predate their
wording correction. Preserve it in the proposed package as a historical snapshot,
not as a current document checksum inventory. No old manifest is overwritten.

The package manifest preserves the reviewed starting HEAD and evidence hashes,
and adds the verified local archive receipt. Local commits and local packaging
are complete; external delivery is not. Documentation execution metadata is
separate from immutable evaluation evidence.

## Exactly one category per relevant file

The expanded machine inventory is local:
results/pre-push-validation/file-classification.json. Each enumerated file has
exactly one A-I category. Explicit subtree entries classify cache contents and
the sibling frozen baseline without opening secrets or altering evidence.

| Category | Decision and current contents |
|---|---|
| A IMPLEMENTATION | Scorer files committed in A; already committed runtime/evaluator/integrity files remain unchanged |
| B TEST | Commit the new assertion test file; existing runtime/scorer tests remain tracked and unchanged |
| C BENCHMARK / CONTRACT | Commit the proposed canonical-v2/request/contracts group; preserve original provisional benchmark unchanged |
| D DOCUMENTATION | Commit the exact current report/handoff groups above |
| E REVIEWER / EVIDENCE | Raw reviewer sources and both frozen recordings are selected for the proposed separate package; old machine inventories remain local except the explicitly inventoried historical snapshot |
| F FINAL EVALUATION OUTPUT | Both final scoring directories, comparison JSON and freeze/protection records are inventoried for the separate package, not force-added to Git |
| G REPRODUCIBILITY HELPER | Historical builder/scoring/comparison scripts and this audit helper stay local; do not blindly execute scripts that write frozen targets |
| H SCRATCH / CACHE / TEMP | Test logs, test temp databases, caches and environments remain isolated and ignored; no cleanup needed to exclude them from commits |
| I HISTORICAL / SUPERSEDED | Five referenced v1/non-voting artifacts, earlier score outputs and useful compatibility manifests are included in the package proposal to close audit references; other superseded material stays local |

The existing repository tracks benchmark fixtures under examples/ and small
machine evidence under docs/evidence/. That supports committing canonical JSON
and a compact portable manifest. It explicitly ignores results/, so forcing large
raw scoring directories into Git would contradict the current convention.

Earlier RELIABILITY_WORKSTREAM_FINAL_SUMMARY.md and
RELIABILITY_LOCAL_REVIEW_AND_COMMIT_PLAN.md are retained local snapshots, superseded
by this explanation/plan set. FINAL_RELIABILITY_EVIDENCE_MANIFEST.json and
RELIABILITY_FINAL_INVENTORY.json retain machine-specific paths and earlier checks;
they are not included in the proposed commits. Old provenance paths remain intact
as audit metadata, not private credentials.

## Evidence delivery selection and review status

See EVIDENCE_DELIVERY_PLAN.md for the portable overlay layout, reference coverage,
privacy holds, size breakdown and optional local-only diagnostic references. The
package currently contains an exact inventory of 108 source files totaling
10,605,790 uncompressed bytes. Eight byte-identical compatibility result copies
remain local; the manifest maps each to the equivalent payload bytes. Four useful
validation records are included; caches, temp databases, scripts and redundant
logs are excluded.

No key evidence file is missing in the checked scope. The five historical external
reviewer-source references have hash-matching repository copies in the package;
original attachment directories are not a delivery dependency. Optional scratch
diagnostics referenced by old audit snapshots stay local and are explicitly
identified in the reference map. User authorization for local commits and packaging was received, and those
local actions are complete. Teammate review, external privacy approval and
delivery-channel approval remain pending. No transfer, push or PR occurred.

No unrelated tracked modification or accidental formatting-only diff was found.
Do not stage the whole docs/reliability_review directory: it mixes proposed docs,
raw evidence and historical material. Local commits were explicitly authorized. Teammate review and separate
authorization must precede any external delivery/push decision. .env, credentials
and local caches remain excluded.


## Completed local package

results/reliability-evidence-2026-10-17/agent-reliability-evidence-2026-10-17.zip

SHA-256: `5d56bf0bb8d64f36b5dadd090292b2e233144b901ac47d88145cece3d636e6c3`

108 original evidence files plus 3 controls were extracted and verified. See
PRE_PUSH_READINESS.md and the local packaging receipt for exact size/status.
