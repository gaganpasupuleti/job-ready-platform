"""Deterministic hashing and light similarity for interview questions."""

from __future__ import annotations

import hashlib
import re
import string

_PUNCT_TABLE = str.maketrans("", "", string.punctuation)
_WS = re.compile(r"\s+")
_TOKEN = re.compile(r"[a-z0-9]+")


def normalize_question_text(text: str) -> str:
    lowered = (text or "").lower().strip().replace("_", " ")
    lowered = lowered.translate(_PUNCT_TABLE)
    return _WS.sub(" ", lowered).strip()


def content_hash(question_text: str) -> str:
    normalized = normalize_question_text(question_text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def token_set(text: str) -> set[str]:
    return set(_TOKEN.findall(normalize_question_text(text)))


def jaccard_similarity(a: str, b: str) -> float:
    sa, sb = token_set(a), token_set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def slug_from_question(question_text: str, *, max_len: int = 80) -> str:
    base = normalize_question_text(question_text).replace(" ", "-")
    base = re.sub(r"-+", "-", base).strip("-")[:max_len].rstrip("-")
    return base or "interview-question"
