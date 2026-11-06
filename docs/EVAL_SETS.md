# Generated chat evaluation sets

`dss5105.eval_sets` generates 105 chat requests from a fixed seed: a 70-request
train split and a 35-request test split, each balanced across the seven Data v3
request kinds (10 and 5 per kind). There is no model training in this project;
"train" means the split you may inspect and tune prompts or tools against.

## How cases are labelled

No model labels anything. Each request is built from structured facts chosen by the
generator (order, quantity, date, exclusion and its imposer, preference, suggested
workshop, missing field), so the expected extraction is known by construction. The
expected response state and review flags come from running the deterministic
preview on those facts. Draws whose tool outcome does not match the intended kind,
such as a "meetable" date that no workshop can make, are rejected and redrawn.

A test regenerates both splits and requires them to match the committed files, and
another checks every label is reachable from perfect extraction. That checks the
rubric against the tools, not the model.

## Train versus test

The splits use disjoint message templates, so test wording is never seen in
tuning. Orders, customers and workshops recur across splits because the data has
only 34 open orders. Several train templates paraphrase the supplied inbox; none of
the generated texts repeats it. The test split is held out only while nobody tunes
on its results; after that, bump `VERSION`, change the seed or templates, and say so.

## Run

```bash
uv run python -m dss5105.eval_sets          # regenerate examples/eval_sets/
uv run python -m dss5105.evaluate_chat --live --set train --output results/train-1
uv run python -m dss5105.evaluate_chat --live --set test  --output results/test-1
```

The two evaluation commands call the configured provider and cost money. The
summary reports results by kind, category and template.

## Limits

- Template wording is cleaner and less varied than real chat; this measures
  robustness to known patterns, not open-ended language understanding.
- Labels inherit the tool's decisions. A tool bug that the rubric encodes will not
  show up as a model error.
- One initial turn per request; clarification follow-ups are not scored.
- Not a substitute for independent human labels of the supplied inbox.
