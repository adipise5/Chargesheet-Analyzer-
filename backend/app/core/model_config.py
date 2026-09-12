"""Hardware-aware, localhost-only local model configuration."""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import urlparse


APPROVED_HOSTNAMES = {"localhost", "host.docker.internal"}


def detect_memory_gb() -> int:
    """Return unified memory in GiB without assuming sysctl is available."""
    try:
        value = subprocess.check_output(
            ["sysctl", "-n", "hw.memsize"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        return max(1, round(int(value) / (1024**3)))
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    try:
        text = subprocess.check_output(
            ["system_profiler", "SPHardwareDataType"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        match = re.search(r"Memory:\s*(\d+)\s*GB", text)
        if match:
            return int(match.group(1))
    except (OSError, subprocess.SubprocessError):
        pass
    return 16


def default_llm_model(memory_gb: int | None = None) -> str:
    return "qwen3.5:9b" if (memory_gb or detect_memory_gb()) >= 24 else "qwen3.5:4b"


def is_approved_local_url(value: str) -> bool:
    """Reject public endpoints. Private IPs are allowed for future police LAN deployment."""
    try:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https", "bolt", "neo4j"} or not parsed.hostname:
            return False
        host = parsed.hostname.lower()
        if host in APPROVED_HOSTNAMES:
            return True
        return ip_address(host).is_loopback or ip_address(host).is_private
    except ValueError:
        return False


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    ollama_base_url: str
    llm_model: str
    embedding_model: str
    memory_gb: int

    @classmethod
    def from_env(cls) -> "ModelConfig":
        memory = detect_memory_gb()
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        if not is_approved_local_url(base_url):
            raise ValueError("OLLAMA_BASE_URL must resolve to localhost or an approved private address")
        provider = os.getenv("LLM_PROVIDER", "ollama")
        if provider != "ollama":
            raise ValueError("D1 supports only the local Ollama provider")
        return cls(
            provider=provider,
            ollama_base_url=base_url,
            llm_model=os.getenv("LLM_MODEL", default_llm_model(memory)),
            embedding_model=os.getenv("EMBEDDING_MODEL", "bge-m3"),
            memory_gb=memory,
        )

