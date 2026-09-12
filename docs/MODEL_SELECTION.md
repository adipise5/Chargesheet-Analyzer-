# Model selection

`backend/app/core/model_config.py` detects unified memory. The default is Qwen3.5 4B on 16 GB and Qwen3.5 9B on 24/32 GB. Both use Ollama at a validated local/private URL. BGE-M3 supplies multilingual embeddings without translating Gujarati. Context is deliberately capped below model maximum, extraction temperatures stay at 0–0.1, analysis at 0.1, and vision transcription at 0.

27B/35B models are never auto-selected. Missing weights are a visible readiness issue. Download is an explicit setup action, not a runtime fallback.

