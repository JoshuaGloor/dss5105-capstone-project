# Natural-language intake contract

Finalized for the first language increment. The allocation and preview contracts
remain in [DISPATCH_CONTRACT.md](DISPATCH_CONTRACT.md). This adds a narrow model
extraction boundary, not model arithmetic or automatic business commitments.

## Interpret one turn

`interpret_turn(conversation, text, desk, model=None)` returns a new conversation.
The default model is constructed only on explicit submission, using `get_model()`
and the existing environment configuration. An injected fake model supports offline
tests. No model invocation happens on page load, objective changes, or ordinary reruns.

Use LangChain structured output with a JSON schema. The model returns:

- `updates`: `{field, value, evidence}` entries for changed scalar fields only.
- `exclusions`: `{workshop, imposed_by, evidence}` entries to add to existing exclusions.
  A blank imposer means the speaker; a named imposer must occur in the evidence.
- `needs`: controlled clarification codes; never free-form model explanations.

Each evidence string must occur verbatim in the current user message. Referenced
IDs, quantities, customer/product/workshop names, and date phrases must occur in
their evidence. Python maps register aliases and converts dates/quantities. Model
output cannot supply costs, estimates, probabilities, allocation scores, chosen
workshops, or confirmation. Reject extra/unknown fields and invalid schemas.

Scalar fields: order_id, customer, product, pieces, due_date, date_kind,
date_uncertain, suggested_workshop, preference, split_requested, intent.
The existing enum values apply; boolean updates use literal `true` / `false`.
Intent/preference/boolean interpretation is semantic model work, with a supporting
quote. A quote check proves traceability, NOT that the interpretation is correct
or that no relevant instruction was omitted.

The prompt provides the prior validated draft, previous questions, user turns, and
reference catalogs. It does not provide workshop costs, capacities, risks, queues,
or simulator outcomes. Do not send fixture interpretations as model input.

## Normalization and clarification

- Order IDs must be explicitly present in user evidence. Customer/product filters
  can resolve orders via the Python lookup; a model cannot invent an ID from a list.
- Normalize known workshop IDs/names and common product plurals against the course
  register. Unknown customer/product filters may produce NOT_FOUND normally.
- Quantities accept digits and correctly grouped thousands separators. Quantity
  words need clarification; the model must not convert them to arithmetic results.
- Dates accept ISO, English month/day with optional year, today, and tomorrow.
  Python applies the inbox year when omitted and the declared snapshot for relative
  dates. Ambiguous formats and other relative phrases prompt for an explicit date.
- An unknown revised date marks the prior deadline uncertain. A validated new date
  clears date uncertainty. The model marks a ship date with `date_kind=shipping` but
  never asks about it; the dispatch tool compares it with the recorded due date and
  asks only when they differ (intake-v2).
- Question codes: order, quantity, deadline, scope, constraint_change.
  Python supplies the question text. Missing-state codes remain pending until the
  corresponding field is supplied; scope/constraint-change require a new request.
- A different explicit order ID after one has been established requires starting a
  new request. This avoids accidentally carrying an old order's constraints forward.

## Persistent constraints and evidence

Changes are patches, not full replacements. Omitted fields and exclusions persist.
Exclusions cannot be removed through this first extraction schema. A request to
relax one needs a new explicitly scoped request; the UI has a New request action.
Capture the quoted evidence, actual speaker, attributed imposer, and turn index.
Different requests and browser sessions have separate conversation state.

The preview envelope combines original user turns so each exclusion quote remains
available to the existing adapter. The audit retains the individual messages and
field provenance; the combined text is not a fabricated original message.
Append-only turn/extraction records include schema/prompt version and prompt hash;
do not retain provider credentials or raw provider exceptions.

## Error and UI behavior

The conversation advances only after successful schema and evidence validation.
Missing provider configuration, unavailable/unsupported models, and invalid output
produce a safe error. Hide the prior preview and clear demo confirmation immediately.
Retain the failed user message separately. Require Retry or New request before a
different follow-up so a failed constraint-bearing message is not silently skipped.
Retries are explicit; there is no background model-call loop.

Group-chat request is the default mode; offline supplied examples remain one click
away. Sending a
message in that mode calls the configured provider and may incur its normal usage
charges. Read-only previews cannot create allocations. Saved-plan mode wraps the
same validated input in a separate human-confirmed persistence workflow; the model
never supplies commit authority or a confirming dispatcher identity.
On reruns, re-evaluate the validated draft through Python with the selected weights.
All assistant questions and numerical cards come from deterministic tool outputs;
unverified model prose is never displayed as an explanation.

Answer buttons are a second input path. `apply_selection` turns a clicked order ID or
alternative workshop into a quoted patch and validates it with `apply_patch`, exactly
like model output. The dispatcher is the speaker, provenance records the change, and
the trace says no model was called. Buttons are offered only from tool results: the
in-progress orders behind an ambiguous reference, or the alternative the tool chose
for a refused workshop. A clicked alternative still passes eligibility and exclusions.

No automatic chat logs are written to disk. Session evidence is downloadable by
the user. Explicit saved-plan confirmation retains reviewed intake evidence in the
allocation record. All development artifacts, caches, and test temporary files remain in
the repository. Live provider verification is not part of default tests.

## Evaluation limits

Offline fake-model tests can establish orchestration, validation, state preservation,
failure handling, and tool integration. They cannot establish extraction quality
against real wording or provider-specific structured-output behavior. Independent
annotation and held-out results remain pending. The authorized first live run is
documented in [CHAT_EVALUATION_RESULTS.md](CHAT_EVALUATION_RESULTS.md); its draft
checks do not establish complete semantic accuracy. The UI must not present draft
fixtures or offline tests as real-provider results.

## Sprint 2 additions (intake-v3)

- `intent` gains `capacity`: a question about who could take a quantity of a product by a
  date, with no order named to send out. The model copies the product (or the word tops
  or accessories), quantity and date phrase; a message naming an order stays `allocate`.
  `needs` gains `product` for a capacity question without a recognisable product.
- `interpret_turn(..., restart_new_requests=True)` is used by the voice assistant. When the
  latest message names a different order, or switches between allocating and a capacity
  question, the same validated patch is applied to an empty request. There is no second
  model call, and the trace records `restarted: true`. Without the flag, a different
  order still raises, as before.
- A quantity question the model raises on its own is dropped when the request names a
  recorded order: `orders.csv` holds its quantity, and the dispatch tool still asks about
  any stated amendment. A stated but unclear quantity ("usual quantities") still asks.
  This fixes the live R14 failure, where an unneeded quantity question blocked the refusal.
