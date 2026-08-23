# Working in this repo

Notes for AI coding agents. Humans want [README.md](README.md); this is the
short version of the same rules, so keep the two in agreement.

## Environment

- `uv` only. `uv sync --all-groups` to install, `uv run <cmd>` to run anything.
- Never `pip install`, never activate a venv by hand.
- If you change `pyproject.toml`, commit the updated `uv.lock` too. CI runs
  `uv sync --locked` and fails when the two disagree.

## Models

- Build chat models with `get_model()` from `src/dss5105_capstone_project/llm.py`.
  Do not construct `ChatAnthropic`, `ChatOpenAI`, or call `init_chat_model()`
  anywhere else.
- The model comes from `LLM_MODEL` in `.env`. Never hardcode a model name.

## Tests

- No test may call a real provider unless marked `@pytest.mark.live`.
- `uv run pytest` must stay free and offline. Do not run `-m live` unless
  explicitly asked: it spends real money.

## Notebooks

- Notebooks in `notebooks/` are jupytext-paired with a `py:percent` twin.
- Prefer committing the `.py`. If an `.ipynb` is committed, it must be in sync
  with its `.py`, and CI will fail if it isn't.

## Style

- `ruff` owns formatting and linting (line length 119). Don't hand-format.
- Plain ASCII in code, comments, and docs: no em dashes, no smart quotes.

## Never

- Commit `.env`, an API key, or any other secret.
- Push directly to `main`. Branch, open a PR, let CI run.
