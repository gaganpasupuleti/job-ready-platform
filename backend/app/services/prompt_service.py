"""Student and admin services for deterministic prompt challenges."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import AppException
from app.models.enums import Difficulty
from app.models.learn import PracticePath
from app.models.learn_enums import PracticePathType
from app.models.practice import Bookmark, PracticeAnswer, PracticeSession
from app.models.prompt import (
    PromptChallenge,
    PromptChallengeCase,
    PromptProblemProgress,
    PromptSubmission,
    PromptSubmissionCaseResult,
)
from app.models.prompt_enums import PromptProgressStatus, PromptTaskType
from app.models.question import Question
from app.models.taxonomy import Category, Domain, Topic
from app.models.user import User
from app.schemas.prompt import (
    AIProgressResponse,
    AIProgressTopic,
    PromptBookmarkItem,
    PromptCasePublic,
    PromptCaseResultOut,
    PromptChallengeAdminIn,
    PromptChallengeCard,
    PromptChallengeDetail,
    PromptEvaluateResponse,
    PromptSubmissionDetail,
    PromptSubmissionListItem,
)
from app.services.prompt_evaluator import PromptEvaluator, validate_challenge_config

_now = lambda: datetime.now(UTC)  # noqa: E731

AI_PROGRESS_TOPICS = [
    ("genai", "Generative AI", ["llm-fundamentals", "transformers", "embeddings"]),
    ("rag", "RAG", ["rag", "retrieval", "vector-databases"]),
    ("prompt", "Prompt Engineering", ["zero-shot", "few-shot", "structured-outputs", "prompt-injection"]),
    ("agents", "AI Agents", ["agent-loops", "multi-agent-systems", "agent-fundamentals"]),
    ("mcp", "MCP", ["mcp-fundamentals"]),
    ("tools", "Tool Calling", ["tool-calling"]),
    ("evaluation", "LLM Evaluation", ["llm-evaluation"]),
    ("security", "AI Security", ["ai-security", "prompt-injection"]),
]


class PromptService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.evaluator = PromptEvaluator()

    async def list_challenges(self, user: User, *, difficulty: str | None = None) -> list[PromptChallengeCard]:
        stmt = select(PromptChallenge).where(PromptChallenge.is_active.is_(True))
        if difficulty:
            stmt = stmt.where(PromptChallenge.difficulty == Difficulty(difficulty))
        challenges = (await self.db.execute(stmt.order_by(PromptChallenge.title))).scalars().all()
        progress = {
            row.challenge_id: row
            for row in (
                await self.db.execute(select(PromptProblemProgress).where(PromptProblemProgress.user_id == user.id))
            ).scalars().all()
        }
        bookmarks = set(
            (
                await self.db.execute(
                    select(Bookmark.prompt_challenge_id).where(
                        Bookmark.user_id == user.id, Bookmark.prompt_challenge_id.is_not(None)
                    )
                )
            ).scalars().all()
        )
        return [
            PromptChallengeCard(
                id=c.id,
                slug=c.slug,
                title=c.title,
                description=c.description,
                difficulty=c.difficulty.value if hasattr(c.difficulty, "value") else str(c.difficulty),
                task_type=c.task_type.value if hasattr(c.task_type, "value") else str(c.task_type),
                mastery_threshold=c.mastery_threshold,
                best_score=progress[c.id].best_score if c.id in progress else 0,
                status=progress[c.id].status.value if c.id in progress else None,
                bookmarked=c.id in bookmarks,
            )
            for c in challenges
        ]

    async def get_challenge(self, slug: str, user: User) -> PromptChallengeDetail:
        challenge = await self._load_active(slug)
        progress = (
            await self.db.execute(
                select(PromptProblemProgress).where(
                    PromptProblemProgress.user_id == user.id,
                    PromptProblemProgress.challenge_id == challenge.id,
                )
            )
        ).scalar_one_or_none()
        bookmarked = (
            await self.db.scalar(
                select(Bookmark.id).where(
                    Bookmark.user_id == user.id, Bookmark.prompt_challenge_id == challenge.id
                )
            )
        ) is not None
        public = []
        hidden = 0
        for case in challenge.cases:
            if case.is_hidden:
                hidden += 1
                continue
            public.append(
                PromptCasePublic(
                    id=case.id,
                    input_text=None if case.hide_input else case.input_text,
                    variables={} if case.hide_input else (case.variables or {}),
                    is_hidden=False,
                    weight=case.weight,
                    sort_order=case.sort_order,
                )
            )
        return PromptChallengeDetail(
            id=challenge.id,
            slug=challenge.slug,
            title=challenge.title,
            description=challenge.description,
            difficulty=challenge.difficulty.value if hasattr(challenge.difficulty, "value") else str(challenge.difficulty),
            task_type=challenge.task_type.value if hasattr(challenge.task_type, "value") else str(challenge.task_type),
            scenario=challenge.scenario,
            instructions=challenge.instructions,
            input_description=challenge.input_description,
            expected_behavior=challenge.expected_behavior,
            starter_prompt=challenge.starter_prompt,
            max_prompt_length=challenge.max_prompt_length,
            mastery_threshold=challenge.mastery_threshold,
            evaluation_criteria_summary=challenge.evaluation_criteria_summary,
            hints=list(challenge.hints or []),
            common_mistakes=list(challenge.common_mistakes or []),
            public_cases=public,
            hidden_case_count=hidden,
            bookmarked=bookmarked,
            best_score=progress.best_score if progress else 0,
            status=progress.status.value if progress else None,
        )

    async def evaluate(self, slug: str, user: User, prompt_text: str, *, is_test: bool) -> PromptEvaluateResponse:
        prompt_text = (prompt_text or "").strip()
        if not prompt_text:
            raise AppException("Prompt text is required", status_code=400)
        if len(prompt_text) > settings.prompt_max_chars:
            raise AppException("Prompt exceeds PROMPT_MAX_CHARS", status_code=400)
        challenge = await self._load_active(slug)
        if len(prompt_text) > challenge.max_prompt_length:
            raise AppException("Prompt exceeds this challenge's length limit", status_code=400)

        cases = [c for c in challenge.cases if (not is_test) or (not c.is_hidden)]
        case_rows = []
        results_out: list[PromptCaseResultOut] = []
        for case in cases:
            raw = self.evaluator.evaluate_case(
                prompt=prompt_text,
                case_variables=case.variables or {},
                evaluation_config=case.evaluation_config or {},
                expected_schema=case.expected_schema,
            )
            reveal = not case.is_hidden
            safe_feedback = raw["feedback"] if reveal else ("Hidden case passed" if raw["passed"] else "Hidden case failed")
            case_rows.append({**raw, "weight": case.weight})
            results_out.append(
                PromptCaseResultOut(
                    case_id=case.id,
                    passed=raw["passed"],
                    score=raw["score"],
                    feedback=safe_feedback,
                    revealed=reveal,
                    check_results=raw["check_results"] if reveal else [],
                )
            )

        overall, breakdown, note = self.evaluator.aggregate(case_rows, challenge.rubric_weights)
        passed_n = sum(1 for r in results_out if r.passed)
        mastered = (not is_test) and overall >= challenge.mastery_threshold

        submission = PromptSubmission(
            user_id=user.id,
            challenge_id=challenge.id,
            prompt_text=prompt_text,
            is_test=is_test,
            overall_score=overall,
            passed_cases=passed_n,
            total_cases=len(results_out),
            rubric_breakdown=breakdown,
            feedback=note,
        )
        self.db.add(submission)
        await self.db.flush()
        for result, case in zip(results_out, cases, strict=False):
            self.db.add(
                PromptSubmissionCaseResult(
                    submission_id=submission.id,
                    case_id=case.id,
                    passed=result.passed,
                    score=result.score,
                    feedback=result.feedback,
                    check_results=result.check_results,
                    revealed=result.revealed,
                )
            )

        if not is_test:
            await self._touch_progress(user.id, challenge, overall, mastered)
        await self.db.commit()
        return PromptEvaluateResponse(
            overall_score=overall,
            passed_cases=passed_n,
            total_cases=len(results_out),
            rubric_breakdown=breakdown,
            feedback=note,
            case_results=results_out,
            mastered=mastered,
            submission_id=submission.id,
            is_test=is_test,
        )

    async def list_submissions(self, user: User) -> list[PromptSubmissionListItem]:
        rows = (
            await self.db.execute(
                select(PromptSubmission, PromptChallenge)
                .join(PromptChallenge, PromptChallenge.id == PromptSubmission.challenge_id)
                .where(PromptSubmission.user_id == user.id, PromptSubmission.is_test.is_(False))
                .order_by(PromptSubmission.created_at.desc())
                .limit(50)
            )
        ).all()
        return [
            PromptSubmissionListItem(
                id=sub.id,
                challenge_id=ch.id,
                challenge_title=ch.title,
                difficulty=ch.difficulty.value if hasattr(ch.difficulty, "value") else str(ch.difficulty),
                overall_score=sub.overall_score,
                passed_cases=sub.passed_cases,
                total_cases=sub.total_cases,
                is_test=sub.is_test,
                created_at=sub.created_at,
            )
            for sub, ch in rows
        ]

    async def get_submission(self, submission_id: UUID, user: User) -> PromptSubmissionDetail:
        row = (
            await self.db.execute(
                select(PromptSubmission)
                .options(selectinload(PromptSubmission.case_results))
                .where(PromptSubmission.id == submission_id)
            )
        ).scalar_one_or_none()
        if row is None:
            raise AppException("Submission not found", status_code=404)
        sub = row
        ch = await self.db.get(PromptChallenge, sub.challenge_id)
        if ch is None:
            raise AppException("Submission not found", status_code=404)
        if sub.user_id != user.id:
            raise AppException("Forbidden", status_code=403)
        return PromptSubmissionDetail(
            id=sub.id,
            challenge_title=ch.title,
            difficulty=ch.difficulty.value if hasattr(ch.difficulty, "value") else str(ch.difficulty),
            prompt_text=sub.prompt_text,
            created_at=sub.created_at,
            overall_score=sub.overall_score,
            passed_cases=sub.passed_cases,
            total_cases=sub.total_cases,
            rubric_breakdown=sub.rubric_breakdown or {},
            feedback=sub.feedback,
            case_results=[
                PromptCaseResultOut(
                    case_id=r.case_id,
                    passed=r.passed,
                    score=r.score,
                    feedback=r.feedback,
                    revealed=r.revealed,
                    check_results=r.check_results if r.revealed else [],
                )
                for r in sub.case_results
            ],
            mastered=sub.overall_score >= ch.mastery_threshold,
            submission_id=sub.id,
            is_test=sub.is_test,
        )

    async def toggle_bookmark(self, challenge_id: UUID, user: User) -> dict:
        challenge = await self.db.get(PromptChallenge, challenge_id)
        if challenge is None or not challenge.is_active:
            raise AppException("Challenge not found", status_code=404)
        existing = (
            await self.db.execute(
                select(Bookmark).where(
                    Bookmark.user_id == user.id, Bookmark.prompt_challenge_id == challenge_id
                )
            )
        ).scalar_one_or_none()
        if existing:
            await self.db.delete(existing)
            await self.db.commit()
            return {"bookmarked": False}
        self.db.add(Bookmark(user_id=user.id, prompt_challenge_id=challenge_id))
        await self.db.commit()
        return {"bookmarked": True}

    async def list_bookmarks(self, user: User) -> list[PromptBookmarkItem]:
        rows = (
            await self.db.execute(
                select(PromptChallenge)
                .join(Bookmark, Bookmark.prompt_challenge_id == PromptChallenge.id)
                .where(Bookmark.user_id == user.id)
                .order_by(Bookmark.created_at.desc())
            )
        ).scalars().all()
        return [
            PromptBookmarkItem(
                id=c.id,
                slug=c.slug,
                title=c.title,
                difficulty=c.difficulty.value if hasattr(c.difficulty, "value") else str(c.difficulty),
                task_type=c.task_type.value if hasattr(c.task_type, "value") else str(c.task_type),
            )
            for c in rows
        ]

    async def ai_home(self, user: User) -> dict:
        progress = await self.ai_progress(user)
        paths = (
            await self.db.execute(
                select(PracticePath).where(
                    PracticePath.is_active.is_(True),
                    PracticePath.path_type == PracticePathType.AI,
                )
            )
        ).scalars().all()
        challenges = await self.list_challenges(user)
        mastered = sum(1 for c in challenges if c.status == "mastered")
        return {
            "tracks": [
                {"key": "genai", "label": "Generative AI", "href": "/ai/genai"},
                {"key": "prompt", "label": "Prompt Engineering", "href": "/ai/prompt-engineering"},
                {"key": "rag", "label": "RAG", "href": "/ai/rag"},
                {"key": "embeddings", "label": "Embeddings", "href": "/ai/genai"},
                {"key": "vectors", "label": "Vector Databases", "href": "/ai/rag"},
                {"key": "agents", "label": "AI Agents", "href": "/ai/agents"},
                {"key": "mcp", "label": "MCP", "href": "/ai/mcp"},
                {"key": "tools", "label": "Tool Calling", "href": "/ai/tool-calling"},
                {"key": "eval", "label": "LLM Evaluation", "href": "/ai/evaluation"},
                {"key": "security", "label": "AI Security", "href": "/ai/security"},
                {"key": "design", "label": "AI System Design", "href": "/ai/system-design"},
            ],
            "continue_ai": progress.continue_href,
            "weak_topics": progress.weak_topics,
            "prompt_progress": {"attempted": progress.prompt_attempted, "mastered": mastered or progress.prompt_mastered},
            "topics": [t.model_dump() for t in progress.topics],
            "recommended": [p.slug for p in paths[:4]],
            "paths": [{"slug": p.slug, "title": p.title, "href": f"/practice/paths/{p.slug}"} for p in paths],
        }

    async def ai_progress(self, user: User) -> AIProgressResponse:
        topics_out: list[AIProgressTopic] = []
        weak: list[str] = []
        for key, label, slugs in AI_PROGRESS_TOPICS:
            stats = await self._mcq_stats(user.id, slugs)
            prompt_stats = await self._prompt_stats(user.id) if key == "prompt" else (0, 0, 0.0)
            topic = AIProgressTopic(
                key=key,
                label=label,
                mcq_attempts=stats[0],
                mcq_accuracy=stats[1],
                prompt_attempts=prompt_stats[0] if key == "prompt" else 0,
                prompt_mastered=prompt_stats[1] if key == "prompt" else 0,
                best_prompt_score=prompt_stats[2] if key == "prompt" else 0,
            )
            topics_out.append(topic)
            if stats[1] is not None and stats[1] < 60:
                weak.append(label)
        p_att, p_mas, _best = await self._prompt_stats(user.id)
        continue_href = "/ai/prompt-engineering/challenges" if p_att else "/ai/genai"
        return AIProgressResponse(
            topics=topics_out,
            weak_topics=weak,
            continue_href=continue_href,
            prompt_attempted=p_att,
            prompt_mastered=p_mas,
        )

    async def _mcq_stats(self, user_id: UUID, topic_slugs: list[str]) -> tuple[int, float | None]:
        rows = (
            await self.db.execute(
                select(PracticeAnswer.is_correct)
                .join(PracticeSession, PracticeSession.id == PracticeAnswer.session_id)
                .join(Question, Question.id == PracticeAnswer.question_id)
                .join(Topic, Topic.id == Question.topic_id)
                .where(PracticeSession.user_id == user_id, Topic.slug.in_(topic_slugs))
            )
        ).all()
        if not rows:
            return 0, None
        correct = sum(1 for (flag,) in rows if flag)
        return len(rows), round(100.0 * correct / len(rows), 1)

    async def _prompt_stats(self, user_id: UUID) -> tuple[int, int, float]:
        rows = (
            await self.db.execute(select(PromptProblemProgress).where(PromptProblemProgress.user_id == user_id))
        ).scalars().all()
        mastered = sum(1 for r in rows if r.status == PromptProgressStatus.MASTERED)
        best = max((r.best_score for r in rows), default=0)
        return len(rows), mastered, best

    async def _touch_progress(self, user_id: UUID, challenge: PromptChallenge, score: float, mastered: bool) -> None:
        row = (
            await self.db.execute(
                select(PromptProblemProgress).where(
                    PromptProblemProgress.user_id == user_id,
                    PromptProblemProgress.challenge_id == challenge.id,
                )
            )
        ).scalar_one_or_none()
        now = _now()
        if row is None:
            row = PromptProblemProgress(
                user_id=user_id,
                challenge_id=challenge.id,
                first_attempted_at=now,
            )
            self.db.add(row)
        row.attempt_count = (row.attempt_count or 0) + 1
        row.last_attempt_at = now
        row.best_score = max(row.best_score or 0, score)
        if mastered:
            row.status = PromptProgressStatus.MASTERED
            row.first_mastered_at = row.first_mastered_at or now
        else:
            row.status = PromptProgressStatus.ATTEMPTED

    async def _load_active(self, slug: str) -> PromptChallenge:
        challenge = (
            await self.db.execute(
                select(PromptChallenge)
                .options(selectinload(PromptChallenge.cases))
                .where(PromptChallenge.slug == slug, PromptChallenge.is_active.is_(True))
            )
        ).scalar_one_or_none()
        if challenge is None:
            raise AppException("Challenge not found", status_code=404)
        return challenge


class PromptAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def coverage(self) -> dict:
        domain = (await self.db.execute(select(Domain).where(Domain.slug == "ai"))).scalar_one_or_none()
        mcq = 0
        by_topic: dict[str, int] = {}
        if domain:
            rows = (
                await self.db.execute(
                    select(Topic.slug, func.count(Question.id))
                    .join(Question, Question.topic_id == Topic.id)
                    .join(Category, Category.id == Topic.category_id)
                    .where(Category.domain_id == domain.id, Question.is_active.is_(True))
                    .group_by(Topic.slug)
                )
            ).all()
            by_topic = {slug: int(n) for slug, n in rows}
            mcq = sum(by_topic.values())
        prompts = int(await self.db.scalar(select(func.count()).select_from(PromptChallenge)) or 0)
        active = int(
            await self.db.scalar(select(func.count()).select_from(PromptChallenge).where(PromptChallenge.is_active.is_(True)))
            or 0
        )
        return {
            "ai_mcqs": mcq,
            "mcq_by_topic": by_topic,
            "prompt_challenges": prompts,
            "active_prompt_challenges": active,
        }

    async def list_challenges(self) -> list[dict]:
        rows = (await self.db.execute(select(PromptChallenge).order_by(PromptChallenge.title))).scalars().all()
        return [self._dict(c) for c in rows]

    async def get_challenge(self, challenge_id: UUID) -> dict:
        challenge = (
            await self.db.execute(
                select(PromptChallenge)
                .options(selectinload(PromptChallenge.cases))
                .where(PromptChallenge.id == challenge_id)
            )
        ).scalar_one_or_none()
        if challenge is None:
            raise AppException("Challenge not found", status_code=404)
        data = {
            "id": str(challenge.id),
            "slug": challenge.slug,
            "title": challenge.title,
            "description": challenge.description,
            "difficulty": challenge.difficulty.value if hasattr(challenge.difficulty, "value") else str(challenge.difficulty),
            "task_type": challenge.task_type.value if hasattr(challenge.task_type, "value") else str(challenge.task_type),
            "scenario": challenge.scenario,
            "instructions": challenge.instructions,
            "input_description": challenge.input_description,
            "expected_behavior": challenge.expected_behavior,
            "starter_prompt": challenge.starter_prompt,
            "reference_prompt": challenge.reference_prompt,
            "max_prompt_length": challenge.max_prompt_length,
            "mastery_threshold": challenge.mastery_threshold,
            "rubric_weights": challenge.rubric_weights or {},
            "hints": challenge.hints or [],
            "common_mistakes": challenge.common_mistakes or [],
            "evaluation_criteria_summary": challenge.evaluation_criteria_summary,
            "is_active": challenge.is_active,
        }
        data["cases"] = [
            {
                "id": str(c.id),
                "input_text": c.input_text,
                "variables": c.variables,
                "expected_output": c.expected_output,
                "expected_schema": c.expected_schema,
                "evaluation_config": c.evaluation_config,
                "is_hidden": c.is_hidden,
                "hide_input": c.hide_input,
                "weight": c.weight,
                "sort_order": c.sort_order,
            }
            for c in challenge.cases
        ]
        return data

    async def create_challenge(self, payload: PromptChallengeAdminIn, admin: User) -> dict:
        errors = validate_challenge_config(payload.model_dump(), payload.cases)
        if payload.is_active and errors:
            raise AppException("; ".join(errors), status_code=400)
        if await self.db.scalar(select(PromptChallenge.id).where(PromptChallenge.slug == payload.slug)):
            raise AppException("Slug already exists", status_code=400)
        challenge = PromptChallenge(
            slug=payload.slug,
            title=payload.title,
            description=payload.description,
            difficulty=Difficulty(payload.difficulty),
            task_type=PromptTaskType(payload.task_type),
            scenario=payload.scenario,
            instructions=payload.instructions,
            input_description=payload.input_description,
            expected_behavior=payload.expected_behavior,
            starter_prompt=payload.starter_prompt,
            reference_prompt=payload.reference_prompt,
            max_prompt_length=payload.max_prompt_length,
            mastery_threshold=payload.mastery_threshold,
            rubric_weights=payload.rubric_weights,
            hints=payload.hints,
            common_mistakes=payload.common_mistakes,
            evaluation_criteria_summary=payload.evaluation_criteria_summary,
            is_active=payload.is_active and not errors,
            created_by=admin.id,
        )
        self.db.add(challenge)
        await self.db.flush()
        for idx, case in enumerate(payload.cases):
            self.db.add(self._case(challenge.id, case, idx))
        await self.db.commit()
        await self.db.refresh(challenge)
        return self._dict(challenge)

    async def update_challenge(self, challenge_id: UUID, payload: dict[str, Any]) -> dict:
        challenge = (
            await self.db.execute(
                select(PromptChallenge)
                .options(selectinload(PromptChallenge.cases))
                .where(PromptChallenge.id == challenge_id)
            )
        ).scalar_one_or_none()
        if challenge is None:
            raise AppException("Challenge not found", status_code=404)
        cases_payload = payload.pop("cases", None)
        allowed = {
            "slug",
            "title",
            "description",
            "scenario",
            "instructions",
            "input_description",
            "expected_behavior",
            "starter_prompt",
            "reference_prompt",
            "max_prompt_length",
            "mastery_threshold",
            "rubric_weights",
            "hints",
            "common_mistakes",
            "evaluation_criteria_summary",
            "is_active",
        }
        for key, value in payload.items():
            if key == "difficulty":
                challenge.difficulty = Difficulty(value)
            elif key == "task_type":
                challenge.task_type = PromptTaskType(value)
            elif key in allowed:
                setattr(challenge, key, value)
        if cases_payload is not None:
            for old in list(challenge.cases):
                await self.db.delete(old)
            await self.db.flush()
            for idx, case in enumerate(cases_payload):
                self.db.add(self._case(challenge.id, case, idx))
        snapshot_cases = cases_payload if cases_payload is not None else [
            {"evaluation_config": c.evaluation_config, "is_hidden": c.is_hidden, "expected_schema": c.expected_schema}
            for c in challenge.cases
        ]
        errors = validate_challenge_config(
            {"rubric_weights": challenge.rubric_weights},
            snapshot_cases,
        )
        if challenge.is_active and errors:
            challenge.is_active = False
            await self.db.commit()
            raise AppException("Challenge invalid and was deactivated: " + "; ".join(errors), status_code=400)
        await self.db.commit()
        return await self.get_challenge(challenge_id)

    async def validate_only(self, challenge_id: UUID) -> dict:
        data = await self.get_challenge(challenge_id)
        errors = validate_challenge_config(data, data.get("cases") or [])
        return {"ok": not errors, "errors": errors}

    def _case(self, challenge_id: UUID, case: dict[str, Any], idx: int) -> PromptChallengeCase:
        return PromptChallengeCase(
            challenge_id=challenge_id,
            input_text=case.get("input_text") or "",
            variables=case.get("variables") or {},
            expected_output=case.get("expected_output"),
            expected_schema=case.get("expected_schema"),
            evaluation_config=case.get("evaluation_config") or {},
            is_hidden=bool(case.get("is_hidden")),
            hide_input=bool(case.get("hide_input")),
            weight=float(case.get("weight") or 1),
            sort_order=int(case.get("sort_order") or idx),
        )

    def _dict(self, c: PromptChallenge) -> dict:
        return {
            "id": str(c.id),
            "slug": c.slug,
            "title": c.title,
            "description": c.description,
            "difficulty": c.difficulty.value if hasattr(c.difficulty, "value") else str(c.difficulty),
            "task_type": c.task_type.value if hasattr(c.task_type, "value") else str(c.task_type),
            "is_active": c.is_active,
            "mastery_threshold": c.mastery_threshold,
            "max_prompt_length": c.max_prompt_length,
        }
