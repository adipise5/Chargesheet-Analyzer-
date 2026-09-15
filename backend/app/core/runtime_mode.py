"""Small runtime-policy helpers shared by API and service layers."""
from __future__ import annotations

from app.core.config import settings


class ReadOnlyDemoError(PermissionError):
    """Raised when a write is attempted against the hosted snapshot demo."""


def is_read_only_demo() -> bool:
    return bool(getattr(settings, "render_demo", False))


def require_writable() -> None:
    if is_read_only_demo():
        raise ReadOnlyDemoError(
            "This hosted demo is a read-only snapshot. Upload, correction, import, and purge actions are disabled."
        )
