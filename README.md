# DSS5105 Capstone Project: Group 11

Track 2: the Quick-Response Subcontracting Desk. The first working increment is
an offline, configurable allocator evaluated with the course's shared simulator.
The Streamlit prototype adds natural-language intake and structured dispatch previews.
Course sources: Spec v5, Tracks v4 and Data v3. See [the update review](docs/V3_REFINEMENT.md)
and [refreshed evaluation evidence](docs/V3_EVALUATION.md).

## Quickstart

```bash
git clone git@github.com:JoshuaGloor/dss5105-capstone-project.git
cd dss5105-capstone-project
uv sync --all-groups         # installs everything into .venv
uv run pre-commit install    # sets up the commit-time checks
uv run pytest                # see current tests pass
```

As suggested by the course, we run and manage everything using `uv`.
No API key is needed for tests, allocation experiments, or the prototype. Set up
`.env` only when deliberately running a provider-backed feature or live test.

## Streamlit dispatch desk

```bash
sh scripts/run_app.sh
```

Open `http://localhost:8501` in Chrome. The page supports request selection, live
Python previews, objective presets and custom weight sliders, candidate comparison,
exclusion reasons, evidence export, and confirmation. Supplied examples need no API key.
The default **Independent previews** workspace keeps the course snapshot unchanged.
Choose **Saved local plan**, review an on-time recommendation, enter the confirming
dispatcher's name, and select **Confirm and save allocation** to persist a record
and update local planning queues. Saved records survive restarts and can be exported.
They live in Git-ignored `runtime/dispatch.sqlite3`; no workshop is contacted.
See [the record contract](docs/ALLOCATION_RECORD_CONTRACT.md) for queue semantics,
duplicate/stale-preview protection, and local-prototype limitations.
The page opens on **Chat request (live model)**: paste a message or start from a course
inbox message, and answer clarification questions using the configured model.
Each reply is a card built by Python from tool output. Answer buttons for ambiguous
orders and refused workshops apply the choice without another model call.
Provider calls happen only on send/retry. **Inbox examples (offline)** is the offline mode
with no model and no API key. See [the language guide](docs/NATURAL_LANGUAGE.md).
The launcher keeps caches/temp files in this project and does not open a browser.
The default port is fixed at 8501. Saved Python, CSS, data and example-input changes
automatically rerun the open page; no model call or allocation is triggered by a rerun.
See [the web app guide](docs/STREAMLIT_APP.md) for examples, tests, and limitations.

Choose **Workshop register (offline)** to inspect the workshop register,
check a batch against an explicit delivery date, and compare delivery before and
after additional work. Checks use the selected workspace's queues and never reserve
capacity. This is a direct tool workspace; free-text capacity questions are still
planned. The refreshed layout keeps scoring details under an advanced expander.

The [first real-model evaluation](docs/CHAT_EVALUATION_RESULTS.md) covers the old inbox
and is historical evidence only. Data v3 fixture replay is refreshed; a new live
language run on the corrected inbox is still required.
See [the evaluation command](docs/CHAT_EVALUATION.md) to reproduce a paid run;
default tests remain offline. Its draft-check results are not held-out accuracy.

## Portable HTML prototype and CLI

```bash
uv run python -m dss5105.dispatch --request R12 --preset lateness
uv run python -m dss5105.prototype
```

Open [the HTML prototype](docs/prototype/index.html) directly in a browser. It
compares Python-generated previews, explains exclusions, and exports evidence.
The web interface uses **Streamlit**; this HTML remains a standalone design reference.
No Streamlit installation is needed to open the HTML.
Its request interpretations are hand-authored development fixtures, not a working
language agent. Confirmation demonstrates the UI only; it saves no allocation.

See [PLAN.md](PLAN.md) for the staged build plan,
[the dispatch run guide](docs/DISPATCH_PREVIEW.md) for input/state conventions, and
[the Sprint 1 architecture](docs/sprint1-architecture.svg) for implemented vs planned
components. The team's primary objective is **minimise lateness**, measured by
late fraction and mean late days.

Keep new artifacts, helper scripts, caches, and temporary files within the project.
Prototype review does not require browser automation or an external browser profile;
open the HTML directly in Chrome.

## Allocation experiments (no API key needed)

```bash
uv run python -m dss5105.evaluate --output results/allocation-normal.json
uv run python -m dss5105.evaluate --shock --seeds 10 --output results/allocation-shock.json
```

