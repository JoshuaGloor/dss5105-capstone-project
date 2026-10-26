# Streamlit dispatch desk

Data v3 is now loaded. Candidate tables show the April queue values; the Streamlit
estimate breakdown also shows processing, transport and expected rework. Impossible
requests show the earliest permitted estimated delivery and review options, with
confirmation disabled. See [the update review](V3_REFINEMENT.md).


The web app follows the [HTML prototype](prototype/index.html) and calls the existing
Python dispatch tools directly. Request selection, objective presets, and custom
weight sliders produce new tool previews; the app does not read the prototype's
bundled results or reproduce the scoring formula in browser code.

## Start locally

From the repository root:

```bash
sh scripts/run_app.sh
```

Then open `http://localhost:8501` in Chrome. Stop the server with Ctrl+C in the same
terminal. The script uses the locked project environment, keeps uv caches and
temporary files under `.cache/` in this repository, and does not open a browser.
It downloads missing dependencies on the first run if the environment needs syncing.
Supplied examples need no API key. Natural language uses the configured model only
when you submit or retry a message; see [NATURAL_LANGUAGE.md](NATURAL_LANGUAGE.md).

To choose a different port:

```bash
sh scripts/run_app.sh --server.port 8502
```

The Streamlit entrypoint is `streamlit_app.py`. Application code and local styling
live in `src/dss5105/web_app.py` and `src/dss5105/assets/desk.css`. Project config
sets a local-only listener on port 8501, headless operation, automatic file watching,
save-triggered reruns and disabled usage telemetry. The launcher also watches CSS
assets, course data and example inputs. Keep the page open to see saved changes;
ordinary reruns do not submit model requests or confirm allocations. Generated
results, saved state and caches are excluded from watching to avoid rerun loops.
Dependency or server-configuration changes can still require a server restart.
No separate frontend build or API service is needed.

## Try the workflow

The page opens on **Chat request (live model)**, which needs the model configured in `.env`
(see [NATURAL_LANGUAGE.md](NATURAL_LANGUAGE.md)). For the steps below, choose
**Inbox examples (offline)** in the sidebar.
Start in **Independent previews** for the original reproducible inbox demo.

1. Start with R25. BudgetWorks must remain excluded regardless of objective.
2. Switch delivery / quality / mixed policy and inspect candidates on the same snapshot.
3. Select Set relative priorities. Sliders call the same Python scorer; setting every weight
   to zero shows an error and removes the old preview and confirmation state.
4. Try R08 (refusal), R03 or R05 (clarification), R13 (missing records), and R20
   (deadline exception). None can enter the confirmation demonstration.
5. Try R21. Its cheapest-on-time instruction overrides global presets; the page
   shows the effective weights and the feasibility-filtered recommendation.
6. Return to an on-time recommendation, click Review confirmation, then Confirm demo
   only. This records an acknowledgement in the browser session's server-side state;
   it does not save an allocation, change queues, or contact a workshop.
7. Change the request or weights. The previous review/receipt disappears, including
   when switching back to the earlier configuration.
8. Export tool evidence or inspect its source hashes, inputs, constraints, estimates,
   score components, and configured/effective weights.

The source dates, independent snapshot convention, estimates, and interpretation
limits are specified in [DISPATCH_CONTRACT.md](DISPATCH_CONTRACT.md). Each session's
UI choices are independent; no process-wide mutable desk is cached between users.

## Save a local allocation

Choose **Saved local plan** in the sidebar. Select a ready request, click **Review
confirmation**, enter the confirming dispatcher name, and click **Confirm and save
allocation**. This persists the audited decision and updates shared local planning
queues. Review and export records in **Saved allocation records**. Supplied examples
can exercise this complete flow without calling a provider.

Queues start from the course inbox snapshot and remain at that planning date.
Saved reservations add expected processing/rework occupancy and exclude transport.
The original course files, independent previews and simulator are unaffected.
Switching modes or changing a preview cancels a pending confirmation.

Saved state lives in Git-ignored `runtime/dispatch.sqlite3`. Keep that file to retain
the plan across restarts. Do not delete it to recover from a stale preview; refresh
and review again. Source changes require a separate workspace migration and fail
explicitly. Concurrent saves cannot silently reuse an old state. The same order
cannot be saved again under a new chat message. This version has no cancellation
or reset workflow. See [the record contract](ALLOCATION_RECORD_CONTRACT.md).

## Workshop capacity and additional work

Choose **Workshop register (offline)** in the sidebar. The initial table
shows recorded capabilities, status, batch limits and queues. Enter a category,
quantity and explicit delivery deadline, then select **Check delivery capacity**.
The table explains suspended/capped workshops and shows estimates for eligible ones.

Under **What if we send more work here?**, choose a workshop and extra pieces.
**Compare before and after** places that additional same-category batch ahead of
the reference batch at the fixed planning date. The tools show delivery changes
and the fastest eligible alternative. Both batches must satisfy the course helper.
The scenario adds expected processing/rework, excluding transport. It never changes
the stored plan and does not assess other jobs' deadlines or predict closures.

Both tables recompute from the selected independent or saved-plan queues. Exports
retain source/code hashes and snapshot identity; saved mode includes state revision.
Model calls are never needed in this workspace. Chat routing for these tools is
still planned. See [TOOL_SPEC.md](TOOL_SPEC.md) for the finalized contracts.

## Current boundaries

- Supplied examples use hand-authored fixtures. The separate Natural language mode
  connects model extraction and follow-up clarification to the same Python tools;
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
