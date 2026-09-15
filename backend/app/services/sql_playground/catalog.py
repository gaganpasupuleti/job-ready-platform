"""Documented playground datasets. These are not assessed SQL problems."""

from __future__ import annotations

from typing import Any

DATASETS: dict[str, dict[str, Any]] = {
    "campus-bookstore": {
        "title": "Campus bookstore",
        "summary": "Books on the shelf and open loans. Use this to practice filters, sorting, and joins.",
        "documentation": (
            "A campus store keeps books and loans in two tables. price_rupees is the shelf price, not a discount. "
            "A loan with returned = false is still out. member_name is the borrower, not a student id. "
            "There is no grades table in this dataset."
        ),
        "starter_query": "SELECT title, genre, price_rupees\nFROM books\nWHERE in_stock = true\nORDER BY title;",
        "tables": [
            {
                "table_name": "books",
                "description": "One row per title currently catalogued.",
                "columns": [
                    {"column_name": "id", "data_type": "integer", "is_nullable": False},
                    {"column_name": "title", "data_type": "text", "is_nullable": False},
                    {"column_name": "genre", "data_type": "text", "is_nullable": False},
                    {"column_name": "price_rupees", "data_type": "integer", "is_nullable": False},
                    {"column_name": "in_stock", "data_type": "boolean", "is_nullable": False},
                ],
                "rows": [
                    {"id": 1, "title": "Quiet Algorithms", "genre": "computing", "price_rupees": 450, "in_stock": True},
                    {"id": 2, "title": "City Maps", "genre": "reference", "price_rupees": 280, "in_stock": True},
                    {"id": 3, "title": "River Poems", "genre": "poetry", "price_rupees": 190, "in_stock": False},
                    {"id": 4, "title": "Ledger Basics", "genre": "computing", "price_rupees": 520, "in_stock": True},
                ],
            },
            {
                "table_name": "loans",
                "description": "A copy checked out by a member. returned is false while it is still out.",
                "columns": [
                    {"column_name": "id", "data_type": "integer", "is_nullable": False},
                    {"column_name": "book_id", "data_type": "integer", "is_nullable": False},
                    {"column_name": "member_name", "data_type": "text", "is_nullable": False},
                    {"column_name": "due_on", "data_type": "date", "is_nullable": False},
                    {"column_name": "returned", "data_type": "boolean", "is_nullable": False},
                ],
                "rows": [
                    {"id": 11, "book_id": 1, "member_name": "Asha", "due_on": "2026-09-20", "returned": False},
                    {"id": 12, "book_id": 3, "member_name": "Ravi", "due_on": "2026-09-12", "returned": True},
                    {"id": 13, "book_id": 2, "member_name": "Asha", "due_on": "2026-09-28", "returned": False},
                ],
            },
        ],
    },
    "clinic-visits": {
        "title": "Clinic visits",
        "summary": "Visits and payments. Some visits have no payment row, which is useful for NULL practice.",
        "documentation": (
            "A small clinic records visits and payments separately. fee_rupees is the amount quoted. "
            "A visit with no matching payments.visit_id has not been paid. method is cash or upi. "
            "Do not invent a zero payment when the payment row is missing."
        ),
        "starter_query": "SELECT patient_name, reason, fee_rupees\nFROM visits\nORDER BY visit_date;",
        "tables": [
            {
                "table_name": "visits",
                "description": "One row per appointment that happened.",
                "columns": [
                    {"column_name": "id", "data_type": "integer", "is_nullable": False},
                    {"column_name": "patient_name", "data_type": "text", "is_nullable": False},
                    {"column_name": "visit_date", "data_type": "date", "is_nullable": False},
                    {"column_name": "reason", "data_type": "text", "is_nullable": False},
                    {"column_name": "fee_rupees", "data_type": "integer", "is_nullable": False},
                ],
                "rows": [
                    {"id": 1, "patient_name": "Meera", "visit_date": "2026-09-01", "reason": "checkup", "fee_rupees": 500},
                    {"id": 2, "patient_name": "Omar", "visit_date": "2026-09-02", "reason": "follow-up", "fee_rupees": 300},
                    {"id": 3, "patient_name": "Meera", "visit_date": "2026-09-08", "reason": "lab review", "fee_rupees": 700},
                    {"id": 4, "patient_name": "Lila", "visit_date": "2026-09-09", "reason": "checkup", "fee_rupees": 500},
                ],
            },
            {
                "table_name": "payments",
                "description": "Money received for a visit. A missing row is not the same as amount 0.",
                "columns": [
                    {"column_name": "id", "data_type": "integer", "is_nullable": False},
                    {"column_name": "visit_id", "data_type": "integer", "is_nullable": False},
                    {"column_name": "amount_rupees", "data_type": "integer", "is_nullable": False},
                    {"column_name": "method", "data_type": "text", "is_nullable": False},
                ],
                "rows": [
                    {"id": 21, "visit_id": 1, "amount_rupees": 500, "method": "upi"},
                    {"id": 22, "visit_id": 3, "amount_rupees": 200, "method": "cash"},
                ],
            },
        ],
    },
    "course-enrollments": {
        "title": "Course enrollments",
        "summary": "Students and course rows. A null grade means the result is not posted yet.",
        "documentation": (
            "year is 1, 2, 3, or 4. grade is a letter when posted, otherwise NULL. "
            "course_code is text such as CS101. A student can have more than one enrollment. "
            "This dataset is not an assessed assignment."
        ),
        "starter_query": "SELECT name, year, major\nFROM students\nORDER BY name;",
        "tables": [
            {
                "table_name": "students",
                "description": "One row per student.",
                "columns": [
                    {"column_name": "id", "data_type": "integer", "is_nullable": False},
                    {"column_name": "name", "data_type": "text", "is_nullable": False},
                    {"column_name": "year", "data_type": "integer", "is_nullable": False},
                    {"column_name": "major", "data_type": "text", "is_nullable": False},
                ],
                "rows": [
                    {"id": 1, "name": "Anil", "year": 1, "major": "computing"},
                    {"id": 2, "name": "Bea", "year": 2, "major": "commerce"},
                    {"id": 3, "name": "Chitra", "year": 1, "major": "computing"},
                    {"id": 4, "name": "Dev", "year": 3, "major": "commerce"},
                ],
            },
            {
                "table_name": "enrollments",
                "description": "A student in a course. grade is null until it is posted.",
                "columns": [
                    {"column_name": "id", "data_type": "integer", "is_nullable": False},
                    {"column_name": "student_id", "data_type": "integer", "is_nullable": False},
                    {"column_name": "course_code", "data_type": "text", "is_nullable": False},
                    {"column_name": "grade", "data_type": "text", "is_nullable": True},
                ],
                "rows": [
                    {"id": 31, "student_id": 1, "course_code": "CS101", "grade": "A"},
                    {"id": 32, "student_id": 1, "course_code": "MA101", "grade": None},
                    {"id": 33, "student_id": 2, "course_code": "EC110", "grade": "B"},
                    {"id": 34, "student_id": 3, "course_code": "CS101", "grade": "B"},
                    {"id": 35, "student_id": 4, "course_code": "EC110", "grade": None},
                ],
            },
        ],
    },
}

