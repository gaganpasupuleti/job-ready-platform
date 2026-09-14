"""Student materials, assignments, and quiz packs."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.version_snapshots import assignment_brief_snapshot
from app.core.deps import get_current_admin, get_current_user
from app.core.exceptions import AppException
from app.db.session import get_db
from app.models.enums import PracticeMode, SessionStatus
from app.models.practice import PracticeSession, PracticeSessionQuestion
from app.models.question import Question
from app.models.sql_practice import SqlProblemProgress
from app.models.sql_enums import SqlProgressStatus
from app.models.studio import (
    Assignment,
    AssignmentReview,
    AssignmentSubmission,
    ContentPack,
    ContentPackQuestion,
    LearningMaterial,
    LearningMaterialRead,
)
from app.models.user import User
from app.services.job_taxonomy import JOB_FAMILIES, family_label
from app.services.practice_service import question_snapshot

router = APIRouter()
CONTENT_ROOT = Path(__file__).resolve().parents[3] / "content" / "batches"


class DraftIn(BaseModel):
    answer_text: str = ""
    evidence_url: str | None = None


class ReviewIn(BaseModel):
    feedback: str = Field(min_length=1)
    grade: str | None = None
    rubric_notes: list[str] = []


def _family_filter(column, family: str | None):
    if not family:
        return True
    return column.contains([family])


@router.get("/studio/catalog")
async def catalog(
    family: str | None = None,
    kind: str | None = None,
    level: str | None = None,
    skill: str | None = None,
    progress: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    published_materials = (await db.execute(select(LearningMaterial).where(LearningMaterial.is_published.is_(True)))).scalars().all()
    published_assignments = (await db.execute(select(Assignment).where(Assignment.is_published.is_(True)))).scalars().all()
    published_packs = (await db.execute(select(ContentPack).where(ContentPack.is_published.is_(True)))).scalars().all()
    family_counts: dict[str, int] = {row[0]: 0 for row in JOB_FAMILIES if row[0] != "other-review"}
    skill_counts: dict[str, int] = {}
    level_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    for row in published_materials:
        level_counts[row.level] = level_counts.get(row.level, 0) + 1
        kind_counts[row.kind] = kind_counts.get(row.kind, 0) + 1
        for tag in row.skill_tags or []:
            skill_counts[tag] = skill_counts.get(tag, 0) + 1
    for row in published_materials + published_assignments + published_packs:
        for item_family in row.families or []:
            if item_family in family_counts:
                family_counts[item_family] += 1
    materials = list(published_materials)
    assignments = list(published_assignments)
    packs = list(published_packs)
    if family:
        materials = [row for row in materials if family in (row.families or [])]
        assignments = [row for row in assignments if family in (row.families or [])]
        packs = [row for row in packs if family in (row.families or [])]
    if kind:
        materials = [row for row in materials if row.kind == kind]
    if level:
        materials = [row for row in materials if row.level == level]
    if skill:
        materials = [row for row in materials if skill in (row.skill_tags or [])]
        assignments = [row for row in assignments if skill in (row.skill_tags or [])]
        packs = [row for row in packs if skill in (row.skill_tags or [])]
    reads = set(
        (await db.execute(select(LearningMaterialRead.material_id).where(LearningMaterialRead.user_id == user.id))).scalars().all()
    )
    drafts = (
        await db.execute(
            select(AssignmentSubmission).where(AssignmentSubmission.user_id == user.id, AssignmentSubmission.status == "draft")
        )
    ).scalars().all()
    draft_ids = {row.assignment_id for row in drafts}
    if progress == "in_progress":
        materials = [row for row in materials if row.id in reads]
        assignments = [row for row in assignments if row.id in draft_ids]
    materials = sorted(materials, key=lambda row: row.updated_at or row.created_at, reverse=True)
    return {
        "families": [{"id": row[0], "label": family_label(row[0]), "count": family_counts[row[0]]} for row in JOB_FAMILIES if row[0] != "other-review"],
        "skills": [{"id": key, "count": skill_counts[key]} for key in sorted(skill_counts)],
        "levels": [{"id": key, "count": level_counts[key]} for key in sorted(level_counts)],
        "kinds": [{"id": key, "count": kind_counts[key]} for key in sorted(kind_counts)],
        "materials": [
            {"key": row.content_key, "title": row.title, "kind": row.kind, "level": row.level, "minutes": row.estimated_minutes, "families": row.families, "skills": row.skill_tags, "read": row.id in reads, "updated_at": row.updated_at.isoformat() if row.updated_at else None}
            for row in materials
        ],
        "assignments": [
            {"key": row.content_key, "title": row.title, "mode": row.submission_mode, "families": row.families, "in_progress": row.id in draft_ids}
            for row in assignments
        ],
        "packs": [{"key": row.content_key, "title": row.title, "kind": row.kind, "questions": row.question_count, "families": row.families} for row in packs],
    }


@router.get("/studio/materials/{key}")
async def material_detail(key: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    row = (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key == key, LearningMaterial.is_published.is_(True)))).scalar_one_or_none()
    if row is None:
        raise AppException("Material not found", status_code=404)
    read = (
        await db.execute(select(LearningMaterialRead).where(LearningMaterialRead.user_id == user.id, LearningMaterialRead.material_id == row.id))
    ).scalar_one_or_none()
    return {
        "key": row.content_key,
        "title": row.title,
        "summary": row.summary,
        "kind": row.kind,
        "level": row.level,
        "audience": row.audience,
        "minutes": row.estimated_minutes,
        "objectives": row.objectives,
        "prerequisites": row.prerequisites,
        "body_md": row.body_md,
        "examples": row.examples,
        "exercises": row.exercises,
        "summary_md": row.summary_md,
        "sources": row.sources,
        "families": row.families,
        "skills": row.skill_tags,
        "version": row.version,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "has_download": bool(row.download_relpath),
        "read": read is not None,
        "related_pack": _related_pack(row.families),
    }


def _related_pack(families: list) -> str | None:
    mapping = {"data-analyst": "pack-data-analyst", "data-engineer": "pack-data-engineer", "python-dev": "pack-python-dev"}
    for family in families or []:
        if family in mapping:
            return mapping[family]
    return None


@router.post("/studio/materials/{key}/read")
async def mark_read(key: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    row = (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key == key, LearningMaterial.is_published.is_(True)))).scalar_one_or_none()
    if row is None:
        raise AppException("Material not found", status_code=404)
    existing = (
        await db.execute(select(LearningMaterialRead).where(LearningMaterialRead.user_id == user.id, LearningMaterialRead.material_id == row.id))
    ).scalar_one_or_none()
    if existing is None:
        db.add(LearningMaterialRead(user_id=user.id, material_id=row.id, read_at=datetime.now(UTC)))
        await db.commit()
    return {"read": True, "competence": False}


@router.get("/studio/materials/{key}/download")
async def download_material(key: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key == key, LearningMaterial.is_published.is_(True)))).scalar_one_or_none()
    if row is None or not row.download_relpath:
        raise AppException("No file is available for this material", status_code=404)
    path = None
    root = CONTENT_ROOT.resolve()
    for candidate in CONTENT_ROOT.glob(f"*/{row.download_relpath}"):
        resolved = candidate.resolve()
        if str(resolved).startswith(str(root)) and resolved.is_file():
            path = resolved
            break
    if path is None:
        raise AppException("No file is available for this material", status_code=404)
    return FileResponse(path, media_type="text/markdown", filename=path.name)


@router.get("/studio/assignments/{key}")
async def assignment_detail(key: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    row = (await db.execute(select(Assignment).where(Assignment.content_key == key, Assignment.is_published.is_(True)))).scalar_one_or_none()
    if row is None:
        raise AppException("Assignment not found", status_code=404)
    mine = (
        await db.execute(
            select(AssignmentSubmission).where(AssignmentSubmission.assignment_id == row.id, AssignmentSubmission.user_id == user.id).order_by(AssignmentSubmission.attempt_number)
        )
    ).scalars().all()
    reviews = []
    if mine:
        reviews = (
            await db.execute(select(AssignmentReview).where(AssignmentReview.submission_id.in_([item.id for item in mine])))
        ).scalars().all()
    return {
        "key": row.content_key,
        "title": row.title,
        "goal": row.goal,
        "brief_md": row.brief_md,
        "requirements": row.requirements,
        "deliverables": row.deliverables,
        "hints": row.hints,
        "prerequisites": row.prerequisites,
        "rubric": row.rubric,
        "mode": row.submission_mode,
        "minutes": row.estimated_minutes,
        "due_at": None,
        "families": row.families,
        "version": row.version,
        "sql_problem_slug": row.sql_problem_slug,
        "local_python": row.submission_mode == "local_python",
        "submissions": [_submission_out(item, reviews) for item in mine],
    }


def _submission_out(item: AssignmentSubmission, reviews: list[AssignmentReview]) -> dict:
    matched = [review for review in reviews if review.submission_id == item.id]
    return {
        "id": str(item.id),
        "attempt": item.attempt_number,
        "status": item.status,
        "version": item.assignment_version,
        "answer_text": item.answer_text,
        "evidence_url": item.evidence_url,
        "brief": (item.brief_snapshot or {}).get("brief_md"),
        "rubric": (item.brief_snapshot or {}).get("rubric"),
        "submitted_at": item.submitted_at.isoformat() if item.submitted_at else None,
        "reviews": [
            {
                "feedback": review.feedback,
                "grade": review.grade,
                "version": review.submission_version,
                "reviewed_at": review.reviewed_at.isoformat(),
            }
            for review in matched
        ],
    }


async def _latest(db: AsyncSession, assignment_id, user_id: UUID) -> AssignmentSubmission | None:
    return (
        await db.execute(
            select(AssignmentSubmission)
            .where(AssignmentSubmission.assignment_id == assignment_id, AssignmentSubmission.user_id == user_id)
            .order_by(AssignmentSubmission.attempt_number.desc())
        )
    ).scalars().first()


@router.post("/studio/assignments/{key}/draft")
async def save_draft(key: str, payload: DraftIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    row = await _assignment(db, key)
    _check_url(payload.evidence_url)
    current = await _latest(db, row.id, user.id)
    if current and current.status == "draft":
        current.answer_text = payload.answer_text
        current.evidence_url = payload.evidence_url
        if not current.brief_snapshot:
            current.brief_snapshot = assignment_brief_snapshot(row)
            current.assignment_version = row.version
    else:
        attempt = 1 if current is None else current.attempt_number + 1
        snapshot = assignment_brief_snapshot(row)
        db.add(
            AssignmentSubmission(
                assignment_id=row.id,
                user_id=user.id,
                assignment_version=snapshot["version"],
                attempt_number=attempt,
                status="draft",
                answer_text=payload.answer_text,
                evidence_url=payload.evidence_url,
                brief_snapshot=snapshot,
            )
        )
    await db.commit()
    return {"status": "draft"}


@router.post("/studio/assignments/{key}/submit")
async def submit_assignment(key: str, payload: DraftIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    row = await _assignment(db, key)
    _check_url(payload.evidence_url)
    if row.submission_mode == "sql_evidence" and row.sql_problem_slug:
        from app.models.sql_practice import SqlProblem

        problem = (await db.execute(select(SqlProblem).where(SqlProblem.slug == row.sql_problem_slug))).scalar_one_or_none()
        if problem is None:
            raise AppException("Linked SQL problem is not available", status_code=409)
        solved = (
            await db.execute(
                select(SqlProblemProgress).where(
                    SqlProblemProgress.user_id == user.id,
                    SqlProblemProgress.problem_id == problem.id,
                    SqlProblemProgress.status == SqlProgressStatus.SOLVED,
                )
            )
        ).scalar_one_or_none()
        recorded = solved.content_version if solved is not None and solved.content_version is not None else 1
        if solved is None or recorded != (problem.content_version or 1):
            raise AppException("Submit the linked SQL problem in SQL Studio before this assignment can be filed.", status_code=409)
    current = await _latest(db, row.id, user.id)
    if current is None or current.status != "draft":
        attempt = 1 if current is None else current.attempt_number + 1
        snapshot = assignment_brief_snapshot(row)
        current = AssignmentSubmission(
            assignment_id=row.id,
            user_id=user.id,
            assignment_version=snapshot["version"],
            attempt_number=attempt,
            status="draft",
            answer_text=payload.answer_text,
            evidence_url=payload.evidence_url,
            brief_snapshot=snapshot,
        )
        db.add(current)
    if not current.brief_snapshot:
        current.brief_snapshot = assignment_brief_snapshot(row)
    current.answer_text = payload.answer_text
    current.evidence_url = payload.evidence_url
    current.status = "submitted"
    current.submitted_at = datetime.now(UTC)
    current.assignment_version = current.brief_snapshot.get("version", row.version)
    await db.commit()
    return {"status": "submitted", "version": current.assignment_version}


@router.post("/studio/packs/{key}/start")
async def start_pack(key: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    pack = (await db.execute(select(ContentPack).where(ContentPack.content_key == key, ContentPack.is_published.is_(True)))).scalar_one_or_none()
    if pack is None:
        raise AppException("Pack not found", status_code=404)
    links = (
        await db.execute(select(ContentPackQuestion).where(ContentPackQuestion.pack_id == pack.id).order_by(ContentPackQuestion.sort_order))
    ).scalars().all()
    questions = []
    for link in links:
        question = (
            await db.execute(select(Question).options(selectinload(Question.options)).where(Question.id == link.question_id))
        ).scalar_one_or_none()
        if question and question.is_active:
            questions.append(question)
    if not questions:
        raise AppException("Pack has no questions", status_code=404)
    session = PracticeSession(
        user_id=user.id,
        mode=PracticeMode.PRACTICE,
        domain_id=questions[0].domain_id,
        category_id=questions[0].category_id,
        topic_id=questions[0].topic_id,
        question_count=len(questions),
        status=SessionStatus.ACTIVE,
        unanswered_count=len(questions),
    )
    db.add(session)
    await db.flush()
    for index, question in enumerate(questions):
        db.add(
            PracticeSessionQuestion(
                session_id=session.id,
                question_id=question.id,
                question_number=index + 1,
                snapshot_json=question_snapshot(question),
            )
        )
    await db.commit()
    return {"session_id": str(session.id), "question_count": len(questions)}


@router.get("/admin/studio/submissions")
async def review_queue(user: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = (await db.execute(select(AssignmentSubmission).where(AssignmentSubmission.status == "submitted"))).scalars().all()
    payload = []
    for row in rows:
        assignment = await db.get(Assignment, row.assignment_id)
        payload.append(
            {
                "id": str(row.id),
                "status": row.status,
                "version": row.assignment_version,
                "assignment_key": assignment.content_key if assignment else None,
                "title": assignment.title if assignment else None,
                "answer_text": row.answer_text,
                "evidence_url": row.evidence_url,
                "brief": (row.brief_snapshot or {}).get("brief_md"),
                "rubric": (row.brief_snapshot or {}).get("rubric"),
            }
        )
    return payload


@router.post("/admin/studio/submissions/{submission_id}/review")
async def review_submission(
    submission_id: UUID,
    payload: ReviewIn,
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    row = await db.get(AssignmentSubmission, submission_id)
    if row is None:
        raise AppException("Submission not found", status_code=404)
    db.add(
        AssignmentReview(
            submission_id=row.id,
            reviewer_id=user.id,
            submission_version=row.assignment_version,
            feedback=payload.feedback,
            grade=payload.grade,
            rubric_notes=payload.rubric_notes,
            reviewed_at=datetime.now(UTC),
        )
    )
    row.status = "accepted" if payload.grade else "needs_changes"
    await db.commit()
    return {"status": row.status, "version": row.assignment_version}


async def _assignment(db: AsyncSession, key: str) -> Assignment:
    row = (await db.execute(select(Assignment).where(Assignment.content_key == key, Assignment.is_published.is_(True)))).scalar_one_or_none()
    if row is None:
        raise AppException("Assignment not found", status_code=404)
    return row


def _check_url(value: str | None) -> None:
    if not value:
        return
    if not value.startswith("https://"):
        raise AppException("Evidence URL must be HTTPS", status_code=400)
