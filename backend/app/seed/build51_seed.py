# ruff: noqa: E501
"""Idempotent Build 5.1 seed: guided projects and richer practice path items."""

from __future__ import annotations

from sqlalchemy import select

from app.models.coding import CodingProblem
from app.models.learn import PracticePath, PracticePathItem, PracticePathSection, Project, ProjectModule, ProjectTask
from app.models.learn_enums import (
    PathAvailability,
    PracticePathDifficulty,
    PracticePathItemType,
    PracticePathType,
    ProjectTaskType,
)
from app.models.sql_practice import SqlProblem
from app.models.taxonomy import Topic
from app.seed.build51_catalog import (
    COMPANY_DISCLAIMER,
    NEW_ALGO_PATHS,
    NEW_DS_PATHS,
    PROJECT_SPECS,
)


async def seed_build51_content(session) -> None:
    coding_by_slug = {
        slug: pid
        for slug, pid in (await session.execute(select(CodingProblem.slug, CodingProblem.id))).all()
    }
    sql_by_slug = {
        slug: pid
        for slug, pid in (await session.execute(select(SqlProblem.slug, SqlProblem.id))).all()
    }
    topic_by_slug = {
        slug: tid for slug, tid in (await session.execute(select(Topic.slug, Topic.id))).all()
    }

    await _seed_projects(session, coding_by_slug, sql_by_slug, topic_by_slug)
    await _expand_paths(session, coding_by_slug, sql_by_slug, topic_by_slug)
    await session.flush()


