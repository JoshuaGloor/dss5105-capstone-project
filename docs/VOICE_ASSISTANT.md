# Voice dispatch assistant

The app is called StitchFlow: say an order, and it finds the right workshop.

The Sprint 2 announcement asks Track 2 teams to think like the user: "a dispatcher might
talk to your system on their phone and ask it to send products to a customer." This is
that flow, built on the same tools the desk and the simulator use.

Run `sh scripts/run_app.sh` and open `http://localhost:8501` in Chrome. The app opens on
**Assistant**. Voice needs Chrome, Edge or Safari on `localhost` (or HTTPS); every other
browser can type.

## The user and the job

Our user is SweaterCo's production dispatcher, the person who handles the dispatch chat,
on the factory floor rather than at a desk. Five people post requests there (Ravi, Priya, Mei,
Chen and the boss), for example "ORD-109, 500 vests, keep it away from BudgetWorks", and
today the answer comes from memory: which of eight workshops can make it, which is free,
which is allowed. The dispatcher needs to say what has to go out, hear a safe answer to trust, book it in one gesture, and know
the record is there if anyone asks later.

## The journey, step by step

| Step | The dispatcher does | The assistant does |
|---|---|---|
| 1. Glance | Opens the app on the phone | Greets the dispatcher by name. The workshop strip shows each shop's queue as a ring (green to red); OldMill is greyed out as suspended, FreshStart carries its 300-piece cap |
| 2. Ask | Holds the microphone: "ORD-109, 500 vests for Harbor Knits, due April 13. Keep it away from BudgetWorks." | Shows the live transcript while the dispatcher talks, then "Checking every workshop" |
| 3. Hear the answer | Listens | Card and voice: "GiantWeave can deliver order 109 by Thursday 9 April, 3.71 days early. Cost 550, defect risk 6.0%." The card shows the delivery timeline against the deadline, why this shop, the other permitted shops, and why the rest cannot take it ("BudgetWorks: Excluded by Charles") |
| 4. Book | Says "book it" | Opens a confirmation sheet: order, shop, arrival, cost, the constraint kept, and the dispatcher's name. Nothing is saved yet |
| 5. Confirm | Slides to book | Recomputes the answer, checks nothing changed, saves the booking with its evidence, reserves capacity, and reads back a reference |
| 6. Teach | Taps "Remember" on "Always avoid BudgetWorks for Harbor Knits?" | Stores a standing rule with the requester's own words and the booking it came from |
| 7. Next order | "ORD-081 needs to go out" | Applies the rule and says so on the card: "From memory: Avoid BudgetWorks for Harbor Knits", with who said it, when, and their words |
| 8. Check | "What did we book today?" | Lists this plan's bookings from the ledger, with no model call |

The **Desk** page is the same decision for a desktop; **Objective lab** replays the
simulator under any priorities; **Memory** shows and manages everything remembered.

## How one turn works

```text
voice (browser speech recognition) or typing
  -> router (Python): "book it", "cancel", "new request", "what did we book", "how busy is X"
       -> answered from records and memory; the model is never called
  -> otherwise the language intake (LLM): a typed patch, every field quoting the message
  -> Python validation: quotes must occur, dates and quantities normalised, questions asked
  -> tools: order lookup, remembered rules, course eligibility, delivery estimates, ranking
  -> card and spoken reply: Python templates over tool strings
  -> booking: slide to confirm with a name -> SQLite record, queues updated, episode logged
```

The model makes one call per spoken or typed request. Tapped answers, priority changes,
memory questions and control phrases make none. The right-hand panel on a desktop
("Behind the answer") shows each of these steps for the latest answer, including the
exact fields the model extracted and their quotes.

## Key choices, and the alternative each one beat

