#!/bin/zsh
set -u

repo_dir="${0:A:h:h}"
architecture="$(uname -m)"
memory="$(system_profiler SPHardwareDataType 2>/dev/null | awk -F': ' '/Memory:/{print $2; exit}')"

echo "CHARGESHEET INTELLIGENCE — LOCAL SYSTEM CHECK"
echo "Repository: $repo_dir"
echo "Architecture: $architecture"
echo "Apple Silicon: $([[ $architecture == arm64 ]] && echo ready || echo unsupported)"
echo "Memory: ${memory:-unknown}"
echo "Python: $(python3 --version 2>&1)"
echo "Node: $(node --version 2>&1)"
echo "npm: $(npm --version 2>&1)"
echo "Tesseract: $(command -v tesseract >/dev/null && tesseract --version 2>&1 | head -1 || echo NOT INSTALLED)"
if command -v tesseract >/dev/null; then
  languages="$(tesseract --list-langs 2>/dev/null)"
  echo "Gujarati tessdata: $([[ $languages == *guj* ]] && echo ready || echo MISSING)"
else
  echo "Gujarati tessdata: MISSING"
fi
echo "Ollama binary: $(brew list --versions ollama 2>/dev/null || echo NOT INSTALLED)"
if curl --noproxy '*' --silent --fail --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Ollama service: ready on 127.0.0.1:11434"
else
  echo "Ollama service: NOT REACHABLE (start it locally)"
fi
echo "Neo4j: $(command -v neo4j >/dev/null && neo4j --version 2>&1 || echo NOT INSTALLED — optional SQLite graph remains available)"
echo "Selected LLM: $([[ ${memory%% *} -ge 24 ]] 2>/dev/null && echo qwen3.5:9b || echo qwen3.5:4b)"
echo "Embedding model: bge-m3"

