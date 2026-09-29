#!/bin/sh
# Keep dependency caches and runtime temporary files inside this checkout.
set -eu
project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_root"
mkdir -p "$project_root/.cache/tmp"
export UV_CACHE_DIR="$project_root/.cache/uv"
export TMPDIR="$project_root/.cache/tmp"
export XDG_CACHE_HOME="$project_root/.cache"
export PYTHONDONTWRITEBYTECODE=1
export UV_PYTHON_DOWNLOADS=never
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
# Python imports are watched automatically; include files read directly by the app.
exec uv run --locked streamlit run streamlit_app.py \
  --server.folderWatchList "$project_root/src/dss5105/assets" \
  --server.folderWatchList "$project_root/track2/data" \
  --server.folderWatchList "$project_root/examples" \
  "$@"
