# AI-native plan for Sprint 2

Status: team proposal, drafted 2026-10-15 for agreement before Sprint 2 work starts.
Nothing here is implemented yet. Course requirements still come from Spec v5 and
Tracks v4; this document only proposes how we meet them.

## What AI-native means for this desk

The conversation is the desk's main interface, and the model does the language work end
to end: it understands the request, asks what is missing, chooses a read-only tool for a
question, explains the decision and drafts the reply. Python tools own every number and
every rule. A person owns every commitment.

Three course rules bound this. The LLM never does arithmetic (Tracks v4, Warnings). No
LLM call goes inside the allocator, because the simulator calls it 120 times per run. A
plain dispatcher with excellent tools beats a multi-agent conversation.

## Today (Sprint 1)

- Intake: LangChain structured output fills a typed patch; every value must quote the
  message, or Python rejects the turn (`intake.py`).
- Clarifying questions are fixed Python text. Replies are Python templates
  (`replies.py`), with tool-authored reasons (`decision_basis` in `dispatch.py`).
- Short-term memory: Streamlit session state, resent to the model each turn.
  Long-term state: SQLite audit records and planning queues (`records.py`).
- The model never chooses a tool. This is a workflow agent.

## Proposed capabilities

| # | Capability | GenAI technique | The model does | Python does | Measured by | Size |
|---|---|---|---|---|---|---|
| 1 | Tool calling for questions | Function calling, routing | Picks one read-only tool and its typed arguments: `query_register`, `probe_load`, a preview, recorded status | Validates the arguments, runs the tool, writes every number | Tool-choice accuracy on labelled questions; zero untraced numerals | M |
| 2 | Grounded explanations | Constrained generation, grounding | Writes the explanation in plain English with placeholders such as `{eta}` or `{slack_days}` | Fills placeholders from tool fields; rejects output containing any digit or unknown workshop name; falls back to the template | Faithfulness pass rate; human clarity rating | M |
| 3 | Drafted replies to the requester | Generation with a human in the loop | Drafts the group-chat reply for a refusal, a question or an impossible date | Same placeholder fill; nothing is sent; the dispatcher edits, approves and copies | Human rating; how much the dispatcher edits | S |
| 4 | Adversarial set and guardrails | Prompt-injection defence, hallucination bait | Nothing new | Quote check, schema and eligibility stay in code | Correct refusals on 5+ injection and 5+ bait items | S |
| 5 | LLM judge, checked against people | LLM-as-judge evaluation | Scores explanations at scale | Two teammates label independently; report agreement (Cohen's kappa); people stay the ground truth | Kappa against both labellers | S |
| 6 | Prompt and model comparison | Prompt engineering, model selection | Nothing new | Versioned prompts with their hash in the trace; few-shot examples from the development split only; two models compared | Accuracy, latency and tokens per request | S |

## Design rules

- Every model output is one of three things: a typed patch, a tool call with typed
  arguments, or text with placeholders. A number the model typed never reaches the screen.
- Write tools such as `commit_allocation` are never offered to the model.
- At most one tool call per turn in Sprint 2.
- Each capability has an injected fake-model test. No test calls a real provider.
- If the model is unavailable, the desk falls back to today's form and template path.

## Deliberately not doing

- An LLM in the allocator: the track forbids it, and it would burn the API budget.
- Multi-agent negotiation: the track says it loses to a plain dispatcher with good tools.
- Vector retrieval (RAG): the corpus is 8 workshop cards and 120 order rows. Typed tools
  are exact, and embeddings would add a retrieval failure mode with no upside.
- Fine-tuning: 30 labelled requests are too few. Prompts and few-shot examples are
  cheaper and auditable.
- Long-term preference memory: nothing in the data supports it, and standing rules
  would need provenance and expiry.

## Order of work

1. Merge `main` first. PR #13 (chat-first redesign) and PR #8 (deployment) changed the
   same modules.
2. Capability 4 and the labelled question set before anything else: write the
   evaluation set before the system.
3. Capabilities 1, 2 and 3, each behind its fake-model tests.
4. Capabilities 5 and 6 alongside the Sprint 2 evaluation runs.

Owners are to be agreed by the team.
