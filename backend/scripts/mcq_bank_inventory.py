"""Source-bank inventory (not production DB). Run: python -m scripts.mcq_bank_inventory"""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from pathlib import Path

from app.seed.phase11_aptitude_mcq import APTITUDE_MCQS
from app.seed.phase11_technical_mcq import TECHNICAL_MCQS
from app.seed.problems_bank import PROBLEM_BANK


def _mcq_inventory(rows: list[tuple], label: str) -> dict:
    by_topic = Counter((r[2], r[3]) for r in rows)
    by_diff = Counter(r[3] for r in rows)
    return {
        "source": label,
        "total": len(rows),
        "by_topic_difficulty": {f"{t}/{d}": c for (t, d), c in sorted(by_topic.items())},
        "by_difficulty": dict(by_diff),
    }


def _coding_inventory() -> dict:
    by_topic = Counter(p["topic"] for p in PROBLEM_BANK)
    by_diff = Counter(p["difficulty"].value for p in PROBLEM_BANK)
    return {
        "source": "problems_bank.PROBLEM_BANK",
        "total": len(PROBLEM_BANK),
        "by_topic": dict(by_topic),
        "by_difficulty": dict(by_diff),
    }


async def _live_counts() -> dict | None:
    try:
        from sqlalchemy import func, select

        from app.db.session import AsyncSessionLocal
        from app.models.question import Question
        from app.models.taxonomy import Category, Domain, Topic

        async with AsyncSessionLocal() as db:
            stmt = (
                select(
                    Domain.slug,
                    Category.slug,
                    Topic.slug,
                    Question.difficulty,
                    Question.is_active,
                    Question.is_sample,
                    func.count(),
                )
                .join(Category, Category.id == Question.category_id)
                .join(Domain, Domain.id == Question.domain_id)
                .join(Topic, Topic.id == Question.topic_id)
                .group_by(
                    Domain.slug,
                    Category.slug,
                    Topic.slug,
                    Question.difficulty,
                    Question.is_active,
                    Question.is_sample,
                )
            )
            rows = (await db.execute(stmt)).all()
            return {
                "source": "database",
                "rows": [
                    {
                        "domain": r[0],
                        "category": r[1],
                        "topic": r[2],
                        "difficulty": str(r[3]),
                        "is_active": r[4],
                        "is_sample": r[5],
                        "count": r[6],
                    }
                    for r in rows
                ],
            }
    except Exception as exc:
        return {"source": "database", "error": str(exc), "note": "Set DATABASE_URL for live inventory"}


def main() -> None:
    report = {
        "aptitude_mcq_source": _mcq_inventory(APTITUDE_MCQS, "phase11_aptitude_mcq"),
        "technical_mcq_source": _mcq_inventory(TECHNICAL_MCQS, "phase11_technical_mcq"),
        "coding_source": _coding_inventory(),
        "live": asyncio.run(_live_counts()),
        "notes": [
            "Aptitude/technical MCQs share the practice Question engine.",
            "DSA theory items live in technical MCQ seeds; DSA coding uses CodingProblem.",
            "Learning Studio quizzes use separate studio Question links — not this Excel bank.",
        ],
    }
    out = Path(__file__).resolve().parents[1] / "content" / "mcq-bank" / "inventory_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
