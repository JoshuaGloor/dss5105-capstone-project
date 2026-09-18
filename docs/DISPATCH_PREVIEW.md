# Dispatch preview: run and inspect

The supplied `dispatch_requests.txt` is the natural-language evaluation inbox.
`simulate.py` never reads it. This increment reads the inbox envelopes and connects
explicit structured interpretations to the existing Python allocator. It does not
yet implement natural-language extraction or multi-turn clarification.

## Run without a provider

```bash
uv sync --all-groups
uv run python -m dss5105.dispatch
uv run python -m dss5105.dispatch --request R12 --preset lateness
uv run python -m dss5105.dispatch --request R08 --output results/R08-preview.json
uv run python -m dss5105.dispatch --request R25 --weights examples/custom-weights.json
uv run python -m dss5105.prototype
uv run pytest
```

The first command lists raw requests. Request previews use
`examples/dispatch_inputs.json`, a hand-authored development interpretation for
each supplied request. These fixtures need team review and are not gold labels.
Request IDs select inputs, not allocation policies. No model is called, no messages
are sent, no source data is modified, and no capacity is reserved.

`examples/custom-weights.json` is an exploratory configuration from the existing
development search. Its inclusion is not a selection of the primary objective or
final hybrid. Explicit request preferences take priority over configured weights.

For a new or corrected interpretation, save a JSON object with the fields in
[DISPATCH_CONTRACT.md](DISPATCH_CONTRACT.md), then run:

```bash
uv run python -m dss5105.dispatch --request R25 --input path/to/input.json --preset defects
```

Example input for that request:

```json
{
  "order_id": "ORD-109",
  "pieces": 500,
  "due_date": "2026-04-13",
  "exclusions": [{
    "workshop_id": "W3",
    "imposed_by": "Mei",
    "evidence": "keep it away from BudgetWorks"
  }]
}
```

The evidence text must appear in the selected request. This catches untraceable
inputs but does not prove interpretation correctness; that needs separate evaluation.

## Open the prototype

Open `docs/prototype/index.html` directly in a browser. There are no external fonts,
CDNs, API keys, or network calls. The generated page bundles all supplied requests
and Python previews for the existing presets. It supports request selection,
objective comparison, exclusion explanations, an evidence inspector/export, and
a clearly labeled confirmation interaction that does not persist any allocation.

The prototype defaults to R25 because it demonstrates an explicit exclusion and
objective-dependent choices. Try R08 for a cap violation, R03 for ambiguity, R05 for
an unknown new date, R13 for missing quote data, R20 for late options, and R21 for
cheapest-on-time. A specific request preference overrides global presets; the UI
displays the effective weights so an unchanged choice is understandable.

Edit `docs/prototype/template.html` and regenerate with `dss5105.prototype`. Do not
edit the generated `index.html` directly. The evidence bundle is saved to the
Git-ignored `results/dispatch-previews.json`; retain chosen artifacts for reporting.
The generator escapes embedded JSON and reproduces the page without timestamps.
The architecture link assumes the page stays inside `docs/prototype/`; when sharing
the page alone, also share `docs/sprint1-architecture.svg` separately.

The screen is a proposed final product layout. The [Streamlit page](STREAMLIT_APP.md)
now calls the Python tools directly, including live weight sliders. Free-text chat
remains planned, as specified in [PLAN.md](../PLAN.md). The standalone HTML page
does not silently recalculate scores in JavaScript or pretend to make a reservation.
To review this prototype, simply open the HTML in Chrome; Streamlit is not required.

## Interpretation and state conventions

- Every inbox item independently starts from the same 2026-04-01 queue snapshot.
  The source queue values are reused by convention; they are not reconstructed
  historical queues. Simulation replay remains a separate experiment.
- Explicit valid IDs resolve exactly. Missing IDs can use exact customer/product
  filters; ambiguous results remain unresolved. Unknown explicit IDs do not fall
  back to an arbitrary customer order.
- An explicit known delivery date overrides the stored deadline, preserving both
  values. An uncertain new date blocks ranking. "Ship date" needs clarification
  rather than being silently treated as a delivery deadline.
- A quantity, customer, or product conflict requires clarification. A future order
  amendment workflow must define who authorizes changed quantities.
- Past/infeasible deadlines and split requests require review. No best-scoring
  candidate implicitly authorizes lateness, splitting, or a constraint override.
- A suggested eligible workshop is honored in the preview. An ineligible suggestion
  is refused, with an eligible alternative where possible. Explicit exclusions
  remain hard constraints across every objective setting.
- Customer quote and historical allocation questions are declined. Recorded status
  may be returned as a source fact; it is not live tracking.

## What the numbers mean

Candidate estimates reuse `allocator.estimate_delivery`. Costs are source cost
units, not asserted currency or customer price. Defect risk is per batch. Expected
turnaround includes expected rework, not a sampled outcome or a delivery guarantee.
The expected timestamp starts at inbox-day midnight and rounds upward to the next
minute for display; feasibility uses the unrounded duration against days to due.
This differs from the simulator's sampled, rounded completion dates.

The output retains input, order, constraints, effective weights, scales, every
candidate, exclusions, and source/state hashes. The prototype displays Python's
formatted values. It does not establish model explanation faithfulness, because
there is no generated model explanation in this increment.

## Start independent annotation

```bash
uv run python -m dss5105.prototype --annotations results/annotations-rater-a.csv
```

The worksheet contains raw request envelopes and blank annotation fields. It does
not copy draft fixture judgments or predicted tool statuses into the expected
answers, and it refuses to overwrite an existing file. Use separate files for
independent raters, then adjudicate using [EVALUATION_PLAN.md](EVALUATION_PLAN.md).

Tests exercise the tool boundary, not NLP quality. Full chat evaluation, a field-level
faithfulness checker, continuous queue updates, durable audit storage, and live
provider checks remain future work.
