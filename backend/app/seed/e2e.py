"""Deterministic E2E fixtures for Build 7.2. Safe for local/test DB only.

Usage:
  python -m app.seed.e2e

Environment:
  E2E_ALLOW_SEED=1  required unless APP_ENV/ENVIRONMENT is development/test/local
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.coding import CodingProblem
from app.models.enums import UserRole
from app.models.learn import Course, PracticePath, Project
from app.models.prompt import PromptChallenge
from app.models.scenario import ScenarioChallenge
from app.models.sql_practice import SqlProblem
from app.models.taxonomy import Topic
from app.models.user import User


E2E_STUDENT_EMAIL = "e2e.student@jobready.dev"
E2E_STUDENT_PASSWORD = "E2eStudent123!"
E2E_STUDENT_USERNAME = "e2e_student"
E2E_ADMIN_EMAIL = "admin@jobready.dev"
E2E_ADMIN_PASSWORD = "Admin123!"

FIXTURES = {
    "sql_slug": "active-catalog-items",
    "sql_accepted_query": (
        "SELECT product_name, price\n"
        "FROM products\n"
        "WHERE is_active = TRUE\n"
        "ORDER BY price DESC"
    ),
    "sql_wrong_query": "SELECT product_name FROM products LIMIT 1",
    # Must pass safety (looks like SELECT) but fail at the database — not a safety rejection.
    "sql_invalid_query": "SELECT product_name FROM products WHERE",
    "sql_blocked_query": "DELETE FROM products",
    "path_slug": "beginner-arrays",
    "project_slug": "python-calculator",
    "sql_project_slug": "sql-ecommerce-analytics",
    "course_slug": "python-foundations",
}


def _env_allows_seed() -> bool:
    if os.getenv("E2E_ALLOW_SEED", "").strip() in {"1", "true", "yes"}:
        return True
    env = (os.getenv("APP_ENV") or os.getenv("ENVIRONMENT") or "development").lower()
    return env in {"development", "dev", "test", "local", "ci"}


async def _ensure_user(
    *,
    email: str,
    username: str,
    password: str,
    role: UserRole,
    full_name: str,
) -> None:
    async with AsyncSessionLocal() as session:
        existing = (
            await session.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                User(
                    email=email,
                    username=username,
                    full_name=full_name,
                    password_hash=hash_password(password),
                    role=role,
                    is_active=True,
                )
            )
            await session.commit()
            return
        existing.password_hash = hash_password(password)
        existing.role = role
        existing.is_active = True
        await session.commit()


async def build_manifest() -> dict[str, Any]:
    async with AsyncSessionLocal() as session:
        sql = (
            await session.execute(select(SqlProblem).where(SqlProblem.slug == FIXTURES["sql_slug"]))
        ).scalar_one_or_none()
        coding = (await session.execute(select(CodingProblem).where(CodingProblem.is_active.is_(True)).limit(1))).scalar_one_or_none()
        path = (
            await session.execute(select(PracticePath).where(PracticePath.slug == FIXTURES["path_slug"]))
        ).scalar_one_or_none()
        project = (
            await session.execute(select(Project).where(Project.slug == FIXTURES["project_slug"]))
        ).scalar_one_or_none()
        sql_project = (
            await session.execute(select(Project).where(Project.slug == FIXTURES["sql_project_slug"]))
        ).scalar_one_or_none()
        course = (
            await session.execute(select(Course).where(Course.slug == FIXTURES["course_slug"]))
        ).scalar_one_or_none()
        prompt = (
            await session.execute(select(PromptChallenge).where(PromptChallenge.is_active.is_(True)).limit(1))
        ).scalar_one_or_none()
        scenario = (
            await session.execute(select(ScenarioChallenge).where(ScenarioChallenge.is_active.is_(True)).limit(1))
        ).scalar_one_or_none()
        topic = (
            await session.execute(select(Topic).where(Topic.slug == "percentages").limit(1))
        ).scalar_one_or_none()

    return {
        "users": {
            "student": {
                "email": E2E_STUDENT_EMAIL,
                "password": E2E_STUDENT_PASSWORD,
                "username": E2E_STUDENT_USERNAME,
            },
            "admin": {"email": E2E_ADMIN_EMAIL, "password": E2E_ADMIN_PASSWORD},
        },
        "sql": {
            "slug": FIXTURES["sql_slug"],
            "id": str(sql.id) if sql else None,
            "accepted_query": FIXTURES["sql_accepted_query"],
            "wrong_query": FIXTURES["sql_wrong_query"],
            "invalid_query": FIXTURES["sql_invalid_query"],
            "blocked_query": FIXTURES["sql_blocked_query"],
        },
        "coding": {
            "id": str(coding.id) if coding else None,
            "slug": coding.slug if coding else None,
            "title": coding.title if coding else None,
        },
        "path": {"slug": FIXTURES["path_slug"], "id": str(path.id) if path else None},
        "project": {"slug": FIXTURES["project_slug"], "id": str(project.id) if project else None},
        "sql_project": {
            "slug": FIXTURES["sql_project_slug"],
            "id": str(sql_project.id) if sql_project else None,
        },
        "course": {"slug": FIXTURES["course_slug"], "id": str(course.id) if course else None},
        "prompt": {
            "slug": prompt.slug if prompt else None,
            "id": str(prompt.id) if prompt else None,
            "title": prompt.title if prompt else None,
        },
        "scenario": {
            "slug": scenario.slug if scenario else None,
            "id": str(scenario.id) if scenario else None,
            "title": scenario.title if scenario else None,
            "domain_key": (
                scenario.domain_key.value
                if scenario and hasattr(scenario.domain_key, "value")
                else (str(scenario.domain_key) if scenario else None)
            ),
        },
        "mcq_topic": {
            "slug": "percentages",
            "id": str(topic.id) if topic else None,
            "name": topic.name if topic else "Percentages",
        },
    }


def run_e2e_seed(*, write_manifest_path: str | None = None) -> dict[str, Any]:
    if not _env_allows_seed():
        raise SystemExit(
            "Refusing E2E seed outside development/test. Set E2E_ALLOW_SEED=1 to override."
        )
    print("Running base seed (idempotent)...")
    import asyncio

    from app.db.session import engine

    async def _seed_stack() -> dict[str, Any]:
        from app.seed.runner import (
            ensure_content_factory_catalog,
            seed_all,
            seed_build6_content_entry,
            seed_build7_content_entry,
            seed_coding_problems,
            seed_learn_content as seed_learn_via_runner,
            seed_sql_problems,
        )

        await seed_all()
        await ensure_content_factory_catalog()
        await seed_coding_problems()
        await seed_sql_problems()
        await seed_learn_via_runner()
        try:
            await seed_build6_content_entry()
        except Exception as exc:  # noqa: BLE001
            print(f"Build 6 seed skipped/failed: {exc}")
        try:
            await seed_build7_content_entry()
        except Exception as exc:  # noqa: BLE001
            print(f"Build 7 seed skipped/failed: {exc}")
        try:
            from app.seed.build8_seed import seed_build8_content

            await seed_build8_content()
        except Exception as exc:  # noqa: BLE001
            print(f"Build 8 seed skipped/failed: {exc}")
        # Users must exist before Build 9 sample saved-job / application fixtures.
        await _ensure_user(
            email=E2E_ADMIN_EMAIL,
            username="admin",
            password=E2E_ADMIN_PASSWORD,
            role=UserRole.ADMIN,
            full_name="Platform Admin",
        )
        await _ensure_user(
            email=E2E_STUDENT_EMAIL,
            username=E2E_STUDENT_USERNAME,
            password=E2E_STUDENT_PASSWORD,
            role=UserRole.STUDENT,
            full_name="E2E Student",
        )
        try:
            from app.seed.build9_seed import seed_build9_jobs

            await seed_build9_jobs()
        except Exception as exc:  # noqa: BLE001
            print(f"Build 9 seed skipped/failed: {exc}")
        try:
            from app.seed.build10_seed import seed_build10

            await seed_build10()
        except Exception as exc:  # noqa: BLE001
            print(f"Build 10 seed skipped/failed: {exc}")
        manifest = await build_manifest()
        await engine.dispose()
        return manifest

    manifest = asyncio.run(_seed_stack())
    path = write_manifest_path or os.getenv("E2E_MANIFEST_PATH")
    if path:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
        print(f"Wrote E2E manifest to {path}")
    print(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    out = None
    if len(sys.argv) > 1:
        out = sys.argv[1]
    run_e2e_seed(write_manifest_path=out)
