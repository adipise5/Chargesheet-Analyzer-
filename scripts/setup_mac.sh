#!/bin/zsh
set -euo pipefail

repo_dir="${0:A:h:h}"
cd "$repo_dir"

[[ "$(uname -m)" == arm64 ]] || { echo "Apple Silicon (arm64) is required for the primary D1 path."; exit 1; }
command -v brew >/dev/null || { echo "Homebrew is required. Install it manually, then rerun."; exit 1; }

missing=()
command -v tesseract >/dev/null || missing+=("tesseract" "tesseract-lang")
command -v ollama >/dev/null || missing+=("ollama")
if (( ${#missing[@]} )); then
  echo "Missing local system packages: ${missing[*]}"
  echo "Run this reviewed command if desired: brew install ${missing[*]}"
  if [[ "${AUTO_INSTALL_SYSTEM:-0}" == "1" ]]; then brew install "${missing[@]}"; fi
fi

if [[ ! -d .venv ]]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r backend/requirements.txt
(cd frontend && npm install)
echo "Setup complete. Run: make check"

