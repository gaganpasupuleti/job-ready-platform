"""Student and admin services for deterministic scenario challenges."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.enums import Difficulty
from app.models.learn import PracticePath, Project
from app.models.learn_enums import PracticePathType
from app.models.practice import PracticeAnswer, PracticeSession
from app.models.question import Question
from app.models.scenario import (
    ScenarioChallenge,
    ScenarioOption,
    ScenarioProgress,
    ScenarioStep,
    ScenarioStepAnswer,
    ScenarioSubmission,
)
from app.models.scenario_enums import ScenarioDomain, ScenarioProgressStatus, ScenarioType
from app.models.taxonomy import Category, Domain, Topic
from app.models.user import User
from app.schemas.scenario import (
    DomainProgressResponse,
    DomainProgressTopic,
    ScenarioAdminIn,
    ScenarioAnswerIn,
    ScenarioCard,
    ScenarioDetail,
    ScenarioOptionPublic,
    ScenarioStepPublic,
    ScenarioStepResult,
    ScenarioSubmitResponse,
)
from app.services.catalog_service import CatalogService

_now = lambda: datetime.now(UTC)  # noqa: E731

DOMAIN_PATH_TYPE = {
    "cloud": PracticePathType.CLOUD,
    "devops": PracticePathType.DEVOPS,
    "cybersecurity": PracticePathType.CYBERSECURITY,
}

DOMAIN_PROJECT_KEYS = {
    "cloud": "cloud",
    "devops": "devops",
    "cybersecurity": "cybersecurity",
}

PROGRESS_TOPICS: dict[str, list[tuple[str, str, list[str]]]] = {
    "cloud": [
        ("fundamentals", "Cloud Fundamentals", ["shared-responsibility", "iaas", "paas", "saas", "high-availability"]),
        ("aws", "AWS", ["iam", "ec2", "s3", "vpc", "lambda"]),
        ("azure", "Azure", ["entra-id", "virtual-machines", "blob-storage", "rbac"]),
        ("gcp", "GCP", ["gcp-iam", "compute-engine", "cloud-storage", "bigquery"]),
        ("architecture", "Architecture", ["ha-web-app", "event-processing", "disaster-recovery"]),
        ("security", "Cloud Security", ["kms", "secrets", "security-groups"]),
    ],
    "devops": [
        ("linux", "Linux", ["permissions", "processes", "logs"]),
        ("git", "Git", ["branch", "merge", "pull-requests"]),
        ("docker", "Docker", ["dockerfile", "compose", "images"]),
        ("kubernetes", "Kubernetes", ["pod", "deployment", "service"]),
        ("cicd", "CI/CD", ["pipeline-stages", "rollback", "cicd-secrets"]),
        ("terraform", "Terraform", ["state", "plan-apply", "modules"]),
        ("observability", "Observability", ["metrics", "obs-logs", "traces"]),
        ("sre", "SRE", ["sli-slo-sla", "error-budgets", "incident-management"]),
    ],
    "cybersecurity": [
        ("fundamentals", "Fundamentals", ["cia-triad", "least-privilege", "zero-trust"]),
        ("network", "Network Security", ["tls", "firewalls", "waf"]),
        ("iam", "IAM", ["mfa", "rbac", "secrets-management"]),
        ("web", "Web / OWASP", ["owasp", "xss-concepts", "injection-concepts"]),
        ("api", "API Security", ["object-level-authorization", "rate-limiting"]),
        ("soc", "SOC / SIEM", ["soc-roles", "siem", "triage"]),
        ("ir", "Incident Response", ["containment", "eradication", "lessons-learned"]),
        ("secure-coding", "Secure Coding", ["parameterized-queries", "input-validation"]),
    ],
}


class ScenarioService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_challenges(self, user: User, *, domain: str | None = None) -> list[ScenarioCard]:
        stmt = select(ScenarioChallenge).where(ScenarioChallenge.is_active.is_(True))
        if domain:
            stmt = stmt.where(ScenarioChallenge.domain_key == ScenarioDomain(domain))
        rows = (await self.db.execute(stmt.order_by(ScenarioChallenge.title))).scalars().all()
        progress = {
            p.challenge_id: p
            for p in (
                await self.db.execute(select(ScenarioProgress).where(ScenarioProgress.user_id == user.id))
            ).scalars().all()
        }
        return [
            ScenarioCard(
                id=c.id,
                slug=c.slug,
                title=c.title,
                description=c.description,
                domain_key=c.domain_key.value if hasattr(c.domain_key, "value") else str(c.domain_key),
                scenario_type=c.scenario_type.value if hasattr(c.scenario_type, "value") else str(c.scenario_type),
                difficulty=c.difficulty.value if hasattr(c.difficulty, "value") else str(c.difficulty),
                unofficial_cert_tag=c.unofficial_cert_tag,
                best_score=progress[c.id].best_score if c.id in progress else 0,
                status=progress[c.id].status.value if c.id in progress else None,
            )
            for c in rows
        ]

    async def get_challenge(self, slug: str, user: User) -> ScenarioDetail:
        challenge = await self._load_active(slug)
        progress = (
            await self.db.execute(
                select(ScenarioProgress).where(
                    ScenarioProgress.user_id == user.id, ScenarioProgress.challenge_id == challenge.id
                )
            )
        ).scalar_one_or_none()
        steps = []
        for step in challenge.steps:
            steps.append(
                ScenarioStepPublic(
                    id=step.id,
                    sort_order=step.sort_order,
                    prompt=step.prompt,
                    context_snippet=step.context_snippet,
                    is_critical=step.is_critical,
                    options=[
                        ScenarioOptionPublic(id=o.id, label=o.label, sort_order=o.sort_order)
                        for o in step.options
                    ],
                )
            )
        return ScenarioDetail(
            id=challenge.id,
            slug=challenge.slug,
            title=challenge.title,
            description=challenge.description,
            domain_key=challenge.domain_key.value if hasattr(challenge.domain_key, "value") else str(challenge.domain_key),
            scenario_type=challenge.scenario_type.value if hasattr(challenge.scenario_type, "value") else str(challenge.scenario_type),
            difficulty=challenge.difficulty.value if hasattr(challenge.difficulty, "value") else str(challenge.difficulty),
            context_text=challenge.context_text,
            evidence_json=challenge.evidence_json or {},
            unofficial_cert_tag=challenge.unofficial_cert_tag,
            mastery_threshold=challenge.mastery_threshold,
            steps=steps,
            best_score=progress.best_score if progress else 0,
            status=progress.status.value if progress else None,
        )

    async def submit(self, slug: str, user: User, answers: list[ScenarioAnswerIn]) -> ScenarioSubmitResponse:
        challenge = await self._load_active(slug)
        by_step = {a.step_id: a.option_id for a in answers}
        option_map = {o.id: o for step in challenge.steps for o in step.options}
        if len(by_step) != len(challenge.steps):
            raise AppException("Answer every step in order", status_code=400)

        results: list[ScenarioStepResult] = []
        missed: list[str] = []
        weighted = 0.0
        total_w = 0.0
        correct_n = 0
        for step in challenge.steps:
            oid = by_step.get(step.id)
            if oid is None or oid not in option_map:
                raise AppException("Invalid option for a step", status_code=400)
            option = option_map[oid]
            if option.step_id != step.id:
                raise AppException("Option does not belong to this step", status_code=400)
            ok = option.is_correct
            weight = step.scoring_weight or 1
            total_w += weight
            if ok:
                weighted += weight
                correct_n += 1
            elif step.is_critical:
                missed.append(step.prompt[:120])
            results.append(
                ScenarioStepResult(
                    step_id=step.id,
                    option_id=oid,
                    is_correct=ok,
                    explanation=step.explanation if ok else option.explanation or step.explanation,
                    is_critical=step.is_critical,
                )
            )
        score = round(100.0 * weighted / total_w, 2) if total_w else 0
        if missed:
            score = round(max(0, score - 10 * len(missed)), 2)
        mastered = score >= challenge.mastery_threshold
        note = "Deterministic practice score. Critical misses are listed when a high-impact step was wrong."
        submission = ScenarioSubmission(
            user_id=user.id,
            challenge_id=challenge.id,
            overall_score=score,
            correct_decisions=correct_n,
            total_steps=len(challenge.steps),
            missed_critical=missed,
            explanation=note,
        )
        self.db.add(submission)
        await self.db.flush()
        for row, step in zip(results, challenge.steps, strict=False):
            self.db.add(
                ScenarioStepAnswer(
                    submission_id=submission.id,
                    step_id=step.id,
                    option_id=row.option_id,
                    is_correct=row.is_correct,
                    score=100 if row.is_correct else 0,
                )
            )
        await self._touch_progress(user.id, challenge, score, mastered)
        await self.db.commit()
        return ScenarioSubmitResponse(
            overall_score=score,
            correct_decisions=correct_n,
            total_steps=len(challenge.steps),
            missed_critical=missed,
            explanation=note,
            step_results=results,
            mastered=mastered,
            submission_id=submission.id,
        )

    async def get_submission(self, submission_id: UUID, user: User) -> ScenarioSubmitResponse:
        sub = (
            await self.db.execute(
                select(ScenarioSubmission)
                .options(selectinload(ScenarioSubmission.answers))
                .where(ScenarioSubmission.id == submission_id)
            )
        ).scalar_one_or_none()
        if sub is None:
            raise AppException("Submission not found", status_code=404)
        if sub.user_id != user.id:
            raise AppException("Forbidden", status_code=403)
        return ScenarioSubmitResponse(
            overall_score=sub.overall_score,
            correct_decisions=sub.correct_decisions,
            total_steps=sub.total_steps,
            missed_critical=list(sub.missed_critical or []),
            explanation=sub.explanation,
            step_results=[],
            mastered=False,
            submission_id=sub.id,
        )

    async def domain_home(self, user: User, domain: str) -> dict:
        progress = await self.domain_progress(user, domain)
        tracks = {
            "cloud": [
                ("fundamentals", "Cloud Fundamentals", "/cloud/fundamentals"),
                ("aws", "AWS", "/cloud/aws"),
                ("azure", "Azure", "/cloud/azure"),
                ("gcp", "GCP", "/cloud/gcp"),
                ("architecture", "Architecture", "/cloud/architecture"),
                ("security", "Cloud Security", "/cloud/security"),
            ],
            "devops": [
                ("linux", "Linux", "/devops/linux"),
                ("git", "Git", "/devops/git"),
                ("docker", "Docker", "/devops/docker"),
                ("kubernetes", "Kubernetes", "/devops/kubernetes"),
                ("cicd", "CI/CD", "/devops/cicd"),
                ("terraform", "Terraform", "/devops/terraform"),
                ("observability", "Observability", "/devops/observability"),
                ("sre", "SRE", "/devops/sre"),
            ],
            "cybersecurity": [
                ("fundamentals", "Fundamentals", "/cybersecurity/fundamentals"),
                ("network", "Network Security", "/cybersecurity/network-security"),
                ("iam", "IAM", "/cybersecurity/iam"),
                ("web", "Web Security", "/cybersecurity/web-security"),
                ("owasp", "OWASP", "/cybersecurity/owasp"),
                ("api", "API Security", "/cybersecurity/api-security"),
                ("cloud", "Cloud Security", "/cybersecurity/cloud-security"),
                ("soc", "SOC", "/cybersecurity/soc"),
                ("siem", "SIEM", "/cybersecurity/siem"),
                ("ir", "Incident Response", "/cybersecurity/incident-response"),
                ("coding", "Secure Coding", "/cybersecurity/secure-coding"),
            ],
        }
        scenarios = await self.list_challenges(user, domain=domain)
        return {
            "domain": domain,
            "tracks": [{"key": k, "label": lab, "href": href} for k, lab, href in tracks.get(domain, [])],
            "continue": progress.continue_href,
            "weak_topics": progress.weak_topics,
            "scenarios": [s.model_dump() for s in scenarios[:8]],
            "paths": progress.paths,
            "projects": progress.projects,
            "progress": progress.model_dump(),
            "unofficial_disclaimer": "Unofficial preparation. Not affiliated with any certification vendor.",
        }

    async def domain_progress(self, user: User, domain: str) -> DomainProgressResponse:
        topics_out = []
        weak = []
        for key, label, slugs in PROGRESS_TOPICS.get(domain, []):
            att, acc = await self._mcq_stats(user.id, slugs, domain)
            topic = DomainProgressTopic(key=key, label=label, mcq_attempts=att, mcq_accuracy=acc)
            topics_out.append(topic)
            if acc is not None and acc < 60:
                weak.append(label)
        sc_att, sc_mas, sc_best = await self._scenario_stats(user.id, domain)
        if topics_out:
            topics_out[0].scenario_attempts = sc_att
            topics_out[0].scenario_best = sc_best
        path_type = DOMAIN_PATH_TYPE.get(domain)
        paths = []
        if path_type:
            rows = (
                await self.db.execute(
                    select(PracticePath).where(
                        PracticePath.is_active.is_(True), PracticePath.path_type == path_type
                    )
                )
            ).scalars().all()
            paths = [{"slug": p.slug, "title": p.title, "href": f"/practice/paths/{p.slug}"} for p in rows]
        proj_key = DOMAIN_PROJECT_KEYS.get(domain)
        projects = []
        if proj_key:
            rows = (
                await self.db.execute(
                    select(Project).where(Project.is_published.is_(True), Project.category_key == proj_key)
                )
            ).scalars().all()
            projects = [{"slug": p.slug, "title": p.title, "href": f"/practice/projects/{p.slug}"} for p in rows]
        continue_href = f"/{domain}" if domain != "cybersecurity" else "/cybersecurity"
        if sc_att:
            continue_href = "/scenarios"
        return DomainProgressResponse(
            domain=domain,
            topics=topics_out,
            weak_topics=weak,
            continue_href=continue_href,
            scenario_attempted=sc_att,
            scenario_mastered=sc_mas,
            paths=paths,
            projects=projects,
        )

    async def _mcq_stats(
        self, user_id: UUID, topic_slugs: list[str], domain_slug: str | None = None
    ) -> tuple[int, float | None]:
        stmt = (
            select(PracticeAnswer.is_correct)
            .join(PracticeSession, PracticeSession.id == PracticeAnswer.session_id)
            .join(Question, Question.id == PracticeAnswer.question_id)
            .join(Topic, Topic.id == Question.topic_id)
            .where(PracticeSession.user_id == user_id, Topic.slug.in_(topic_slugs))
        )
        if domain_slug:
            stmt = (
                stmt.join(Category, Category.id == Topic.category_id)
                .join(Domain, Domain.id == Category.domain_id)
                .where(Domain.slug == domain_slug)
            )
        rows = (await self.db.execute(stmt)).all()
        if not rows:
            return 0, None
        correct = sum(1 for (flag,) in rows if flag)
        return len(rows), round(100.0 * correct / len(rows), 1)

    async def _scenario_stats(self, user_id: UUID, domain: str) -> tuple[int, int, float]:
        rows = (
            await self.db.execute(
                select(ScenarioProgress)
                .join(ScenarioChallenge, ScenarioChallenge.id == ScenarioProgress.challenge_id)
                .where(
                    ScenarioProgress.user_id == user_id,
                    ScenarioChallenge.domain_key == ScenarioDomain(domain),
                )
            )
        ).scalars().all()
        mastered = sum(1 for r in rows if r.status == ScenarioProgressStatus.MASTERED)
        best = max((r.best_score for r in rows), default=0)
        return len(rows), mastered, best

    async def _touch_progress(self, user_id: UUID, challenge: ScenarioChallenge, score: float, mastered: bool) -> None:
        row = (
            await self.db.execute(
                select(ScenarioProgress).where(
                    ScenarioProgress.user_id == user_id, ScenarioProgress.challenge_id == challenge.id
                )
            )
        ).scalar_one_or_none()
        now = _now()
        if row is None:
            row = ScenarioProgress(user_id=user_id, challenge_id=challenge.id)
            self.db.add(row)
        row.attempt_count = (row.attempt_count or 0) + 1
        row.last_attempt_at = now
        row.best_score = max(row.best_score or 0, score)
        row.status = ScenarioProgressStatus.MASTERED if mastered else ScenarioProgressStatus.ATTEMPTED

    async def _load_active(self, slug: str) -> ScenarioChallenge:
        challenge = (
            await self.db.execute(
                select(ScenarioChallenge)
                .options(selectinload(ScenarioChallenge.steps).selectinload(ScenarioStep.options))
                .where(ScenarioChallenge.slug == slug, ScenarioChallenge.is_active.is_(True))
            )
        ).scalar_one_or_none()
        if challenge is None:
            raise AppException("Scenario not found", status_code=404)
        return challenge


class ScenarioAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def coverage(self, domain: str | None = None) -> dict:
        from app.models.question import Question as Q

        out: dict[str, Any] = {}
        for slug in ("cloud", "devops", "cybersecurity"):
            if domain and domain != slug:
                continue
            d = (await self.db.execute(select(Domain).where(Domain.slug == slug))).scalar_one_or_none()
            mcq = 0
            by_topic = {}
            if d:
                rows = (
                    await self.db.execute(
                        select(Topic.slug, func.count(Q.id))
                        .join(Q, Q.topic_id == Topic.id)
                        .join(Category, Category.id == Topic.category_id)
                        .where(Category.domain_id == d.id, Q.is_active.is_(True))
                        .group_by(Topic.slug)
                    )
                ).all()
                by_topic = {s: int(n) for s, n in rows}
                mcq = sum(by_topic.values())
            sc = int(
                await self.db.scalar(
                    select(func.count())
                    .select_from(ScenarioChallenge)
                    .where(ScenarioChallenge.domain_key == ScenarioDomain(slug))
                )
                or 0
            )
            out[slug] = {"mcqs": mcq, "mcq_by_topic": by_topic, "scenarios": sc}
        return out

    async def list_challenges(self) -> list[dict]:
        rows = (await self.db.execute(select(ScenarioChallenge).order_by(ScenarioChallenge.title))).scalars().all()
        return [self._card(c) for c in rows]

    async def get_challenge(self, challenge_id: UUID) -> dict:
        challenge = (
            await self.db.execute(
                select(ScenarioChallenge)
                .options(selectinload(ScenarioChallenge.steps).selectinload(ScenarioStep.options))
                .where(ScenarioChallenge.id == challenge_id)
            )
        ).scalar_one_or_none()
        if challenge is None:
            raise AppException("Scenario not found", status_code=404)
        data = self._card(challenge)
        data["context_text"] = challenge.context_text
        data["evidence_json"] = challenge.evidence_json
        data["unofficial_cert_tag"] = challenge.unofficial_cert_tag
        data["steps"] = [
            {
                "id": str(s.id),
                "sort_order": s.sort_order,
                "prompt": s.prompt,
                "context_snippet": s.context_snippet,
                "is_critical": s.is_critical,
                "explanation": s.explanation,
                "scoring_weight": s.scoring_weight,
                "options": [
                    {
                        "id": str(o.id),
                        "label": o.label,
                        "is_correct": o.is_correct,
                        "explanation": o.explanation,
                        "sort_order": o.sort_order,
                    }
                    for o in s.options
                ],
            }
            for s in challenge.steps
        ]
        return data

    async def create_challenge(self, payload: ScenarioAdminIn, admin: User) -> dict:
        errors = validate_scenario_payload(payload.model_dump())
        if payload.is_active and errors:
            raise AppException("; ".join(errors), status_code=400)
        if await self.db.scalar(select(ScenarioChallenge.id).where(ScenarioChallenge.slug == payload.slug)):
            raise AppException("Slug already exists", status_code=400)
        challenge = ScenarioChallenge(
            slug=payload.slug,
            title=payload.title,
            description=payload.description,
            domain_key=ScenarioDomain(payload.domain_key),
            scenario_type=ScenarioType(payload.scenario_type),
            difficulty=Difficulty(payload.difficulty),
            context_text=payload.context_text,
            evidence_json=payload.evidence_json,
            unofficial_cert_tag=payload.unofficial_cert_tag,
            mastery_threshold=payload.mastery_threshold,
            is_active=payload.is_active and not errors,
            created_by=admin.id,
        )
        self.db.add(challenge)
        await self.db.flush()
        await self._add_steps(challenge.id, payload.steps)
        await self.db.commit()
        await CatalogService(self.db).invalidate_cache()
        return self._card(challenge)

    async def update_challenge(self, challenge_id: UUID, payload: dict[str, Any]) -> dict:
        challenge = (
            await self.db.execute(
                select(ScenarioChallenge)
                .options(selectinload(ScenarioChallenge.steps).selectinload(ScenarioStep.options))
                .where(ScenarioChallenge.id == challenge_id)
            )
        ).scalar_one_or_none()
        if challenge is None:
            raise AppException("Scenario not found", status_code=404)
        steps = payload.pop("steps", None)
        for key, value in payload.items():
            if key == "difficulty":
                challenge.difficulty = Difficulty(value)
            elif key == "domain_key":
                challenge.domain_key = ScenarioDomain(value)
            elif key == "scenario_type":
                challenge.scenario_type = ScenarioType(value)
            elif hasattr(challenge, key):
                setattr(challenge, key, value)
        if steps is not None:
            for old in list(challenge.steps):
                await self.db.delete(old)
            await self.db.flush()
            await self._add_steps(challenge.id, steps)
        errors = validate_scenario_payload({"steps": steps}) if steps is not None else []
        if challenge.is_active and steps is not None and errors:
            challenge.is_active = False
            await self.db.commit()
            raise AppException("Invalid scenario deactivated: " + "; ".join(errors), status_code=400)
        await self.db.commit()
        await CatalogService(self.db).invalidate_cache()
        return await self.get_challenge(challenge_id)

    async def _add_steps(self, challenge_id: UUID, steps: list[dict[str, Any]]) -> None:
        for idx, step in enumerate(steps):
            row = ScenarioStep(
                challenge_id=challenge_id,
                sort_order=int(step.get("sort_order") or idx),
                prompt=step.get("prompt") or "",
                context_snippet=step.get("context_snippet") or "",
                is_critical=bool(step.get("is_critical")),
                explanation=step.get("explanation") or "",
                scoring_weight=float(step.get("scoring_weight") or 1),
            )
            self.db.add(row)
            await self.db.flush()
            for j, opt in enumerate(step.get("options") or []):
                self.db.add(
                    ScenarioOption(
                        step_id=row.id,
                        label=opt.get("label") or "",
                        is_correct=bool(opt.get("is_correct")),
                        explanation=opt.get("explanation") or "",
                        sort_order=int(opt.get("sort_order") or j),
                    )
                )

    def _card(self, c: ScenarioChallenge) -> dict:
        return {
            "id": str(c.id),
            "slug": c.slug,
            "title": c.title,
            "domain_key": c.domain_key.value if hasattr(c.domain_key, "value") else str(c.domain_key),
            "scenario_type": c.scenario_type.value if hasattr(c.scenario_type, "value") else str(c.scenario_type),
            "difficulty": c.difficulty.value if hasattr(c.difficulty, "value") else str(c.difficulty),
            "is_active": c.is_active,
        }


def validate_scenario_payload(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    steps = data.get("steps") or []
    if not steps:
        errors.append("At least one step is required")
    for idx, step in enumerate(steps):
        options = step.get("options") or []
        if len(options) < 2:
            errors.append(f"Step {idx + 1} needs at least two options")
        if not any(o.get("is_correct") for o in options):
            errors.append(f"Step {idx + 1} needs a correct option")
        if not str(step.get("prompt") or "").strip():
            errors.append(f"Step {idx + 1} needs a prompt")
    return errors
