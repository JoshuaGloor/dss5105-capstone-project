# Natural-language requests and clarification

The Streamlit page has two input modes:

- **Typed message (Start here box and the box under the answer):** submitted messages are
  interpreted by the configured model, validated in Python, then passed to the same dispatch tools.
- **Examples (scenario cards and the Examples list, offline, no model):** the original development fixtures.

The first real-provider development run is documented in
[CHAT_EVALUATION_RESULTS.md](CHAT_EVALUATION_RESULTS.md), including a blocking
clarification failure and additional manual-review issues. It is not held-out accuracy.
Offline tests establish orchestration and validation, not language quality.
The primary objective is minimise lateness. Independent previews use demo confirmation;
Saved local plan supports a separate human-confirmed durable allocation. The model
cannot commit a record, and confirming does not invoke the model again.

## Run

```bash
sh scripts/run_app.sh
```

Open `http://localhost:8501` in Chrome. Saved Python, CSS, data and example-input
changes automatically rerun the open page. Dependency or server-configuration
changes can still require a restart.
The launcher keeps new caches/temp files within this repository and does not open
a browser. No external scripts or browser profiles are needed.

Use the existing `.env` configuration described in the README: `LLM_MODEL` chooses
the provider/model and its corresponding provider key must be present. Models are
always constructed through `get_model()`; this increment introduces no hard-coded
model. Do not commit `.env` or put API keys into chat messages.

Opening the page or selecting the group-chat mode does not call the provider. Sending a message, pressing
Interpret inbox message, or pressing Retry interpretation does. Those actions use
the configured provider and can incur its normal charges. Changing objectives,
sliders, opening evidence, and ordinary reruns do not make model calls.

## Try a clarification

Submit:

```text
Please allocate ORD-109. Boss says no BudgetWorks. The new delivery date is not confirmed yet.
```

Then answer:

```text
Delivery Apr 15.
```

The intended behavior is a deadline question followed by a Python-computed preview.
The BudgetWorks exclusion must survive the follow-up. Inspect the evidence to see
the quotations and attributed imposer. This example is a suggested manual test,
not a claim that the current provider has passed it.

Use the start panel to submit a supplied inbox request's raw text through the
language path. Its hand-authored interpretation is not passed to the model and is
not used as a fallback. Missing or malformed extraction cannot quietly become a
successful fixture-based allocation.

The snapshot remains the course inbox date shown on screen. A phrase such as
"tomorrow" is converted by Python relative to that snapshot, not today's real date.
Use an explicit ISO date when other date formats require clarification.

## What the assistant shows

Each reply is a card built by `replies.py` from the dispatch result. The model writes
none of it. A card has:

- a status badge and a headline identifying the recommended workshop for the order;
- facts copied from the tool's display strings: workshop, estimated delivery,
  expected turnaround, deadline, cost and batch defect risk;
- notes: the ranking basis, refusal reasons, the ship-date note, and every review
  option, including the earliest whole-batch date and the two-workshop split;
- "How this answer was produced": the extracted fields, the order lookup,
  eligibility and exclusions (with who imposed them), the estimates and the outcome.

A test replays every inbox request under every preset and checks that each numeral
on a card appears in the tool output. The latest card follows the objective and
weight controls; earlier cards stay as they were when the next message was sent.

Answer buttons appear under the latest card when the tool can offer a safe choice:

- an ambiguous reference lists the matching in-progress orders (completed orders
  are counted, not listed);
- a refused workshop offers the tool's eligible alternative.

A click applies the answer in Python without calling the model; see the
[intake contract](INTAKE_CONTRACT.md). Dates and quantities are never offered as
buttons, because choosing one would be a guess.

## Demo script

One message per behavior the course grades. Each send is one model call.

| Behavior | Type | Expected tool outcome |
|---|---|---|
| Complete | `ORD-041 needs a home today. 600 beanies, back by Apr 21.` | Ready to review, with delivery date |
| Exclusion with provenance | `ORD-109 - 500 vests for Harbor Knits, due Apr 13. Keep it away from BudgetWorks, the last batch came back rough.` | BudgetWorks excluded by the speaker |
| Hard date rule | `ORD-081 - 1500 crewneck sweaters, due Apr 13. Cheapest shop that can still make Apr 13.` | Cheapest on-time workshop |
| Ambiguous | `Can we get the TrendCart order moving?` | Six order buttons; click one |
| Missing date | `ORD-066 due date just moved up, will confirm after the call` | Deadline question; reply `The new date is Apr 24` |
| Refusal | `OldMill is free right now - give them ORD-008.` | Refusal with reason; alternative button |
| Impossible | `Please allocate ORD-099: 1500 polo shirts, Northwind Apparel. Deadline Apr 05.` | Earliest date, split estimate, escalation |
| Split | `ORD-005 - 500 scarves, due Apr 20. Split it across two shops if that gets it back faster.` | Whole batch and split compared |
| Unanswerable | `What price did we quote TrendCart on ORD-120?` | States that no quotes are recorded |

These are suggested manual checks, not evaluation results. Several are inbox
messages, so they are development cases, not held-out ones.

## Design and implementation

The [intake contract](INTAKE_CONTRACT.md) specifies the schema and state rules.
`src/dss5105/intake.py` accepts evidence-backed patches, preserves prior fields and
exclusions, converts supported date/quantity phrases, and validates the request.
`src/dss5105/chat_ui.py` manages explicit submissions, answer buttons, retry, reset,
and the single answer view with its session history. `src/dss5105/replies.py` builds the reply cards, and
`src/dss5105/cards.py` renders the same deterministic candidate evidence.

The model extracts intent and fields using LangChain's structured-output interface.
It cannot output numerical estimates, score weights, workshop allocations, or a
confirmation. Python supplies both clarification text and the numerical cards.
No unverified model answer is displayed as the explanation.

A changed explicit order ID requires New request. Existing exclusions are append-only
within a conversation. If relaxing a prior instruction is required, start a new
request with the agreed complete constraints; this version does not adjudicate who
has authority to override an earlier instruction.

On a model/configuration/validation failure, the old preview and confirmation are
removed. The failed turn remains visible, and the next action must be Retry or New
request. This avoids silently skipping a message that might contain a constraint.
Provider errors are shown as safe messages, without raw exception details or keys.

Exported evidence includes conversation turns, field provenance, structured patches,
prompt version/hash, configured model identifier, and normal allocation tool evidence.
The app keeps conversation state in the session and writes no automatic chat logs.
An explicit saved-plan confirmation stores the reviewed conversation evidence with
its allocation record. Local records are reviewed/exported in the UI; the history
intent still refers to unavailable course historical allocations.

## Tested vs untested

Offline tests use fake structured-output models and Streamlit AppTest to cover
clarification, preserved exclusions, preference precedence, literal evidence checks,
unsupported output rejection, safe failure/retry, reset, and absence of duplicate
provider calls on reruns. They do not launch a browser or contact a model provider.

Initial provider compatibility and supplied-inbox evaluation are now recorded.
Still pending: independent annotation, a frozen held-out set, live multi-turn
evaluation, and team review of semantic correctness and completeness.
A quotation can be real while the model misinterprets it or omits a
different instruction; evidence validation alone cannot prove full faithfulness.
