"""Seed stems that a reviewed content batch has reworded under a stable content key.

Seed scripts skip a row only when its exact text already exists. After a batch rewords an
adopted row, the original text no longer exists, so the seed would insert a duplicate
question. Seeds must skip a stem listed here once its content key is present.
"""

from __future__ import annotations

REVISED_SEED_STEMS: dict[str, str] = {
    "No phone is a laptop. All laptops are gadgets. Which follows?": "sprint1-syl-03",
}


def superseded_by_revision(text: str, existing_keys: set[str]) -> bool:
    return REVISED_SEED_STEMS.get(text) in existing_keys