SAMPLE_ROW_LIMIT = 5


def list_datasets() -> list[dict[str, Any]]:
    items = []
    for key, row in DATASETS.items():
        items.append(
            {
                "id": key,
                "title": row["title"],
                "summary": row["summary"],
                "tables": [table["table_name"] for table in row["tables"]],
            }
        )
    return items


def get_dataset(dataset_id: str) -> dict[str, Any] | None:
    row = DATASETS.get(dataset_id)
    if row is None:
        return None
    tables = []
    for table in row["tables"]:
        columns = [column["column_name"] for column in table["columns"]]
        sample = table["rows"][:SAMPLE_ROW_LIMIT]
        tables.append(
            {
                "table_name": table["table_name"],
                "description": table["description"],
                "columns": table["columns"],
                "sample_columns": columns,
                "sample_rows": [[item.get(column) for column in columns] for item in sample],
                "sample_row_count": len(table["rows"]),
                "sample_truncated": len(table["rows"]) > SAMPLE_ROW_LIMIT,
            }
        )
    return {
        "id": dataset_id,
        "title": row["title"],
        "summary": row["summary"],
        "documentation": row["documentation"],
        "starter_query": row["starter_query"],
        "assessed": False,
        "tables": tables,
    }


def dataset_payload(dataset_id: str) -> list[dict[str, Any]] | None:
    row = DATASETS.get(dataset_id)
    if row is None:
        return None
    return [
        {
            "table_name": table["table_name"],
            "columns": table["columns"],
            "rows": table["rows"],
        }
        for table in row["tables"]
    ]
