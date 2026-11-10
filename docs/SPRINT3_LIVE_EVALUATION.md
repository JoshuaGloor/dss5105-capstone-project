# Sprint 3 live chat evaluation

One live run of the chat intake on frozen `main`
([`01f2524`](https://github.com/JoshuaGloor/dss5105-capstone-project/commit/01f2524f7f0198886bb5c4d99499845eacc90f5a))
over the 30 supplied inbox requests and the 65 designated held-out requests. Compact
evidence, including file and artifact hashes, is in
[evidence/sprint3-live-01f2524.json](evidence/sprint3-live-01f2524.json).

## Run

| Item | Value |
|---|---|
| Date | 9 November 2026; splits started 14:51, 14:52 and 14:54 UTC |
| Runner | `python -m dss5105.evaluate_chat --live --set <split> --output results/sprint3-live-01f2524/<split>`, one fresh output directory per split; `supplied` also used `--kind-labels examples/human_request_kinds_v1.json`. The manifests do not record the exact command line |
| Model and intake | `openai:gpt-5.6`, `intake-v3` |
| Provider settings | 30 s timeout, automatic retries disabled (`max_retries=0`) |
| Objective weights | Default `ObjectiveWeights()`: lateness 1.0, all other terms 0 |
| Queue snapshot | 2026-04-01, identical source hashes in all three splits |
| Conversation | Fresh conversation per request; first response only |

All three manifests record the same model, intake version, system prompt, schema,
settings, weights and source hashes, and their file hashes match the frozen commit.
Source files are hashed with `normalized_text_sha256` from
[`benchmark_integrity.py`](../src/dss5105/benchmark_integrity.py), so a checkout
verifies them whatever its line endings; the `track2/` data and the archived run
artifacts are hashed as raw bytes.
Each split has exactly one record per expected ID, every saved request envelope
matches its source file, and no ID or normalized request text repeats across splits.
Every request completed on its first attempt. The artifacts show retries were
disabled and one record exists per ID; they cannot show whether other runs exist
in other directories.

## Answer references

The three splits use different kinds of answer reference. Read every number below
with its basis.

| Split | IDs | Role | Answer reference |
|---|---|---|---|
| `supplied` | R01-R30 | Development; inspected and used during development | Team draft rubric `examples/chat_rubric.json`. Human-reviewed request kinds (`examples/human_request_kinds_v1.json`) for all 30, and three human-confirmed behavior checks (R01, R10, R23) |
| `test` | TE001-TE035 | Designated held-out, generated | `examples/eval_sets/test_rubric.json`: fields known by construction, expected states and flags from the deterministic dispatch preview |
| `test_extra` | TE071-TE100 | Designated held-out, generated | `examples/eval_sets/test_extra_rubric.json`, built the same way with separate templates |

None of these is an independent human gold annotation of the model output. A rubric
pass means agreement with that reference on one run, not model accuracy.

The `test` split is a weaker held-out claim than `test_extra`. It was run once before
under `intake-v2` and its one failure (TE035) is recorded in
[CHAT_TRAIN_TEST_RESULTS.md](CHAT_TRAIN_TEST_RESULTS.md); `intake-v3` came later. The
artifacts cannot show whether that result influenced development. `test_extra` had
no earlier live run.

## Results

Counts were recomputed offline from all 95 saved case files with `check_rubric`,
`check_tool_integrity` and `summarize` from `src/dss5105/evaluate_chat.py`. They
match each saved `summary.json` exactly.

| Split | Completed | Extraction | Behavior | Rubric (both) | Tool integrity | Display fields |
|---|---:|---:|---:|---:|---:|---:|
| `supplied` (development) | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 | 935 |
| `test` (held-out) | 35/35 | 35/35 | 35/35 | 35/35 | 35/35 | 848 |
| `test_extra` (held-out) | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 | 915 |
| Held-out combined | 65/65 | 65/65 | 65/65 | 65/65 | 65/65 | 1,763 |

- *Extraction* compares extracted fields, exclusions and required clarification needs
  with the rubric. *Behavior* compares the response state and required flags.
- *Tool integrity* re-derives each displayed candidate field (ETA, cost, defect risk,
  lateness, score and so on) from the tool's own estimate, checks that candidates are
  exactly the eligible, permitted workshops, and checks split arithmetic. It checked
  2,698 display fields across the three splits. It does not judge the wording of an
  explanation.
- Provider-reported tokens: 35,362 (`supplied`), 41,022 (`test`), 34,945 (`test_extra`).

### By expected behavior

The course asks for results by behavior. Rubric kinds map to behavior as follows:
extract and answer (`complete_meetable`, `complete_impossible`, `constraint`),
clarify (`ambiguous`, `missing_number_or_date`), refuse an ineligible suggestion
(`ineligible_suggestion`), and decline to answer (`unanswerable`). Counts are
rubric passes over attempted.

| Behavior | `supplied` | `test` | `test_extra` | Observed states |
|---|---:|---:|---:|---|
| Extract and answer | 16/16 | 15/15 | 16/16 | `RECOMMEND` or `NEEDS_REVIEW` |
| Clarify | 7/7 | 10/10 | 7/7 | `CLARIFY` |
| Refuse suggestion | 4/4 | 5/5 | 4/4 | `REFUSE_SUGGESTION` |
| Decline to answer | 3/3 | 5/5 | 3/3 | `DECLINE` |

For `supplied` this table uses the rubric's kinds. The human-reviewed kinds group a
few inbox requests differently (for example R01 is `ambiguous` there and
`missing_number_or_date` in the rubric); every supplied request passed the rubric, so
each human-kind group also passed in full. Per-kind counts are in the evidence file.

### Targeted inbox behavior checks

`behavior_acceptance` in `src/dss5105/request_kinds.py` passed **2 of 3**.

| Case | Expected | Observed | Outcome |
|---|---|---|---|
| R01 | Ask for order ID and quantity together | One `CLARIFY` reply asked for the order ID and the quantity | PASS |
| R10 | Ask for product, quantity and delivery date without asking for an existing order ID | The reply asked all three and also "Which order do you mean?" | FAIL |
| R23 | Use unrounded estimates; suggest a split only if strictly faster | Fastest whole batch W6 at 5.9423 days; split W4 199 + W6 301 finishes at 4.3733 days, saving 1.57 days; state `NEEDS_REVIEW` with `SPLIT_REVIEW` | PASS |

R23 exercised only the branch where the split is faster. The branch where a split is
not faster was not exercised by this run.

## Failures and why

No case failed the primary rubric. The issues below come from the additional checks
and from reading the saved replies. Paths are relative to the run directory.

| Case | Status | Expected | Observed evidence | Supported cause |
|---|---|---|---|---|
| R10 | Confirmed failure (human-confirmed check) | A new order with details to follow: ask for product, quantity and date, not an existing order ID | `supplied/R10.json`: `model_output.patch.needs` is `[order, product, quantity, deadline]`; `preview.message` opens with the order-ID question | The model emitted the `order` need and intake kept it. The draft rubric only required state `CLARIFY`, so it did not catch which questions were asked. Whether the order lookup was ambiguous is an inference, not checked here |
| R02 | Provisional diagnostic (offline reliability audit) | Decline a historical lookup; no order or deadline needs | `supplied/R02.json`: `model_output.patch` maps "last October" to `due_date`; `preview.input.date_uncertain` is `true`; `preview.conversation.needs` is `[order, deadline]`. `inbox-review/checks.csv` marks `forbidden_needs_violation_rate` and `request_exact_match` FAIL | Internal extraction error. The user-facing reply is a correct decline |
| TE032, TE035, TE099 | Known limitation (explanation quality; not part of any scored metric) | A decline that names what is missing (margin or selling price) | `preview.message` is the shared text "The supplied data contains neither customer quotes nor past workshop allocations." | All quote and history declines share one templated reason. The decision is correct; the explanation does not address margin or agreed price |

The offline reliability audit in `inbox-review/` scores only provisional expectations.
It left 9 of the 30 inbox cases as `UNRESOLVED_POLICY` (R01, R03, R06, R10, R15, R16,
R19, R23, R29), so its rates cover 21 cases and are diagnostics, not gold accuracy.

## Limitations

- Answer references are team rubrics and generated labels, not independent human
  gold annotations. Generated held-out wording is templated.
- One run, one model, first response only. Multi-turn clarification, UI disclosure
  (for example R10's no-reservation notice), saving and real booking were not tested.
- Tool integrity is a field-level audit. Explanation faithfulness was not scored
  separately; the decline wording above shows a case it misses.
- `test` was seen in an earlier run; only `test_extra` has no earlier live result.

## Reproducing the counts

Raw per-case records hold the recorded prompts and model replies, so they stay in the
ignored `results/` directory and are shared within the team as an archive. Check
`artifact_sha256` in the evidence file before use. With the run directory restored
into a checkout of `01f2524`, the inbox audit can be regenerated offline:

```bash
uv run --locked --offline python -m dss5105.reliability_score --input results/sprint3-live-01f2524/supplied --kind-labels examples/human_request_kinds_v1.json --output results/independent-inbox-review --html-report
```

On Windows with a non-UTF-8 locale, set `PYTHONUTF8=1` before reading the saved
source snapshot with Python.
