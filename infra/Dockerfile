# Multi-stage image build to create final image without uv. For inspiration/ref,
# see https://github.com/astral-sh/uv-docker-example/blob/main/multistage.Dockerfile

# Build this from the repo root: `{podman | docker} build -f infra/Dockerfile .`

# ---------------------------------------------------------------------------
# Version knobs. Each can be bumped on its own; uv is independent of the rest.
#
# Both stages compose their image name from PYTHON_VERSION and DEBIAN_SUITE, so
# they cannot drift apart. That matters because the venv links against the
# builder's interpreter: a mismatch fails.
# Names are fully qualified since podman has no implicit docker.io; leave as is.
# ---------------------------------------------------------------------------
ARG UV_VERSION=0.12.5
ARG PYTHON_VERSION=3.12
ARG DEBIAN_SUITE=trixie


# ---------------------------------------------------------------------------
# Stage 1/2: resolve dependencies into /app/.venv. Nothing here is shipped.
# ---------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:${UV_VERSION}-python${PYTHON_VERSION}-${DEBIAN_SUITE}-slim AS builder

# uv settings, from https://docs.astral.sh/uv/guides/integration/docker/
#   COMPILE_BYTECODE=1   Makes `uv sync` write .pyc beside each installed .py,
#                        so first import does not pay to compile.
#   PYTHON_DOWNLOADS=0   Use the Python already in this image instead of letting
#                        uv fetch a second interpreter.
ENV UV_COMPILE_BYTECODE=1 UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependencies only, never the project itself: harness.py finds the course
# simulator via Path(__file__).resolve().parents[2], which breaks if dss5105
# lands in site-packages. The final stage puts our code on PYTHONPATH instead.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project


# ---------------------------------------------------------------------------
# Stage 2/2: the image we ship. No uv, no build cache.
# ---------------------------------------------------------------------------
FROM docker.io/library/python:${PYTHON_VERSION}-slim-${DEBIAN_SUITE}

# The app should not run as root, so create the user that USER switches to below.
# --create-home because Streamlit writes ~/.streamlit at startup.
# Created before the copies so we never need `chown -R /app`, which would rewrite
# every file into a new layer and ship the venv twice.
RUN useradd --create-home --home-dir /home/app --uid 10001 app

WORKDIR /app

# Same path as the builder used: the venv hardcodes /app/.venv in its scripts.
COPY --from=builder /app/.venv /app/.venv

# All read at runtime, resolved relative to /app. track2/ and examples/ are data.
COPY src/ ./src/
COPY track2/ ./track2/
COPY examples/ ./examples/
COPY .streamlit/ ./.streamlit/
COPY streamlit_app.py ./

# records.py (the saved plan and its archived copies) and memory.py (the dispatcher's
# profile and standing rules) store SQLite under /app/runtime, creating the directory
# on first use. The rest of /app is root-owned and read-only to the app user, so this
# one directory has to be writable.
RUN mkdir -p /app/runtime && chown app:app /app/runtime

# Python runtime settings, see
# https://dev.to/cod3mason/python-env-variables-in-dockerfile-5920
#   UNBUFFERED=1         Logs leave the process immediately, so `podman logs`
#                        shows them as they happen.
#   DONTWRITEBYTECODE=1  No .pyc written beside our source at runtime. The
#                        dependencies were already compiled in the builder.
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# Where our own code is imported from, because it is deliberately not installed
# into the venv. See the builder stage for why.
ENV PYTHONPATH=/app/src

# Put the venv first so `streamlit` and `python` resolve to it without `uv run`.
# The CMD at the bottom relies on this.
ENV PATH=/app/.venv/bin:$PATH

# Safety check: fail the build, not at runtime. TL;DR check everything is there.
# Every page streamlit_app.py registers is imported, and the assistant's HTML, CSS and JS are read:
# they ship as data under src/, so we read the files to make sure they are there.
#
# The point of the list comprehension is the read_text call on each of app.html, app.css and app.js,
# which raises FileNotFoundError here instead of blanking the default page in production.
RUN python -c "import dss5105.harness, dss5105.dispatch, dss5105.web_app, \
    dss5105.workshop_ui, dss5105.lab_page, dss5105.memory_page; \
    from dss5105.assistant_page import ASSETS; \
    [(ASSETS / f'app.{part}').read_text(encoding='utf-8') for part in ('html', 'css', 'js')]; \
    print('Import check ok')"

# Streamlit writes ~/.streamlit at startup, so runtime user needs its own HOME.
USER app
ENV HOME=/home/app

EXPOSE 8501

# .streamlit/config.toml binds 127.0.0.1: right for local build, doesn't work behind Caddy.
# Flags outrank config file, so override here instead of editing .streamlit/config.toml.
CMD ["streamlit", "run", "streamlit_app.py", \
    "--server.address=0.0.0.0", \
    "--server.port=8501", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false"]
