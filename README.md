# DSS5105 Capstone Project: Group 11

Track 2: the Quick-Response Subcontracting Desk. A dispatcher describes a job in plain language, and the app turns it into a structured request, picks a workshop and shows its reasoning. The model never does the arithmetic. Every number on screen comes from a Python tool.

What the system optimises for is a set of numbers rather than a code path. One scorer takes five weights (lateness, defects, fairness, robustness, cost), a safety buffer and two lateness settings. A preset is one filled-in set of those.

## Requirements

- **[uv](https://docs.astral.sh/uv/getting-started/installation/)**, the Python package and project manager.
- **Python 3.12**, pinned in `.python-version`. `uv sync` installs it for you.
- **git**
- **Chrome, Edge or Safari** if you want to talk to the assistant instead of typing. It uses the browser's own speech recognition, and the microphone needs either `localhost` or HTTPS. Running it as below gives you `localhost`.
- **An OpenAI API key**, or an Anthropic one. The Assistant and the Desk call the provider whenever you hand them a request of your own. The supplied examples, the allocation experiments and the tests all run without one.
- **Docker or Podman**, only if you want the container route below.

## Setup

```bash
git clone https://github.com/JoshuaGloor/dss5105-capstone-project.git
cd dss5105-capstone-project
uv sync --locked --all-groups  # installs the right Python and every dependency into .venv
uv run pytest                  # confirms the install works
```

Now add your key. Without one you only get the supplied examples:

```bash
cp .env.example .env
```

Set `LLM_MODEL=openai:gpt-5.6` and your own `OPENAI_API_KEY`. We ran the demos and every recorded evaluation on that model, so stay on it if you want your numbers to line up with ours. For Anthropic, `anthropic:claude-opus-4-8` works, with `ANTHROPIC_API_KEY` instead. A model that has extended thinking on by default does not. You only need the key for whichever provider you name.

That is all you need to run things.

## Run it locally

### The app

```bash
sh scripts/run_app.sh
```

Open <http://localhost:8501>. Five pages across the top:

| Page | What it does |
|---|---|
| **Assistant** (opens first) | The dispatcher's phone. Hold the microphone and say what needs to go out, or type it. The answer is a card, read aloud, both written by Python from tool output. "Book it" confirms and saves the booking |
| **Desk** | The same job on a desktop: type or paste a group-chat message, or run an example offline. Objective presets and weight sliders, candidate comparison, exclusion reasons, evidence export |
| **Workshops** | Read-only. The workshop register, delivery checks against a given date, and what extra work would do to an estimate. Never reserves capacity |
| **Objective lab** | Sliders for the four course objectives, cost and a safety buffer, plus two lateness toggles. Every change replays the course simulator over the ten course seeds, normal and with the closure |
| **Memory** | Standing rules, the booking ledger, the conversation log, the profile, and a non-destructive "start a fresh demo plan" |

The pages are documented in more detail under [docs/](https://github.com/JoshuaGloor/dss5105-capstone-project/tree/main/docs).

The Desk works in two modes. **Preview only**, the default, scores every request against the untouched course snapshot, so one request never affects the next. **Saved local plan** keeps a running plan instead: confirming a recommendation, which takes a dispatcher's name, writes it to a local file, and later requests see the capacity it used up.
Switch between the two in the **Objective** panel at the top of the Desk, under "Where do saved allocations go?", which is also where the presets live. [The record contract](https://github.com/JoshuaGloor/dss5105-capstone-project/blob/main/docs/ALLOCATION_RECORD_CONTRACT.md) says what a saved plan can and cannot do.

### In a container

Slower, since it builds the image, but this is what the server runs:

```bash
cd infra
docker compose up --build  # podman compose works the same
```

Open <http://localhost:8080> rather than 8501: Caddy sits in front, and `infra/compose.override.yaml` publishes `8080:80`. You will get a password prompt, because the same Caddyfile serves the public demo. The user is `demo_user`, and the password is `KopiCKosong`. Saving a file does nothing here, and the SQLite state goes to the `app_runtime` volume rather than your `runtime/` directory. The rest is in [DEPLOYMENT.md](https://github.com/JoshuaGloor/dss5105-capstone-project/blob/main/docs/DEPLOYMENT.md).

### The allocator on its own

No API key needed for the below runs.

```bash
# The three course baselines, a short earliest-finish heuristic, and the five
# objective presets
uv run python -m dss5105.evaluate --output results/allocation-normal.json
uv run python -m dss5105.evaluate --shock --seeds 10 --output results/allocation-shock.json

# One preset, or a custom mix
uv run python -m dss5105.evaluate --preset lateness
uv run python -m dss5105.evaluate --lateness-weight 1 --defects-weight 0.05 --cost-weight 0.1
```

Each run prints its table. The first two also save JSON wherever `--output` points. Delivery arithmetic stays in Python, eligibility uses the course helper, and the course simulator is left unchanged.

### The tests

```bash
uv run pytest
```

That is what CI runs too: free and offline. The `live` marker is there so tests that really call a provider can be opted into with `uv run pytest -m live`, but we only ever wrote one, a check that your key and `LLM_MODEL` work.

## Contributing

`main` is protected: branch, open a pull request, let CI run. [CONTRIBUTING.md](https://github.com/JoshuaGloor/dss5105-capstone-project/blob/main/CONTRIBUTING.md) has the rest, with screenshots, and [AGENTS.md](https://github.com/JoshuaGloor/dss5105-capstone-project/blob/main/AGENTS.md) is the same for AI coding agents.
