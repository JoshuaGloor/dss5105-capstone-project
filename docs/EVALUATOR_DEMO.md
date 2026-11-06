# Offline evaluator mechanism and local demo

This walkthrough covers the evaluator in the reliability branch. The optional
HTML report improves diagnosis and presentation. It does not change scoring
rules, add human gold, improve the model, or rerun the held-out test set.
The demo makes no provider calls and writes no allocation queues.

## Three different evaluation paths

| Module | Input | Role | Model use |
|---|---|---|---|
| `evaluate.py` | Structured orders, policies, seeds | Shared-simulator allocation metrics and baselines | None |
| `evaluate_chat.py` | Requests and rubric | Live run, model patches, previews and preliminary rubric checks | Paid and opt-in |
| `reliability_score.py` | Saved run plus benchmark | Deterministic assertion scoring and partial tool audit | None |

This demo covers the third path. A saved artifact contains a request envelope,
execution status and preview. Its manifest declares source hashes, date, weights
and available model/prompt provenance. The benchmark supplies expected fields,
behavior, constraints, review state and source context. The evaluator does not
ask a new LLM to judge an old LLM.

## Scoring pipeline

1. Validate benchmark shape, case identities, duplicate IDs and approval metadata.
2. Load records from a directory, bundle or single record with manifest.
3. Verify source hashes, date, queues, weights, request text and requester.
   Incompatible semantic evidence is NOT_SCORABLE. Execution and other independent
   integrity observations remain available rather than erased by that gate.
4. Compare declared fields. Extraction and retrieved fields stay separate. JSON
   types matter; missing evidence is different from an observed null.
5. Check needs, flags and exclusions. Audit source-compatible tool outputs:
   candidate identities, eligibility, choices, displayed values and split evidence.
   Eligibility uses the official course helper.
6. Apply review gates. Unresolved legacy cases withhold benchmark-dependent
   assertions. The optional explicit assertion-approval adapter scores supported
   approvals; AI consensus does not become independently adjudicated human gold.
7. Aggregate by metric AND annotation basis, then export canonical files and
   optional HTML. There is no overall accuracy across overlapping assertions.

Candidate display checks compare formatted values with that candidate's saved
estimate. They do not independently recompute every raw candidate estimate from
source data; split estimates have a separate recomputation check. A consistent
corruption of a raw estimate and its display can escape this partial audit.

### Outcomes and annotation bases

| Outcome | Meaning |
|---|---|
| PASS | Observable eligible assertion is satisfied |
| FAIL | Evidence establishes a violation |
| NOT_SCORABLE | Necessary evidence/context is missing or incompatible |
| UNRESOLVED_POLICY | Acceptance requires an unresolved human/policy decision |
| NOT_APPLICABLE | No applicable requirement is declared |

The bases are `provisional`, `adjudicated` and `integrity_audit`. The supplied
benchmark is provisional. READY_FOR_GOLD means ready for review, not approved
gold. Exact standard-question repetition is checked; semantic paraphrase
repetition is outside this contract.

Per metric/basis, the denominator is PASS + FAIL. Correctness/recall counts PASS;
violation metrics count FAIL. Coverage is
`(PASS + FAIL) / (PASS + FAIL + NOT_SCORABLE)`.
UNRESOLVED_POLICY and NOT_APPLICABLE are excluded. A zero denominator yields null.

Example only: 8 PASS, 2 FAIL and 5 NOT_SCORABLE gives correctness 8/10, coverage
10/15, or violation rate 2/10 for a violation metric. This is not overall model
accuracy. Correlated assertions are not independent samples.

## Lightweight improvement

Add `--html-report` to the offline CLI. The default five files are retained. With
the flag, `report.html` is added and the manifest records the renderer hash.
The report uses local CSS/JS and escaped scored data, without raw provider logs.

- Compatibility, missing records and attempted/planned counts appear first.
- Filter by case, outcome, annotation basis or text. Attention defaults to FAIL
  plus NOT_SCORABLE; use Show all to inspect passing and unresolved checks.
- Expand an assertion for expected/observed values, missing-value markers,
  reason codes and existing evidence paths.
- Each metric retains its own denominator and coverage. JSON/CSV remain canonical.

No scoring result changes when HTML is enabled. Known failures retain precedence
over unrelated gaps. Assertion counts are not request pass rates. The HTML cannot
call a provider, rescore records, alter labels or commit an allocation.

## Run locally on Windows

Open PowerShell and change to the checkout containing this evaluator demo:

