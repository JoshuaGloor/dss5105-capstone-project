# Project brief: Quick-Response Subcontracting Desk

Track 2 replaces informal subcontracting decisions in a factory group chat with
an assistant that understands requests, recommends an eligible workshop, and
records the evidence behind the recommendation.

## Sources and how to use these documents

Course requirements come from `Capstone_Project_Spec_v5.pdf` and
`Capstone_Project_Tracks_v4.pdf` under Week 0 / Capstone Project. The TA announcement
clarifies that teams choose their own primary objective and declare it at Sprint 1.
Use Data v3 and the updated announcement for inbox dates, queue snapshots and shock evaluation.
See [the migration review](V3_REFINEMENT.md) for the implemented changes and remaining gates.

- Spec pp. 2-4: objective declaration and sprint requirements.
- Spec pp. 4-7: final deliverables, evaluation, and grading.
- Tracks pp. 4-7: Track 2 capabilities, simulator, and language evaluation.
- [Course data dictionary](../track2/data/data_dictionary.md): data definitions.
- [Data findings](DATA_FINDINGS.md): reproducible observations and their limits.
- [Tool specification](TOOL_SPEC.md): implemented interfaces and proposed extensions.
- [Evaluation plan](EVALUATION_PLAN.md): required evidence and remaining work.
- [Allocation guide](ALLOCATION_ENGINE.md): current algorithm and run commands.

Course requirements, current implementation, and team proposals are different
things. An idea in these documents is not a completed feature or a verified result.

## What the system needs to do

For each request, establish which order is meant, which workshops can make it,
which are allowed to receive it, and how their current queues affect delivery.
Recommend an allocation using a configurable objective and explain the tradeoffs.
Ask about ambiguity, refuse an ineligible suggestion with a reason and alternative,
and acknowledge questions that cannot be answered from the available data.

The course requires natural-language intake, a queryable workshop register,
per-candidate delivery estimates, handling of no-good-option cases, documented
tools, auditable output, and a usable dispatcher interface. An allocator alone
covers only part of Track 2.

## Current implementation

| Component | Status | Location |
|---|---|---|
| Course simulator and eligibility rule | Official Data v3, imported byte-for-byte | `track2/harness/simulate.py` |
| Queue-aware earliest-finish reference | Implemented | `src/dss5105/allocator.py` |
| Weighted scorer and allocator callback | Implemented: lateness, defects, fairness, robustness and cost weights; deadline buffer; capacity reservation; replay ledger | `src/dss5105/allocator.py` |
| Objective presets | One per course objective plus our lateness-then-defects hybrid, frozen on development seeds | `src/dss5105/objective_study.py`, [OBJECTIVE_STUDY.md](OBJECTIVE_STUDY.md) |
| Baseline and preset experiments | Implemented: normal, ten-seed shock and paired controls, JSON traces | `src/dss5105/evaluate.py` |
| Exploratory weight search | Implemented: fixed grid, frozen candidates, additional seed checks | `src/dss5105/tune.py` |
| Model construction helper | Implemented; not used by allocation experiments | `src/dss5105/llm.py` |
| Structured request resolution and constraints | Implemented read-only previews; hand-authored inputs | `src/dss5105/dispatch.py` |
| Natural-language extraction and clarification conversation | Implemented; pre-v3 live evaluation historical, revised live run pending | `src/dss5105/intake.py`, `src/dss5105/chat_ui.py` |
| Dispatcher UI | Streamlit: voice-first mobile assistant, desk (independent previews and saved plan), objective lab, memory page; HTML design reference retained | `streamlit_app.py`, `assistant_page.py`, `web_app.py`, `lab_page.py`, `memory_page.py` |
| Voice assistant | Browser speech recognition, Python-routed commands and memory questions, tool-authored cards and speech, slide-to-confirm booking | `src/dss5105/assistant.py`, [VOICE_ASSISTANT.md](VOICE_ASSISTANT.md) |
| Long-term memory | Standing rules learned from confirmed bookings, episode log, dispatcher profile (SQLite) | `src/dss5105/memory.py` |
| Workshop lookup and extra-work scenarios | Implemented direct read-only tools and offline Streamlit controls; capacity questions reachable from chat and voice (`intent=capacity`) | `dispatch.py`, `workshop_ui.py` |
| Confirmed allocation records and queue updates | Implemented in local saved-plan mode: SQLite transactions, retries, stale-state checks, audit export | `src/dss5105/records.py` |
| Chat evaluation and faithfulness checker | Live inbox runner and partial tool-integrity checks implemented; independent gold/held-out/full faithfulness pending | See evaluation plan |

Offline tests cover eligibility, queue sensitivity, configuration changes,
estimates, empty candidates, and reproducible simulator runs. They do not establish
chat accuracy, deployed usability, or optimal allocation quality.

