"""Production-safe quiz/MCQ coverage report.

Usage:
  python -m app.content.quiz_coverage
  python -m app.content.quiz_coverage --json
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections import defaultdict
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.content.hashing import content_hash
from app.db.session import AsyncSessionLocal, engine
from app.models.question import Question, QuestionOption
from app.models.taxonomy import Category, Domain, Subtopic, Topic

# Priority tracks from Phase 1.1 — used for empty/thin classification emphasis.
PRIORITY_TOPIC_HINTS: dict[str, list[str]] = {
    "placement": [
        "percentages",
        "profit-and-loss",
        "time-and-work",
        "probability",
        "series",
        "syllogisms",
        "grammar",
        "vocabulary",
        "tables",
        "charts",
    ],
    "technical": [
        "sql-fundamentals",
        "joins",
        "aggregations",
        "fundamentals",
        "concepts",
        "core-concepts",
        "principles",
        "basics",
        "arrays",
    ],
    "ai": [
        "llm-fundamentals",
        "rag",
        "embeddings",
        "vector-databases",
        "tool-calling",
        "mcp-fundamentals",
        "ai-security",
        "prompt-patterns",
    ],
    "cloud": ["iam", "vpc", "ec2", "s3", "compute", "networking"],
    "devops": ["docker", "kubernetes", "cicd", "terraform", "linux", "git"],
    "cybersecurity": ["fundamentals", "iam", "soc", "incident-response", "api-security"],
}


def _band(n: int) -> str:
    if n <= 0:
        return "EMPTY"
    if n <= 4:
        return "VERY_THIN"
    if n <= 9:
        return "THIN"
    return "GOOD"


async def quiz_coverage_report(session: AsyncSession) -> dict[str, Any]:
    option_stats = (
        await session.execute(
            select(
                QuestionOption.question_id,
                func.count(QuestionOption.id).label("option_count"),
                func.sum(case((QuestionOption.is_correct.is_(True), 1), else_=0)).label(
                    "correct_count"
                ),
            ).group_by(QuestionOption.question_id)
        )
    ).all()
    options_by_q = {
        row.question_id: {
            "option_count": int(row.option_count or 0),
            "correct_count": int(row.correct_count or 0),
        }
        for row in option_stats
    }

    Sub = aliased(Subtopic)
    rows = (
        await session.execute(
            select(
                Domain.id,
                Domain.name,
                Domain.slug,
                Category.id,
                Category.name,
                Category.slug,
                Topic.id,
                Topic.name,
                Topic.slug,
                Sub.name,
                Sub.slug,
                Question.id,
                Question.is_active,
                Question.explanation,
                Question.difficulty,
                Question.question_text,
            )
            .select_from(Domain)
            .join(Category, Category.domain_id == Domain.id)
            .join(Topic, Topic.category_id == Category.id)
            .outerjoin(Question, Question.topic_id == Topic.id)
            .outerjoin(Sub, Sub.id == Question.subtopic_id)
            .order_by(Domain.name, Category.name, Topic.name)
        )
    ).all()

    topic_buckets: dict[tuple, dict[str, Any]] = {}
    domain_totals: dict[str, int] = defaultdict(int)
    difficulty_totals: dict[str, int] = defaultdict(int)
    hash_to_ids: dict[str, list[str]] = defaultdict(list)
    total_active = 0
    with_explanations = 0
    with_valid_options = 0
    quality_complete = 0

    for (
        _did,
        dname,
        dslug,
        _cid,
        cname,
        cslug,
        tid,
        tname,
        tslug,
        sub_name,
        sub_slug,
        qid,
        is_active,
        explanation,
        difficulty,
        qtext,
    ) in rows:
        key = (dslug, cslug, tslug, tid)
        bucket = topic_buckets.get(key)
        if bucket is None:
            bucket = {
                "domain": dname,
                "domain_slug": dslug,
                "category": cname,
                "category_slug": cslug,
                "topic": tname,
                "topic_slug": tslug,
                "active_questions": 0,
                "approved_questions": 0,
                "with_options": 0,
                "with_explanations": 0,
                "difficulty": {"easy": 0, "medium": 0, "hard": 0},
                "subtopics": {},
                "band": "EMPTY",
            }
            topic_buckets[key] = bucket

        if qid is None:
            continue

        if not is_active:
            continue

        total_active += 1
        domain_totals[dname] += 1
        bucket["active_questions"] += 1

        diff_key = getattr(difficulty, "value", str(difficulty)).lower()
        if diff_key not in bucket["difficulty"]:
            bucket["difficulty"][diff_key] = 0
        bucket["difficulty"][diff_key] += 1
        difficulty_totals[diff_key] += 1

        has_expl = bool(explanation and str(explanation).strip())
        if has_expl:
            with_explanations += 1
            bucket["with_explanations"] += 1

        opt = options_by_q.get(qid, {"option_count": 0, "correct_count": 0})
        valid_opts = opt["option_count"] >= 4 and opt["correct_count"] == 1
        if opt["option_count"] >= 2:
            bucket["with_options"] += 1
        if valid_opts:
            with_valid_options += 1

        # MCQs have no separate approval flag; "approved" = active + explanation + valid options.
        if has_expl and valid_opts:
            quality_complete += 1
            bucket["approved_questions"] += 1

        if sub_slug:
            sub_key = sub_slug
            sub_entry = bucket["subtopics"].setdefault(
                sub_key, {"name": sub_name or sub_slug, "active_questions": 0}
            )
            sub_entry["active_questions"] += 1

        if qtext:
            h = content_hash(qtext)
            hash_to_ids[h].append(str(qid))

    topics_out: list[dict[str, Any]] = []
    empty: list[dict[str, Any]] = []
    very_thin: list[dict[str, Any]] = []
    thin: list[dict[str, Any]] = []
    for bucket in topic_buckets.values():
        n = bucket["active_questions"]
        band = _band(n)
        bucket["band"] = band
        topics_out.append(bucket)
        slim = {
            "domain": bucket["domain"],
            "category": bucket["category"],
            "topic": bucket["topic"],
            "topic_slug": bucket["topic_slug"],
            "active_questions": n,
        }
        if band == "EMPTY":
            empty.append(slim)
        elif band == "VERY_THIN":
            very_thin.append(slim)
        elif band == "THIN":
            thin.append(slim)

    duplicates = [
        {"content_hash": h, "question_ids": ids, "count": len(ids)}
        for h, ids in hash_to_ids.items()
        if len(ids) > 1
    ]

    priority_gaps: list[dict[str, Any]] = []
    for domain_slug, topic_slugs in PRIORITY_TOPIC_HINTS.items():
        for tslug in topic_slugs:
            matches = [
                b
                for b in topics_out
                if b["domain_slug"] == domain_slug and b["topic_slug"] == tslug
            ]
            if not matches:
                priority_gaps.append(
                    {
                        "domain_slug": domain_slug,
                        "topic_slug": tslug,
                        "active_questions": 0,
                        "band": "EMPTY",
                        "note": "topic missing or unmapped",
                    }
                )
                continue
            for m in matches:
                if m["active_questions"] < 10:
                    priority_gaps.append(
                        {
                            "domain": m["domain"],
                            "category": m["category"],
                            "topic": m["topic"],
                            "topic_slug": m["topic_slug"],
                            "active_questions": m["active_questions"],
                            "band": m["band"],
                        }
                    )

    pct_expl = round(100.0 * with_explanations / total_active, 1) if total_active else 0.0
    pct_opts = round(100.0 * with_valid_options / total_active, 1) if total_active else 0.0

    return {
        "summary": {
            "total_active_mcqs": total_active,
            "quality_complete_approved": quality_complete,
            "with_explanations": with_explanations,
            "with_explanations_pct": pct_expl,
            "with_valid_options": with_valid_options,
            "with_valid_options_pct": pct_opts,
            "by_domain": dict(sorted(domain_totals.items())),
            "by_difficulty": dict(sorted(difficulty_totals.items())),
            "exact_duplicate_groups": len(duplicates),
            "topics_empty": len(empty),
            "topics_very_thin": len(very_thin),
            "topics_thin": len(thin),
            "topics_good": sum(1 for t in topics_out if t["band"] == "GOOD"),
        },
        "topics": topics_out,
        "empty_topics": empty,
        "very_thin_topics": very_thin,
        "thin_topics": thin,
        "priority_gaps": priority_gaps,
        "exact_duplicates": duplicates,
    }


def _print_human(report: dict[str, Any]) -> None:
    s = report["summary"]
    print("=== QUIZ COVERAGE ===")
    print(f"Total active MCQs: {s['total_active_mcqs']}")
    print(f"Quality-complete (expl+4opts+1correct): {s['quality_complete_approved']}")
    print(f"With explanations: {s['with_explanations']} ({s['with_explanations_pct']}%)")
    print(f"With valid options: {s['with_valid_options']} ({s['with_valid_options_pct']}%)")
    print("By domain:")
    for name, n in s["by_domain"].items():
        print(f"  {name}: {n}")
    print("By difficulty:")
    for name, n in s["by_difficulty"].items():
        print(f"  {name}: {n}")
    print(
        f"Topics EMPTY={s['topics_empty']} VERY_THIN={s['topics_very_thin']} "
        f"THIN={s['topics_thin']} GOOD={s['topics_good']}"
    )
    print(f"Exact duplicate groups: {s['exact_duplicate_groups']}")
    print("\n--- By domain / category / topic ---")
    current_domain = None
    for t in sorted(
        report["topics"],
        key=lambda x: (x["domain"], x["category"], x["topic"]),
    ):
        if t["domain"] != current_domain:
            current_domain = t["domain"]
            print(f"\n{current_domain}")
        print(
            f"  {t['category']} / {t['topic']}: {t['active_questions']} "
            f"[{t['band']}] opts={t['with_options']} expl={t['with_explanations']} "
            f"approved={t['approved_questions']}"
        )
        for sub in t.get("subtopics", {}).values():
            print(f"    subtopic {sub['name']}: {sub['active_questions']}")
    if report["priority_gaps"]:
        print("\n--- Priority gaps (<10) ---")
        for g in report["priority_gaps"]:
            print(
                f"  {g.get('domain', g.get('domain_slug'))} / "
                f"{g.get('topic', g.get('topic_slug'))}: "
                f"{g['active_questions']} [{g['band']}]"
            )


async def _run(as_json: bool) -> None:
    async with AsyncSessionLocal() as session:
        report = await quiz_coverage_report(session)
    await engine.dispose()
    if as_json:
        print(json.dumps(report, indent=2, default=str))
    else:
        _print_human(report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Quiz/MCQ coverage report")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()
    asyncio.run(_run(args.json))


if __name__ == "__main__":
    main()
