# Build plan: QuickResponse dispatch desk

Working version for team discussion. The product prototype is our proposed target
experience, not a statement that every pictured feature is production-ready.

## The product we are building

The final product is a **Streamlit web application**, opened in Chrome. The current
standalone HTML is a visual and interaction prototype for team review; it is not
the implementation framework. Opening the HTML requires no server or installation.
All new artifacts, scripts, caches, and temporary files must stay inside this project.

A dispatcher brings a factory chat request to the desk. The assistant establishes
the order and constraints, asks about missing information, and calls Python tools
to compare eligible workshops. The dispatcher sees the recommendation, tradeoffs,
and evidence before confirming an allocation. The system records the decision and
updates capacity only after confirmation against current state.

The primary objective remains **undecided**. Lateness is the prototype's initial
example. The team must select and justify its primary at Sprint 1, retain another
objective for comparison, and justify a hybrid. Cost is a measured tradeoff; it is
not one of the course's four candidate primary objectives. Do not promise a hybrid
will be numerically between other policies on every metric.

Product references:

- [Interactive prototype](docs/prototype/index.html): open directly in a browser.
- [Sprint 1 architecture](docs/sprint1-architecture.svg): slide-ready SVG.
- [Architecture explanation and demo script](docs/SPRINT1_ARCHITECTURE.md).
- [Dispatch contract](docs/DISPATCH_CONTRACT.md): implemented preview boundary.
- [Course scope and deadlines](docs/PROJECT_BRIEF.md).

## Target user journey

1. **Understand.** Paste a request or select an inbox item. Show the original text,
   matched order, requested date, quantity, and instruction provenance. If ambiguous,
   ask a targeted question and keep the decision blocked until resolved.
2. **Compare.** Show permitted workshops with expected delivery, cost, batch defect
   risk, and exclusion reasons. Default to the team's primary objective. Offer the
   comparison objective and hybrid against the SAME order and queue snapshot.
3. **Refine.** Advanced controls can change weights and recompute Python previews.
   Changing a weight cannot relax eligibility or an explicit exclusion. A request
   such as "cheapest that meets the date" sets a hard date constraint. Show when a
   request-specific preference overrides the global preset.
4. **Resolve exceptions.** Refuse an invalid suggested workshop and offer eligible
   alternatives. Explain late options without silently approving them. Clarify a
   new date, obtain an explicit permitted change, or escalate. Split planning needs
   separate semantics and evidence; it is not supported by the shared callback.
5. **Confirm.** Review the final order/workshop/configuration/evidence. Revalidate
   the state version, then save one auditable allocation and update queues atomically.
   A preview is not a reservation. Retrying confirmation must not duplicate work.

## Current increment: delivered vs proposed

| Area | Current state |
|---|---|
| Allocator, shared simulator comparison, exploratory tuning | Existing, implemented |
| Inbox parsing | Reads all supplied envelopes and raw messages |
| Structured preview service | Implemented: resolution, constraints, estimates, ranking, explicit exception states |
| Natural-language extraction | Connected; first live development run recorded, clarification fixes pending |
| Numerical presentation | Python returns formatted values and source/state evidence |
| Portable HTML prototype | Interactive inbox, preset comparison, evidence export, demo confirmation |
| Streamlit web page | Implemented: native controls call live Python previews |
| Custom weights | Available through CLI and live Streamlit sliders |
| Confirmed allocation storage and queue mutation | Not implemented; prototype confirmation is local demonstration only |
| Full chat evaluation and faithfulness checker | Initial live inbox run and partial tool-integrity audit complete; independent gold, held-out and full explanation checks pending |

## Implementation sequence and acceptance gates

### Phase A - Agree the behavior and test the tool boundary (this increment)

- [x] Preserve the course harness and reuse its eligibility helper.
- [x] Specify structured requests, ambiguity, exclusions, deadlines, and preview states.
- [x] Read the supplied inbox without treating request IDs as decision logic.
- [x] Implement independent read-only previews on the declared inbox snapshot.
- [x] Add draft structured fixtures for reproducible demonstrations, clearly separate
      from human gold annotations and model extraction.
