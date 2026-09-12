import pytest

from app.core.model_config import default_llm_model, is_approved_local_url


def test_memory_selects_supported_model():
    assert default_llm_model(16) == "qwen3.5:4b"
    assert default_llm_model(24) == "qwen3.5:9b"


@pytest.mark.parametrize("url", ["http://127.0.0.1:11434", "bolt://localhost:7687", "http://10.1.2.3:8000"])
def test_private_urls_are_approved(url):
    assert is_approved_local_url(url)


@pytest.mark.parametrize("url", ["https://api.example.com", "https://8.8.8.8", "ftp://127.0.0.1"])
def test_external_or_unsupported_urls_are_rejected(url):
    assert not is_approved_local_url(url)

