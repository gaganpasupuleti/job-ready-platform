"""Emit runnable Power Query M snippets for student CSV imports."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "public" / "reports" / "executive-sales-toast-lab"


def csv_query(table: str, file: str, type_lines: list[str]) -> str:
    types = ",\n            ".join(type_lines)
    return f"""let
    Source = Csv.Document(
        File.Contents(DataFolder & "\\{file}"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{
            {types}
        }})
in
    #"Changed Type" """


def main() -> None:
    queries = [
        {
            "table": "Sales",
            "file": "Sales.csv",
            "loadName": "Sales",
            "expression": csv_query(
                "Sales",
                "Sales.csv",
                [
                    '{"Sales Date", type date}',
                    '{"Order qty", Int64.Type}',
                    '{"unit price", type number}',
                    '{"unit cost", type number}',
                    '{"Productindex", Int64.Type}',
                    '{"Storeindex", Int64.Type}',
                    '{"Salesteamindex", Int64.Type}',
                    '{"Sales_Index", Int64.Type}',
                    '{"Order Number", type text}',
                    '{"Sales Channel", type text}',
                ],
            ),
        },
        {
            "table": "Date Table",
            "file": "Date_Table.csv",
            "loadName": "Date Table",
            "expression": csv_query(
                "Date Table",
                "Date_Table.csv",
                [
                    '{"Date", type date}',
                    '{"Year", Int64.Type}',
                    '{"QuarterOfYear", Int64.Type}',
                    '{"Quarter & Year", type text}',
                    '{"QuarternYear", Int64.Type}',
                    '{"MonthOfYear", Int64.Type}',
                    '{"Month & Year", type text}',
                    '{"MonthnYear", Int64.Type}',
                    '{"Month Short", type text}',
                    '{"DayOfMonth", Int64.Type}',
                    '{"ISO Weeknumber", Int64.Type}',
                    '{"Week & Year", type text}',
                    '{"WeeknYear", Int64.Type}',
                    '{"DayOfWeekNum", Int64.Type}',
                    '{"DayOfWeek", type text}',
                    '{"DayOfWeek Initial", type text}',
                    '{"Day Type", type text}',
                ],
            ),
        },
        {
            "table": "Products_Data",
            "file": "Products_Data.csv",
            "loadName": "Products_Data",
            "expression": csv_query(
                "Products_Data",
                "Products_Data.csv",
                ['{"Productindex", Int64.Type}', '{"Product Name", type text}'],
            ),
        },
        {
            "table": "storelocations",
            "file": "storelocations.csv",
            "loadName": "storelocations",
            "expression": csv_query(
                "storelocations",
                "storelocations.csv",
                ['{"Storeindex", Int64.Type}', '{"name", type text}'],
            ),
        },
        {
            "table": "Salesteams",
            "file": "Salesteams.csv",
            "loadName": "Salesteams",
            "expression": csv_query(
                "Salesteams",
                "Salesteams.csv",
                ['{"Salesteamindex", Int64.Type}', '{"Sales Team", type text}'],
            ),
        },
        {
            "table": "Higher Percentile",
            "file": "Higher_Percentile.csv",
            "loadName": "Higher Percentile",
            "expression": csv_query(
                "Higher Percentile",
                "Higher_Percentile.csv",
                ['{"Higher Percentile", type number}'],
            ),
        },
        {
            "table": "Lower Percentile",
            "file": "Lower_Percentile.csv",
            "loadName": "Lower Percentile",
            "expression": csv_query(
                "Lower Percentile",
                "Lower_Percentile.csv",
                ['{"Lower Percentile", type number}'],
            ),
        },
        {
            "table": "Date M-W-D",
            "file": "Date_M-W-D.csv",
            "loadName": "Date M-W-D",
            "expression": csv_query(
                "Date M-W-D",
                "Date_M-W-D.csv",
                ['{"Date M-W-D", type text}', '{"Date M-W-D Order", Int64.Type}'],
            ),
            "note": "Helper lookup only — recreate the real Fields parameter in Desktop (see workshop date-03).",
        },
    ]
    (LAB / "csv-import-queries.json").write_text(json.dumps(queries, indent=2), encoding="utf-8")
    md = [
        "# CSV import (student M)",
        "",
        "1. **Home → Transform data → Manage Parameters → New** → name `DataFolder` (Text) → your extracted `data` folder path.",
        "2. For each table below: **New Source → Blank Query**, paste M, rename query to **load name**, enable load.",
        "3. Author Excel M in `power-query.json` is reference-only.",
        "",
    ]
    for q in queries:
        md.append(f"## {q['table']} (`{q['file']}`)")
        if q.get("note"):
            md.append(f"_{q['note']}_")
        md.append("")
        md.append("```powerquery")
        md.append(q["expression"].strip())
        md.append("```")
        md.append("")
    (LAB / "csv-import.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote csv-import-queries.json ({len(queries)} queries)")


if __name__ == "__main__":
    main()
