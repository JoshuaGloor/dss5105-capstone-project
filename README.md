# DSS5105 Capstone Project: Group 11

> TODO: project description once the topic is fixed.

## Quickstart

```bash
git clone git@github.com:JoshuaGloor/dss5105-capstone-project.git
cd dss5105-capstone-project
uv sync --all-groups         # installs everything into .venv
uv run pre-commit install    # sets up the commit-time checks
cp .env.example .env         # then paste in your own API key
uv run pytest                # see current tests pass
```

As suggested by the course, we run and manage everything using `uv`.

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

Right-click a `.py` file and select **Open With > Notebook** to run it as a notebook.

For VS Code, install the
[jupytext extension](https://marketplace.visualstudio.com/items?itemName=congyiwu.vscode-jupytext)
and right-click the `.py` file and select **Open as a Jupyter Notebook**.
