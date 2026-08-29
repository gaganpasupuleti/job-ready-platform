"""Centralized Judge0 language configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageDefinition:
    id: int
    name: str
    monaco_id: str
    file_extension: str


SUPPORTED_LANGUAGES: dict[int, LanguageDefinition] = {
    71: LanguageDefinition(71, "Python 3", "python", "py"),
    62: LanguageDefinition(62, "Java", "java", "java"),
    54: LanguageDefinition(54, "C++ (GCC)", "cpp", "cpp"),
    63: LanguageDefinition(63, "JavaScript (Node.js)", "javascript", "js"),
}

DEFAULT_LANGUAGE_ID = 71


def get_language(language_id: int) -> LanguageDefinition | None:
    return SUPPORTED_LANGUAGES.get(language_id)


def get_language_name(language_id: int) -> str | None:
    lang = get_language(language_id)
    return lang.name if lang else None


def list_languages() -> list[LanguageDefinition]:
    return list(SUPPORTED_LANGUAGES.values())


def validate_language_id(language_id: int) -> LanguageDefinition:
    lang = get_language(language_id)
    if lang is None:
        raise ValueError(f"Unsupported language id: {language_id}")
    return lang
