"""Server-side GitHub token discovery and failover helpers."""

from __future__ import annotations

import os
from threading import Lock
from typing import Any

_rotation_lock = Lock()
_rotation_index = 0


def _streamlit_secret(name: str) -> str | None:
    try:
        import streamlit as st

        value = st.secrets.get(name)
    except (ImportError, AttributeError, KeyError, RuntimeError, TypeError):
        value = None

    if value is None:
        return None

    value = str(value).strip()
    return value or None


def configured_tokens() -> list[str]:
    """Return unique server-side tokens without exposing their values."""
    tokens: list[str] = []
    # Keep the original name as a backward-compatible fallback for existing deployments.
    for name in ("GITHUB_TOKEN_1", "GITHUB_TOKEN_2", "GITHUB_TOKEN_3", "GITHUB_TOKEN"):
        value = os.getenv(name) or _streamlit_secret(name)
        if value and value not in tokens:
            tokens.append(value)
    return tokens


def token_candidates(explicit_token: str | None = None) -> list[str | None]:
    """Return the explicit user token or an ordered server-token failover list."""
    if explicit_token and explicit_token.strip():
        return [explicit_token.strip()]

    tokens = configured_tokens()
    if not tokens:
        return [None]

    global _rotation_index
    with _rotation_lock:
        start = _rotation_index % len(tokens)
        _rotation_index = (start + 1) % len(tokens)

    return tokens[start:] + tokens[:start]


def is_token_failure(response: Any) -> bool:
    """Identify responses that justify trying another configured token."""
    if response.status_code in (401, 429):
        return True
    if response.status_code != 403:
        return False

    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining == "0":
        return True

    try:
        payload = response.json()
    except (AttributeError, ValueError):
        payload = {}

    message = payload.get("message", "") if isinstance(payload, dict) else ""
    return isinstance(message, str) and "rate limit" in message.lower()
