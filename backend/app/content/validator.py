# ruff: noqa: E501
"""Validate generated interview JSON before staging or approval."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.hashing import content_hash, jaccard_similarity, normalize_question_text
from app.models.enums import Difficulty
from app.models.interview import InterviewQuestion, JobListing
from app.models.interview_enums import ContentReviewStatus, ExperienceLevel, InterviewQuestionType
from app.models.tagging import Company, JobRole, Skill
from app.models.taxonomy import Category, Domain, Topic

MIN_QUESTION_LEN = 12
MAX_QUESTION_LEN = 2000
MIN_ANSWER_LEN = 40
MAX_ANSWER_LEN = 20000
MIN_KEY_POINTS = 2
MAX_KEY_POINTS = 20
MIN_POINT_LEN = 8
SIMILARITY_WARN = 0.85

PLACEHOLDER_SNIPPETS = (
    "todo",
    "lorem ipsum",
    "sample answer",
    "answer here",
    "placeholder",
    "tbd",
    "fix me",
)

REQUIRED_FIELDS = (
    "question_text",
    "question_type",
    "difficulty",
    "experience_level",
    "expected_answer",
    "key_points",
)


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    content_hash: str | None = None
    resolved: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_json(self) -> dict[str, Any]:
        return {"errors": self.errors, "warnings": self.warnings}


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return []


def _contains_placeholder(text: str) -> bool:
    lowered = (text or "").lower()
    return any(snippet in lowered for snippet in PLACEHOLDER_SNIPPETS)


async def _lookup_named(session: AsyncSession, model, names: list[str]) -> tuple[list, list[str]]:
    found = []
    missing = []
    for name in names:
        stmt = select(model).where(
            func.lower(model.name) == name.lower().strip()
            if hasattr(model, "name")
            else func.lower(model.slug) == name.lower().strip()
        )
        if hasattr(model, "slug"):
            stmt = select(model).where(
                (func.lower(model.name) == name.lower().strip())
                | (func.lower(model.slug) == name.lower().strip())
            )
        row = (await session.execute(stmt)).scalar_one_or_none()
        if row is None:
            missing.append(name)
        else:
            found.append(row)
    return found, missing


async def validate_question_payload(
    session: AsyncSession,
    payload: dict[str, Any],
    *,
    batch_hashes: set[str] | None = None,
) -> ValidationResult:
    result = ValidationResult()
    if not isinstance(payload, dict):
        result.errors.append("Question payload must be an object.")
        return result

    for required_field in REQUIRED_FIELDS:
        if required_field not in payload or payload[required_field] in (None, "", []):
            result.errors.append(f"Missing required field: {required_field}")

    question_text = str(payload.get("question_text") or "").strip()
    expected_answer = str(payload.get("expected_answer") or "").strip()
    explanation = str(payload.get("explanation") or "").strip() or None
    key_points = payload.get("key_points") or []

    if question_text and (len(question_text) < MIN_QUESTION_LEN or len(question_text) > MAX_QUESTION_LEN):
        result.errors.append(
            f"question_text must be between {MIN_QUESTION_LEN} and {MAX_QUESTION_LEN} characters."
        )
    if expected_answer and (len(expected_answer) < MIN_ANSWER_LEN or len(expected_answer) > MAX_ANSWER_LEN):
        result.errors.append(
            f"expected_answer must be between {MIN_ANSWER_LEN} and {MAX_ANSWER_LEN} characters."
        )
    if _contains_placeholder(question_text) or _contains_placeholder(expected_answer):
        result.errors.append("Placeholder or low-quality content is not allowed.")
    if explanation and _contains_placeholder(explanation):
        result.errors.append("Explanation contains placeholder text.")

    qtype = str(payload.get("question_type") or "").strip().lower()
    difficulty = str(payload.get("difficulty") or "").strip().lower()
    experience = str(payload.get("experience_level") or "").strip().lower()
    allowed_types = {e.value for e in InterviewQuestionType}
    allowed_diff = {e.value for e in Difficulty}
    allowed_exp = {e.value for e in ExperienceLevel}
    if qtype and qtype not in allowed_types:
        result.errors.append(f"Invalid question_type: {qtype}")
    if difficulty and difficulty not in allowed_diff:
        result.errors.append(f"Invalid difficulty: {difficulty}")
    if experience and experience not in allowed_exp:
        result.errors.append(f"Invalid experience_level: {experience}")

    if not isinstance(key_points, list):
        result.errors.append("key_points must be a list of strings.")
        key_points = []
    points = [str(p).strip() for p in key_points if str(p).strip()]
    if points and len(points) < MIN_KEY_POINTS:
        result.errors.append(f"At least {MIN_KEY_POINTS} key points are required.")
    if len(points) > MAX_KEY_POINTS:
        result.errors.append(f"At most {MAX_KEY_POINTS} key points are allowed.")
    for point in points:
        if len(point) < MIN_POINT_LEN:
            result.errors.append(f"Key point is too short: {point[:40]}")
        if _contains_placeholder(point):
            result.errors.append("Key points contain placeholder text.")

    digest = content_hash(question_text) if question_text else None
    result.content_hash = digest
    if digest and batch_hashes is not None and digest in batch_hashes:
        result.errors.append("Duplicate question within this batch.")
    if digest:
        existing = await session.execute(
            select(InterviewQuestion.id, InterviewQuestion.question_text).where(
                InterviewQuestion.content_hash == digest
            )
        )
        row = existing.first()
        if row:
            result.errors.append("Duplicate of an existing interview question (same content hash).")

        similar_rows = (
            await session.execute(
                select(InterviewQuestion.question_text, InterviewQuestion.slug).where(
                    InterviewQuestion.review_status == ContentReviewStatus.APPROVED
                ).limit(400)
            )
        ).all()
        for text, slug in similar_rows:
            score = jaccard_similarity(question_text, text)
            if score >= SIMILARITY_WARN and content_hash(text) != digest:
                result.warnings.append(
                    f"Similar to existing question '{slug}' (Jaccard {score:.2f})."
                )
                break

    skills, missing_skills = await _lookup_named(session, Skill, _as_list(payload.get("skills")))
    if missing_skills:
        result.errors.append(f"Unknown skills: {', '.join(missing_skills)}")
    roles, missing_roles = await _lookup_named(session, JobRole, _as_list(payload.get("roles")))
    if missing_roles:
        result.errors.append(f"Unknown roles: {', '.join(missing_roles)}")
    companies, missing_companies = await _lookup_named(
        session, Company, _as_list(payload.get("companies"))
    )
    if missing_companies:
        result.errors.append(f"Unknown companies: {', '.join(missing_companies)}")

    jobs = []
    missing_jobs = []
    for name in _as_list(payload.get("jobs")):
        job = (
            await session.execute(
                select(JobListing).where(
                    (func.lower(JobListing.slug) == name.lower().strip())
                    | (func.lower(JobListing.title) == name.lower().strip())
                )
            )
        ).scalar_one_or_none()
        if job is None:
            missing_jobs.append(name)
        else:
            jobs.append(job)
    if missing_jobs:
        result.errors.append(f"Unknown jobs: {', '.join(missing_jobs)}")

    domain = category = topic = None
    domain_name = str(payload.get("domain") or "").strip()
    category_name = str(payload.get("category") or "").strip()
    topic_name = str(payload.get("topic") or "").strip()
    if domain_name:
        domain = (
            await session.execute(
                select(Domain).where(
                    (func.lower(Domain.name) == domain_name.lower())
                    | (func.lower(Domain.slug) == domain_name.lower())
                )
            )
        ).scalar_one_or_none()
        if domain is None:
            result.errors.append(f"Unknown domain: {domain_name}")
    if category_name:
        category = (
            await session.execute(
                select(Category).where(
                    (func.lower(Category.name) == category_name.lower())
                    | (func.lower(Category.slug) == category_name.lower())
                )
            )
        ).scalar_one_or_none()
        if category is None:
            result.errors.append(f"Unknown category: {category_name}")
    if topic_name:
        topic = (
            await session.execute(
                select(Topic).where(
                    (func.lower(Topic.name) == topic_name.lower())
                    | (func.lower(Topic.slug) == topic_name.lower())
                )
            )
        ).scalar_one_or_none()
        if topic is None:
            result.errors.append(f"Unknown topic: {topic_name}")

    result.resolved = {
        "question_text": question_text,
        "expected_answer": expected_answer,
        "explanation": explanation,
        "key_points": points,
        "question_type": qtype,
        "difficulty": difficulty,
        "experience_level": experience,
        "skills": skills,
        "roles": roles,
        "companies": companies,
        "jobs": jobs,
        "domain": domain,
        "category": category,
        "topic": topic,
        "normalized": normalize_question_text(question_text),
    }
    return result


async def validate_file_payload(
    session: AsyncSession, data: dict[str, Any]
) -> tuple[list[ValidationResult], list[dict[str, Any]]]:
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object.")
    kind = (data.get("content_kind") or data.get("kind") or "interview_qa").strip().lower()
    if kind in {"interview_qa", "interview", "qa"}:
        questions = data.get("questions")
        if not isinstance(questions, list):
            raise ValueError("JSON must contain a 'questions' array.")
        results: list[ValidationResult] = []
        batch_hashes: set[str] = set()
        for item in questions:
            result = await validate_question_payload(session, item, batch_hashes=batch_hashes)
            if result.content_hash:
                batch_hashes.add(result.content_hash)
            results.append(result)
        return results, questions
    if kind in {"project", "projects"}:
        items = data.get("projects") or data.get("items")
        if not isinstance(items, list):
            raise ValueError("Project JSON must contain a 'projects' array.")
        return [validate_project_payload(item) for item in items], items
    if kind in {"practice_path", "path", "paths"}:
        items = data.get("paths") or data.get("items")
        if not isinstance(items, list):
            raise ValueError("Path JSON must contain a 'paths' array.")
        return [validate_path_payload(item) for item in items], items
    if kind in {"lesson", "lessons", "course_lesson"}:
        items = data.get("lessons") or data.get("items")
        if not isinstance(items, list):
            raise ValueError("Lesson JSON must contain a 'lessons' array.")
        return [validate_lesson_payload(item) for item in items], items
    if kind in {"project_task", "tasks"}:
        items = data.get("tasks") or data.get("items")
        if not isinstance(items, list):
            raise ValueError("Task JSON must contain a 'tasks' array.")
        return [validate_task_payload(item) for item in items], items
    raise ValueError(f"Unsupported content_kind: {kind}")


def validate_project_payload(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult()
    if not isinstance(item, dict):
        result.errors.append("Item must be an object")
        return result
    for field in ("slug", "title", "category_key", "short_description"):
        if not str(item.get(field) or "").strip():
            result.errors.append(f"Missing {field}")
    if _contains_placeholder(str(item.get("title") or "") + str(item.get("short_description") or "")):
        result.errors.append("Placeholder text is not allowed")
    if item.get("task_types"):
        allowed = {"concept", "coding", "sql", "mcq", "checklist", "implementation", "review"}
        bad = [t for t in item["task_types"] if t not in allowed]
        if bad:
            result.errors.append(f"Unknown task_types: {bad}")
    return result


def validate_path_payload(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult()
    if not isinstance(item, dict):
        result.errors.append("Item must be an object")
        return result
    for field in ("slug", "title", "path_type"):
        if not str(item.get(field) or "").strip():
            result.errors.append(f"Missing {field}")
    if _contains_placeholder(str(item.get("title") or "")):
        result.errors.append("Placeholder text is not allowed")
    return result


def validate_lesson_payload(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult()
    if not isinstance(item, dict):
        result.errors.append("Item must be an object")
        return result
    for field in ("slug", "title", "lesson_type"):
        if not str(item.get(field) or "").strip():
            result.errors.append(f"Missing {field}")
    if item.get("hints") and not isinstance(item["hints"], list):
        result.errors.append("hints must be a list")
    if item.get("doubts") and not isinstance(item["doubts"], list):
        result.errors.append("doubts must be a list")
    if _contains_placeholder(str(item.get("title") or "")):
        result.errors.append("Placeholder text is not allowed")
    return result


def validate_task_payload(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult()
    if not isinstance(item, dict):
        result.errors.append("Item must be an object")
        return result
    if not str(item.get("title") or "").strip():
        result.errors.append("Missing title")
    task_type = item.get("task_type")
    allowed = {"concept", "coding", "sql", "mcq", "checklist", "implementation", "review"}
    if task_type and task_type not in allowed:
        result.errors.append(f"Unknown task_type: {task_type}")
    return result
