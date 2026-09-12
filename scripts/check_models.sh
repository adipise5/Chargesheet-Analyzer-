#!/bin/zsh
set -euo pipefail

memory="$(system_profiler SPHardwareDataType 2>/dev/null | awk -F': ' '/Memory:/{print $2; exit}')"
memory_gb="${memory%% *}"
llm_model="${LLM_MODEL:-$([[ ${memory_gb:-16} -ge 24 ]] && echo qwen3.5:9b || echo qwen3.5:4b)}"
embedding_model="${EMBEDDING_MODEL:-bge-m3}"

command -v ollama >/dev/null || { echo "Ollama is not installed. Install locally with: brew install ollama"; exit 1; }
if ! curl --noproxy '*' --silent --fail --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null; then
  echo "Ollama is not listening on 127.0.0.1:11434. Start the local service first."
  exit 1
fi
models="$(curl --noproxy '*' --silent --fail http://127.0.0.1:11434/api/tags)"
for model in "$llm_model" "$embedding_model"; do
  if [[ "$models" == *"\"name\":\"$model"* ]]; then
    echo "$model: ready"
  elif [[ "${1:-}" == "--pull" ]]; then
    echo "Downloading $model once for offline operation..."
    ollama pull "$model"
  else
    echo "$model: MISSING (run: make models)"
  fi
done
