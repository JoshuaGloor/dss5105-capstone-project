# Working in this repo

Notes for AI coding agents. Humans want [README.md](README.md); this is the
short version of the same rules, so keep the two in agreement.

## The project

We are building Track 2: the Quick-Response Subcontracting Desk. Read these before
writing code, in this order:

- [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) - the problem, our thesis, the
  architecture, roles, deliverables and dates.
- [docs/DATA_FINDINGS.md](docs/DATA_FINDINGS.md) - source facts, reproducible experiments,
  and inference limits. Use the recorded commands when verification is needed. Update
  the evidence if data or policies change; do not reconstruct lost probes as established facts.
- [docs/TOOL_SPEC.md](docs/TOOL_SPEC.md) - implemented interfaces and proposed tool
  contracts. Finalize a proposed contract before implementing its tool.
- [docs/EVALUATION_PLAN.md](docs/EVALUATION_PLAN.md) - what "working" means and how it is
  measured.

Course requirements come from Spec v5 and Tracks v4 (Data v3); implementation status comes from
code and reproducible evidence. Keep team proposals distinct from requirements and
results. The primary objective is not yet selected. See
[docs/ALLOCATION_ENGINE.md](docs/ALLOCATION_ENGINE.md) for the current offline allocator.

Two rules that override convenience:

- **The LLM never does arithmetic.** Every numeral shown to a user must trace back to a
  tool output. A hallucinated delivery estimate is the worst failure in this track and we
  check compliance automatically.
- **The objective is configuration, not a branch.** The current scorer takes lateness,
  defects and cost weights. Future objective terms must also be configurable, never
  policy-name `if` statements in allocation logic. Fairness scoring is not implemented yet.

## Track 2 data and harness

- `track2/data/` and `track2/harness/simulate.py` are provided course material, committed
  deliberately: the tracks document places no usage restriction on them.
- **Do not modify `simulate.py` in place.** Every team runs the same file so the numbers
  stay comparable. To challenge its assumptions, wrap or subclass it and say so in the
  report.
- `simulate.py` resolves its data as `../data` relative to itself. Keep the `track2/`
  layout intact.
- Call `eligible_workshops()` from the harness rather than reimplementing the eligibility
  rule, so our decisions and the simulator can never disagree.

## Environment

- Keep all newly created artifacts, helper scripts, caches, and temporary files
  inside this project. Do not create external browser profiles or launch browser
  automation for prototype review; the user opens the standalone HTML in Chrome.
- The final web interface uses Streamlit. The HTML prototype is a design reference;
  do not introduce a separate frontend stack or API service without a concrete need.
- Independent previews and simulator evaluation never use saved planning queues.
  Saved local allocations use `records.py` and the contract in
  `docs/ALLOCATION_RECORD_CONTRACT.md`; keep `runtime/` out of version control.
- `uv` only. `uv sync --all-groups` to install, `uv run <cmd>` to run anything.
- Never `pip install`, never activate a venv by hand.
- If you change `pyproject.toml`, commit the updated `uv.lock` too. CI runs
  `uv sync --locked` and fails when the two disagree.

## Deployment

- Everything deployment-related lives in `infra/`: the Dockerfile, the compose
  files, the Caddyfile, and OpenTofu under `infra/tofu/`. Workflows are in
  `.github/workflows/`. Read [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) before
  changing any of it.
- `tofu`, not `terraform`. The two configs are separate on purpose: `bootstrap/`
  creates the state bucket the main config uses as its backend.
- Secrets reach the server from SSM Parameter Store, fetched by the instance's
  own role. Never route them through GitHub Actions, and never put them in
  OpenTofu state.
- Editing `infra/tofu/user_data.sh` replaces the instance and wipes `/opt/app`,
  so the site is down until the next deploy.

## Models

- Build chat models with `get_model()` from `src/dss5105/llm.py`.
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
