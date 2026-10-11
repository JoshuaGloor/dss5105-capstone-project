# Streamlit dispatch desk

Data v3 is now loaded. Candidate tables show the April queue values; the Streamlit
estimate breakdown also shows processing, transport and expected rework. Impossible
requests show the earliest permitted estimated delivery and review options, with
confirmation disabled. See [the update review](V3_REFINEMENT.md).


The web app follows the [chat-first HTML prototype](prototype/redesign_chat.html) and calls the
existing Python dispatch tools directly. Each request sent to the desk produces a new tool preview
and the page shows one request and its answer at a time; the app does not read the prototype's bundled results or reproduce the
scoring formula in browser code.

## Start locally

From the repository root:

```bash
sh scripts/run_app.sh
```

Then open `http://localhost:8501` in Chrome. Stop the server with Ctrl+C in the same
terminal. The script uses the locked project environment, keeps uv caches and
temporary files under `.cache/` in this repository, and does not open a browser.
It downloads missing dependencies on the first run if the environment needs syncing.
Supplied examples need no API key. Typed messages use the configured model only
when you send or retry one; see [NATURAL_LANGUAGE.md](NATURAL_LANGUAGE.md).

To choose a different port:

```bash
sh scripts/run_app.sh --server.port 8502
```

The Streamlit entrypoint is `streamlit_app.py`. Application code and local styling
live in `src/dss5105/web_app.py` (page frame), `src/dss5105/chat_ui.py` (the answer view, sending and saving),
`src/dss5105/cards.py` (answer tiles and the working section) and `src/dss5105/assets/desk.css`. Project config
sets a local-only listener on port 8501, headless operation, automatic file watching,
save-triggered reruns and disabled usage telemetry. The launcher also watches CSS
assets, course data and example inputs. Keep the page open to see saved changes;
ordinary reruns do not submit model requests or confirm allocations. Generated
results, saved state and caches are excluded from watching to avoid rerun loops.
Dependency or server-configuration changes can still require a server restart.
No separate frontend build or API service is needed.

## Try the workflow

The page opens on **Start here** ("Which order needs a workshop today?"). Typing a message uses the
model configured in `.env` (see [NATURAL_LANGUAGE.md](NATURAL_LANGUAGE.md)). The **Try an example
scenario** cards, one per request kind in the course data dictionary, and the **Examples** list below
the page send supplied examples to the desk offline, with no model call. The page shows the newest
request and its answer; sending another replaces it. The example on screen is the one marked with a check, and sending scrolls the page back to the answer.

The gold **Objective** button in the banner opens the objective choice (Lateness, Defect, Hybrid,
Custom) and the **Preview only / Saved local plan** workspace switch. A change applies to the next
request you send; each answer shows the objective it was produced with. The **Saved plan** button
lists saved allocations. **Show working** on an answer opens a column to the right of the answer
(the answer text shrinks to make room) with the comparison, exclusions, estimate breakdown, reference policies, weights, tool trace and the
raw evidence export. The working follows the newest answer; the column stays in view while you scroll.

1. Click the R25 example. BudgetWorks must remain excluded regardless of objective.
2. Switch the objective and send R25 again. The newer answer replaces the first and shows its own objective.
3. Select Custom. Sliders set the weights the Python scorer uses for the next request. Setting
   every weight to zero shows an error and sends nothing.
4. Try R08 (refusal), R03 or R05 (clarification), R13 (missing records), and R20
   (deadline exception). Only a ready recommendation offers **Review confirmation**.
5. Try R21. Its cheapest-on-time instruction overrides global presets; the answer shows the
   request's own priority and the feasibility-filtered recommendation.
6. On an on-time recommendation, click Review confirmation, then Confirm preview only.
   This marks the answer in the session; it does not save an allocation, change queues, or
   contact a workshop. A **Next** button then sends the next unsent example.
7. Sending another request or switching workspace closes a pending review.
8. Open **Show working** to export tool evidence or inspect its inputs, constraints,
   estimates, score components, and configured/effective weights.

The source dates, independent snapshot convention, estimates, and interpretation
limits are specified in [DISPATCH_CONTRACT.md](DISPATCH_CONTRACT.md). Each session's
UI choices are independent; no process-wide mutable desk is cached between users.

## Save a local allocation

Choose **Saved local plan** in the Objective panel. Select a ready request, click **Review
and save**, enter the confirming dispatcher name, and click **Confirm and save
allocation**. This persists the audited decision and updates shared local planning
queues. Review and export records under **Saved plan** in the banner. Supplied examples
can exercise this complete flow without calling a provider.

Queues start from the course inbox snapshot and remain at that planning date.
Saved reservations add expected processing/rework occupancy and exclude transport.
The original course files, independent previews and simulator are unaffected.
Switching workspace or sending another request cancels a pending confirmation. An answer produced before the plan changed is rejected as stale, so send the request again.

Saved state lives in Git-ignored `runtime/dispatch.sqlite3`. Keep that file to retain
the plan across restarts. Do not delete it to recover from a stale preview; refresh
and review again. Source changes require a separate workspace migration and fail
explicitly. Concurrent saves cannot silently reuse an old state. The same order
cannot be saved again under a new chat message. This version has no cancellation
or reset workflow. See [the record contract](ALLOCATION_RECORD_CONTRACT.md).

## Current boundaries

- Supplied examples use hand-authored fixtures. Typed messages connect model extraction and follow-up clarification to the same Python tools;
  its first live development evaluation and open issues are recorded in
  [CHAT_EVALUATION_RESULTS.md](CHAT_EVALUATION_RESULTS.md).
- All costs, dates, and risk values shown in the comparison come from Python tool
  outputs. Defect risk is per batch; cost uses unspecified source cost units.
- Global weights cannot relax eligibility, exclusions, or explicit request preferences.
- Custom sliders span nonnegative relative weights. The app keeps the existing
  reference scales and exposes them; those scales are not empirically validated.
- Independent mode retains demo confirmation and `commit_allowed=false`. Saved
  mode allows explicit durable confirmation only for an on-time, unallocated,
  in-progress order. The local dispatcher identity is self-declared, not authenticated;
  this is a local planning prototype, not a deployed workshop-booking service.
- Static HTML remains independently viewable in Chrome. It is a design reference;
  the running Streamlit app uses native Streamlit controls with the same layout and
  color direction, rather than embedding a fake interactive screenshot.

## Offline verification

Tests use Streamlit's [AppTest](https://docs.streamlit.io/develop/api-reference/app-testing)
to execute the page and interact with its controls without launching a browser.
They check numerical tool integration, errors, request-preference precedence,
confirmation invalidation, saved-plan restart durability, failure handling and session
isolation. Storage tests also cover concurrent stale saves, idempotency, tampering,
and transactional rollback. No live provider is called.

Keep verification caches and temporary files local:

```bash
mkdir -p .cache/tmp
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" \
XDG_CACHE_HOME="$PWD/.cache" PYTHONDONTWRITEBYTECODE=1 \
uv run --locked pytest --basetemp=.cache/pytest
```

`.cache/pytest` is a disposable test directory; pytest replaces its contents on a
run. Do not put annotations or other valuable files there. Browser layout is not
covered by AppTest; review the page manually in Chrome. No browser automation is
part of this workflow.
