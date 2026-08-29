"""Result comparison for SQL practice submissions."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def _looks_numeric(text: str) -> bool:
    if not text:
        return False
    try:
        Decimal(text)
        return True
    except (InvalidOperation, ValueError):
        return False


def _normalize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value)).normalize()
        except (InvalidOperation, ValueError):
            return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    text = str(value)
    try:
        if _looks_numeric(text):
            return Decimal(text).normalize()
    except (InvalidOperation, ValueError):
        pass
    return text


def _normalize_row(row: list[Any] | tuple[Any, ...]) -> tuple[Any, ...]:
    return tuple(_normalize_value(v) for v in row)


def compare_results(
    *,
    expected_columns: list[str],
    expected_rows: list[list[Any]],
    actual_columns: list[str],
    actual_rows: list[list[Any]],
    order_sensitive: bool,
) -> dict[str, Any]:
    """Compare query results. Never returns hidden expected rows."""
    exp_cols = [c.lower() for c in expected_columns]
    act_cols = [c.lower() for c in actual_columns]

    if exp_cols != act_cols:
        return {
            "matched": False,
            "reason": "column_mismatch",
            "expected_columns": expected_columns,
            "your_columns": actual_columns,
            "message": (
                "Your query ran successfully, but the result did not match the expected answer. "
                f"Expected columns: {', '.join(expected_columns)}. "
                f"Your columns: {', '.join(actual_columns) or '(none)'}."
            ),
        }

    exp_norm = [_normalize_row(r) for r in expected_rows]
    act_norm = [_normalize_row(r) for r in actual_rows]

    if len(exp_norm) != len(act_norm):
        return {
            "matched": False,
            "reason": "row_count_mismatch",
            "expected_row_count": len(exp_norm),
            "your_row_count": len(act_norm),
            "message": (
                "Your query ran successfully, but the result did not match the expected answer. "
                f"Expected {len(exp_norm)} row(s), got {len(act_norm)}."
            ),
        }

    if not order_sensitive:
        # None-safe sort key for mixed NULL / numeric / string rows
        def _sort_key(row: tuple[Any, ...]) -> tuple:
            return tuple((v is None, str(type(v)), str(v)) for v in row)

        exp_norm = sorted(exp_norm, key=_sort_key)
        act_norm = sorted(act_norm, key=_sort_key)

    if exp_norm != act_norm:
        return {
            "matched": False,
            "reason": "value_mismatch",
            "expected_row_count": len(exp_norm),
            "your_row_count": len(act_norm),
            "message": (
                "Your query ran successfully, but the result did not match the expected answer. "
                "Check filters, joins, aggregations, and ordering."
            ),
        }

    return {"matched": True, "message": "Accepted"}