These compare the course baselines, a short earliest-finish heuristic, and
lateness/defects/hybrid weight configurations. Delivery arithmetic stays in Python;
objectives are configuration. Eligibility uses the course helper, and the course
simulator is left unchanged. See [the allocation guide](docs/ALLOCATION_ENGINE.md)
for the score definition, assumptions, saved traces, and current limitations.

The same entry point can run one preset or a custom mix without editing code:

```bash
uv run python -m dss5105.evaluate --preset defects
uv run python -m dss5105.evaluate --lateness-weight 1 --defects-weight 0.05 --cost-weight 0.1
```

For an exploratory weight grid and additional random-seed checks, run
`uv run python -m dss5105.tune`. This saves `results/weight-search.json` without
changing the existing presets. See [WEIGHT_TUNING.md](docs/WEIGHT_TUNING.md) for
the selection rules, observed tradeoffs, and limits of these development results.

## Project documents

Read [PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) for course sources, scope, milestones,
and implementation status. [DATA_FINDINGS.md](docs/DATA_FINDINGS.md) records source
facts and reproducible experiment results;
[TOOL_SPEC.md](docs/TOOL_SPEC.md) separates implemented interfaces from planned tools;
[EVALUATION_PLAN.md](docs/EVALUATION_PLAN.md) distinguishes course requirements from
our proposed methodology. Team proposals are not verified results or extra course
requirements. [SPRINT1_REVIEW.md](docs/SPRINT1_REVIEW.md) ranks the open gaps before Sprint 2,
and [DEFECTS_FRONTIER.md](docs/DEFECTS_FRONTIER.md) shows where a baseline still wins. The team has selected **minimise lateness** as its primary objective.

When data or policies change, reproduce affected results with the documented runner
and update their evidence. Do not treat the earlier, unretained probes as established
findings. Finalize proposed tool contracts before implementing them. The current
scorer supports lateness, defects and cost weights; fairness scoring is future work.

## Understanding the repo

Below is a brief overview of the repo.

In practice we spend our time in `notebooks/`, `src/`
and `tests/`, and the rest quietly keeps everyone's setup in sync.

| File | What it's for | When it comes up |
|---|---|---|
| `src/dss5105/` | Our actual code | This is where we build |
| `tests/` | Tests for that code | Alongside the code we write |
| `notebooks/` | Exploration and analysis | For exploration using notebooks |
| `.env` (yours; don't commit) | Your own API key | Once, during setup |
| `pyproject.toml` | Dependency list + tool settings | When we add a package |
| `uv.lock` | The exact version of every package | Updates itself, we just commit it |
| `.python-version` | The one Python we all run; `pyproject.toml` only sets a minimum | Static, never changes for this course |
| `.env.example` | Template listing which keys exist | When a new env variable should be added |
| `.gitignore` | What git deliberately ignores | Sometimes |
| `CONTRIBUTING.md` | Step-by-step setup and how to contribute | Whenever helpful |
| `AGENTS.md` | Same rules, written for AI coding agents | When an agent (or you) decides to modify this |
| `CLAUDE.md` | One-line pointer to `AGENTS.md` | Never |
| `.pre-commit-config.yaml` | Checks that run as we commit | Runs on its own, at commit time |
| `.github/workflows/ci.yaml` | Checks that run on a pull request | Runs on its own, on every PR |

### 1. The environment: `pyproject.toml`, `uv.lock`, `.python-version`

These make sure we all have the same environment.
`uv sync` makes `.venv` match `uv.lock`.

**Adding a package:**

```bash
uv add <package-name>
```

This edits `pyproject.toml` *and* `uv.lock`. Commit both. If you forget the
lock file, CI fails: it runs `uv sync --locked`, which refuses to run when the
two have drifted apart.

### 2. The code: `src/`, `tests/`

`src/dss5105/` holds the package, `tests/` holds its tests.

LangChain allows us to code in a vendor agnostic way.
Both classes, `ChatOpenAI` and `ChatAnthropic` are `BaseChatModel`s.
We can use [`init_chat_model`](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model) with the model string to take advantage of this.
`get_model()` in `llm.py` provides a simple wrapper for that: in our scripts we
call `get_model()` and it returns the model named by `LLM_MODEL` in `.env`. If
`LLM_MODEL` isn't set, it fails right away with a message telling you what to
fix, instead of breaking confusingly later.

We deliberately don't set `temperature`. Recent Anthropic models (Sonnet 5,
Opus 5 and newer) reject it with a 400, so passing it would break the default
provider. That means we can't dial in determinism that way, and identical
prompts can give slightly different answers.

We can use `llm.py` to add anything that is model related later as well.

