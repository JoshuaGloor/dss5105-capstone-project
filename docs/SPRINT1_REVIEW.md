# Sprint 1 critical review

A review of the repository on 15 Oct 2026, the day before the Sprint 1 presentation,
against Spec v5 and Tracks v4. Findings are ranked by how much they affect the grade
(problem solving 35%, engineering 20%, evaluation 15%, UI 15%, documentation 8%,
presentation 7%).

## Where the project is strong

- **The tool boundary is real, not decoration.** The model only produces a typed patch
  with quoted spans; Python validates it, computes every number and authors every reply
  card. This is exactly the track's central warning, handled structurally.
- **Evidence discipline.** Results carry source hashes and seeds; the margin study froze
  its protocol before touching the course seeds; the earliest-finish tie is reported
  rather than hidden. Few teams will show this.
- **Engineering hygiene.** 297 offline tests, ruff clean, no provider call in CI,
  idempotent and stale-safe confirmation in SQLite.
- **Every one of the 30 inbox kinds has a designed behaviour**, including the three
  deliberately impossible requests (earliest date plus options) and split estimates.

## Gaps, ranked

### 1. No live language result on the Data v3 inbox (evaluation, problem solving)

The only live run predates Data v3 and is labelled historical. The 30/30 on the slides is
fixture replay on hand-written inputs: it proves the tools, not language understanding.
The R14 defect (an unneeded quantity question blocked a refusal) is still open. This is
the single most important Sprint 2 item, and it is cheap: the first run used about 35k
tokens in total.

**Do next:** fix R14, then rerun all 30 requests with `dss5105.evaluate_chat`. Report by
behaviour kind, decision and explanation judged separately.

### 2. The hybrid must mix course objectives, and it is not frozen (evaluation)

Tracks v4 requires "at least one other objective and one hybrid setting (a weighted mix
of two or more)" of the four candidate objectives. Cost is not one of the four, so the
margin study's `cost_buffer10` is a good finding but is unlikely to count as the hybrid.
The current `hybrid` preset (0.7 lateness / 0.3 defects) runs 18.8% late and was chosen
before any experiment.

New evidence from this review ([DEFECTS_FRONTIER.md](DEFECTS_FRONTIER.md)): no
defects-weighted setting beats greedy_biggest on `% def pcs` within the lateness guardrail
on the course seeds. That is a legitimate "baseline still wins" finding.

**Do next:** freeze a lateness + defects hybrid on development seeds with a stated rule
(for example, lowest `% def pcs` subject to `% late` at most 5%). The defects-frontier
grid already contains candidates such as `defects0.05_buffer10`. Explain the common scale:
the scorer divides by fixed reference units (7 days, 10% defect risk, 1 cost unit), which
is the "common scale" Tracks v4 asks for. Write that sentence in the report.

### 3. Capacity questions are not reachable from chat (problem solving)

"Who can take 1,500 crewnecks this week?" is quoted in the core capabilities. The Python
`query_register` and `probe_load` tools exist and have a UI, but the chat cannot route to
them. Add a `workshop_query` intent to `intake.py`: the model extracts category, pieces and
date, and Python answers with the existing register card.

### 4. The labels are self-authored (evaluation honesty)

The fixture labels and the rubric were written by the same people who wrote the tools.
Spec v5 grades "why it is not rigged in your favour". Two teammates should label all 30
requests independently before seeing the fixtures, then adjudicate. Also write about ten
reworded held-out requests before any prompt tuning.

### 5. Sprint 2 logistics that will cost marks if missed

- The Sprint 2 first slide needs student IDs, a **public** GitHub link and a demo link.
  The README says the repository is private. Plan the switch to public, and audit the
  history for `.env` first.
- 24 modified and several untracked files sit uncommitted on `czp/dispatch-ui`. Commit
  and open a PR, so a laptop failure cannot take the work with it.
- `scripts/build_sprint1.mjs` (untracked) needs a runtime nobody on the team has, and it
  writes to the same path as the new deck. Delete it; `scripts/build_sprint1_deck.mjs`
  replaces it.

### 6. The UI under time pressure (UI, 15%)

The page now shows candidates, estimates and the recommendation at a glance. Remaining
friction:

- Several stacked grey caveat captions ("Draft inputs and numerical previews stay
  separate...") push the decision down the page. One "About this data" expander would do.
- "Independent previews / Saved local plan" is developer language. "Sandbox / Live plan"
  is what a dispatcher would understand.
- Split plans and deadline amendments cannot be confirmed, so R20/R23/R28/R30 end in
  "review" with no way to act. Even an "escalate with these options" record would close
  the loop.
- No usability test yet. Five minutes with two classmates acting as the dispatcher, on
  four tasks, would give the UI section real evidence.

### 7. Documentation reads defensively (documentation, presentation)

Almost every paragraph carries a disclaimer ("draft", "not held-out", "not a guarantee").
Each one is true, but repeated everywhere they bury the findings. The teammates rewrote
the first deck for the same reason. Put the caveats once in a Limitations section in each
doc, and state the findings plainly.

## Likely questions from a technology lead

| Question | Short answer |
|---|---|
| Why an LLM at all? | The input is chat; the track requires a language surface. The model extracts and asks; it never decides numbers. The allocator has no model call. |
| How do you stop hallucinated numbers? | The model returns a typed patch with quoted spans; Python validates and fails closed; every number on screen is formatted by a tool and checked automatically. |
| Earliest finish ties you. What do you add? | Chat intake, constraints enforced and attributed, confirmation with an audit trail, and a configurable objective that can trade cost for lateness. On lateness alone the simple rule is as good. |
| Can someone audit a decision six weeks later? | Each saved allocation stores the request, constraints and who set them, all candidate estimates, weights, data hashes, who confirmed and when. |
| Model risk and cost? | One structured-output call per chat turn. Offline modes and the simulator need no key. Malformed output is rejected, not repaired. |
| Scale and security? | Single-node SQLite and self-declared dispatcher identity: fine for a prototype, not production. Next would be authentication and a server database behind the same record contract. |

## Changes made in this review

- New Sprint 1 deck, generated from evidence JSON: `scripts/build_sprint1_deck.mjs` writes
  `docs/slides/reviewed/Presentation_Group11_Sprint1.pptx` (PDF copy alongside). The
  earlier GPT revision is preserved under `docs/slides/reviewed/previous/`.
- Speaker script trimmed to about 4 minutes 10 seconds at 150 words per minute; it is also
  the source of the slide notes.
- Streamlit desk restyled in the SweaterCo house style (ink, ivory, camel; serif display
  type): clearer sidebar labels, the toolbar hidden, alert colours in the palette, and a
  compact table of excluded workshops. The page eyebrow takes its date from the data
  snapshot.
- New study: `scripts/defects_frontier.py`, with [the write-up](DEFECTS_FRONTIER.md) and
  [the evidence](evidence/defects-frontier.json).