- [x] Test errors that could produce invalid allocations or unsupported promises.
- [x] Build a portable prototype with actual Python estimates and preset comparisons.
- [x] Produce the architecture and a blank annotation-sheet generator.

Gate: another teammate can reproduce an ordinary recommendation, clarification,
refusal, exclusion, and late option with no API key. Source CSVs and queues remain
unchanged after previews. Fixtures are reviewed before use as reference inputs.

### Phase B - Connect natural language and clarification (initial live evaluation complete)

- [ ] Independently annotate supplied requests and adjudicate disagreements. Record
      prior exposure to draft fixtures; do not claim blind annotation.
- [ ] Freeze a small additional held-out chat set before prompt/tool tuning.
- [x] Define a typed extraction contract and clarification state; keep source spans
      for quantities, dates, references, exclusions, and request preferences.
- [x] Build a single dispatcher language layer using `get_model()` and `LLM_MODEL`.
      A basic structured-output/tool-calling agent is sufficient initially.
- [x] Let the model propose intent and tool inputs; Python validates them. Never let
      model prose bypass eligibility or become an executable commitment.
- [x] Resolve follow-up answers into the prior request without losing constraints.
- [x] Present numerical fields and clarification text from tools, with no generated
      narrative displayed as an explanation.
- [x] Test orchestration with fake models. Retain validated patches, source evidence,
      model identifier, prompt version/hash, and tool outputs in session evidence.
- [x] Run an explicitly authorized initial paid evaluation of the supplied inbox;
      retain raw evidence and distinguish draft checks from manual semantic review.
      See [the results and open issues](docs/CHAT_EVALUATION_RESULTS.md).
- [ ] Fix unnecessary/duplicate clarification questions and historical-date extraction;
      test live follow-ups separately from initial-response coverage.

Gate: unseen wording reaches the same validated tools; missing information causes a
question, malformed model output fails closed, and decision correctness is reported
separately from explanation faithfulness. Do not label fixture replay an agent demo.

### Phase C - Build the Streamlit web application

- [ ] Confirm the visual hierarchy and exception flows with teammates using this prototype.
- [x] Build inbox, original-message, candidate comparison, and evidence views in
      Streamlit, using the HTML as a visual reference.
- [x] Call the existing Python preview functions directly from Streamlit.
- [x] Connect language interpretation and a clarification conversation using the Phase B boundary.
- [x] Keep each user's selected request, objective settings, and preview in session
      state; keep demo acknowledgement separate from persistent allocations.
- [x] Add optional advanced weight sliders that recompute Python previews. Bind each
      preview to its request, weights, and snapshot; invalidate outdated confirmations.
- [x] Show configured vs effective weights and meaningful units/scales. All-zero
      or nonfinite configurations must be rejected with a clear message.
- [x] Show configuration/data errors, clarification, refusal, and empty-candidate states.
- [x] Add model-pending and unavailable-model states with explicit retry and no stale preview.

Stack decision: Streamlit for the web interface, existing Python modules for tools
and scoring, and the existing model helper for language intake. A separate frontend
build or REST service is not needed for the first application. The Streamlit dependency
and lockfile are now updated; launch the first page with `sh scripts/run_app.sh`.
See [STREAMLIT_APP.md](docs/STREAMLIT_APP.md) for examples and current limits.

Gate: changing an objective calls the same Python scorer; no duplicated arithmetic
in the browser, no queue mutation on previews, and no rerun implicitly commits work.

### Phase D - Confirm and record an allocation safely

- [ ] Finalize `commit_allocation` before implementing it: request identity, approved
      constraints, state version, confirmation identity, idempotency key, and audit schema.
- [ ] Define queue units and processing/rework update conventions. Delivery transport
      must not accidentally become workshop processing occupancy.