**Recommendation:** we build models with `get_model()`, not `ChatAnthropic()`,
`ChatOpenAI()`, or `init_chat_model()` directly.

**Running tests:**

```bash
uv run pytest          # fast, free, no API calls
uv run pytest -m live  # really calls the provider, costs money
```

Anything that reaches a real provider needs `@pytest.mark.live`. Plain
`uv run pytest` skips those, and so does CI, so no PR ever spends tokens. When
a test does need a model, pass a fake one in (`FakeListChatModel`) rather than
importing the real thing, so it stays free and deterministic.

### 3. Keys: `.env.example`, `.gitignore`

`.env.example` is the committed template: variable names, no values. `.env` is
your own copy with the real keys, and `.gitignore` keeps it out of git.

```bash
cp .env.example .env  # then paste in your own key
```

You only need the key for the provider you actually use.

**If a key does get committed**, revoke it in the provider console and generate
a new one. No need to panic, this repo is private.

### 4. Commit-time checks: `.pre-commit-config.yaml`

These run automatically on `git commit`, against the files you staged.
As described in the [Quickstart](#quickstart), you set them up as follows:

```bash
uv run pre-commit install  # once per person, per clone
```

What runs:

- **ruff** lints and formats our Python.
- A few cheap safety nets: catch leftover merge conflict markers, check that
  YAML and TOML still parse, and tidy up whitespace and end-of-file newlines.

**If a commit gets blocked, the hook has usually already fixed the file.** Look
at what changed, `git add` it, and commit again.

Run everything manually any time, without committing:

```bash
uv run pre-commit run --all-files
```

### 5. PR-time checks: `ci.yaml`

Runs on every pull request to `main`, and on `main` itself:

1. **`uv sync --locked`** fails if `uv.lock` is stale
   (see [environment section](#1-the-environment-pyprojecttoml-uvlock-python-version)).
2. **`pre-commit run --all-files`** runs the exact same hooks as your machine,
   which also catches anyone who hasn't run `pre-commit install`.
3. **Notebook sync** re-runs `jupytext --sync` and fails if that produces a
   diff, so a committed `.ipynb` and its `.py` can't drift apart.
4. **`uv run pytest`** skips `live` tests by default (`addopts = "-m 'not live'"`),
   so a PR never spends tokens. CI also has no API keys, as a second line of defence.

### 6. Notebooks: `notebooks/` and jupytext

We use [jupytext](https://jupytext.org) because `.ipynb` files are JSON
and their diffs are unreadable.
That means every notebook in `notebooks/` is paired with a `.py` "percent" twin. The
`.ipynb` is what you run, the `.py` is what git diffs and what is reviewable.

If you edit notebooks in JupyterLab, jupytext syncs the `.py` on save
automatically. In VS Code the same holds once you install the extension linked
in [6.1](#61-how-to-use-jupytext); without it, nothing syncs on its own.
You can always trigger a sync manually:

```bash
uv run jupytext --sync notebooks/*.ipynb
```

**Recommendation: commit the `.py`, not the `.ipynb`.** The `.py` holds the full
source, so anyone can rebuild a runnable notebook from it:

```bash
uv run jupytext --sync notebooks/my_notebook.py  # recreates the my_notebook.ipynb
```

That keeps outputs and unreadable JSON diffs out of Git, and avoids bloating the repo.

**If we do decide to commit an `.ipynb` (e.g., fear of plots not being reproducible etc.),
it has to be in sync with its `.py`.**
CI checks exactly that and fails if the two disagree ([PR-time checks](#5-pr-time-checks-ciyaml)).

**Committing rewrites the notebook.** The commit hooks sync your edits into the
`.py`, let ruff format it, then write the result back into the `.ipynb`. So if
the notebook is open in Jupyter while you commit, reload it before carrying on.
Otherwise the stale buffer saves the old, unformatted source back over what the
hooks just did.

For the same reason, **edit one side at a time**. If both an `.ipynb` and its
`.py` change before a sync, jupytext keeps whichever was written last and
silently discards the other. Work in the notebook, or work in the script, and
sync in between.

#### 6.1 How to use Jupytext

For a quick run, start JupyterLab with:

```bash
uv run jupyter lab
```

Right-click a `.py` file and select **Open With > Jupytext Notebook** to run it as a notebook.

For VS Code, install the
[jupytext extension](https://marketplace.visualstudio.com/items?itemName=congyiwu.vscode-jupytext)
and right-click the `.py` file and select **Open as a Jupyter Notebook**.
