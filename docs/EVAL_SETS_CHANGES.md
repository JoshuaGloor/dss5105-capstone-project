# Change summary: generated train/test chat evaluation sets

This change adds 105 generated chat requests, split into train and test, with labels
the system produces itself, and lets the existing chat evaluator score either split.
Method details are in [EVAL_SETS.md](EVAL_SETS.md); this file records what changed,
why, and what the first runs found.

## Why

The supplied 30-request inbox was used during development, so its score is not a
held-out result (Tracks v4 asks for one when this happens). The team also needed
more cases per request kind than the inbox provides: it has as few as three.

## What changed

### 1. Generator: `src/dss5105/eval_sets.py` (new)

- Builds requests from templates using a fixed seed (5105), so output is reproducible.
- 70 train and 35 test requests, 10 and 5 for each of the seven Data v3 kinds.
- Train and test use different message templates, so test wording is unseen.
- Templates cycle evenly; orders, dates, workshops and speakers are drawn at random.
- **Self-labelling, no model involved:**
  - Expected fields come from construction: the generator knows which order,
    quantity, date, exclusion and imposer, preference, suggestion or missing field
    it wrote into the message.
  - Expected state and review flags come from running the deterministic
    `DispatchDesk.preview` on those facts.
  - A draw whose tool outcome does not fit its kind (for example a "meetable" date
    no workshop can make) is discarded and redrawn.
- Command: `uv run python -m dss5105.eval_sets` writes `examples/eval_sets/`.

### 2. Generated data: `examples/eval_sets/` (new)

| File | Contents |
|---|---|
| `train_requests.txt` | 70 requests, IDs TR001-TR070, same envelope format as the inbox |
| `train_rubric.json` | Expected fields, states, flags, kind, category and template per request |
| `test_requests.txt` | 35 requests, IDs TE001-TE035 |
| `test_rubric.json` | Same, for test |

Do not edit these by hand; a test fails if they differ from the generator output.

### 3. Evaluator: `src/dss5105/evaluate_chat.py` (modified)

- New `--set {supplied,train,test}` option; default `supplied` keeps old behavior.
- Manifest and summary record which set ran; the request file is hashed too.
- Summary adds a `by_template` breakdown; each case records its template.
- Limitation text in the summary now states which kind of set was run.

### 4. Inbox parser: `src/dss5105/dispatch.py` (one line)

`read_inbox` accepted only `R` IDs; it now accepts any uppercase prefix, so `TR001`
and `TE001` parse. Supplied-inbox behavior is unchanged.

### 5. Tests: `tests/test_eval_sets.py` (new, 5 tests, offline)

- Committed files equal fresh generator output.
- For train, test and the supplied inbox, every label is reachable from perfect
  extraction (checks the rubric against the tools, not the model).
- Kinds are balanced, train and test templates are disjoint, and no text repeats
  across train, test and the supplied inbox.

### 6. Docs

- `docs/EVAL_SETS.md` (new): method, how to run, limits.
- `docs/CHAT_EVALUATION.md`: mentions `--set train` / `--set test`.
- `docs/EVALUATION_PLAN.md`: held-out requirement row now points to the generated sets.
- `docs/prototype/index.html`: regenerated; only the embedded `dispatch.py` hash changed.

## How to run

```bash
uv run pytest tests/test_eval_sets.py          # free, offline
uv run python -m dss5105.evaluate_chat --live --set train --output results/train-N   # paid
uv run python -m dss5105.evaluate_chat --live --set test  --output results/test-N    # paid
```

Each run needs a new output folder. `LLM_MODEL` and the provider key must be set in `.env`.

## First results (model `openai:gpt-5.6`, 2026-10-26)

| Split | Passed | Extraction | Behavior | Tool integrity |
|---|---|---|---|---|
| Train | 67/70 | 70/70 | 67/70 | 70/70 |
| Test | 34/35 | 34/35 | 34/35 | 35/35 |

Raw outputs are in `results/train-1/` and `results/test-1/` (Git-ignored).

## Findings

1. **Short workshop suggestions get a question, not a refusal (TR053, TR056, TR059).**
   "OldMill for the cardigans on ORD-017?" and similar return CLARIFY instead of
   REFUSE_SUGGESTION. Extraction passed, so the model read the fields correctly; the
   failure is in the resulting state. All three use the same train template.
2. **Margin question answered with the wrong message (TE035).** "How much margin are
   we making on ORD-099?" was marked out of scope instead of `quote`, so the user was
   told to start a new order request rather than that the data has no prices. The
   identical wording for ORD-080 (TE032) passed, so the model is inconsistent here.
   Nothing was invented or allocated.
3. **Passing case with hidden over-extraction (TE014).** "Split it ... if that gets it
   back faster" also set `preference: fastest`. No effect under default weights, but
   it would override a configured cost or defect weighting. The rubric did not check
   unmentioned fields, so it passed.
4. **Changed deadlines are accepted without confirmation.** A message date that
   differs from `orders.csv` is used directly, while a changed quantity triggers a
   question. Needs a team decision.
5. **Tied scores.** With lateness-only weights, every on-time workshop scores 0.0000;
   the pick is decided by earliest finish, not by the objective.

## Limits

- Labels come from the tools, so a tool bug is copied into the rubric.
- Template wording is cleaner than real chat; this tests known patterns.
- Orders recur across splits (only 34 open orders exist); several train templates
  paraphrase the supplied inbox.
- One turn per request; clarification follow-ups are not scored.
- The rubric checks only the fields listed per case (see finding 3).

## Held-out status and next steps

The test result above has been inspected. Record it as the `generated-v1` held-out
score before changing prompts or code because of it. After any fix, confirm it on
train, then regenerate test with a new seed or `VERSION` and report that run separately.

Suggested next steps:

- Check unmentioned fields stay at defaults (`preference`, `split_requested`,
  `suggested_workshop`) in `generated-v2`.
- Route an out-of-scope request with no allocation facts to the DECLINE message.
- Investigate why short suggestion questions return CLARIFY.
- Agree with the reliability benchmark on the `TangZheling/agent-reliability`
  branch on one scoring format.