- [ ] Add transactional local storage (SQLite is the initial proposal), request
      uniqueness, stale-preview rejection, and an audit export.
- [ ] Require renewed review if queue state, order details, or configuration changes.
- [ ] Support explicit deadline amendments/escalation without editing course source CSVs.

Gate: repeated clicks create one allocation; simultaneous stale confirmations cannot
overbook; stored decisions reproduce their inputs, constraints, configuration, and evidence.

### Phase E - Evaluate, deploy, and prepare final evidence

- [ ] Freeze and justify primary, comparison, and hybrid configurations.
- [ ] Run all required shared baselines, short heuristic, and normal/shock scenarios.
      Preserve seeds, source hashes, raw results, baseline wins, and inference limits.
- [ ] Evaluate every supplied chat request and the frozen additional held-out cases;
      report behavior categories, decision correctness, explanation faithfulness,
      and useful clarification coverage rather than one flattering aggregate.
- [ ] Analyze at least ten genuine failures or disclosed stress cases individually.
- [ ] Test UI tasks with teammates, including ambiguity, refusal, and stale confirmation.
- [ ] Deploy a controlled demo, document environment setup and data reset, and prepare
      required reports, presentation, reproducibility package, and team contributions.

Gate: a new teammate reproduces the published results and completes the dispatch
flow. All final claims link to retained evidence, not only a screenshot or a score.

## Milestone mapping

These are team planning targets; the actual course dates/formats are documented in
the project brief. Do not claim that Sprint 1 requires the complete application.

| Milestone | Proposed emphasis | Evidence to show |
|---|---|---|
| Sprint 1, 16 Oct | Problem, business value, objective declaration, architecture, risks, roadmap | Prototype; reproducible tool preview; initial policy tradeoffs; clearly labeled implementation status |
| Sprint 2, 30 Oct | End-to-end chat and connected preview; confirmation in progress | Clarification and exclusion demo; logged tools; preliminary behavior evaluation; working demo link |
| Sprint 3, 13 Nov | Confirmed allocation, stable UI, full evaluation | Transactional confirmation, failure cases, faithfulness results, reproducibility |
| Final, 15 Nov | Freeze and package | Required documents/video/code/evaluation and contribution evidence |

## Team decisions for the next meeting

1. Select a primary candidate based on evidence; agree how the other objective and
   hybrid expose its tradeoffs. The formal declaration is at Sprint 1.
2. Review date semantics: "ship date" may mean dispatch or delivery. Our current
   conservative interpretation asks for clarification. Confirm the independent
   inbox snapshot convention and later operational queue assumptions.
3. Agree the prototype's essential workflow and choose owners for tools/data,
   language intake, UI/state, and evaluation/documentation. Names remain unassigned.
4. Split independent annotation work before discussing expected answers. Decide
   held-out coverage and the rule for judging multiple acceptable allocations.
5. Review the first live evaluation, resolve the clarification defects, then finalize
   the Phase D persistence contract. Defer multi-agent/DeepAgents and sophisticated split
   planning until a demonstrated need justifies them.

## Reproduce this increment

```bash
uv sync --all-groups
uv run pytest
uv run python -m dss5105.dispatch --request R12 --preset lateness
uv run python -m dss5105.dispatch --request R21 --preset defects
uv run python -m dss5105.prototype
```

Open `docs/prototype/index.html` directly. It needs no server, network, or API key.
The second dispatch command deliberately shows a request preference overriding the
global preset: cheapest-on-time remains a hard-date constrained cost choice.

Generate a new blank annotation worksheet (choose a fresh filename for each rater):

```bash
uv run python -m dss5105.prototype --annotations results/annotations-rater-a.csv
```

It refuses to overwrite an existing worksheet. Review or replace the draft inputs
through `--input path/to/request.json`; custom weights use `--weights path/to/weights.json`.
See [the run guide](docs/DISPATCH_PREVIEW.md) for complete examples and limitations.
