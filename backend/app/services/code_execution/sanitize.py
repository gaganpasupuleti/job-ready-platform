"""Sanitize Judge0 compiler/runtime messages before returning to clients."""

from __future__ import annotations

import re

_PATH_PATTERNS = [
    re.compile(r"/box/\S+", re.IGNORECASE),
    re.compile(r"/tmp/\S+", re.IGNORECASE),
    re.compile(r"/usr/\S+", re.IGNORECASE),
    re.compile(r"/home/\S+", re.IGNORECASE),
    re.compile(r"[A-Za-z]:\\[^\s]+"),
    re.compile(r"file://\S+", re.IGNORECASE),
]
_HOST_PATTERNS = [
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?\b"),
    re.compile(r"\b[\w.-]+\.railway\.(?:internal|app)\b", re.IGNORECASE),
    re.compile(r"\blocalhost(?::\d+)?\b", re.IGNORECASE),
]
_TOKEN_PATTERNS = [
    re.compile(r"(?i)(x-auth-token|authorization|bearer)\s*[:=]\s*\S+"),
    re.compile(r"(?i)password\s*[:=]\s*\S+"),
]


def sanitize_execution_message(message: str | None, *, max_len: int = 4000) -> str:
    if not message:
        return ""
    text = message
    for pattern in _PATH_PATTERNS:
        text = pattern.sub("[path]", text)
    for pattern in _HOST_PATTERNS:
        text = pattern.sub("[host]", text)
    for pattern in _TOKEN_PATTERNS:
        text = pattern.sub("[redacted]", text)
    text = text.strip()
    if len(text) > max_len:
        text = text[: max_len - 3] + "..."
    return text
