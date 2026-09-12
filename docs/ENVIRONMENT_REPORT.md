# Environment report

Detected on 2026-09-09 in `/Users/aditya/Desktop/SAT_del1`.

| Component | Detected value | D1 decision |
|---|---|---|
| Architecture | `arm64` | native Apple Silicon path |
| Machine | MacBook Air `Mac16,12`, Apple M4, 10 cores | no CUDA dependencies |
| Unified memory | 16 GB | `qwen3.5:4b`, one LLM request at a time |
| macOS | 26.5.1 (build 25F80) | native services preferred over Docker |
| Python | 3.14.7, `/opt/homebrew/bin/python3` | supported by project constraint (3.11+); isolated `.venv` |
| Node / npm | v25.1.0 / 11.6.2 | Vite/React frontend |
| Homebrew | 6.0.20 | local dependency manager |
| Ollama | upgraded from 0.17.0 to 0.33.3 | bound to `127.0.0.1:11434`; Qwen and BGE-M3 calls verified |
| Tesseract | 5.5.3 + `tesseract-lang` 4.1.0 | `guj+eng` verified with a mixed Gujarati/English image |
| Java | OpenJDK 25 | available for local Neo4j |
| Neo4j | Community 2026.07.1 | temporary localhost projection verified (24 nodes/21 relationships); secure service disabled by default |

Chosen defaults:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
LLM_MODEL=qwen3.5:4b
EMBEDDING_MODEL=bge-m3
OCR_WORKERS=2
LLM_CONCURRENCY=1
```

The application exposes missing local components as readiness/configuration errors and never uses an automatic cloud fallback. BGE-M3 returned 1,024-dimensional vectors. A local Qwen answer and a source-cited case query were executed successfully.
