"""Seed stems that a reviewed content batch has reworded under a stable content key.

Seed scripts skip a row only when its exact text already exists. After a batch rewords an
adopted row, the original text no longer exists, so the seed would insert a duplicate
question. Seeds must skip a stem listed here once its content key is present.
"""

from __future__ import annotations

REVISED_SEED_STEMS: dict[str, str] = {
    "No phone is a laptop. All laptops are gadgets. Which follows?": "sprint1-syl-03",
    "Inserting at the front of a plain dynamic array is typically?": "sprint1-arr-02",
    "Two arrays of equal length; element-wise sum loop is?": "sprint1-arr-04",
    "Kadane-style max subarray sum (classic contiguous) runs in?": "sprint1-arr-05",
    "Reversing an array in place swaps from ends toward center. Extra space?": "sprint1-arr-07",
    "Dutch National Flag (3-way partition) for an array of 0/1/2 values runs in?": "sprint1-arr-10",
}


def superseded_by_revision(text: str, existing_keys: set[str]) -> bool:
    return REVISED_SEED_STEMS.get(text) in existing_keys