async def _seed_projects(session, coding_by_slug, sql_by_slug, topic_by_slug) -> None:
    for index, spec in enumerate(PROJECT_SPECS):
        existing = (
            await session.execute(select(Project).where(Project.slug == spec["slug"]))
        ).scalar_one_or_none()
        if existing is not None:
            existing.prerequisites = spec["prerequisites"]
            existing.skills = spec["skills"]
            existing.final_objective = spec["final_objective"]
            existing.estimated_minutes = spec["estimated_minutes"]
            existing.availability = spec["availability"]
            existing.is_published = True
            existing.is_featured = spec["featured"]
            existing.short_description = spec["short_description"]
            existing.description = spec["description"]
            project = existing
        else:
            project = Project(
                slug=spec["slug"],
                title=spec["title"],
                short_description=spec["short_description"],
                description=spec["description"],
                difficulty=spec["difficulty"],
                technology=spec["technology"],
                category_key=spec["category_key"],
                estimated_minutes=spec["estimated_minutes"],
                is_published=True,
                is_featured=spec["featured"],
                sort_order=100 + index,
                availability=spec["availability"],
                prerequisites=spec["prerequisites"],
                skills=spec["skills"],
                final_objective=spec["final_objective"],
                reference_json=(
                    {"note": "No live LLM or cloud APIs in this build. Design and checklists only."}
                    if spec.get("genai_skeleton")
                    else {"note": "Complete tasks in order. Linked coding/SQL/MCQ reuse existing engines."}
                ),
            )
            session.add(project)
            await session.flush()

        task_count = await session.scalar(
            select(ProjectTask.id)
            .join(ProjectModule, ProjectModule.id == ProjectTask.module_id)
            .where(ProjectModule.project_id == project.id)
            .limit(1)
        )
        if task_count is not None:
            await _ensure_engine_links(session, project.id, spec, coding_by_slug, sql_by_slug, topic_by_slug)
            continue

        understand = ProjectModule(project_id=project.id, title="Understand the problem", sort_order=0)
        build = ProjectModule(project_id=project.id, title="Build", sort_order=1)
        ship = ProjectModule(project_id=project.id, title="Review and ship", sort_order=2)
        session.add_all([understand, build, ship])
        await session.flush()

        session.add(
            ProjectTask(
                module_id=understand.id,
                title="Read the objective",
                sort_order=0,
                task_type=ProjectTaskType.CONCEPT,
                summary=spec["final_objective"],
                body_json={"blocks": [{"type": "text", "value": spec["description"]}]},
                estimated_minutes=10,
            )
        )
        session.add(
            ProjectTask(
                module_id=understand.id,
                title="Prerequisites checklist",
                sort_order=1,
                task_type=ProjectTaskType.CHECKLIST,
                summary="Confirm you can complete the listed prerequisites before coding.",
                checklist_json=spec["prerequisites"],
                estimated_minutes=10,
            )
        )

        session.add(
            ProjectTask(
                module_id=build.id,
                title="Implement the core flow",
                sort_order=0,
                task_type=ProjectTaskType.IMPLEMENTATION,
                summary="Build the smallest version that meets the final objective using original code.",
                body_json={"blocks": [{"type": "text", "value": spec["final_objective"]}]},
                estimated_minutes=max((spec["estimated_minutes"] or 60) // 2, 20),
            )
        )

        sort_extra = 1
        for slug in spec["coding_slugs"]:
            pid = coding_by_slug.get(slug)
            if not pid:
                continue
            session.add(
                ProjectTask(
                    module_id=build.id,
                    title=f"Linked coding practice: {slug}",
                    sort_order=sort_extra,
                    task_type=ProjectTaskType.CODING,
                    coding_problem_id=pid,
                    summary="Reuse the DSA workspace for a related warm-up. Original problem bank.",
                    estimated_minutes=25,
                )
            )
            sort_extra += 1
        for slug in spec["sql_slugs"]:
            pid = sql_by_slug.get(slug)
            session.add(
                ProjectTask(
                    module_id=build.id,
                    title=f"SQL challenge: {slug}",
                    sort_order=sort_extra,
                    task_type=ProjectTaskType.SQL,
                    sql_problem_id=pid,
                    summary="Solve this challenge in the existing SQL practice engine (or the SQL hub if the problem is not loaded yet).",
                    estimated_minutes=20,
                )
            )
            sort_extra += 1
        topic_id = topic_by_slug.get(spec["topic_slug"]) if spec.get("topic_slug") else None
        if topic_id:
            session.add(
                ProjectTask(
                    module_id=build.id,
                    title="Related MCQ set",
                    sort_order=sort_extra,
                    task_type=ProjectTaskType.MCQ,
                    topic_id=topic_id,
                    summary="Practice related multiple-choice items in the existing MCQ engine.",
                    estimated_minutes=15,
                )
            )

        session.add(
            ProjectTask(
                module_id=ship.id,
                title="Review against the objective",
                sort_order=0,
                task_type=ProjectTaskType.REVIEW,
                summary="Check completeness, edge cases, and the skills list.",
                checklist_json=["Meets final objective", "Handles invalid input", "Notes complexity or ops risks"],
                reference_json={"skills": spec["skills"]},
                estimated_minutes=15,
            )
        )


async def _ensure_engine_links(session, project_id, spec, coding_by_slug, sql_by_slug, topic_by_slug) -> None:
    build = (
        await session.execute(
            select(ProjectModule).where(ProjectModule.project_id == project_id, ProjectModule.sort_order == 1)
        )
    ).scalar_one_or_none()
    if build is None:
        return
    existing_sql = {
        row
        for row in (
            await session.execute(
                select(ProjectTask.sql_problem_id).where(
                    ProjectTask.module_id == build.id, ProjectTask.sql_problem_id.is_not(None)
                )
            )
        ).scalars().all()
    }
    sort_extra = 10
    for slug in spec["sql_slugs"]:
        pid = sql_by_slug.get(slug)
        if pid and pid in existing_sql:
            continue
        title = f"SQL challenge: {slug}"
        already = (
            await session.scalar(
                select(ProjectTask.id).where(ProjectTask.module_id == build.id, ProjectTask.title == title)
            )
        )
        if already:
            continue
        session.add(
            ProjectTask(
                module_id=build.id,
                title=title,
                sort_order=sort_extra,
                task_type=ProjectTaskType.SQL,
                sql_problem_id=pid,
                summary="Solve this challenge in the existing SQL practice engine.",
                estimated_minutes=20,
            )
        )
        sort_extra += 1
    existing_coding = {
        row
        for row in (
            await session.execute(
                select(ProjectTask.coding_problem_id).where(
                    ProjectTask.module_id == build.id, ProjectTask.coding_problem_id.is_not(None)
                )
            )
        ).scalars().all()
    }
    for slug in spec["coding_slugs"]:
        pid = coding_by_slug.get(slug)
        if not pid or pid in existing_coding:
            continue
        session.add(
            ProjectTask(
                module_id=build.id,
                title=f"Linked coding practice: {slug}",
                sort_order=sort_extra,
                task_type=ProjectTaskType.CODING,
                coding_problem_id=pid,
                summary="Reuse the DSA workspace for a related warm-up. Original problem bank.",
                estimated_minutes=25,
            )
        )
        sort_extra += 1


async def _expand_paths(session, coding_by_slug, sql_by_slug, topic_by_slug) -> None:
    for slug, title, short in NEW_DS_PATHS:
        await _ensure_path(
            session,
            slug=slug,
            title=title,
            short=short,
            path_type=PracticePathType.DATA_STRUCTURE,
        )
    for slug, title, short in NEW_ALGO_PATHS:
        await _ensure_path(
            session,
            slug=slug,
            title=title,
            short=short,
            path_type=PracticePathType.ALGORITHM,
        )

    # Mark remaining DS/algo shells available with Learn / Practice / Checkpoint.
    shells = (
        await session.execute(
            select(PracticePath).where(
                PracticePath.path_type.in_([PracticePathType.DATA_STRUCTURE, PracticePathType.ALGORITHM, PracticePathType.BEGINNER_DSA])
            )
        )
    ).scalars().all()
    for path in shells:
        path.availability = PathAvailability.AVAILABLE
        await _ensure_lpc_sections(session, path, coding_by_slug, topic_by_slug)

    # Difficulty: mix coding + SQL + MCQ
    difficulty_map = {
        "difficulty-beginner": ("easy", "active-catalog-items"),
        "difficulty-easy": ("easy", "high-priority-open-tickets"),
        "difficulty-medium": ("medium", "top-customers-by-revenue"),
        "difficulty-hard": ("hard", "weekly-active-retention"),
    }
    for slug, (diff, sql_slug) in difficulty_map.items():
        path = (await session.execute(select(PracticePath).where(PracticePath.slug == slug))).scalar_one_or_none()
        if path is None:
            continue
        path.availability = PathAvailability.AVAILABLE
        path.description = (
            path.description
            or f"Aggregate practice at {diff} difficulty across coding, SQL, and MCQ. Original content only."
        )
        await _ensure_section_with_items(
            session,
            path,
            "Practice mix",
            "practice",
            [
                {
                    "item_type": PracticePathItemType.EXTERNAL_ROUTE,
                    "title": "Coding filter",
                    "external_route": f"/practice/dsa?difficulty={diff}",
                },
                {
                    "item_type": PracticePathItemType.SQL_PROBLEM,
                    "title": "SQL sample",
                    "sql_problem_id": sql_by_slug.get(sql_slug),
                },
                {
                    "item_type": PracticePathItemType.EXTERNAL_ROUTE,
                    "title": "Technical MCQs",
                    "external_route": "/practice/mcq",
                },
            ],
        )

    companies = (
        await session.execute(select(PracticePath).where(PracticePath.path_type == PracticePathType.COMPANY))
    ).scalars().all()
    for path in companies:
        path.availability = PathAvailability.AVAILABLE
        path.description = COMPANY_DISCLAIMER
        await _ensure_section_with_items(
            session,
            path,
            "Skill mix",
            "mix",
            [
                {"item_type": PracticePathItemType.EXTERNAL_ROUTE, "title": "Aptitude / CRT", "external_route": "/practice/aptitude"},
                {"item_type": PracticePathItemType.EXTERNAL_ROUTE, "title": "Technical MCQs", "external_route": "/practice/mcq"},
                {"item_type": PracticePathItemType.EXTERNAL_ROUTE, "title": "SQL practice", "external_route": "/practice/sql"},
                {"item_type": PracticePathItemType.EXTERNAL_ROUTE, "title": "Coding practice", "external_route": "/practice/dsa"},
                {"item_type": PracticePathItemType.EXTERNAL_ROUTE, "title": "Interview Q&A", "external_route": "/interviews"},
            ],
        )


async def _ensure_path(session, *, slug: str, title: str, short: str, path_type: PracticePathType) -> PracticePath:
    path = (await session.execute(select(PracticePath).where(PracticePath.slug == slug))).scalar_one_or_none()
    if path is not None:
        path.availability = PathAvailability.AVAILABLE
        return path
    path = PracticePath(
        slug=slug,
        title=title,
        short_description=short,
        description=short,
        path_type=path_type,
        difficulty=PracticePathDifficulty.BEGINNER,
        availability=PathAvailability.AVAILABLE,
        is_active=True,
        is_featured=False,
        sort_order=50,
    )
    session.add(path)
    await session.flush()
    return path


async def _ensure_lpc_sections(session, path: PracticePath, coding_by_slug, topic_by_slug) -> None:
    existing_titles = {
        t
        for t in (
            await session.execute(select(PracticePathSection.title).where(PracticePathSection.path_id == path.id))
        ).scalars().all()
    }
    if "Learn" not in existing_titles:
        learn = PracticePathSection(path_id=path.id, title="Learn", section_key="learn", sort_order=0)
        session.add(learn)
        await session.flush()
        session.add(
            PracticePathItem(
                section_id=learn.id,
                item_type=PracticePathItemType.EXTERNAL_ROUTE,
                title="Concept notes",
                sort_order=0,
                external_route="/learn" if path.slug.startswith("beginner-") else f"/practice/paths/{path.slug}",
            )
        )
    if "Checkpoint" not in existing_titles:
        chk = PracticePathSection(path_id=path.id, title="Checkpoint", section_key="checkpoint", sort_order=20)
        session.add(chk)
        await session.flush()
        session.add(
            PracticePathItem(
                section_id=chk.id,
                item_type=PracticePathItemType.CHECKPOINT,
                title="Self-check: can you explain the pattern and solve one problem without notes?",
                sort_order=0,
            )
        )


async def _ensure_section_with_items(session, path: PracticePath, title: str, key: str, items: list[dict]) -> None:
    section = (
        await session.execute(
            select(PracticePathSection).where(
                PracticePathSection.path_id == path.id,
                PracticePathSection.section_key == key,
            )
        )
    ).scalar_one_or_none()
    if section is None:
        section = PracticePathSection(path_id=path.id, title=title, section_key=key, sort_order=5)
        session.add(section)
        await session.flush()
    existing = await session.scalar(
        select(PracticePathItem.id).where(PracticePathItem.section_id == section.id).limit(1)
    )
    if existing is not None:
        return
    for index, spec in enumerate(items):
        kwargs = dict(spec)
        if kwargs.get("sql_problem_id") is None and kwargs.get("item_type") == PracticePathItemType.SQL_PROBLEM:
            continue
        session.add(
            PracticePathItem(
                section_id=section.id,
                sort_order=index,
                **kwargs,
            )
        )
