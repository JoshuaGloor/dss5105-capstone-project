# Sprint 1 deck

Upload [the deck](slides/reviewed/Presentation_Group11_Sprint1.pptx) by 15:00 on
Fri 16 Oct 2026, with its exact filename. A [PDF copy](slides/reviewed/Presentation_Group11_Sprint1.pdf)
sits alongside; both names satisfy the course rule. If the lecture-theatre PC renders fonts
differently, present the PDF. The format is a live 5-minute talk plus 2 minutes of Q&A, with
a hard stop.

The [speaker script](slides/reviewed/Opening_Script_Group11.txt) is about 670 words, roughly
4 minutes 28 seconds at 150 words per minute. CHEN ZEPENG presents slides 1-3.

## Build

```bash
mkdir -p .cache/deck-node && npm --prefix .cache/deck-node install pptxgenjs@3.12.0
uv run python scripts/defects_frontier.py   # only if the evidence needs refreshing
node scripts/build_sprint1_deck.mjs
```

Every metric on the slides is read from `docs/evidence/data-v3.json`,
`margin-study.json` and `defects-frontier.json`, every workshop fact from
`track2/data/workshops.csv`, and the inbox mix from `track2/data/data_dictionary.md`.
Nothing is typed in by hand. The speaker notes are copied
from the script file, so the two cannot drift. The product screenshot is
`slides/assets/desk-r25.png`, the desk on request R25 showing the tool-written reasons
for its pick. Recapture it after UI changes; the build reads its size from the file.

The supplied source deck remains at `slides/Presentation_Group11_Sprint1.pptx`, and the
earlier GPT revision is kept under `slides/reviewed/previous/`.

## Flow, in the order Spec v5 asks for

| Slide | Content | Time |
|---|---|---|
| 1 | Title, team, primary objective, the workshop network | 0:25 |
| 2 | Problem: one chat message is the decision; three questions; only 7 of 30 inbox requests are plain | 0:35 |
| 3 | Solution and architecture: the modules behind "the model reads, Python calculates, a person approves", their data flows and stores, and the trust boundary around the one external model call | 0:50 |
| 4 | Objective declaration and an honest scoreboard across all four course objectives | 0:35 |
| 5 | Business value | 0:30 |
| 6 | Progress: simulator evidence, the earliest-finish tie, and the AWS deployment pipeline | 0:35 |
| 7 | Progress: the desk today | 0:25 |
| 8 | Risks and key assumptions | 0:30 |
| 9 | Sprint 2 roadmap: an AI-native desk, with success criteria | 0:25 |
| 10 | Questions (Q&A crib notes in the speaker notes) | - |

## Design

The house style is SweaterCo as a classic fashion house: ink, ivory and camel, a Georgia
serif for display type, Arial for body text, and letter-spaced small capitals for labels.
Oxblood marks bad news and forest green marks a win. Georgia and Arial ship with both
Windows and macOS. Charts are drawn as shapes, so PowerPoint, Keynote and Google Slides
render them identically.

## Claims to keep precise

- The 30/30 inbox result is fixture replay on hand-written inputs. It tests the tools, not
  language understanding.
- Simulator results are not factory results. Slide 5 shows costs in $ for readability; the
  data gives cost per piece with no currency, so say so if asked.
- Slide 9's AI-native items are a team proposal in [AI_NATIVE_PLAN.md](AI_NATIVE_PLAN.md),
  not built yet. Say "we plan", never "the desk does".
- The deployment on slide 6 is the AWS pipeline merged to main (infra/, deploy.yaml,
  docs/DEPLOYMENT.md). Every merge that touches the app builds an image; deploying is a
  manual workflow run, and the instance is stopped when unused.
- Earliest finish ties the lateness preset; say so.
- On defects, greedy_biggest still wins. See [DEFECTS_FRONTIER.md](DEFECTS_FRONTIER.md).
- On fairness, random has the lower max share (22.6% vs 26.2%); no fairness setting is tuned yet.
- On robustness, cheapest's late share does not move under closure only because it is
  already 92% late in both runs.
- The 10-day buffer setting costs less than random per replay; it is a lateness-first
  configuration with a small cost weight, chosen on development seeds.
- The Sprint 2 target of 27/30 live requests is a team proposal, not a result. Agree it
  before presenting, or change `SPRINT2_TARGET` in the build script.
