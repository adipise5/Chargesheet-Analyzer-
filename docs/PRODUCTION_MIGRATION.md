# Production migration

For Gujarat Police infrastructure, deploy the same API contract on internal Linux hosts. Replace `TesseractOCRProvider` with approved IndicOCR/HTR, `OllamaService` with an internal vLLM provider, `OllamaEmbeddingProvider` with a locally hosted BGE-M3 service, and `DocumentStorage` with government object storage. Keep `GraphRepository` but move Neo4j from laptop projection to a secured internal cluster.

Add RBAC, SSO, case-level authorization, encryption at rest, key management, immutable audit export, malware scanning, backup/retention policy, signed model manifests, offline package mirrors, observability with redaction, and load/performance qualification. No provider change may weaken provenance or add public network egress.