| Choice | Alternative considered | Why |
|---|---|---|
| Browser speech recognition (Web Speech API) | Upload audio to a server transcription model | No extra key, cost or latency; live words appear while the dispatcher talks. Trade-off: Chrome sends audio to its own service, and Firefox has no support, so typing always works too |
| Voice proposes, a slide commits | Book on a spoken "yes" | A misheard "yes" on a noisy floor would send real work to a workshop. The slide shows exactly what will be saved |
| Control phrases matched by Python | Let the model classify every utterance | Deterministic, free, and a message cannot talk the system into a booking |
| Spoken text from Python templates | Let the model summarise | The track's worst failure is a hallucinated delivery date. The voice reads the same tool strings as the card |
| Memory as confirmed, attributed rules in SQLite | Vector store or model "memory" | Auditable, applied as hard constraints, never invented. A rule exists only because a dispatcher confirmed a booking with that constraint |
| Streamlit custom component (no iframe) | A separate React app and API | One server, the same Python tools, and the repository's Streamlit rule. The component runs in the page, so the browser can use the microphone |

## Memory

| Layer | Holds | Lifetime |
|---|---|---|
| Working memory | The request so far, open questions, quoted evidence | This session |
| Standing rules | Constraints confirmed with a booking, scoped to a customer | Saved in `runtime/memory.sqlite3` |
| Booking ledger | Confirmed allocations, their evidence and queue changes; also the fairness ledger | Saved in `runtime/dispatch.sqlite3` |
| Conversation log | What was said and what the tools answered | Saved, append-only |
| Profile | Name on bookings, priorities, voice settings | Saved |

Rules are applied by Python as exclusions with their provenance. A message's own
constraint keeps its own provenance. Only an explicit tap pauses or resumes a rule.
See [TOOL_SPEC.md](TOOL_SPEC.md#memory-store) for the contract.

## Hard cases

| Case | What happens |
|---|---|
| Misheard quantity or order | The transcript is shown, and the card repeats order, customer, pieces and date from `orders.csv`. A quantity that contradicts the order asks for confirmation. Booking needs the slide |
| Ambiguous order ("the TrendCart order") | Tap-to-answer chips list only in-progress matches; no guess |
| Impossible date (ORD-103, 2,000 scarves by 4 April) | "No workshop can make it"; earliest date, days late, a two-shop split estimate; no booking button |
| Suggested shop that cannot take it (QuickStitch for scarves) | Refused with the reason, and the best permitted alternative |
| Data we do not have ("which shop did we use last October?") | Declined; lists only this desk's own bookings, says nothing earlier exists |
| Model unavailable | Retry button. Without a configured model, the course inbox examples still run from their reviewed interpretations |
| No microphone permission, noisy floor | A clear message and the text box |
| The plan changed before confirming | The booking is recomputed in one transaction and refused if stale |

## A two-minute demo script

The recorded Sprint 2 video follows the script in
[docs/slides/Sprint2_Video_Script_Group11.txt](slides/Sprint2_Video_Script_Group11.txt); this is the
short version for a live run.

1. (0:00) Phone view. "I'm Charles, playing the dispatcher." Point at the workshop strip.
2. (0:10) Hold the mic: "ORD-109, 500 vests for Harbor Knits, due April 13. Keep it away
   from BudgetWorks." Let the reply play. Open "Compare" and "Can't take it".
3. (0:40) Say "book it", slide to confirm, show the receipt, tap Remember.
4. (1:00) Hard case: "QuickStitch for the scarves on ORD-103?" Refusal, reason, and the
   impossible-date options.
5. (1:25) "ORD-081 needs to go out": the memory chip appears.
6. (1:40) Open Priorities, pick Quality, apply: same request re-ranked with no model call.
7. (1:50) Point at "Behind the answer": what the model extracted, what Python computed.

## Limits

- Speech recognition quality depends on the browser's service; recognition is not
  evaluated yet. Typed requests remain the reference input for the inbox evaluation.
- A phone on the same Wi-Fi needs HTTPS for the microphone; on plain HTTP, type.
- VS Code's built-in browser and other Electron windows expose the speech API but have no
  speech service, so every attempt fails as a network error. The app treats them as
  unsupported and says so; open it in Chrome, Edge or Safari to talk.
- Dispatcher identity is self-declared; there is no authentication.
- Bookings are a local plan: no workshop is contacted, and splits cannot be booked.
