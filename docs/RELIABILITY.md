# Reliability changes

The intake fixes avoid repeated order questions and unnecessary quantity or
deadline questions when a resolved registered order already supplies those fields.
Explicit uncertainty and amendments remain blocking. Conversation updates preserve
pending and deferred clarification state, including when the UI saves a tool reply.

The offline scorer evaluates saved evidence without provider calls or queue writes:

```bash
uv run python -m dss5105.reliability_score --input results/saved-run --output results/scored-run
```

- [Benchmark contract](RELIABILITY_BENCHMARK.md): provisional development cases,
  source hashes, and held-out authoring requirements.
- [Review worksheet](RELIABILITY_GOLD_REVIEW.md): unresolved policies and blank
  independent human sign-off fields.
- [Scorer contract](RELIABILITY_SCORER.md): input compatibility, metrics,
  assertion approval, output files, and limitations.

The default benchmark is `examples/reliability_benchmark.json`. It is not
independently adjudicated gold. Assertion approvals are an optional input contract;
synthetic tests cover that adapter without requiring external reviewer responses.

## Verified scope and remaining work

| Feature | Offline verification |
|---|---|
| Registered quantity/deadline retrieval | Resolved and ambiguous orders, explicit uncertainty, invalid fields, amendments, and follow-ups |
| Clarification state | Deferred needs survive selection, model traces, and UI replies; exclusions remain enforced |
| Saved-artifact scoring | Bundle, directory, single-record inputs, held-out IDs, compatibility gates, and deterministic exports |
| Integrity checks | Known violations survive partial evidence; missing evidence does not become a pass |
| Assertion approval | Only explicitly approved assertions score; unsupported prose claims remain not scorable |

This completes the implemented offline scope. Independent human gold, a frozen
held-out dataset, semantic prose/faithfulness evaluation, and repeated live model
evaluation remain unfinished. Passing offline tests does not complete those tasks.

AI review packets, alternative consensus datasets, historical comparison reports,
and commit/delivery plans are development artifacts, excluded from this change.
Their local archive is `results/pr-cleanup-2026-10-24/`, ignored by Git. The scorer
and default benchmark do not depend on that archive. Historical commits also retain
the previously committed artifacts. No model-performance claims are made here
from those excluded experiments.
