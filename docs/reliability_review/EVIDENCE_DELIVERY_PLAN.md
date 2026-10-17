# Local evidence package and pending external delivery

Status: local commits and packaging authorized by the user on 2026-10-17. The
package is created and verified locally; external delivery remains unapproved
and not performed. Original bytes were copied into the archive and a local
verification extraction, without modifying, moving or deleting originals. No live
API, model evaluation, scoring rerun, push, PR, upload or sharing occurred.

## Selected split

Git receives the 23 exact files grouped in PRE_PUSH_COMMIT_PLAN.md and
COMMIT_SELECTION.json. Existing production fixes, tests and the original
provisional benchmark are already in local history and are not selected again.

The separate local evidence package contains raw reviewer responses, both frozen
recordings, final scores/comparison and referenced historical audit dependencies.
The exact per-file inventory is EVIDENCE_PACKAGE_MANIFEST.json: source-root tag,
relative source path, proposed package path, byte size, SHA-256, category and
delivery/privacy status. The verified archive remains local under ignored results/.

Caches, temporary databases, reproduction scripts, redundant result copies and
logs without delivery value stay local. The four useful validation records listed
in the manifest are retained for the reported test/compatibility claims; their
metadata still needs privacy approval.

## Package size and contents

108 files total **10,605,790 bytes uncompressed** (10.61 MB; 10.11 MiB).
This excludes the Git checkout and controls. The completed ZIP is
1,175,236 bytes. It contains 111 entries: 108 original evidence
files plus 3 controls, totaling 10,668,566
uncompressed bytes. Original source hashes remain unchanged.

| Evidence category | Files | Uncompressed bytes |
|---|---:|---:|
| Raw reviewer sources and non-voting QA | 6 | 233,195 |
| Frozen BEFORE recording | 33 | 1,280,267 |
| Frozen AFTER recording | 33 | 1,298,218 |
| Final canonical-v2 scoring outputs | 10 | 2,013,408 |
| Final comparison JSON and freeze/protection records | 3 | 1,971,554 |
| Earlier provisional scoring outputs | 10 | 2,278,635 |
| Earlier comparison JSON | 1 | 67,862 |
| Referenced historical v1/non-voting materials | 5 | 1,364,395 |
| Historical preparation manifest | 1 | 11,393 |
| Useful validation evidence | 4 | 81,779 |
| Compatibility-run manifests | 2 | 5,084 |

The eight compatibility result copies omitted from the package are byte-identical
to earlier scoring files already included. Their paths, hashes and equivalent
package destinations are in byte_identical_duplicates_kept_local. No duplicate
or original file was deleted. The two different compatibility manifests remain
in the package to retain scorer-version metadata.

## Portable layout

The verified archive has these top-level folders (plus three root controls):

```text
repository/
  docs/reliability_review/   raw reviews and historical snapshots
  examples/                 referenced historical v1 artifacts
  results/                  saved evidence, scores and useful validation records
dss5105-baseline-bea5028/
  results/chat-baseline-bea5028-first/
```

After approval, a recipient would overlay repository/ onto the matching Git
checkout and place dss5105-baseline-bea5028/ beside that checkout. The checkout's
own directory name is unrestricted. The existing sibling reference
../dss5105-baseline-bea5028/results/chat-baseline-bea5028-first then resolves
without the author's drive letter, desktop path or username. This describes a
future recipient layout. A local validation extraction was created and verified;
no recipient delivery directory or external transfer was created.

Old absolute paths in immutable JSON/Markdown are historical provenance values.
Use the manifest's relative paths and EVIDENCE_REFERENCE_MAP.json instead of
executing old hard-coded paths. Do not rewrite evidence just to make paths local.
The original baseline Git worktree itself is not required to inspect these
recordings: all 33 recorder files, including source_snapshot.json, are inventoried.

## Reference coverage and dependencies

The checked reference map covers explicit structured paths in canonical
provenance/manifests and explicit repository-prefixed paths in selected reports.
Every original planned file exists. Critical evidence routes are:

