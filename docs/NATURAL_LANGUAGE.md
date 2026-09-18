# Natural-language requests and clarification

The Streamlit page now has two input modes:

- **Supplied examples (offline):** the original development fixtures, with no model calls.
- **Natural language:** submitted messages are interpreted by the configured model,
  validated in Python, then passed to the same dispatch tools.

The first real-provider development run is documented in
[CHAT_EVALUATION_RESULTS.md](CHAT_EVALUATION_RESULTS.md), including a blocking
clarification failure and additional manual-review issues. It is not held-out accuracy.
Offline tests establish orchestration and validation, not language quality.
The primary objective remains undecided and confirmation remains demo-only.

## Run

```bash
sh scripts/run_app.sh
```

Open `http://localhost:8501` in Chrome. If an earlier server is running, restart it
to load the new Python modules; the project deliberately disables file watching.
The launcher keeps new caches/temp files within this repository and does not open
a browser. No external scripts or browser profiles are needed.

Use the existing `.env` configuration described in the README: `LLM_MODEL` chooses
the provider/model and its corresponding provider key must be present. Models are
always constructed through `get_model()`; this increment introduces no hard-coded
model. Do not commit `.env` or put API keys into chat messages.

Selecting Natural language does not call the provider. Sending a message, pressing
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

Use the original-inbox expander to submit a supplied request's raw text through the
language path. Its hand-authored interpretation is not passed to the model and is
not used as a fallback. Missing or malformed extraction cannot quietly become a
successful fixture-based allocation.

The snapshot remains the course inbox date shown on screen. A phrase such as
"tomorrow" is converted by Python relative to that snapshot, not today's real date.
Use an explicit ISO date when other date formats require clarification.

## Design and implementation

The [intake contract](INTAKE_CONTRACT.md) specifies the schema and state rules.
`src/dss5105/intake.py` accepts evidence-backed patches, preserves prior fields and
exclusions, converts supported date/quantity phrases, and validates the request.
`src/dss5105/chat_ui.py` manages explicit submissions, retry, reset, and session
history. `web_app.py` still renders the same deterministic candidate evidence.

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
