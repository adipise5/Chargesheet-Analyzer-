#!/bin/zsh
set -euo pipefail
repo_dir="${0:A:h:h}"
cd "$repo_dir/backend"
python_bin="$repo_dir/.venv/bin/python"
[[ -x "$python_bin" ]] || { echo "Python environment missing. Run: make setup"; exit 1; }
exec "$python_bin" -m uvicorn app.main:app --host 127.0.0.1 --port "${APP_PORT:-8000}" --reload

