#!/bin/zsh
set -euo pipefail
repo_dir="${0:A:h:h}"
cd "$repo_dir/frontend"
[[ -d node_modules ]] || { echo "Frontend dependencies missing. Run: make setup"; exit 1; }
exec npm run dev

