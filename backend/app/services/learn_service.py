# ruff: noqa: E501
"""Practice Hub, guided courses, lessons, and projects."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.coding import CodingProblem
from app.models.learn import (
    Course,
    CourseLesson,
    CourseModule,
    LessonAttempt,
    LessonDoubt,
    LessonFeedback,
    LessonHint,
    PracticePath,
    PracticePathItem,
    PracticePathSection,
    Project,
    ProjectModule,
    ProjectTask,
    UserCourseProgress,
    UserLessonProgress,
    UserPracticePathProgress,
    UserProjectProgress,
    UserProjectTaskProgress,
)
from app.models.learn_enums import (
    CourseLevel,
    LessonFeedbackVote,
    LessonType,
    LessonUnlockMode,
    PathAvailability,
    PracticePathDifficulty,
    PracticePathItemType,
    PracticePathType,
    ProgressStatus,
    ProjectTaskType,
    SolutionRevealPolicy,
)
from app.models.sql_practice import SqlProblem
from app.models.taxonomy import Topic
from app.models.user import User
from app.schemas.learn import (
    ContinueLearningItem,
    CourseAdminIn,
    CourseDetail,
    CourseListItem,
    LessonAdminIn,
    LessonDetail,
    LessonDoubtOut,
    LessonFeedbackIn,
    LessonHintOut,
    LessonNavItem,
    LessonResourceOut,
    LessonStepOut,
    ModuleAdminIn,
    ModuleOut,
    PracticeHubResponse,
    PracticeHubSection,
    PracticePathAdminIn,
    PracticePathCard,
    PracticePathDetail,
    PracticePathItemAdminIn,
    PracticePathItemOut,
    PracticePathSectionAdminIn,
    PracticePathSectionOut,
    ProjectAdminIn,
    ProjectCard,
    ProjectDetail,
    ProjectModuleAdminIn,
    ProjectModuleOut,
    ProjectTaskAdminIn,
    ProjectTaskOut,
    SearchHit,
    SearchResponse,
)

HUB_SECTIONS: list[tuple[PracticePathType, str]] = [
    (PracticePathType.LANGUAGE, "Programming Languages"),
    (PracticePathType.PROJECT, "Projects"),
    (PracticePathType.BEGINNER_DSA, "Beginner DSA"),
    (PracticePathType.DATA_STRUCTURE, "Data Structures"),
    (PracticePathType.ALGORITHM, "Algorithms"),
    (PracticePathType.DIFFICULTY, "Difficulty Paths"),
    (PracticePathType.INTERVIEW, "Interview Questions"),
    (PracticePathType.COMPANY, "Company Paths"),
    (PracticePathType.CUSTOM, "Other Practice Paths"),
]


_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def _now() -> datetime:
    return datetime.now(UTC)


def _enum_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def course_href(course_slug: str) -> str:
    return f"/learn/courses/{course_slug}"


def lesson_href(course_slug: str, module_slug: str, lesson_slug: str) -> str:
    return f"/learn/courses/{course_slug}/{module_slug}/{lesson_slug}"


def path_href(path: PracticePath) -> str:
    return path.external_route or f"/practice/paths/{path.slug}"


def project_href(project_slug: str) -> str:
    return f"/projects/{project_slug}"


class LearnService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Practice Hub
    # ------------------------------------------------------------------

    async def practice_hub(self, user: User) -> PracticeHubResponse:
        paths = (
            await self.db.execute(
                select(PracticePath)
                .where(PracticePath.is_active.is_(True))
                .order_by(PracticePath.sort_order, PracticePath.title)
            )
        ).scalars().all()

        item_counts = await self._path_item_counts()
        path_progress = await self._path_progress_map(user.id)

        cards: dict[PracticePathType, list[PracticePathCard]] = {}
        for path in paths:
            card = self._path_card(path, item_counts.get(path.id, 0), path_progress.get(path.id, 0))
            cards.setdefault(path.path_type, []).append(card)

        sections = [
            PracticeHubSection(key=_enum_value(path_type), label=label, paths=cards.get(path_type, []))
            for path_type, label in HUB_SECTIONS
            if cards.get(path_type)
        ]

        continue_items = await self.continue_learning(user)
        recommended = [
            self._path_card(p, item_counts.get(p.id, 0), path_progress.get(p.id, 0))
            for p in paths
            if p.is_featured and p.availability == PathAvailability.AVAILABLE
        ][:6]

        return PracticeHubResponse(
            sections=sections,
            continue_learning=continue_items[:4],
            recently_practiced=await self._recently_practiced(user),
            recommended=recommended,
        )

    async def list_paths(self, user: User, *, path_type: str | None = None) -> list[PracticePathCard]:
        stmt = select(PracticePath).where(PracticePath.is_active.is_(True))
        if path_type:
            stmt = stmt.where(PracticePath.path_type == path_type)
        paths = (
            await self.db.execute(stmt.order_by(PracticePath.sort_order, PracticePath.title))
        ).scalars().all()
        item_counts = await self._path_item_counts()
        progress = await self._path_progress_map(user.id)
        return [self._path_card(p, item_counts.get(p.id, 0), progress.get(p.id, 0)) for p in paths]

    async def get_path(self, slug: str, user: User) -> PracticePathDetail:
        path = (
            await self.db.execute(
                select(PracticePath)
                .options(selectinload(PracticePath.sections).selectinload(PracticePathSection.items))
                .where(PracticePath.slug == slug, PracticePath.is_active.is_(True))
            )
        ).scalar_one_or_none()
        if path is None:
            raise AppException("Practice path not found", status_code=404)

        items = [item for section in path.sections for item in section.items]
        hrefs = await self._item_hrefs(items)
        progress = await self._path_progress_map(user.id)

        return PracticePathDetail(
            id=path.id,
            slug=path.slug,
            title=path.title,
            short_description=path.short_description,
            description=path.description,
            path_type=_enum_value(path.path_type),
            difficulty=_enum_value(path.difficulty),
            language=path.language,
            estimated_minutes=path.estimated_minutes,
            availability=_enum_value(path.availability),
            external_route=path.external_route,
            progress_percent=progress.get(path.id, 0),
            sections=[
                PracticePathSectionOut(
                    id=section.id,
                    title=section.title,
                    section_key=section.section_key,
                    sort_order=section.sort_order,
                    items=[
                        PracticePathItemOut(
                            id=item.id,
                            item_type=_enum_value(item.item_type),
                            title=item.title,
                            sort_order=item.sort_order,
                            href=hrefs.get(item.id),
                            coding_problem_id=item.coding_problem_id,
                            course_id=item.course_id,
                            lesson_id=item.lesson_id,
                            project_id=item.project_id,
                            external_route=item.external_route,
                        )
                        for item in section.items
                    ],
                )
                for section in path.sections
            ],
        )

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------

    async def list_courses(self, user: User) -> list[CourseListItem]:
        courses = (
            await self.db.execute(
                select(Course)
                .where(Course.is_published.is_(True))
                .order_by(Course.sort_order, Course.title)
            )
        ).scalars().all()
        out: list[CourseListItem] = []
        for course in courses:
            lessons = await self._course_lessons(course.id)
            percent = await self._course_percent(user.id, [row[1].id for row in lessons])
            out.append(
                CourseListItem(
                    id=course.id,
                    slug=course.slug,
                    title=course.title,
                    summary=course.summary,
                    level=_enum_value(course.level),
                    primary_language_key=course.primary_language_key,
                    estimated_minutes=course.estimated_minutes,
                    lesson_count=len(lessons),
                    progress_percent=percent,
                    is_featured=course.is_featured,
                )
            )
        return out

    async def get_course(self, slug: str, user: User) -> CourseDetail:
        course = await self._load_course(slug)
        ordered = self._ordered_lessons(course)
        statuses = await self._lesson_statuses(user.id, ordered)

        modules: list[ModuleOut] = []
        for module in sorted(course.modules, key=lambda m: m.sort_order):
            lessons = [lsn for lsn in sorted(module.lessons, key=lambda x: x.sort_order) if lsn.is_published]
            nav = [self._nav_item(module, lsn, statuses[lsn.id]) for lsn in lessons]
            modules.append(
                ModuleOut(
                    id=module.id,
                    slug=module.slug,
                    title=module.title,
                    sort_order=module.sort_order,
                    summary=module.summary,
                    lessons=nav,
                    completed_count=sum(1 for n in nav if n.status == ProgressStatus.COMPLETED.value),
                    lesson_count=len(nav),
                )
            )

        completed = sum(1 for _, lsn in ordered if statuses[lsn.id] == ProgressStatus.COMPLETED)
        percent = int(round(completed * 100 / len(ordered))) if ordered else 0
        progress = await self._get_course_progress(user.id, course.id)

        continue_href: str | None = None
        for module, lesson in ordered:
            if statuses[lesson.id] != ProgressStatus.COMPLETED:
                continue_href = lesson_href(course.slug, module.slug, lesson.slug)
                break
        if continue_href is None and ordered:
            module, lesson = ordered[0]
            continue_href = lesson_href(course.slug, module.slug, lesson.slug)

        status = ProgressStatus.NOT_STARTED
        if percent >= 100 and ordered:
            status = ProgressStatus.COMPLETED
        elif progress is not None or completed:
            status = ProgressStatus.IN_PROGRESS

        return CourseDetail(
            id=course.id,
            slug=course.slug,
            title=course.title,
            summary=course.summary,
            level=_enum_value(course.level),
            primary_language_key=course.primary_language_key,
            estimated_minutes=course.estimated_minutes,
            progress_percent=percent,
            status=status.value,
            continue_href=continue_href,
            modules=modules,
        )

    # ------------------------------------------------------------------
    # Lessons
    # ------------------------------------------------------------------

    async def get_lesson(
        self,
        course_slug: str,
        module_slug: str,
        lesson_slug: str,
        user: User,
    ) -> LessonDetail:
        course = await self._load_course(course_slug)
        ordered = self._ordered_lessons(course)
        index = next(
            (
                i
                for i, (mod, lsn) in enumerate(ordered)
                if mod.slug == module_slug and lsn.slug == lesson_slug
            ),
            None,
        )
        if index is None:
            raise AppException("Lesson not found", status_code=404)

        module, lesson = ordered[index]
        statuses = await self._lesson_statuses(user.id, ordered)
        status = statuses[lesson.id]
        if status == ProgressStatus.LOCKED:
            raise AppException("Complete the previous lesson to unlock this one", status_code=403)

        lesson = await self._load_lesson(lesson.id)
        progress = await self._get_lesson_progress(user.id, lesson.id)
        attempts = progress.attempts if progress else 0

        solution_unlocked = lesson.solution_reveal == SolutionRevealPolicy.ALWAYS or (
            lesson.solution_reveal == SolutionRevealPolicy.AFTER_COMPLETION
            and status == ProgressStatus.COMPLETED
        )

        coding_slug: str | None = None
        if lesson.coding_problem_id:
            coding_slug = await self.db.scalar(
                select(CodingProblem.slug).where(CodingProblem.id == lesson.coding_problem_id)
            )

        prev_href = None
        if index > 0:
            prev_mod, prev_lesson = ordered[index - 1]
            prev_href = lesson_href(course.slug, prev_mod.slug, prev_lesson.slug)
        next_href = None
        if index + 1 < len(ordered):
            next_mod, next_lesson = ordered[index + 1]
            next_href = lesson_href(course.slug, next_mod.slug, next_lesson.slug)

        can_mark_complete = True
        if lesson.completion_requires_submit:
            can_mark_complete = await self._has_successful_attempt(user.id, lesson.id)

        return LessonDetail(
            id=lesson.id,
            slug=lesson.slug,
            title=lesson.title,
            lesson_type=_enum_value(lesson.lesson_type),
            statement_json=lesson.statement_json or {},
            starter_code=lesson.starter_code or {},
            coding_problem_id=lesson.coding_problem_id,
            coding_problem_slug=coding_slug,
            question_id=lesson.question_id,
            status=status.value,
            attempts=attempts,
            solution_unlocked=solution_unlocked,
            solution_json=lesson.solution_json if solution_unlocked else None,
            hints=[
                LessonHintOut(
                    id=hint.id,
                    hint_text=hint.hint_text,
                    sort_order=hint.sort_order,
                    unlocked=attempts >= hint.unlock_after_attempts,
                )
                for hint in lesson.hints
            ],
            doubts=[
                LessonDoubtOut(
                    id=doubt.id,
                    question=doubt.question,
                    answer=doubt.answer,
                    sort_order=doubt.sort_order,
                )
                for doubt in lesson.doubts
            ],
            resources=[
                LessonResourceOut(
                    id=res.id,
                    resource_type=_enum_value(res.resource_type),
                    title=res.title,
                    url=res.url,
                    description=res.description,
                )
                for res in lesson.resources
            ],
            steps=[
                LessonStepOut(id=step.id, title=step.title, body_md=step.body_md, sort_order=step.sort_order)
                for step in lesson.steps
            ],
            progress_blocks=[
                self._nav_item(mod, lsn, statuses[lsn.id]) for mod, lsn in ordered
            ],
            prev_href=prev_href,
            next_href=next_href,
            course_slug=course.slug,
            module_slug=module.slug,
            completion_requires_submit=lesson.completion_requires_submit,
            can_mark_complete=can_mark_complete,
        )

    async def start_lesson(self, lesson_id: UUID, user: User) -> dict:
        lesson = await self._get_lesson_or_404(lesson_id)
        progress = await self._get_lesson_progress(user.id, lesson.id)
        if progress is None:
            progress = UserLessonProgress(
                user_id=user.id,
                lesson_id=lesson.id,
                status=ProgressStatus.IN_PROGRESS,
                started_at=_now(),
            )
            self.db.add(progress)
        elif progress.status == ProgressStatus.NOT_STARTED:
            progress.status = ProgressStatus.IN_PROGRESS
            progress.started_at = progress.started_at or _now()
        progress.last_activity_at = _now()

        await self._touch_course_progress(user.id, lesson, current_lesson_id=lesson.id)
        await self.db.commit()
        return {"status": progress.status.value, "attempts": progress.attempts}

    async def complete_lesson(self, lesson_id: UUID, user: User) -> dict:
        lesson = await self._get_lesson_or_404(lesson_id)
        if lesson.completion_requires_submit and not await self._has_successful_attempt(user.id, lesson.id):
            raise AppException("Submit a passing solution before completing this lesson", status_code=400)

        progress = await self._get_lesson_progress(user.id, lesson.id)
        if progress is None:
            progress = UserLessonProgress(user_id=user.id, lesson_id=lesson.id, started_at=_now())
            self.db.add(progress)
        progress.status = ProgressStatus.COMPLETED
        progress.completed_at = progress.completed_at or _now()
        progress.last_activity_at = _now()
        await self.db.flush()

        course, ordered, next_href = await self._course_context(lesson)
        statuses = await self._lesson_statuses(user.id, ordered)
        completed = sum(1 for _, lsn in ordered if statuses[lsn.id] == ProgressStatus.COMPLETED)
        percent = int(round(completed * 100 / len(ordered))) if ordered else 0

        course_progress = await self._touch_course_progress(user.id, lesson)
        course_progress.percent = percent
        if percent >= 100:
            course_progress.status = ProgressStatus.COMPLETED
            course_progress.completed_at = course_progress.completed_at or _now()
        else:
            course_progress.status = ProgressStatus.IN_PROGRESS

        await self.db.commit()
        return {
            "status": ProgressStatus.COMPLETED.value,
            "course_slug": course.slug,
            "course_percent": percent,
            "next_href": next_href,
        }

    async def record_attempt(
        self,
        lesson_id: UUID,
        user: User,
        payload: dict[str, Any] | None = None,
    ) -> dict:
        lesson = await self._get_lesson_or_404(lesson_id)
        data = dict(payload or {})
        is_correct = data.pop("is_correct", None)
        submission_id = data.pop("coding_submission_id", None)
        if isinstance(submission_id, str):
            try:
                submission_id = UUID(submission_id)
            except ValueError:
                submission_id = None

        self.db.add(
            LessonAttempt(
                user_id=user.id,
                lesson_id=lesson.id,
                payload_json=data,
                is_correct=bool(is_correct) if is_correct is not None else None,
                coding_submission_id=submission_id,
            )
        )

        progress = await self._get_lesson_progress(user.id, lesson.id)
        if progress is None:
            progress = UserLessonProgress(
                user_id=user.id,
                lesson_id=lesson.id,
                status=ProgressStatus.IN_PROGRESS,
                started_at=_now(),
            )
            self.db.add(progress)
        if progress.status == ProgressStatus.NOT_STARTED:
            progress.status = ProgressStatus.IN_PROGRESS
        progress.attempts = (progress.attempts or 0) + 1
        progress.last_activity_at = _now()

        await self._touch_course_progress(user.id, lesson, current_lesson_id=lesson.id)
        await self.db.commit()
        return {
            "attempts": progress.attempts,
            "status": progress.status.value,
            "is_correct": bool(is_correct) if is_correct is not None else None,
        }

    async def feedback(self, lesson_id: UUID, user: User, payload: LessonFeedbackIn) -> dict:
        await self._get_lesson_or_404(lesson_id)
        vote: LessonFeedbackVote | None = None
        if payload.vote:
            try:
                vote = LessonFeedbackVote(payload.vote)
            except ValueError as exc:
                raise AppException("Invalid feedback vote", status_code=400) from exc

        existing = (
            await self.db.execute(
                select(LessonFeedback).where(
                    LessonFeedback.user_id == user.id, LessonFeedback.lesson_id == lesson_id
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            existing = LessonFeedback(user_id=user.id, lesson_id=lesson_id)
            self.db.add(existing)
        existing.vote = vote
        existing.report_issue = payload.report_issue
        existing.note = payload.note
        await self.db.commit()
        return {"recorded": True, "vote": vote.value if vote else None}

    # ------------------------------------------------------------------
    # Continue learning / projects / search
    # ------------------------------------------------------------------

    async def continue_learning(self, user: User) -> list[ContinueLearningItem]:
        items: list[ContinueLearningItem] = []

        course_rows = (
            await self.db.execute(
                select(UserCourseProgress, Course)
                .join(Course, Course.id == UserCourseProgress.course_id)
                .where(
                    UserCourseProgress.user_id == user.id,
                    UserCourseProgress.status != ProgressStatus.COMPLETED,
                )
                .order_by(UserCourseProgress.last_activity_at.desc().nulls_last())
                .limit(5)
            )
        ).all()
        for progress, course in course_rows:
            href = course_href(course.slug)
            subtitle = None
            if progress.current_lesson_id:
                located = await self._locate_lesson(progress.current_lesson_id)
                if located:
                    _course, module, lesson = located
                    href = lesson_href(course.slug, module.slug, lesson.slug)
                    subtitle = f"{module.title} - {lesson.title}"
            items.append(
                ContinueLearningItem(
                    kind="course",
                    title=course.title,
                    subtitle=subtitle or course.summary[:120] or None,
                    progress_percent=progress.percent,
                    href=href,
                    last_activity_at=progress.last_activity_at,
                )
            )

        project_rows = (
            await self.db.execute(
                select(UserProjectProgress, Project)
                .join(Project, Project.id == UserProjectProgress.project_id)
                .where(
                    UserProjectProgress.user_id == user.id,
                    UserProjectProgress.status != ProgressStatus.COMPLETED,
                )
                .order_by(UserProjectProgress.last_activity_at.desc().nulls_last())
                .limit(5)
            )
        ).all()
        for progress, project in project_rows:
            items.append(
                ContinueLearningItem(
                    kind="project",
                    title=project.title,
                    subtitle=project.short_description or None,
                    progress_percent=progress.percent,
                    href=project_href(project.slug),
                    last_activity_at=progress.last_activity_at,
                )
            )

        path_rows = (
            await self.db.execute(
                select(UserPracticePathProgress, PracticePath)
                .join(PracticePath, PracticePath.id == UserPracticePathProgress.path_id)
                .where(
                    UserPracticePathProgress.user_id == user.id,
                    UserPracticePathProgress.status != ProgressStatus.COMPLETED,
                )
                .order_by(UserPracticePathProgress.last_activity_at.desc().nulls_last())
                .limit(5)
            )
        ).all()
        for progress, path in path_rows:
            items.append(
                ContinueLearningItem(
                    kind="path",
                    title=path.title,
                    subtitle=path.short_description or None,
                    progress_percent=progress.percent,
                    href=path_href(path),
                    last_activity_at=progress.last_activity_at,
                )
            )

        items.sort(key=lambda i: i.last_activity_at or _EPOCH, reverse=True)
        return items

    async def list_projects(self, user: User, *, category_key: str | None = None) -> list[ProjectCard]:
        stmt = select(Project).where(Project.is_published.is_(True))
        if category_key:
            stmt = stmt.where(Project.category_key == category_key)
        projects = (
            await self.db.execute(stmt.order_by(Project.sort_order, Project.title))
        ).scalars().all()

        progress_map = {
            row.project_id: row.percent
            for row in (
                await self.db.execute(
                    select(UserProjectProgress).where(UserProjectProgress.user_id == user.id)
                )
            ).scalars().all()
        }
        task_counts = await self._project_task_counts()
        return [
            ProjectCard(
                id=p.id,
                slug=p.slug,
                title=p.title,
                short_description=p.short_description,
                difficulty=_enum_value(p.difficulty),
                technology=p.technology,
                category_key=p.category_key,
                availability=_enum_value(p.availability),
                estimated_minutes=p.estimated_minutes,
                task_count=task_counts.get(p.id, 0),
                progress_percent=progress_map.get(p.id, 0),
                href=project_href(p.slug),
            )
            for p in projects
        ]

    async def get_project(self, slug: str, user: User) -> ProjectDetail:
        project = (
            await self.db.execute(
                select(Project)
                .options(selectinload(Project.modules).selectinload(ProjectModule.tasks))
                .where(Project.slug == slug, Project.is_published.is_(True))
            )
        ).scalar_one_or_none()
        if project is None:
            raise AppException("Project not found", status_code=404)

        progress = (
            await self.db.execute(
                select(UserProjectProgress).where(
                    UserProjectProgress.user_id == user.id,
                    UserProjectProgress.project_id == project.id,
                )
            )
        ).scalar_one_or_none()

        ordered_tasks = [task for module in project.modules for task in module.tasks]
        completed_ids = await self._completed_task_ids(user.id, [t.id for t in ordered_tasks])
        hrefs = await self._project_task_hrefs(ordered_tasks)
        current_task = next((t for t in ordered_tasks if t.id not in completed_ids), None)
        completed_count = len(completed_ids)
        total = len(ordered_tasks)
        percent = progress.percent if progress else (int(round(completed_count * 100 / total)) if total else 0)
        status = _enum_value(progress.status) if progress else ProgressStatus.NOT_STARTED.value

        return ProjectDetail(
            id=project.id,
            slug=project.slug,
            title=project.title,
            short_description=project.short_description,
            description=project.description,
            difficulty=_enum_value(project.difficulty),
            technology=project.technology,
            category_key=project.category_key,
            availability=_enum_value(project.availability),
            estimated_minutes=project.estimated_minutes,
            prerequisites=list(project.prerequisites or []),
            skills=list(project.skills or []),
            final_objective=project.final_objective,
            reference_json=project.reference_json,
            progress_percent=percent,
            status=status,
            completed_task_count=completed_count,
            task_count=total,
            current_task_id=current_task.id if current_task else None,
            current_task_href=hrefs.get(current_task.id) if current_task else None,
            continue_href=project_href(project.slug),
            last_activity_at=progress.last_activity_at if progress else None,
            completed_at=progress.completed_at if progress else None,
            modules=[
                ProjectModuleOut(
                    id=module.id,
                    title=module.title,
                    sort_order=module.sort_order,
                    tasks=[
                        ProjectTaskOut(
                            id=task.id,
                            title=task.title,
                            sort_order=task.sort_order,
                            summary=task.summary,
                            task_type=_enum_value(task.task_type),
                            status="completed" if task.id in completed_ids else "not_started",
                            href=hrefs.get(task.id),
                            lesson_id=task.lesson_id,
                            coding_problem_id=task.coding_problem_id,
                            sql_problem_id=task.sql_problem_id,
                            topic_id=task.topic_id,
                            body_json=task.body_json or {},
                            checklist_json=list(task.checklist_json or []),
                            reference_json=task.reference_json,
                            estimated_minutes=task.estimated_minutes,
                        )
                        for task in module.tasks
                    ],
                )
                for module in project.modules
            ],
        )

    async def start_project(self, project_id: UUID, user: User) -> dict:
        project = await self.db.get(Project, project_id)
        if project is None or not project.is_published:
            raise AppException("Project not found", status_code=404)
        progress = await self._ensure_project_progress(user.id, project.id)
        if progress.status == ProgressStatus.NOT_STARTED:
            progress.status = ProgressStatus.IN_PROGRESS
        progress.last_activity_at = _now()
        await self.db.commit()
        return {
            "status": progress.status.value,
            "percent": progress.percent,
            "href": project_href(project.slug),
        }

    async def complete_project_task(self, project_id: UUID, task_id: UUID, user: User) -> dict:
        project = (
            await self.db.execute(
                select(Project)
                .options(selectinload(Project.modules).selectinload(ProjectModule.tasks))
                .where(Project.id == project_id, Project.is_published.is_(True))
            )
        ).scalar_one_or_none()
        if project is None:
            raise AppException("Project not found", status_code=404)
        ordered = [task for module in project.modules for task in module.tasks]
        task = next((t for t in ordered if t.id == task_id), None)
        if task is None:
            raise AppException("Task not found on this project", status_code=404)

        row = (
            await self.db.execute(
                select(UserProjectTaskProgress).where(
                    UserProjectTaskProgress.user_id == user.id,
                    UserProjectTaskProgress.task_id == task_id,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            row = UserProjectTaskProgress(user_id=user.id, task_id=task_id)
            self.db.add(row)
        row.status = ProgressStatus.COMPLETED
        row.completed_at = row.completed_at or _now()
        row.last_activity_at = _now()

        completed_ids = await self._completed_task_ids(user.id, [t.id for t in ordered])
        completed_ids.add(task_id)
        percent = int(round(len(completed_ids) * 100 / len(ordered))) if ordered else 100
        progress = await self._ensure_project_progress(user.id, project.id)
        progress.percent = percent
        progress.last_task_id = task_id
        progress.last_activity_at = _now()
        progress.status = ProgressStatus.COMPLETED if percent >= 100 else ProgressStatus.IN_PROGRESS
        if percent >= 100:
            progress.completed_at = progress.completed_at or _now()
        await self.db.commit()
        return {
            "status": progress.status.value,
            "percent": percent,
            "completed_task_id": str(task_id),
            "href": project_href(project.slug),
        }

    async def start_path(self, path_id: UUID, user: User) -> dict:
        path = await self.db.get(PracticePath, path_id)
        if path is None or not path.is_active:
            raise AppException("Practice path not found", status_code=404)
        progress = await self._ensure_path_progress(user.id, path.id)
        if progress.status == ProgressStatus.NOT_STARTED:
            progress.status = ProgressStatus.IN_PROGRESS
        progress.last_activity_at = _now()
        await self.db.commit()
        return {"status": progress.status.value, "percent": progress.percent, "href": path_href(path)}

    async def complete_path_item(self, path_id: UUID, item_id: UUID, user: User) -> dict:
        path = (
            await self.db.execute(
                select(PracticePath)
                .options(selectinload(PracticePath.sections).selectinload(PracticePathSection.items))
                .where(PracticePath.id == path_id, PracticePath.is_active.is_(True))
            )
        ).scalar_one_or_none()
        if path is None:
            raise AppException("Practice path not found", status_code=404)
        items = [item for section in path.sections for item in section.items]
        if not any(item.id == item_id for item in items):
            raise AppException("Path item not found", status_code=404)
        # Approximate progress by counting completed-looking items via percent steps.
        progress = await self._ensure_path_progress(user.id, path.id)
        total = max(len(items), 1)
        step = max(int(round(100 / total)), 1)
        progress.percent = min(100, (progress.percent or 0) + step)
        progress.status = ProgressStatus.COMPLETED if progress.percent >= 100 else ProgressStatus.IN_PROGRESS
        progress.last_activity_at = _now()
        if progress.percent >= 100:
            progress.completed_at = progress.completed_at or _now()
        await self.db.commit()
        return {"status": progress.status.value, "percent": progress.percent, "href": path_href(path)}

    async def _ensure_project_progress(self, user_id: UUID, project_id: UUID) -> UserProjectProgress:
        progress = (
            await self.db.execute(
                select(UserProjectProgress).where(
                    UserProjectProgress.user_id == user_id,
                    UserProjectProgress.project_id == project_id,
                )
            )
        ).scalar_one_or_none()
        if progress is None:
            progress = UserProjectProgress(user_id=user_id, project_id=project_id, status=ProgressStatus.IN_PROGRESS)
            self.db.add(progress)
            await self.db.flush()
        return progress

    async def _ensure_path_progress(self, user_id: UUID, path_id: UUID) -> UserPracticePathProgress:
        progress = (
            await self.db.execute(
                select(UserPracticePathProgress).where(
                    UserPracticePathProgress.user_id == user_id,
                    UserPracticePathProgress.path_id == path_id,
                )
            )
        ).scalar_one_or_none()
        if progress is None:
            progress = UserPracticePathProgress(user_id=user_id, path_id=path_id, status=ProgressStatus.IN_PROGRESS)
            self.db.add(progress)
            await self.db.flush()
        return progress

    async def _completed_task_ids(self, user_id: UUID, task_ids: list[UUID]) -> set[UUID]:
        if not task_ids:
            return set()
        rows = (
            await self.db.execute(
                select(UserProjectTaskProgress.task_id).where(
                    UserProjectTaskProgress.user_id == user_id,
                    UserProjectTaskProgress.task_id.in_(task_ids),
                    UserProjectTaskProgress.status == ProgressStatus.COMPLETED,
                )
            )
        ).scalars().all()
        return set(rows)

    async def _project_task_hrefs(self, tasks: list[ProjectTask]) -> dict[UUID, str | None]:
        coding_ids = [t.coding_problem_id for t in tasks if t.coding_problem_id]
        sql_ids = [t.sql_problem_id for t in tasks if t.sql_problem_id]
        topic_ids = [t.topic_id for t in tasks if t.topic_id]
        lesson_ids = [t.lesson_id for t in tasks if t.lesson_id]
        coding_slugs: dict[UUID, str] = {}
        sql_slugs: dict[UUID, str] = {}
        topic_slugs: dict[UUID, str] = {}
        if coding_ids:
            coding_slugs = {
                i: s for i, s in (await self.db.execute(select(CodingProblem.id, CodingProblem.slug).where(CodingProblem.id.in_(coding_ids)))).all()
            }
        if sql_ids:
            sql_slugs = {
                i: s for i, s in (await self.db.execute(select(SqlProblem.id, SqlProblem.slug).where(SqlProblem.id.in_(sql_ids)))).all()
            }
        if topic_ids:
            topic_slugs = {
                i: s for i, s in (await self.db.execute(select(Topic.id, Topic.slug).where(Topic.id.in_(topic_ids)))).all()
            }
        lesson_paths: dict[UUID, str] = {}
        if lesson_ids:
            lesson_paths = await self._lesson_href_map(lesson_ids)
        hrefs: dict[UUID, str | None] = {}
        for task in tasks:
            href = None
            if task.coding_problem_id and task.coding_problem_id in coding_slugs:
                href = f"/practice/dsa/{coding_slugs[task.coding_problem_id]}"
            elif task.sql_problem_id and task.sql_problem_id in sql_slugs:
                href = f"/practice/sql/{sql_slugs[task.sql_problem_id]}"
            elif task.topic_id and task.topic_id in topic_slugs:
                href = f"/practice/mcq?topic={topic_slugs[task.topic_id]}"
            elif task.lesson_id and task.lesson_id in lesson_paths:
                href = lesson_paths[task.lesson_id]
            elif _enum_value(task.task_type) == "sql":
                href = "/practice/sql"
            elif _enum_value(task.task_type) == "coding":
                href = "/practice/dsa"
            elif _enum_value(task.task_type) == "mcq":
                href = "/practice/mcq"
            hrefs[task.id] = href
        return hrefs

    async def _lesson_href_map(self, lesson_ids: list[UUID]) -> dict[UUID, str]:
        rows = (
            await self.db.execute(
                select(CourseLesson.id, Course.slug, CourseModule.slug, CourseLesson.slug)
                .join(CourseModule, CourseModule.id == CourseLesson.module_id)
                .join(Course, Course.id == CourseModule.course_id)
                .where(CourseLesson.id.in_(lesson_ids))
            )
        ).all()
        return {lid: lesson_href(c, m, l) for lid, c, m, l in rows}

    async def search(self, query: str, *, limit: int = 20) -> SearchResponse:
        term = (query or "").strip()
        if len(term) < 2:
            return SearchResponse(items=[])
        pattern = f"%{term.lower()}%"
        hits: list[SearchHit] = []

        paths = (
            await self.db.execute(
                select(PracticePath)
                .where(
                    PracticePath.is_active.is_(True),
                    or_(
                        func.lower(PracticePath.title).like(pattern),
                        func.lower(PracticePath.short_description).like(pattern),
                    ),
                )
                .order_by(PracticePath.sort_order)
                .limit(limit)
            )
        ).scalars().all()
        hits.extend(
            SearchHit(
                kind="path",
                slug=p.slug,
                title=p.title,
                subtitle=p.short_description or None,
                href=path_href(p),
            )
            for p in paths
        )

        courses = (
            await self.db.execute(
                select(Course)
                .where(
                    Course.is_published.is_(True),
                    or_(func.lower(Course.title).like(pattern), func.lower(Course.summary).like(pattern)),
                )
                .limit(limit)
            )
        ).scalars().all()
        hits.extend(
            SearchHit(
                kind="course",
                slug=c.slug,
                title=c.title,
                subtitle=c.summary[:140] or None,
                href=course_href(c.slug),
            )
            for c in courses
        )

        lesson_rows = (
            await self.db.execute(
                select(CourseLesson, CourseModule, Course)
                .join(CourseModule, CourseModule.id == CourseLesson.module_id)
                .join(Course, Course.id == CourseModule.course_id)
                .where(
                    CourseLesson.is_published.is_(True),
                    Course.is_published.is_(True),
                    func.lower(CourseLesson.title).like(pattern),
                )
                .limit(limit)
            )
        ).all()
        hits.extend(
            SearchHit(
                kind="lesson",
                slug=lesson.slug,
                title=lesson.title,
                subtitle=f"{course.title} - {module.title}",
                href=lesson_href(course.slug, module.slug, lesson.slug),
            )
            for lesson, module, course in lesson_rows
        )

        projects = (
            await self.db.execute(
                select(Project)
                .where(
                    Project.is_published.is_(True),
                    or_(
                        func.lower(Project.title).like(pattern),
                        func.lower(Project.short_description).like(pattern),
                    ),
                )
                .limit(limit)
            )
        ).scalars().all()
        hits.extend(
            SearchHit(
                kind="project",
                slug=p.slug,
                title=p.title,
                subtitle=p.short_description or None,
                href=project_href(p.slug),
            )
            for p in projects
        )

        return SearchResponse(items=hits[:limit])

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _path_card(self, path: PracticePath, item_count: int, percent: int) -> PracticePathCard:
        return PracticePathCard(
            id=path.id,
            slug=path.slug,
            title=path.title,
            short_description=path.short_description,
            path_type=_enum_value(path.path_type),
            difficulty=_enum_value(path.difficulty),
            language=path.language,
            estimated_minutes=path.estimated_minutes,
            availability=_enum_value(path.availability),
            is_featured=path.is_featured,
            external_route=path.external_route,
            item_count=item_count,
            progress_percent=percent,
        )

    def _nav_item(self, module: CourseModule, lesson: CourseLesson, status: ProgressStatus) -> LessonNavItem:
        return LessonNavItem(
            id=lesson.id,
            slug=lesson.slug,
            title=lesson.title,
            lesson_type=_enum_value(lesson.lesson_type),
            sort_order=lesson.sort_order,
            status=status.value,
            module_slug=module.slug,
            module_title=module.title,
        )

    async def _load_course(self, slug: str) -> Course:
        course = (
            await self.db.execute(
                select(Course)
                .options(selectinload(Course.modules).selectinload(CourseModule.lessons))
                .where(Course.slug == slug, Course.is_published.is_(True))
            )
        ).scalar_one_or_none()
        if course is None:
            raise AppException("Course not found", status_code=404)
        return course

    async def _load_lesson(self, lesson_id: UUID) -> CourseLesson:
        lesson = (
            await self.db.execute(
                select(CourseLesson)
                .options(
                    selectinload(CourseLesson.hints),
                    selectinload(CourseLesson.doubts),
                    selectinload(CourseLesson.resources),
                    selectinload(CourseLesson.steps),
                )
                .where(CourseLesson.id == lesson_id)
            )
        ).scalar_one_or_none()
        if lesson is None:
            raise AppException("Lesson not found", status_code=404)
        return lesson

    async def _get_lesson_or_404(self, lesson_id: UUID) -> CourseLesson:
        lesson = await self.db.get(CourseLesson, lesson_id)
        if lesson is None or not lesson.is_published:
            raise AppException("Lesson not found", status_code=404)
        return lesson

    def _ordered_lessons(self, course: Course) -> list[tuple[CourseModule, CourseLesson]]:
        ordered: list[tuple[CourseModule, CourseLesson]] = []
        for module in sorted(course.modules, key=lambda m: m.sort_order):
            for lesson in sorted(module.lessons, key=lambda x: x.sort_order):
                if lesson.is_published:
                    ordered.append((module, lesson))
        return ordered

    async def _course_lessons(self, course_id: UUID) -> list[tuple[CourseModule, CourseLesson]]:
        rows = (
            await self.db.execute(
                select(CourseModule, CourseLesson)
                .join(CourseLesson, CourseLesson.module_id == CourseModule.id)
                .where(CourseModule.course_id == course_id, CourseLesson.is_published.is_(True))
                .order_by(CourseModule.sort_order, CourseLesson.sort_order)
            )
        ).all()
        return [(module, lesson) for module, lesson in rows]

    async def _lesson_statuses(
        self,
        user_id: UUID,
        ordered: list[tuple[CourseModule, CourseLesson]],
    ) -> dict[UUID, ProgressStatus]:
        lesson_ids = [lesson.id for _, lesson in ordered]
        if not lesson_ids:
            return {}
        rows = (
            await self.db.execute(
                select(UserLessonProgress).where(
                    UserLessonProgress.user_id == user_id,
                    UserLessonProgress.lesson_id.in_(lesson_ids),
                )
            )
        ).scalars().all()
        stored = {row.lesson_id: row for row in rows}

        statuses: dict[UUID, ProgressStatus] = {}
        previous_complete = True
        for _module, lesson in ordered:
            progress = stored.get(lesson.id)
            if progress is not None and progress.status == ProgressStatus.COMPLETED:
                statuses[lesson.id] = ProgressStatus.COMPLETED
                previous_complete = True
                continue
            unlocked = lesson.unlock_mode == LessonUnlockMode.ALWAYS or previous_complete
            if not unlocked:
                statuses[lesson.id] = ProgressStatus.LOCKED
            elif progress is not None and progress.status == ProgressStatus.IN_PROGRESS:
                statuses[lesson.id] = ProgressStatus.IN_PROGRESS
            else:
                statuses[lesson.id] = ProgressStatus.NOT_STARTED
            previous_complete = False
        return statuses

    async def _course_percent(self, user_id: UUID, lesson_ids: list[UUID]) -> int:
        if not lesson_ids:
            return 0
        completed = int(
            await self.db.scalar(
                select(func.count())
                .select_from(UserLessonProgress)
                .where(
                    UserLessonProgress.user_id == user_id,
                    UserLessonProgress.lesson_id.in_(lesson_ids),
                    UserLessonProgress.status == ProgressStatus.COMPLETED,
                )
            )
            or 0
        )
        return int(round(completed * 100 / len(lesson_ids)))

    async def _get_lesson_progress(self, user_id: UUID, lesson_id: UUID) -> UserLessonProgress | None:
        return (
            await self.db.execute(
                select(UserLessonProgress).where(
                    UserLessonProgress.user_id == user_id,
                    UserLessonProgress.lesson_id == lesson_id,
                )
            )
        ).scalar_one_or_none()

    async def _get_course_progress(self, user_id: UUID, course_id: UUID) -> UserCourseProgress | None:
        return (
            await self.db.execute(
                select(UserCourseProgress).where(
                    UserCourseProgress.user_id == user_id,
                    UserCourseProgress.course_id == course_id,
                )
            )
        ).scalar_one_or_none()

    async def _touch_course_progress(
        self,
        user_id: UUID,
        lesson: CourseLesson,
        *,
        current_lesson_id: UUID | None = None,
    ) -> UserCourseProgress:
        module = await self.db.get(CourseModule, lesson.module_id)
        if module is None:
            raise AppException("Course module not found", status_code=404)
        progress = await self._get_course_progress(user_id, module.course_id)
        if progress is None:
            progress = UserCourseProgress(
                user_id=user_id,
                course_id=module.course_id,
                status=ProgressStatus.IN_PROGRESS,
            )
            self.db.add(progress)
        if progress.status == ProgressStatus.NOT_STARTED:
            progress.status = ProgressStatus.IN_PROGRESS
        if current_lesson_id is not None:
            progress.current_lesson_id = current_lesson_id
        progress.last_activity_at = _now()
        await self.db.flush()
        return progress

    async def _course_context(
        self, lesson: CourseLesson
    ) -> tuple[Course, list[tuple[CourseModule, CourseLesson]], str | None]:
        module = await self.db.get(CourseModule, lesson.module_id)
        if module is None:
            raise AppException("Course module not found", status_code=404)
        course = await self.db.get(Course, module.course_id)
        if course is None:
            raise AppException("Course not found", status_code=404)
        ordered = await self._course_lessons(course.id)
        next_href = None
        for i, (_mod, lsn) in enumerate(ordered):
            if lsn.id == lesson.id and i + 1 < len(ordered):
                next_mod, next_lesson = ordered[i + 1]
                next_href = lesson_href(course.slug, next_mod.slug, next_lesson.slug)
                break
        return course, ordered, next_href

    async def _locate_lesson(self, lesson_id: UUID) -> tuple[Course, CourseModule, CourseLesson] | None:
        row = (
            await self.db.execute(
                select(Course, CourseModule, CourseLesson)
                .join(CourseModule, CourseModule.course_id == Course.id)
                .join(CourseLesson, CourseLesson.module_id == CourseModule.id)
                .where(CourseLesson.id == lesson_id)
            )
        ).first()
        if row is None:
            return None
        return row[0], row[1], row[2]

    async def _has_successful_attempt(self, user_id: UUID, lesson_id: UUID) -> bool:
        count = await self.db.scalar(
            select(func.count())
            .select_from(LessonAttempt)
            .where(
                LessonAttempt.user_id == user_id,
                LessonAttempt.lesson_id == lesson_id,
                LessonAttempt.is_correct.is_(True),
            )
        )
        return bool(count)

    async def _path_item_counts(self) -> dict[UUID, int]:
        rows = (
            await self.db.execute(
                select(PracticePathSection.path_id, func.count(PracticePathItem.id))
                .join(PracticePathItem, PracticePathItem.section_id == PracticePathSection.id)
                .group_by(PracticePathSection.path_id)
            )
        ).all()
        return {path_id: int(count) for path_id, count in rows}

    async def _path_progress_map(self, user_id: UUID) -> dict[UUID, int]:
        rows = (
            await self.db.execute(
                select(UserPracticePathProgress).where(UserPracticePathProgress.user_id == user_id)
            )
        ).scalars().all()
        return {row.path_id: row.percent for row in rows}

    async def _project_task_counts(self) -> dict[UUID, int]:
        from app.models.learn import ProjectTask

        rows = (
            await self.db.execute(
                select(ProjectModule.project_id, func.count(ProjectTask.id))
                .join(ProjectTask, ProjectTask.module_id == ProjectModule.id)
                .group_by(ProjectModule.project_id)
            )
        ).all()
        return {project_id: int(count) for project_id, count in rows}

    async def _recently_practiced(self, user: User) -> list[ContinueLearningItem]:
        rows = (
            await self.db.execute(
                select(UserLessonProgress, CourseLesson, CourseModule, Course)
                .join(CourseLesson, CourseLesson.id == UserLessonProgress.lesson_id)
                .join(CourseModule, CourseModule.id == CourseLesson.module_id)
                .join(Course, Course.id == CourseModule.course_id)
                .where(UserLessonProgress.user_id == user.id)
                .order_by(UserLessonProgress.last_activity_at.desc().nulls_last())
                .limit(5)
            )
        ).all()
        return [
            ContinueLearningItem(
                kind="lesson",
                title=lesson.title,
                subtitle=f"{course.title} - {module.title}",
                progress_percent=100 if progress.status == ProgressStatus.COMPLETED else 50,
                href=lesson_href(course.slug, module.slug, lesson.slug),
                last_activity_at=progress.last_activity_at,
            )
            for progress, lesson, module, course in rows
        ]

    async def _item_hrefs(self, items: list[PracticePathItem]) -> dict[UUID, str | None]:
        course_ids = {i.course_id for i in items if i.course_id}
        lesson_ids = {i.lesson_id for i in items if i.lesson_id}
        project_ids = {i.project_id for i in items if i.project_id}
        coding_ids = {i.coding_problem_id for i in items if i.coding_problem_id}
        sql_ids = {i.sql_problem_id for i in items if i.sql_problem_id}
        topic_ids = {i.topic_id for i in items if i.topic_id}

        course_slugs: dict[UUID, str] = {}
        if course_ids:
            course_slugs = {
                cid: slug
                for cid, slug in (
                    await self.db.execute(select(Course.id, Course.slug).where(Course.id.in_(course_ids)))
                ).all()
            }

        lesson_paths: dict[UUID, str] = {}
        if lesson_ids:
            rows = (
                await self.db.execute(
                    select(CourseLesson.id, CourseLesson.slug, CourseModule.slug, Course.slug)
                    .join(CourseModule, CourseModule.id == CourseLesson.module_id)
                    .join(Course, Course.id == CourseModule.course_id)
                    .where(CourseLesson.id.in_(lesson_ids))
                )
            ).all()
            lesson_paths = {
                lid: lesson_href(c_slug, m_slug, l_slug) for lid, l_slug, m_slug, c_slug in rows
            }

        project_slugs: dict[UUID, str] = {}
        if project_ids:
            project_slugs = {
                pid: slug
                for pid, slug in (
                    await self.db.execute(select(Project.id, Project.slug).where(Project.id.in_(project_ids)))
                ).all()
            }

        coding_slugs: dict[UUID, str] = {}
        if coding_ids:
            coding_slugs = {
                cid: slug
                for cid, slug in (
                    await self.db.execute(
                        select(CodingProblem.id, CodingProblem.slug).where(CodingProblem.id.in_(coding_ids))
                    )
                ).all()
            }

        sql_slugs: dict[UUID, str] = {}
        if sql_ids:
            sql_slugs = {
                sid: slug
                for sid, slug in (
                    await self.db.execute(
                        select(SqlProblem.id, SqlProblem.slug).where(SqlProblem.id.in_(sql_ids))
                    )
                ).all()
            }

        topic_slugs: dict[UUID, str] = {}
        if topic_ids:
            topic_slugs = {
                tid: slug
                for tid, slug in (
                    await self.db.execute(select(Topic.id, Topic.slug).where(Topic.id.in_(topic_ids)))
                ).all()
            }

        hrefs: dict[UUID, str | None] = {}
        for item in items:
            href: str | None = item.external_route
            if item.item_type == PracticePathItemType.COURSE and item.course_id:
                slug = course_slugs.get(item.course_id)
                href = course_href(slug) if slug else href
            elif item.item_type == PracticePathItemType.LESSON and item.lesson_id:
                href = lesson_paths.get(item.lesson_id) or href
            elif item.item_type == PracticePathItemType.PROJECT and item.project_id:
                slug = project_slugs.get(item.project_id)
                href = project_href(slug) if slug else href
            elif item.item_type == PracticePathItemType.CODING_PROBLEM and item.coding_problem_id:
                slug = coding_slugs.get(item.coding_problem_id)
                href = f"/practice/dsa/{slug}" if slug else href
            elif item.item_type == PracticePathItemType.SQL_PROBLEM and item.sql_problem_id:
                slug = sql_slugs.get(item.sql_problem_id)
                href = f"/practice/sql/{slug}" if slug else href
            elif item.item_type == PracticePathItemType.MCQ_TOPIC and item.topic_id:
                slug = topic_slugs.get(item.topic_id)
                href = f"/practice/mcq?topic={slug}" if slug else href
            hrefs[item.id] = href
        return hrefs


def _coerce(enum_cls, value: Any, field: str):
    if value is None:
        return None
    try:
        return enum_cls(value)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_cls)
        raise AppException(f"Invalid {field}: expected one of {allowed}", status_code=400) from exc


class LearnAdminService:
    """Authoring surface for Practice Hub paths, courses, modules, and lessons."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_paths(self) -> list[dict]:
        paths = (
            await self.db.execute(select(PracticePath).order_by(PracticePath.sort_order, PracticePath.title))
        ).scalars().all()
        return [self._path_dict(p) for p in paths]

    async def create_path(self, payload: PracticePathAdminIn) -> dict:
        existing = await self.db.scalar(select(PracticePath.id).where(PracticePath.slug == payload.slug))
        if existing is not None:
            raise AppException("A practice path with this slug already exists", status_code=400)
        path = PracticePath(
            slug=payload.slug,
            title=payload.title,
            short_description=payload.short_description,
            description=payload.description,
            path_type=_coerce(PracticePathType, payload.path_type, "path_type"),
            difficulty=_coerce(PracticePathDifficulty, payload.difficulty, "difficulty"),
            language=payload.language,
            estimated_minutes=payload.estimated_minutes,
            availability=_coerce(PathAvailability, payload.availability, "availability"),
            is_active=payload.is_active,
            is_featured=payload.is_featured,
            sort_order=payload.sort_order,
            external_route=payload.external_route,
        )
        self.db.add(path)
        await self.db.commit()
        await self.db.refresh(path)
        return self._path_dict(path)

    async def update_path(self, path_id: UUID, payload: dict[str, Any]) -> dict:
        path = await self.db.get(PracticePath, path_id)
        if path is None:
            raise AppException("Practice path not found", status_code=404)
        enum_fields = {
            "path_type": PracticePathType,
            "difficulty": PracticePathDifficulty,
            "availability": PathAvailability,
        }
        allowed = {
            "slug",
            "title",
            "short_description",
            "description",
            "language",
            "estimated_minutes",
            "is_active",
            "is_featured",
            "sort_order",
            "external_route",
            *enum_fields,
        }
        for key, value in payload.items():
            if key not in allowed:
                continue
            if key in enum_fields:
                value = _coerce(enum_fields[key], value, key)
            setattr(path, key, value)
        await self.db.commit()
        await self.db.refresh(path)
        return self._path_dict(path)

    async def list_courses(self) -> list[dict]:
        courses = (
            await self.db.execute(select(Course).order_by(Course.sort_order, Course.title))
        ).scalars().all()
        out = []
        for course in courses:
            lesson_count = int(
                await self.db.scalar(
                    select(func.count())
                    .select_from(CourseLesson)
                    .join(CourseModule, CourseModule.id == CourseLesson.module_id)
                    .where(CourseModule.course_id == course.id)
                )
                or 0
            )
            out.append({**self._course_dict(course), "lesson_count": lesson_count})
        return out

    async def create_course(self, payload: CourseAdminIn) -> dict:
        existing = await self.db.scalar(select(Course.id).where(Course.slug == payload.slug))
        if existing is not None:
            raise AppException("A course with this slug already exists", status_code=400)
        course = Course(
            slug=payload.slug,
            title=payload.title,
            summary=payload.summary,
            level=_coerce(CourseLevel, payload.level, "level"),
            primary_language_key=payload.primary_language_key,
            estimated_minutes=payload.estimated_minutes,
            is_published=payload.is_published,
            is_featured=payload.is_featured,
            sort_order=payload.sort_order,
        )
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)
        return self._course_dict(course)

    async def update_course(self, course_id: UUID, payload: dict[str, Any]) -> dict:
        course = await self.db.get(Course, course_id)
        if course is None:
            raise AppException("Course not found", status_code=404)
        allowed = {
            "slug",
            "title",
            "summary",
            "level",
            "primary_language_key",
            "estimated_minutes",
            "is_published",
            "is_featured",
            "sort_order",
            "certificate_enabled",
        }
        for key, value in payload.items():
            if key not in allowed:
                continue
            if key == "level":
                value = _coerce(CourseLevel, value, "level")
            setattr(course, key, value)
        await self.db.commit()
        await self.db.refresh(course)
        return self._course_dict(course)

    async def create_module(self, course_id: UUID, payload: ModuleAdminIn) -> dict:
        course = await self.db.get(Course, course_id)
        if course is None:
            raise AppException("Course not found", status_code=404)
        duplicate = await self.db.scalar(
            select(CourseModule.id).where(
                CourseModule.course_id == course_id, CourseModule.slug == payload.slug
            )
        )
        if duplicate is not None:
            raise AppException("A module with this slug already exists in the course", status_code=400)
        module = CourseModule(
            course_id=course_id,
            slug=payload.slug,
            title=payload.title,
            sort_order=payload.sort_order,
            summary=payload.summary,
        )
        self.db.add(module)
        await self.db.commit()
        await self.db.refresh(module)
        return self._module_dict(module)

    async def create_lesson(self, module_id: UUID, payload: LessonAdminIn) -> dict:
        module = await self.db.get(CourseModule, module_id)
        if module is None:
            raise AppException("Course module not found", status_code=404)
        duplicate = await self.db.scalar(
            select(CourseLesson.id).where(
                CourseLesson.module_id == module_id, CourseLesson.slug == payload.slug
            )
        )
        if duplicate is not None:
            raise AppException("A lesson with this slug already exists in the module", status_code=400)
        lesson = CourseLesson(
            module_id=module_id,
            slug=payload.slug,
            title=payload.title,
            sort_order=payload.sort_order,
            lesson_type=_coerce(LessonType, payload.lesson_type, "lesson_type"),
            statement_json=payload.statement_json,
            starter_code=payload.starter_code,
            solution_json=payload.solution_json,
            solution_reveal=_coerce(SolutionRevealPolicy, payload.solution_reveal, "solution_reveal"),
            unlock_mode=_coerce(LessonUnlockMode, payload.unlock_mode, "unlock_mode"),
            coding_problem_id=payload.coding_problem_id,
            question_id=payload.question_id,
            is_published=payload.is_published,
            completion_requires_submit=payload.completion_requires_submit,
            estimated_minutes=payload.estimated_minutes,
        )
        self.db.add(lesson)
        await self.db.flush()
        for index, hint in enumerate(payload.hints):
            self.db.add(
                LessonHint(
                    lesson_id=lesson.id,
                    hint_text=str(hint.get("hint_text", "")),
                    sort_order=int(hint.get("sort_order", index)),
                    unlock_after_attempts=int(hint.get("unlock_after_attempts", 0)),
                )
            )
        for index, doubt in enumerate(payload.doubts):
            self.db.add(
                LessonDoubt(
                    lesson_id=lesson.id,
                    question=str(doubt.get("question", "")),
                    answer=str(doubt.get("answer", "")),
                    sort_order=int(doubt.get("sort_order", index)),
                )
            )
        await self.db.commit()
        await self.db.refresh(lesson)
        return self._lesson_dict(lesson)

    async def update_lesson(self, lesson_id: UUID, payload: dict[str, Any]) -> dict:
        lesson = await self.db.get(CourseLesson, lesson_id)
        if lesson is None:
            raise AppException("Lesson not found", status_code=404)
        enum_fields = {
            "lesson_type": LessonType,
            "solution_reveal": SolutionRevealPolicy,
            "unlock_mode": LessonUnlockMode,
        }
        allowed = {
            "slug",
            "title",
            "sort_order",
            "statement_json",
            "starter_code",
            "solution_json",
            "coding_problem_id",
            "question_id",
            "is_published",
            "completion_requires_submit",
            "estimated_minutes",
            *enum_fields,
        }
        for key, value in payload.items():
            if key not in allowed:
                continue
            if key in enum_fields:
                value = _coerce(enum_fields[key], value, key)
            setattr(lesson, key, value)
        await self.db.commit()
        await self.db.refresh(lesson)
        return self._lesson_dict(lesson)

    async def list_projects(self) -> list[dict]:
        projects = (
            await self.db.execute(select(Project).order_by(Project.sort_order, Project.title))
        ).scalars().all()
        return [self._project_dict(p) for p in projects]

    async def create_project(self, payload: ProjectAdminIn) -> dict:
        if await self.db.scalar(select(Project.id).where(Project.slug == payload.slug)):
            raise AppException("A project with this slug already exists", status_code=400)
        project = Project(
            slug=payload.slug,
            title=payload.title,
            short_description=payload.short_description,
            description=payload.description,
            difficulty=_coerce(PracticePathDifficulty, payload.difficulty, "difficulty"),
            technology=payload.technology,
            category_key=payload.category_key,
            estimated_minutes=payload.estimated_minutes,
            is_published=payload.is_published,
            is_featured=payload.is_featured,
            sort_order=payload.sort_order,
            availability=_coerce(PathAvailability, payload.availability, "availability"),
            prerequisites=payload.prerequisites,
            skills=payload.skills,
            final_objective=payload.final_objective,
            reference_json=payload.reference_json,
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return self._project_dict(project)

    async def update_project(self, project_id: UUID, payload: dict[str, Any]) -> dict:
        project = await self.db.get(Project, project_id)
        if project is None:
            raise AppException("Project not found", status_code=404)
        enum_fields = {"difficulty": PracticePathDifficulty, "availability": PathAvailability}
        allowed = {
            "slug",
            "title",
            "short_description",
            "description",
            "technology",
            "category_key",
            "estimated_minutes",
            "is_published",
            "is_featured",
            "sort_order",
            "prerequisites",
            "skills",
            "final_objective",
            "reference_json",
            *enum_fields,
        }
        for key, value in payload.items():
            if key not in allowed:
                continue
            if key in enum_fields:
                value = _coerce(enum_fields[key], value, key)
            setattr(project, key, value)
        await self.db.commit()
        await self.db.refresh(project)
        return self._project_dict(project)

    async def create_project_module(self, project_id: UUID, payload: ProjectModuleAdminIn) -> dict:
        project = await self.db.get(Project, project_id)
        if project is None:
            raise AppException("Project not found", status_code=404)
        module = ProjectModule(project_id=project.id, title=payload.title, sort_order=payload.sort_order)
        self.db.add(module)
        await self.db.commit()
        await self.db.refresh(module)
        return {"id": str(module.id), "title": module.title, "sort_order": module.sort_order}

    async def create_project_task(self, module_id: UUID, payload: ProjectTaskAdminIn) -> dict:
        module = await self.db.get(ProjectModule, module_id)
        if module is None:
            raise AppException("Project module not found", status_code=404)
        task = ProjectTask(
            module_id=module.id,
            title=payload.title,
            sort_order=payload.sort_order,
            task_type=_coerce(ProjectTaskType, payload.task_type, "task_type"),
            summary=payload.summary,
            coding_problem_id=payload.coding_problem_id,
            sql_problem_id=payload.sql_problem_id,
            topic_id=payload.topic_id,
            lesson_id=payload.lesson_id,
            question_id=payload.question_id,
            body_json=payload.body_json,
            checklist_json=payload.checklist_json,
            reference_json=payload.reference_json,
            estimated_minutes=payload.estimated_minutes,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return self._task_dict(task)

    async def update_project_task(self, task_id: UUID, payload: dict[str, Any]) -> dict:
        task = await self.db.get(ProjectTask, task_id)
        if task is None:
            raise AppException("Project task not found", status_code=404)
        enum_fields = {"task_type": ProjectTaskType}
        allowed = {
            "title",
            "sort_order",
            "summary",
            "coding_problem_id",
            "sql_problem_id",
            "topic_id",
            "lesson_id",
            "question_id",
            "body_json",
            "checklist_json",
            "reference_json",
            "estimated_minutes",
            *enum_fields,
        }
        for key, value in payload.items():
            if key not in allowed:
                continue
            if key in enum_fields:
                value = _coerce(enum_fields[key], value, key)
            setattr(task, key, value)
        await self.db.commit()
        await self.db.refresh(task)
        return self._task_dict(task)

    async def add_path_section(self, path_id: UUID, payload: PracticePathSectionAdminIn) -> dict:
        path = await self.db.get(PracticePath, path_id)
        if path is None:
            raise AppException("Practice path not found", status_code=404)
        section = PracticePathSection(
            path_id=path.id,
            title=payload.title,
            section_key=payload.section_key,
            sort_order=payload.sort_order,
        )
        self.db.add(section)
        await self.db.commit()
        await self.db.refresh(section)
        return {"id": str(section.id), "title": section.title, "sort_order": section.sort_order}

    async def add_path_item(self, section_id: UUID, payload: PracticePathItemAdminIn) -> dict:
        section = await self.db.get(PracticePathSection, section_id)
        if section is None:
            raise AppException("Path section not found", status_code=404)
        item = PracticePathItem(
            section_id=section.id,
            item_type=_coerce(PracticePathItemType, payload.item_type, "item_type"),
            title=payload.title,
            sort_order=payload.sort_order,
            coding_problem_id=payload.coding_problem_id,
            sql_problem_id=payload.sql_problem_id,
            topic_id=payload.topic_id,
            course_id=payload.course_id,
            lesson_id=payload.lesson_id,
            project_id=payload.project_id,
            external_route=payload.external_route,
            is_preview=payload.is_preview,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return {"id": str(item.id), "item_type": _enum_value(item.item_type), "title": item.title}

    def _project_dict(self, project: Project) -> dict:
        return {
            "id": str(project.id),
            "slug": project.slug,
            "title": project.title,
            "short_description": project.short_description,
            "description": project.description,
            "difficulty": _enum_value(project.difficulty),
            "technology": project.technology,
            "category_key": project.category_key,
            "estimated_minutes": project.estimated_minutes,
            "is_published": project.is_published,
            "is_featured": project.is_featured,
            "availability": _enum_value(project.availability),
            "prerequisites": project.prerequisites or [],
            "skills": project.skills or [],
            "final_objective": project.final_objective,
        }

    def _task_dict(self, task: ProjectTask) -> dict:
        return {
            "id": str(task.id),
            "title": task.title,
            "sort_order": task.sort_order,
            "task_type": _enum_value(task.task_type),
            "summary": task.summary,
            "coding_problem_id": str(task.coding_problem_id) if task.coding_problem_id else None,
            "sql_problem_id": str(task.sql_problem_id) if task.sql_problem_id else None,
            "topic_id": str(task.topic_id) if task.topic_id else None,
        }

    def _path_dict(self, path: PracticePath) -> dict:
        return {
            "id": str(path.id),
            "slug": path.slug,
            "title": path.title,
            "short_description": path.short_description,
            "description": path.description,
            "path_type": _enum_value(path.path_type),
            "difficulty": _enum_value(path.difficulty),
            "language": path.language,
            "estimated_minutes": path.estimated_minutes,
            "availability": _enum_value(path.availability),
            "is_active": path.is_active,
            "is_featured": path.is_featured,
            "sort_order": path.sort_order,
            "external_route": path.external_route,
        }

    def _course_dict(self, course: Course) -> dict:
        return {
            "id": str(course.id),
            "slug": course.slug,
            "title": course.title,
            "summary": course.summary,
            "level": _enum_value(course.level),
            "primary_language_key": course.primary_language_key,
            "estimated_minutes": course.estimated_minutes,
            "is_published": course.is_published,
            "is_featured": course.is_featured,
            "sort_order": course.sort_order,
            "certificate_enabled": course.certificate_enabled,
        }

    def _module_dict(self, module: CourseModule) -> dict:
        return {
            "id": str(module.id),
            "course_id": str(module.course_id),
            "slug": module.slug,
            "title": module.title,
            "sort_order": module.sort_order,
            "summary": module.summary,
        }

    def _lesson_dict(self, lesson: CourseLesson) -> dict:
        return {
            "id": str(lesson.id),
            "module_id": str(lesson.module_id),
            "slug": lesson.slug,
            "title": lesson.title,
            "sort_order": lesson.sort_order,
            "lesson_type": _enum_value(lesson.lesson_type),
            "statement_json": lesson.statement_json,
            "starter_code": lesson.starter_code,
            "solution_json": lesson.solution_json,
            "solution_reveal": _enum_value(lesson.solution_reveal),
            "unlock_mode": _enum_value(lesson.unlock_mode),
            "coding_problem_id": str(lesson.coding_problem_id) if lesson.coding_problem_id else None,
            "question_id": str(lesson.question_id) if lesson.question_id else None,
            "is_published": lesson.is_published,
            "completion_requires_submit": lesson.completion_requires_submit,
            "estimated_minutes": lesson.estimated_minutes,
        }