The [local record contract](ALLOCATION_RECORD_CONTRACT.md) defines confirmed saves.
It uses fixed-date planning queues, expected processing occupancy and a self-declared
dispatcher identity. Authentication, cancellations and real workshop booking are not
implemented. Independent inbox evaluation continues to use the untouched snapshot.

The first dispatch increment is documented in [DISPATCH_PREVIEW.md](DISPATCH_PREVIEW.md).
See [PLAN.md](../PLAN.md) for phased acceptance gates and the
[Sprint 1 architecture](sprint1-architecture.svg) for the target system with status labels.

## Architecture and objective choice

The intended flow is:

```text
Chat request -> LLM interpretation and tool-backed resolution
             -> structured order, constraints, and objective configuration
             -> Python estimates and allocation
             -> tool-backed explanation and proposed decision
             -> dispatcher confirmation and persisted record
```

The simulator evaluates the Python allocator directly, without an LLM. The LLM's
current role is extracting intent and quoted fields; Python validates patches,
asks clarification questions, and provides the displayed facts.
All arithmetic belongs in tools. An instruction file or skill does not replace
executable allocation logic.

The course permits a single dispatcher agent or a multi-agent design; it does not
require bidding, negotiation, or a particular scorer formula. Our current design
uses one deterministic weighted scorer. Objectives are parameters, never separate
branches in allocation logic. Eligibility remains a hard constraint.

The team has selected **minimise lateness** as its primary objective for Sprint 1, and
**minimise defects** as its secondary objective for Sprint 2.
Evaluate both late fraction and mean late days. The course candidates are:
minimise lateness, minimise defects, fair allocation, or robustness to workshop
failure. Cost is an additional measured tradeoff, not one of these primary choices.

The scorer now has a term for each candidate, and one preset per objective was frozen on
development seeds before the course seeds ran. The default `hybrid` (lateness first, then
defects) beats all three baselines and the earliest-finish rule on both lateness metrics
in normal runs; the defects preset beats all three baselines on `% def pcs` within the
random-lateness guardrail; the fairness preset matches random's spread while on time.
See [OBJECTIVE_STUDY.md](OBJECTIVE_STUDY.md) for the protocol and where baselines still
win. The earlier Sprint 1 presets and evidence are kept in [V3_EVALUATION.md](V3_EVALUATION.md).

## Milestones and final submission

Source: Spec pp. 2-5. Times below are course local times.

| Milestone | Upload deadline | Review format |
|---|---|---|
| Sprint 1 | Fri 16 Oct 2026, 15:00 | 19:00 session; live 5-minute presentation and 2-minute Q&A; declare primary objective |
| Sprint 2 | Fri 30 Oct 2026, 15:00 | 19:00 session; 5-minute presentation video and 2-minute Q&A |
| Sprint 3 | Fri 13 Nov 2026, 15:00 | 19:00 session; 5-minute presentation video and 2-minute Q&A |
| Final submission | Sun 15 Nov 2026, 23:59 | `GroupNN.zip` |

Presentation stems are `Presentation_GroupNN_Sprint1`,
`Presentation_GroupNN_Sprint2`, and `Presentation_GroupNN`. Slides may be `.pptx`
or `.pdf`; presentation videos are `.mp4`. Use the required two-digit group number
and exact capitalization. Every member must attend the review and be ready for Q&A.
From Sprint 2, the first slide must include the group number, member names and
student IDs, a public GitHub link, and a working demo link.

The final zip contains `Readme.pdf`, `Slide.pdf` or `Slide.pptx`, `Video.mp4`,
`Documentation.pdf` (maximum 15 pages), `Evaluation.pdf`, `Teams.pdf`, and
`Strategic_Recommendations.pdf`. The final `Video.mp4` is a demo video, distinct
from the Sprint 3 presentation video. Strategic recommendations need real market
research and three concrete opportunities, not generic claims.

Grading weights: problem solving 35%, engineering 20%, evaluation 15%, UI 15%,
documentation 8%, presentation 7%. Simulator metrics are not a course grade.

## Next work and ownership

Review the first experiments and their limits before tuning. Define and label the
chat evaluation set before building the intake flow. Then implement resolution,
constraints, and delivery tools around the allocator, followed by the dispatcher
interface and confirmation workflow. Maintain reproducible evidence throughout.

Owners are not assigned here. Agree ownership of allocation/data, language intake,
UI/deployment, evaluation, and documentation/presentation as a team. These are work
areas, not a prescribed headcount or fixed role split.

Use `uv`, keep provider tests opt-in, preserve the course harness, and work through
branches and PRs. See [repository instructions](../AGENTS.md).
