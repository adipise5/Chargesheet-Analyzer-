#!/bin/zsh
set -euo pipefail
repo_dir="${0:A:h:h}"
backend_pid=""
frontend_pid=""
cleanup() {
  [[ -n "$backend_pid" ]] && kill "$backend_pid" 2>/dev/null || true
  [[ -n "$frontend_pid" ]] && kill "$frontend_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
"$repo_dir/scripts/start_backend.sh" & backend_pid=$!
"$repo_dir/scripts/start_frontend.sh" & frontend_pid=$!
echo "Backend: http://127.0.0.1:8000/docs"
echo "Frontend: http://127.0.0.1:5173"
wait

