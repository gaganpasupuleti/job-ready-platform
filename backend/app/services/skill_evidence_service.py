"""Aggregate skill evidence from platform activity — deterministic, no LLM."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coding import CodingProblem, CodingProblemProgress, CodingSubmission
from app.models.coding_enums import ProblemProgressStatus, SubmissionStatus
from app.models.enums import SessionStatus
from app.models.interview import InterviewQuestion
from app.models.interview_session import InterviewQuestionReview, InterviewSessionQuestion
from app.models.learn import Course, Project, UserCourseProgress, UserProjectProgress
from app.models.practice import PracticeAnswer, PracticeSession
from app.models.prompt import PromptChallenge, PromptProblemProgress, PromptSubmission
from app.models.prompt_enums import PromptProgressStatus
from app.models.readiness_enums import EvidenceSourceType, EvidenceStrength
from app.models.scenario import ScenarioChallenge, ScenarioProgress
from app.models.sql_practice import SqlProblem, SqlProblemProgress, SqlSubmission
from app.models.sql_enums import SqlProgressStatus, SqlSubmissionStatus
from app.models.tagging import QuestionSkill, Skill
from app.models.taxonomy import Category, Topic
from app.readiness.formulas import (
    DEFAULT_SOURCE_WEIGHTS,
    SKILL_SOURCE_MULTIPLIERS,
    difficulty_multiplier,
    evidence_strength_from_signals,
    recency_multiplier,
    skill_status,
    weighted_average,
)
from app.readiness.skill_mapping import (
    normalize_skill_key,
    skill_slug_from_category,
    skill_slug_from_tags,
)


@dataclass
class SourceBreakdown:
    source: str
    score: float
    activity_count: int
    last_activity_at: datetime | None = None


@dataclass
class SkillEvidence:
    skill_id: UUID
    skill_name: str
    skill_slug: str
    score: float = 0.0
    effective_score: float = 0.0
    evidence_strength: EvidenceStrength = EvidenceStrength.LOW
    activity_count: int = 0
    last_activity_at: datetime | None = None
    sources: list[SourceBreakdown] = field(default_factory=list)
    status: str = "no_evidence"


class SkillEvidenceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._skill_cache: dict[str, Skill] | None = None

    async def _skills_by_slug(self) -> dict[str, Skill]:
        if self._skill_cache is not None:
            return self._skill_cache
        rows = (await self.db.execute(select(Skill))).scalars().all()
        cache: dict[str, Skill] = {}
        for skill in rows:
            cache[normalize_skill_key(skill.slug)] = skill
            cache[normalize_skill_key(skill.name)] = skill
        self._skill_cache = cache
        return cache

    async def _resolve_skill(self, key: str) -> Skill | None:
        skills = await self._skills_by_slug()
        return skills.get(normalize_skill_key(key))

    def _source_weight(self, skill_slug: str, source: str) -> float:
        base = DEFAULT_SOURCE_WEIGHTS.get(source, 0.1)
        mults = SKILL_SOURCE_MULTIPLIERS.get(skill_slug, {})
        return base * mults.get(source, 1.0)

    def _combine_sources(self, skill_slug: str, sources: list[SourceBreakdown]) -> tuple[float, int, datetime | None, int]:
        if not sources:
            return 0.0, 0, None, 0
        weighted = [
            (s.score, self._source_weight(skill_slug, s.source))
            for s in sources
            if s.activity_count > 0
        ]
        score = weighted_average(weighted)
        activity = sum(s.activity_count for s in sources)
        last = max((s.last_activity_at for s in sources if s.last_activity_at), default=None)
        diversity = len({s.source for s in sources if s.activity_count > 0})
        return score, activity, last, diversity

    async def _mcq_by_skill(self, user_id: UUID) -> dict[str, SourceBreakdown]:
        rows = (
            await self.db.execute(
                select(
                    Skill.slug,
                    func.count(PracticeAnswer.id).label("total"),
                    func.sum(case((PracticeAnswer.is_correct.is_(True), 1), else_=0)).label("correct"),
                    func.max(PracticeAnswer.answered_at),
                )
                .join(PracticeSession, PracticeSession.id == PracticeAnswer.session_id)
                .join(QuestionSkill, QuestionSkill.question_id == PracticeAnswer.question_id)
                .join(Skill, Skill.id == QuestionSkill.skill_id)
                .where(
                    PracticeSession.user_id == user_id,
                    PracticeSession.status == SessionStatus.COMPLETED,
                    PracticeAnswer.is_correct.isnot(None),
                )
                .group_by(Skill.slug)
            )
        ).all()
        result: dict[str, SourceBreakdown] = {}
        for slug, total, correct, last_at in rows:
            total = int(total or 0)
            correct = int(correct or 0)
            score = round((correct / total) * 100, 1) if total else 0.0
            result[normalize_skill_key(slug)] = SourceBreakdown(
                source=EvidenceSourceType.MCQ.value,
                score=score,
                activity_count=total,
                last_activity_at=last_at,
            )
        return result

    async def _sql_by_skill(self, user_id: UUID) -> dict[str, SourceBreakdown]:
        topic_rows = (
            await self.db.execute(
                select(
                    Category.slug,
                    Topic.slug,
                    SqlProblem.difficulty,
                    SqlProblemProgress.status,
                    SqlProblemProgress.updated_at,
                )
                .join(SqlProblem, SqlProblem.id == SqlProblemProgress.problem_id)
                .join(Category, Category.id == SqlProblem.category_id)
                .join(Topic, Topic.id == SqlProblem.topic_id)
                .where(SqlProblemProgress.user_id == user_id)
            )
        ).all()
        buckets: dict[str, list[tuple[float, datetime | None]]] = {}
        for cat_slug, topic_slug, difficulty, status, updated_at in topic_rows:
            skill_key = skill_slug_from_category(cat_slug) or normalize_skill_key(topic_slug)
            diff = difficulty.value if hasattr(difficulty, "value") else str(difficulty)
            st = status.value if hasattr(status, "value") else str(status)
            if st == SqlProgressStatus.SOLVED.value:
                pts = 100 * difficulty_multiplier(diff)
            elif st == SqlProgressStatus.ATTEMPTED.value:
                pts = 45 * difficulty_multiplier(diff)
            else:
                continue
            buckets.setdefault(skill_key, []).append((pts, updated_at))

        failed = (
            await self.db.execute(
                select(Category.slug, func.count(SqlSubmission.id), func.max(SqlSubmission.created_at))
                .join(SqlProblem, SqlProblem.id == SqlSubmission.problem_id)
                .join(Category, Category.id == SqlProblem.category_id)
                .where(
                    SqlSubmission.user_id == user_id,
                    SqlSubmission.status == SqlSubmissionStatus.WRONG_ANSWER,
                )
                .group_by(Category.slug)
            )
        ).all()
        for cat_slug, count, last_at in failed:
            skill_key = skill_slug_from_category(cat_slug) or "sql"
            buckets.setdefault(skill_key, []).append((30.0, last_at))

        result: dict[str, SourceBreakdown] = {}
        for key, entries in buckets.items():
            score = round(sum(e[0] for e in entries) / len(entries), 1)
            last = max((e[1] for e in entries if e[1]), default=None)
            result[key] = SourceBreakdown(
                source=EvidenceSourceType.SQL.value,
                score=min(score, 100),
                activity_count=len(entries),
                last_activity_at=last,
            )
        return result

    async def _coding_by_skill(self, user_id: UUID) -> dict[str, SourceBreakdown]:
        rows = (
            await self.db.execute(
                select(
                    Category.slug,
                    CodingProblem.tags,
                    CodingProblem.difficulty,
                    CodingProblemProgress.status,
                    CodingProblemProgress.updated_at,
                )
                .join(CodingProblem, CodingProblem.id == CodingProblemProgress.problem_id)
                .join(Category, Category.id == CodingProblem.category_id)
                .where(CodingProblemProgress.user_id == user_id)
            )
        ).all()
        buckets: dict[str, list[tuple[float, datetime | None]]] = {}
        for cat_slug, tags, difficulty, status, updated_at in rows:
            keys = skill_slug_from_tags(tags) or [skill_slug_from_category(cat_slug) or "python"]
            diff = difficulty.value if hasattr(difficulty, "value") else str(difficulty)
            st = status.value if hasattr(status, "value") else str(status)
            if st == ProblemProgressStatus.SOLVED.value:
                pts = 100 * difficulty_multiplier(diff)
            elif st == ProblemProgressStatus.ATTEMPTED.value:
                pts = 40 * difficulty_multiplier(diff)
            else:
                continue
            for key in keys:
                buckets.setdefault(key, []).append((pts, updated_at))

        result: dict[str, SourceBreakdown] = {}
        for key, entries in buckets.items():
            score = round(sum(e[0] for e in entries) / len(entries), 1)
            last = max((e[1] for e in entries if e[1]), default=None)
            result[key] = SourceBreakdown(
                source=EvidenceSourceType.CODING.value,
                score=min(score, 100),
                activity_count=len(entries),
                last_activity_at=last,
            )
        return result

    async def _prompt_by_skill(self, user_id: UUID) -> dict[str, SourceBreakdown]:
        rows = (
            await self.db.execute(
                select(
                    PromptChallenge.slug,
                    PromptChallenge.task_type,
                    PromptProblemProgress.best_score,
                    PromptProblemProgress.last_attempt_at,
                )
                .join(PromptChallenge, PromptChallenge.id == PromptProblemProgress.challenge_id)
                .where(PromptProblemProgress.user_id == user_id)
            )
        ).all()
        buckets: dict[str, list[tuple[float, datetime | None]]] = {}
        for slug, task_type, best_score, last_attempt_at in rows:
            tt = task_type.value if hasattr(task_type, "value") else str(task_type)
            keys = skill_slug_from_tags([slug, tt]) or ["prompt-engineering"]
            score = float(best_score or 0)
            if score <= 0:
                continue
            for key in keys:
                buckets.setdefault(key, []).append((score, last_attempt_at))
        result: dict[str, SourceBreakdown] = {}
        for key, entries in buckets.items():
            avg = round(sum(e[0] for e in entries) / len(entries), 1)
            last = max((e[1] for e in entries if e[1]), default=None)
            result[key] = SourceBreakdown(
                source=EvidenceSourceType.PROMPT.value,
                score=min(avg, 100),
                activity_count=len(entries),
                last_activity_at=last,
            )
        return result

    async def _scenario_by_skill(self, user_id: UUID) -> dict[str, SourceBreakdown]:
        rows = (
            await self.db.execute(
                select(
                    ScenarioChallenge.domain_key,
                    ScenarioChallenge.slug,
                    ScenarioProgress.best_score,
                    ScenarioProgress.updated_at,
                )
                .join(ScenarioChallenge, ScenarioChallenge.id == ScenarioProgress.challenge_id)
                .where(ScenarioProgress.user_id == user_id)
            )
        ).all()
        buckets: dict[str, list[tuple[float, datetime | None]]] = {}
        for domain_key, slug, best_score, updated_at in rows:
            domain = domain_key.value if hasattr(domain_key, "value") else str(domain_key)
            keys = skill_slug_from_tags([slug, domain]) or [normalize_skill_key(domain)]
            score = float(best_score or 0)
            if score <= 0:
                continue
            for key in keys:
                buckets.setdefault(key, []).append((score, updated_at))
        result: dict[str, SourceBreakdown] = {}
        for key, entries in buckets.items():
            avg = round(sum(e[0] for e in entries) / len(entries), 1)
            last = max((e[1] for e in entries if e[1]), default=None)
            result[key] = SourceBreakdown(
                source=EvidenceSourceType.SCENARIO.value,
                score=min(avg, 100),
                activity_count=len(entries),
                last_activity_at=last,
            )
        return result

    async def _interview_by_skill(self, user_id: UUID) -> dict[str, SourceBreakdown]:
        from app.models.interview import InterviewQuestionSkill  # noqa: PLC0415

        rows = (
            await self.db.execute(
                select(
                    Skill.slug,
                    InterviewQuestionReview.key_point_coverage,
                    InterviewQuestionReview.needs_review,
                    InterviewQuestionReview.reviewed_at,
                )
                .join(InterviewQuestion, InterviewQuestion.id == InterviewQuestionReview.question_id)
                .join(InterviewQuestionSkill, InterviewQuestionSkill.question_id == InterviewQuestion.id)
                .join(Skill, Skill.id == InterviewQuestionSkill.skill_id)
                .where(InterviewQuestionReview.user_id == user_id)
            )
        ).all()
        buckets: dict[str, list[tuple[float, datetime | None]]] = {}
        for slug, coverage, needs_review, reviewed_at in rows:
            cov = float(coverage or 0)
            if needs_review:
                cov = max(cov * 0.6, 20)
            if cov <= 0:
                continue
            key = normalize_skill_key(slug)
            buckets.setdefault(key, []).append((cov, reviewed_at))
        result: dict[str, SourceBreakdown] = {}
        for key, entries in buckets.items():
            avg = round(sum(e[0] for e in entries) / len(entries), 1)
            last = max((e[1] for e in entries if e[1]), default=None)
            result[key] = SourceBreakdown(
                source=EvidenceSourceType.INTERVIEW.value,
                score=min(avg, 100),
                activity_count=len(entries),
                last_activity_at=last,
            )
        return result

    async def _project_by_skill(self, user_id: UUID) -> dict[str, SourceBreakdown]:
        rows = (
            await self.db.execute(
                select(Project.skills, UserProjectProgress.percent, UserProjectProgress.last_activity_at)
                .join(Project, Project.id == UserProjectProgress.project_id)
                .where(UserProjectProgress.user_id == user_id, UserProjectProgress.percent > 0)
            )
        ).all()
        buckets: dict[str, list[tuple[float, datetime | None]]] = {}
        for skills_list, progress, updated_at in rows:
            skills = skills_list if isinstance(skills_list, list) else []
            keys = [normalize_skill_key(str(s)) for s in skills] or ["python"]
            for key in keys:
                buckets.setdefault(key, []).append((float(progress or 0), updated_at))
        result: dict[str, SourceBreakdown] = {}
        for key, entries in buckets.items():
            avg = round(sum(e[0] for e in entries) / len(entries), 1)
            last = max((e[1] for e in entries if e[1]), default=None)
            result[key] = SourceBreakdown(
                source=EvidenceSourceType.PROJECT.value,
                score=min(avg, 100),
                activity_count=len(entries),
                last_activity_at=last,
            )
        return result

    async def _course_by_skill(self, user_id: UUID) -> dict[str, SourceBreakdown]:
        rows = (
            await self.db.execute(
                select(
                    Course.primary_language_key,
                    Course.slug,
                    UserCourseProgress.percent,
                    UserCourseProgress.last_activity_at,
                )
                .join(Course, Course.id == UserCourseProgress.course_id)
                .where(UserCourseProgress.user_id == user_id, UserCourseProgress.percent > 0)
            )
        ).all()
        buckets: dict[str, list[tuple[float, datetime | None]]] = {}
        for lang_key, slug, progress, updated_at in rows:
            keys = [normalize_skill_key(lang_key or slug or "python")]
            for key in keys:
                buckets.setdefault(key, []).append((float(progress or 0) * 0.7, updated_at))
        result: dict[str, SourceBreakdown] = {}
        for key, entries in buckets.items():
            avg = round(sum(e[0] for e in entries) / len(entries), 1)
            last = max((e[1] for e in entries if e[1]), default=None)
            result[key] = SourceBreakdown(
                source=EvidenceSourceType.COURSE.value,
                score=min(avg, 100),
                activity_count=len(entries),
                last_activity_at=last,
            )
        return result

    async def collect_all(self, user_id: UUID) -> dict[str, SkillEvidence]:
        mcq = await self._mcq_by_skill(user_id)
        sql = await self._sql_by_skill(user_id)
        coding = await self._coding_by_skill(user_id)
        prompt = await self._prompt_by_skill(user_id)
        scenario = await self._scenario_by_skill(user_id)
        interview = await self._interview_by_skill(user_id)
        project = await self._project_by_skill(user_id)
        course = await self._course_by_skill(user_id)

        all_keys = set(mcq) | set(sql) | set(coding) | set(prompt) | set(scenario) | set(interview) | set(project) | set(course)
        skills_map = await self._skills_by_slug()
        out: dict[str, SkillEvidence] = {}

        for key in all_keys:
            skill = skills_map.get(key)
            if skill is None:
                continue
            sources: list[SourceBreakdown] = []
            for bucket, src in [
                (mcq, EvidenceSourceType.MCQ.value),
                (sql, EvidenceSourceType.SQL.value),
                (coding, EvidenceSourceType.CODING.value),
                (prompt, EvidenceSourceType.PROMPT.value),
                (scenario, EvidenceSourceType.SCENARIO.value),
                (interview, EvidenceSourceType.INTERVIEW.value),
                (project, EvidenceSourceType.PROJECT.value),
                (course, EvidenceSourceType.COURSE.value),
            ]:
                if key in bucket:
                    sources.append(bucket[key])
            score, activity, last_at, diversity = self._combine_sources(key, sources)
            strength = evidence_strength_from_signals(activity, diversity)
            from app.readiness.formulas import effective_score  # noqa: PLC0415

            eff = effective_score(score, strength)
            st = skill_status(score, activity > 0)
            out[key] = SkillEvidence(
                skill_id=skill.id,
                skill_name=skill.name,
                skill_slug=skill.slug,
                score=score,
                effective_score=eff,
                evidence_strength=strength,
                activity_count=activity,
                last_activity_at=last_at,
                sources=sources,
                status=st.value,
            )
        return out

    async def get_skill(self, user_id: UUID, skill_id: UUID) -> SkillEvidence | None:
        all_ev = await self.collect_all(user_id)
        for ev in all_ev.values():
            if ev.skill_id == skill_id:
                return ev
        return None

    async def total_activity_count(self, user_id: UUID) -> int:
        ev = await self.collect_all(user_id)
        return sum(e.activity_count for e in ev.values())