```powershell
cd D:\DESKTOP\dss5105\Capstone_Project\pr14-conflicts-ci
.\scripts\run_evaluator_demo.cmd
```

The launcher sets a repository-local uv cache and UTF-8 mode and runs:

```powershell
uv run python -m dss5105.evaluator_demo
```

No API key or Streamlit server is needed. For a fresh environment first run
`uv sync --locked --all-groups`. The demo prints the absolute path of index.html
in a fresh timestamped `results/evaluator-demo/` directory. Open it directly in
Chrome; no browser is launched automatically. Existing runs are never overwritten.

Choose a new output directory explicitly if desired:

```powershell
.\scripts\run_evaluator_demo.cmd --output results/evaluator-demo/my-new-recording
```

Keep the generated directory together: index.html links to six reports and their
disclosed synthetic input JSON.

### Six scenarios

Four requests (R01, R04, R14, R25) use existing handcrafted development fixtures.
The generator uses Python read-only previews BEFORE scoring. The evaluator then
reads saved JSON and never replays dispatch. All scenarios keep the same benchmark
cases and labels. These are disclosed fault injections, not observed model errors
or held-out performance.

| Folder | Evidence change | R04 tool_integrity |
|---|---|---|
| `01-clean` | None | PASS |
| `02-wrong-cost` | First displayed cost changed to 999,999.00 | FAIL |
| `03-missing-cost` | First displayed cost removed | NOT_SCORABLE |
| `04-failure-and-gap` | Wrong cost plus missing meets_deadline | FAIL; gap separately visible |
| `05-incompatible` | Manifest weight changes without preview | NOT_SCORABLE |
| `06-unattempted` | R04 record omitted, benchmark retained | NOT_SCORABLE; 3 attempted / 4 planned |

R01 exposes UNRESOLVED_POLICY for benchmark-dependent assertions. Execution and
applicable integrity checks remain separate. R14 demonstrates an ineligible
workshop refusal; R25 retains a workshop exclusion.

## Recording walkthrough of about four minutes

1. Explain saved run + benchmark and no new model call. Point to the synthetic
   disclosure and four planned cases on index.html.
2. Open `01-clean`, select R04 and PASS. Expand an assertion and identify
   compatibility, outcome, basis and evidence paths.
3. Open `02-wrong-cost`, select R04 and FAIL, search cost. Expand the failed cost
   assertion; clear search and expand tool_integrity.preview for its descriptive
   error. The Input JSON link shows the injected 999,999.00.
4. Open `03-missing-cost`, select R04 and NOT_SCORABLE. Then show
   `04-failure-and-gap`: missing evidence cannot conceal a known wrong value.
5. Open `05-incompatible` and inspect configured_weights_mismatch. Show
   `06-unattempted` with 3 attempted / 4 planned. In any report, select R01 and
   UNRESOLVED_POLICY to explain policy review limits.
6. Scroll to denominators and provenance hashes. Explain that the enhancement
   improves reproducibility and debugging, not model accuracy.

## Use on actual saved evidence

```powershell
uv run python -m dss5105.reliability_score --input results/saved-run --output results/scored-review --source-type recorded_model_run --html-report
```

Use a fresh output directory and matching benchmark/source checkout. Do not edit
hashes to force incompatible evidence to pass. Preserve its original snapshot or
use its matching benchmark. The default benchmark covers development inbox cases;
a separate 65-case run needs a compatible authored benchmark, not just a renamed
input file. Recorded model outputs remain separate from these synthetic examples.

## Remaining improvements

1. Independent labels/adjudication and a frozen current version, then a separately
   authorized 65-request run with agreed provider costs.
2. Independent recomputation of raw candidate estimates, plus a claim ledger
   binding rendered explanations to request, workshop, snapshot, field and rounding.
   Existing display consistency checks are partial.
3. Multi-turn traces for necessary clarification, persistent constraints, order
   switching and semantic question repetition. Single-turn results do not prove these.
4. Repeated live runs and paired comparisons on held-out wording; report uncertainty
   and failure categories without using assertion count as sample size.

## Validation and review boundary

Tests cover deterministic projection, HTML escaping, missing versus null, all six
fault conditions, canonical-file equivalence, fresh-output protection and no model
calls. Run:

```powershell
uv run pytest tests/test_reliability_report.py tests/test_reliability_score.py
```

Keep the pull request open for team review before merging. Local test success
is not a GitHub CI or model-performance result. See
[RELIABILITY_SCORER.md](RELIABILITY_SCORER.md) for the full contract and limits.
