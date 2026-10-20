"""Recompute KPI baselines from packaged Sales.csv with documented rounding."""
from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "public" / "reports" / "executive-sales-toast-lab"
SALES_CSV = LAB / "data" / "Sales.csv"


def money_round(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def row_sum(qty_col: str, value_col: str, frame: pd.DataFrame) -> Decimal:
    total = Decimal("0")
    for qty, price in zip(frame[qty_col], frame[value_col], strict=True):
        total += Decimal(str(int(qty))) * Decimal(str(price))
    return total


def main() -> None:
    sales = pd.read_csv(SALES_CSV)
    total_sales = row_sum("Order qty", "unit price", sales)
    total_cost = row_sum("Order qty", "unit cost", sales)
    total_profit = total_sales - total_cost
    units = int(sales["Order qty"].sum())

    display_sales = money_round(total_sales)
    display_cost = money_round(total_cost)
    display_profit = display_sales - display_cost
    profit_rounded_direct = money_round(total_profit)

    if display_profit != profit_rounded_direct:
        raise SystemExit(
            f"Profit rounding mismatch: {display_profit} vs {profit_rounded_direct} "
            f"(full profit {total_profit})"
        )

    margin = float(total_profit / total_sales) if total_sales else 0.0

    payload = {
        "source": "frontend/public/reports/executive-sales-toast-lab/data/Sales.csv",
        "rowCount": len(sales),
        "formulas": {
            "Total Sales": "SUM over rows of (Order qty × unit price) using Decimal per row",
            "Total Cost": "SUM over rows of (Order qty × unit cost) using Decimal per row",
            "Total Profit": "Total Sales − Total Cost at full precision (not a separate rolled-up import)",
            "Total Orders_units": "SUM(Order qty)",
            "Profit Margin %": "Total Profit / Total Sales at full precision",
        },
        "roundingPolicy": {
            "perRow": "Decimal(str(qty)) * Decimal(str(price)) — avoids float drift in totals",
            "displayCurrency": "ROUND_HALF_UP to 2 decimal places for dollar KPI checks",
            "displayProfit": "money_round(Total Sales) − money_round(Total Cost) so cards reconcile",
            "note": "Do not compare rounded Sales minus a differently rounded Cost copied from prose; use this file.",
        },
        "fullPrecision": {
            "Total Sales": str(total_sales),
            "Total Cost": str(total_cost),
            "Total Profit": str(total_profit),
            "Total Orders_units": units,
            "Profit Margin %": margin,
        },
        "displayCurrency": {
            "Total Sales": float(display_sales),
            "Total Cost": float(display_cost),
            "Total Profit": float(display_profit),
            "Total Orders_units": units,
            "Profit Margin %": round(margin, 4),
        },
        "unfiltered": {
            "Total Sales": float(display_sales),
            "Total Cost": float(display_cost),
            "Total Profit": float(display_profit),
            "Total Orders_units": units,
            "Profit Margin %": round(margin, 4),
        },
        "reconciliation": {
            "displaySalesMinusDisplayCost": float(display_sales - display_cost),
            "matchesDisplayProfit": display_profit == (display_sales - display_cost),
        },
        "notes": "Verify in Power BI Desktop after model build; DAX SUMX may differ slightly in last digit vs Decimal CSV walk.",
    }

    out = LAB / "expected-results.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(
        f"Display: Sales {display_sales} Cost {display_cost} Profit {display_profit} "
        f"(reconciles: {display_profit == display_sales - display_cost})"
    )


if __name__ == "__main__":
    main()
