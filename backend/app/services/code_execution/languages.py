"""Centralized language keys → Judge0 IDs with optional live discovery."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Canonical platform keys
LANGUAGE_KEYS = ("python", "java", "cpp", "javascript")


@dataclass(frozen=True)
class LanguageDefinition:
    key: str
    id: int
    name: str
    monaco_id: str
    file_extension: str
    available: bool = True


# Default Judge0 CE 1.13.x language IDs (overridden by discovery when available)
_DEFAULTS: dict[str, LanguageDefinition] = {
    "python": LanguageDefinition("python", 71, "Python (3.8.1)", "python", "py"),
    "java": LanguageDefinition("java", 62, "Java (OpenJDK 13.0.1)", "java", "java"),
    "cpp": LanguageDefinition("cpp", 54, "C++ (GCC 9.2.0)", "cpp", "cpp"),
    "javascript": LanguageDefinition(
        "javascript", 63, "JavaScript (Node.js 12.14.0)", "javascript", "js"
    ),
}

# Runtime registry: judge0_id → definition
SUPPORTED_LANGUAGES: dict[int, LanguageDefinition] = {
    lang.id: lang for lang in _DEFAULTS.values()
}
DEFAULT_LANGUAGE_ID = 71

_KEY_TO_ID: dict[str, int] = {k: v.id for k, v in _DEFAULTS.items()}
_discovery_ts: float = 0.0
_discovered_labels: dict[int, str] = {}


def get_language(language_id: int) -> LanguageDefinition | None:
    return SUPPORTED_LANGUAGES.get(language_id)


def get_language_name(language_id: int) -> str | None:
    lang = get_language(language_id)
    if lang is None:
        return None
    return _discovered_labels.get(language_id, lang.name)


def list_languages(*, available_only: bool = False) -> list[LanguageDefinition]:
    langs = list(SUPPORTED_LANGUAGES.values())
    if available_only:
        return [lang for lang in langs if lang.available]
    return langs


def language_key_for_id(language_id: int) -> str | None:
    lang = get_language(language_id)
    return lang.key if lang else None


def validate_language_id(language_id: int) -> LanguageDefinition:
    lang = get_language(language_id)
    if lang is None:
        raise ValueError(f"Unsupported language id: {language_id}")
    if not lang.available:
        raise ValueError(f"Language temporarily unavailable: {language_id}")
    return lang


def apply_judge0_language_catalog(languages: list[dict]) -> None:
    """Update display names and availability from Judge0 GET /languages."""
    global _discovery_ts
    by_id = {int(item["id"]): item for item in languages if "id" in item}
    updated: dict[int, LanguageDefinition] = {}
    for key, default in _DEFAULTS.items():
        remote = by_id.get(default.id)
        if remote:
            name = str(remote.get("name") or default.name)
            _discovered_labels[default.id] = name
            updated[default.id] = LanguageDefinition(
                key=key,
                id=default.id,
                name=name,
                monaco_id=default.monaco_id,
                file_extension=default.file_extension,
                available=True,
            )
        else:
            logger.warning("Judge0 language id %s (%s) not available", default.id, key)
            updated[default.id] = LanguageDefinition(
                key=key,
                id=default.id,
                name=default.name,
                monaco_id=default.monaco_id,
                file_extension=default.file_extension,
                available=False,
            )
    SUPPORTED_LANGUAGES.clear()
    SUPPORTED_LANGUAGES.update(updated)
    _discovery_ts = time.monotonic()


def discovery_age_seconds() -> float | None:
    if _discovery_ts <= 0:
        return None
    return time.monotonic() - _discovery_ts
