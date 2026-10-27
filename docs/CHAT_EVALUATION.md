# Live chat evaluation contract

This is a development evaluation, not a held-out result or a human-adjudicated
course grade. The supplied inbox was already used during development. The draft
rubric is authored from the raw messages before the first live run; it must still
be reviewed independently by teammates. It does not import the demo fixtures.

## Frozen run

`dss5105.evaluate_chat --live --output results/chat-first` uses `get_model()` and
the current `LLM_MODEL`. Without `--live`, it refuses to contact a provider.
Each supplied request starts a fresh conversation and the same independent
2026-04-01 queue snapshot defined by Data v3. The revised draft rubric follows
the corrected inbox; prior scores remain historical and must not be relabeled as v3. The initial preset is lateness; explicit request
preferences take precedence. There are no automatic retries or queue updates.
This tests the initial response, not successful completion of a clarification.

The output directory must be new and inside the repository. Before calling the
provider, save a manifest with the rubric, input, prompt, schema, code and lockfile
hashes. Save each case immediately, including failed extraction outputs, safe
error categories, elapsed time, token usage when supplied, validated request,
provenance and complete tool preview. Never save credentials, request headers,
environment contents or raw provider exception messages. Stop on a provider
failure; previously saved cases remain available. Do not silently retry a paid run.

## Separate checks

- Extraction: explicit fields, objective preference, exclusions and their imposer,
  ambiguity without guessing, uncertain dates, shipping semantics and split intent.
- Behavior: acceptable response states and required flags under the stated snapshot
  convention. An infeasible date requires review, not an unsupported promise.
- Tool integrity: selected/candidate workshops obey eligibility and exclusions;
  displayed numerical fields match their own candidate estimate, field and unit;
  no commitment occurs. This is not a complete explanation-faithfulness score.

The UI currently displays deterministic tool text and numerical fields, not an
LLM-written explanation. The runner retains that tool message and display fields;
it does not exercise the browser or judge explanation usefulness. Manual review
must also identify semantic omissions, weak questions and misleading presentation
even when the automated checks pass. A failed validation counts as an unsuccessful
response, while still documenting that it failed safely.

The rubric permits alternative interpretations where the raw wording is ambiguous.
An automated pass means only that its explicit checks passed. Report denominators,
unattempted cases and limitations separately. Never call fixture agreement model
accuracy, and do not tune against this run then describe it as unseen evaluation.

## Reproduce

From the repository, with the existing model configuration:

```bash
mkdir -p .cache/tmp
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" XDG_CACHE_HOME="$PWD/.cache" \
  PYTHONDONTWRITEBYTECODE=1 uv run --locked python -m dss5105.evaluate_chat \
  --live --output results/chat-first
```

Add `--set train` or `--set test` to run the [generated sets](EVAL_SETS.md).
Choose a fresh output directory for another paid run. Raw artifacts are Git-ignored
under `results/`; retain them for the final evidence package. The committed draft
rubric and report are review aids, not independent gold annotations.