| Reference | Proposed availability |
|---|---|
| Current scorer, adapter, tests, canonical packet/benchmark/provenance and core reports | Proposed commits A/B/C |
| Existing runtime code, course CSVs, simulator, original benchmark and provisional comparison report | Existing Git history/checkout |
| All five inventoried reviewer identities and their original files; QA | Separate package; Claude is retained as excluded evidence, not a voter |
| Frozen BEFORE/AFTER manifests, R01-R30, source snapshots and summaries | Separate package |
| Final score files and comparison JSON | Separate package |
| Non-voting workbook, v1 adjudication/consensus materials and old scores | Separate package because current provenance/reports reference them |
| Earlier test/compatibility result evidence | Selected useful records in package; duplicate results map to equivalent bytes |

Five external source locations retained in v1 provenance are not extra delivery
dependencies: their repository_copy paths and recorded SHA-256 values match
local package-selected files. JSON references ending in :cases.Rxx identify a
location inside an existing provenance JSON, not a missing filename. Example CLI
paths results/saved-run and results/scored-run are placeholders, not evidence.
The audit's src/tests/scripts text is shorthand for directories, not a file.

No missing critical file or unresolved external artifact remains in the checked
scope. This is not an exhaustive parser of all prose/bibliographic citations or
embedded historical source-code strings. Explicit directory references can
contain optional examples that are not needed for the final evaluation.

The old preparation snapshot also mentions local audit.json,
file-classification.json, pytest-cache and pytest-temp-final. These are optional
diagnostics/scratch, not dependencies for inspecting votes, recordings or final
checks. They remain local and are listed as optional exclusions, not silently
claimed delivered. Historical hashes of the two explanation documents predate
their later wording changes; the old snapshot is labeled historical and is not
used as a current checksum inventory.

The package depends on the proposed Git files and existing local Git history for
code/contracts/course facts. No provider account, external original attachment
folder, original absolute path, live API call or new model/scoring run is needed
to inspect the evidence. A future recipient needs ordinary file/JSON/PDF/Office
viewing tools; recreating an execution environment is a separate task.

## Sensitive-file review status

Known credential/private-key patterns were checked without opening .env or
printing matches. No credential pattern was detected in the scanned payload.
OOXML XML was inspected for these patterns and author metadata; PDF checking was
limited to bytes, so complete human privacy review remains pending.

The following files contain author/workstation/local-path metadata. They were
privately inspected and retained unchanged in the local-only archive. External
privacy/release approval is still pending; values are deliberately not reproduced:

- repository/docs/reliability_review/Part_A_Claude.docx
- repository/docs/reliability_review/Part_A_DeepSeek.docx
- repository/results/pre-push-validation/offline-tests.log
- repository/results/pre-push-validation/offline-tests.xml

Do not edit their originals. If the team later requires a sanitized delivery copy,
create a separately identified derivative with its own hash and provenance after
approval; do not claim that derivative is the hash-identical original. No such
copy was necessary or made for local-only storage. Raw review sharing rights,
recipient scope and complete external PDF privacy review remain pending, even
where no automated pattern was detected.

## Completed local packaging; external delivery not executed

Archive: results/reliability-evidence-2026-10-17/agent-reliability-evidence-2026-10-17.zip

SHA-256: `5d56bf0bb8d64f36b5dadd090292b2e233144b901ac47d88145cece3d636e6c3`

The archive includes PACKAGE_MANIFEST.json, README.txt and VERIFY_PACKAGE.py.
It was extracted to a new local directory, checked for the exact 111 entries,
and verified against every original/control size and SHA-256; ZIP CRC also passes.
The checksum sidecar and PACKAGING_RECEIPT.json remain beside the ZIP. Original
evidence files still match the approved 108-entry inventory.

No upload or sharing occurred. Teammate review, external privacy/permission
approval and recipient/channel choice remain pending. Any future sanitization
must use separately identified derivatives without rewriting originals. Local
commit/packaging approval is not approval to push, create a PR or deliver evidence.
