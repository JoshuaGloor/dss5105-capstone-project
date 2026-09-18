# Streamlit dispatch desk

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
sets a local-only listener, headless operation, no file watcher, and disabled usage
telemetry. No separate frontend build or API service is needed.

## Try the workflow

1. Start with R25. BudgetWorks must remain excluded regardless of objective.
2. Switch Lateness / Defects / Hybrid and inspect candidates on the same snapshot.
3. Select Custom weights. Sliders call the same Python scorer; setting every weight
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
- Confirmation is a two-step interaction demonstration only. The tool continues to
  report `commit_allowed=false`. Durable, concurrent allocation is a later phase.
- Static HTML remains independently viewable in Chrome. It is a design reference;
  the running Streamlit app uses native Streamlit controls with the same layout and
  color direction, rather than embedding a fake interactive screenshot.

## Offline verification

Tests use Streamlit's [AppTest](https://docs.streamlit.io/develop/api-reference/app-testing)
to execute the page and interact with its controls without launching a browser.
They check numerical tool integration, errors, request-preference precedence,
confirmation invalidation, and session isolation. No live provider is called.

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
