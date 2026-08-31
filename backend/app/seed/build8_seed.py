# ruff: noqa: E501
"""Build 8 seed: approved interview Q&A + packs. Idempotent by slug/content_hash."""

from __future__ import annotations

import hashlib
import re
from uuid import uuid4

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.enums import Difficulty
from app.models.interview import (
    InterviewAnswerPoint,
    InterviewPack,
    InterviewPackQuestion,
    InterviewQuestion,
    InterviewQuestionCompany,
    InterviewQuestionRole,
    InterviewQuestionSkill,
)
from app.models.interview_enums import (
    ContentReviewStatus,
    ContentSourceType,
    ExperienceLevel,
    InterviewQuestionType,
)
from app.models.tagging import Company, JobRole, Skill


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:160]


def _hash(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()


QUESTIONS: list[dict] = [
    {
        "slug": "sql-window-functions-rank",
        "question_text": "Explain SQL window functions and when you would use RANK vs DENSE_RANK vs ROW_NUMBER.",
        "question_type": InterviewQuestionType.TECHNICAL,
        "difficulty": Difficulty.MEDIUM,
        "experience_level": ExperienceLevel.JUNIOR,
        "expected_answer": "Window functions compute values across a set of rows related to the current row without collapsing the result set. ROW_NUMBER assigns unique sequential numbers. RANK leaves gaps after ties. DENSE_RANK does not leave gaps. Use them for top-N per group, running totals, and ranking without self-joins.",
        "explanation": "Prefer clear examples with PARTITION BY and ORDER BY.",
        "key_points": [
            "Operate over a window without collapsing rows",
            "ROW_NUMBER is unique per partition",
            "RANK gaps after ties; DENSE_RANK does not",
            "Common for top-N and running aggregates",
        ],
        "skills": ["SQL"],
        "roles": ["Data Engineer", "Data Analyst", "SQL Developer"],
    },
    {
        "slug": "sql-indexing-tradeoffs",
        "question_text": "How do indexes improve query performance and what are the tradeoffs?",
        "question_type": InterviewQuestionType.TECHNICAL,
        "difficulty": Difficulty.MEDIUM,
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "expected_answer": "Indexes speed lookups and joins by reducing scan cost, but they add write overhead, storage, and maintenance. Choose based on selective predicates, join keys, and workload. Over-indexing hurts inserts/updates.",
        "explanation": None,
        "key_points": [
            "Faster reads for selective predicates/joins",
            "Write/storage overhead",
            "Selectivity and workload matter",
            "Avoid unnecessary indexes",
        ],
        "skills": ["SQL"],
        "roles": ["Data Engineer", "SQL Developer"],
    },
    {
        "slug": "python-gil-concurrency",
        "question_text": "What is the Python GIL and how does it affect concurrency choices?",
        "question_type": InterviewQuestionType.CONCEPTUAL,
        "difficulty": Difficulty.MEDIUM,
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "expected_answer": "The Global Interpreter Lock allows only one thread to execute Python bytecode at a time in CPython. CPU-bound work benefits from multiprocessing or native extensions; I/O-bound work can use threads or asyncio.",
        "explanation": None,
        "key_points": [
            "One bytecode-executing thread in CPython",
            "CPU-bound → processes / native code",
            "I/O-bound → threads or asyncio",
            "Not a language-wide rule for all runtimes",
        ],
        "skills": ["Python"],
        "roles": ["Python Developer", "Data Engineer"],
    },
    {
        "slug": "de-etl-vs-elt",
        "question_text": "Compare ETL and ELT for modern cloud data platforms.",
        "question_type": InterviewQuestionType.ARCHITECTURE,
        "difficulty": Difficulty.MEDIUM,
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "expected_answer": "ETL transforms before load, useful when target compute is limited or transformations must happen upstream. ELT loads raw/staging first and transforms in the warehouse (dbt etc.), leveraging scalable cloud compute and keeping lineage in SQL.",
        "explanation": None,
        "key_points": [
            "ETL: transform then load",
            "ELT: load then transform in warehouse",
            "Cloud warehouses favor ELT/dbt",
            "Tradeoffs: cost, governance, latency",
        ],
        "skills": ["Data Engineering", "SQL"],
        "roles": ["Data Engineer"],
    },
    {
        "slug": "flink-checkpointing",
        "question_text": "What is Apache Flink checkpointing and why does it matter for exactly-once processing?",
        "question_type": InterviewQuestionType.TECHNICAL,
        "difficulty": Difficulty.HARD,
        "experience_level": ExperienceLevel.SENIOR,
        "expected_answer": "Checkpointing captures consistent distributed snapshots of operator state and offsets. On failure, Flink restores from the last successful checkpoint. Combined with transactional sinks, this enables end-to-end exactly-once semantics.",
        "explanation": None,
        "key_points": [
            "Distributed consistent snapshots",
            "State and offset recovery",
            "Supports exactly-once with sinks",
            "Checkpoint storage and alignment matter",
        ],
        "skills": ["Apache Flink", "Data Engineering"],
        "roles": ["Data Engineer"],
    },
    {
        "slug": "snowflake-micro-partitions",
        "question_text": "Explain Snowflake micro-partitions and pruning.",
        "question_type": InterviewQuestionType.TECHNICAL,
        "difficulty": Difficulty.MEDIUM,
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "expected_answer": "Snowflake stores table data in immutable micro-partitions with metadata (min/max, distinct counts). The optimizer prunes partitions that cannot satisfy filters, reducing scanned bytes and cost.",
        "explanation": None,
        "key_points": [
            "Immutable columnar micro-partitions",
            "Metadata enables pruning",
            "Filters reduce scanned bytes",
            "Clustering can improve pruning",
        ],
        "skills": ["Snowflake", "SQL"],
        "roles": ["Data Engineer"],
    },
    {
        "slug": "aws-s3-data-lake-design",
        "question_text": "How would you design an S3-based data lake landing zone for batch analytics?",
        "question_type": InterviewQuestionType.ARCHITECTURE,
        "difficulty": Difficulty.MEDIUM,
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "expected_answer": "Separate raw/curated/serving prefixes, enforce partitioning by date/source, use lifecycle policies, IAM least privilege, encryption, and catalog metadata (Glue). Avoid small files; compact in curated layers.",
        "explanation": None,
        "key_points": [
            "Layered prefixes (raw/curated/serving)",
            "Partitioning and file size hygiene",
            "Security: IAM, encryption, audit",
            "Catalog/metadata for discovery",
        ],
        "skills": ["AWS", "Data Engineering"],
        "roles": ["Data Engineer", "Cloud Engineer"],
        "companies": ["Accenture", "Deloitte"],
    },
    {
        "slug": "devops-blue-green",
        "question_text": "Explain blue-green deployments and their failure modes.",
        "question_type": InterviewQuestionType.CONCEPTUAL,
        "difficulty": Difficulty.MEDIUM,
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "expected_answer": "Blue-green keeps two environments; traffic switches after validation. Benefits: fast rollback. Risks: schema compatibility, stateful services, and incomplete smoke tests before cutover.",
        "explanation": None,
        "key_points": [
            "Two parallel environments",
            "Instant cutover/rollback",
            "Schema and state compatibility",
            "Need solid smoke checks",
        ],
        "skills": ["DevOps", "Kubernetes"],
        "roles": ["DevOps Engineer"],
    },
    {
        "slug": "soc-triage-alert",
        "question_text": "Walk through how you would triage a high-severity authentication failure spike alert.",
        "question_type": InterviewQuestionType.SCENARIO,
        "difficulty": Difficulty.MEDIUM,
        "experience_level": ExperienceLevel.JUNIOR,
        "expected_answer": "Validate alert fidelity, scope affected identities/sources, correlate with threat intel and change windows, contain if malicious (block IP/user), preserve evidence, escalate per runbook, and document findings.",
        "explanation": None,
        "key_points": [
            "Validate and scope the alert",
            "Correlate logs and context",
            "Containment and escalation",
            "Evidence and documentation",
        ],
        "skills": ["Cybersecurity", "SOC"],
        "roles": ["SOC Analyst", "Cybersecurity Analyst"],
    },
    {
        "slug": "rag-chunking-strategy",
        "question_text": "How do you choose a chunking strategy for a RAG system?",
        "question_type": InterviewQuestionType.TECHNICAL,
        "difficulty": Difficulty.MEDIUM,
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "expected_answer": "Balance retrieval precision and context completeness. Prefer semantic/structure-aware chunks with overlap, evaluate with retrieval metrics, and tune by document type. Avoid chunks that are too small (lose meaning) or too large (dilute embeddings).",
        "explanation": None,
        "key_points": [
            "Precision vs context tradeoff",
            "Structure-aware chunking + overlap",
            "Evaluate retrieval quality",
            "Document-type specific tuning",
        ],
        "skills": ["RAG", "Generative AI"],
        "roles": ["RAG Engineer", "GenAI Engineer", "AI Engineer"],
    },
    {
        "slug": "agents-tool-calling-safety",
        "question_text": "What safety controls would you put around an AI agent that can call tools?",
        "question_type": InterviewQuestionType.ARCHITECTURE,
        "difficulty": Difficulty.HARD,
        "experience_level": ExperienceLevel.SENIOR,
        "expected_answer": "Least-privilege tool scopes, allowlists, human-in-the-loop for high-risk actions, rate limits, audit logs, input/output validation, and sandboxing. Treat model output as untrusted until validated.",
        "explanation": None,
        "key_points": [
            "Least privilege and allowlists",
            "Human approval for risky actions",
            "Validation and sandboxing",
            "Auditing and rate limits",
        ],
        "skills": ["AI Agents", "MCP"],
        "roles": ["AI Agent Engineer", "AI Engineer"],
    },
    {
        "slug": "behavioral-conflict",
        "question_text": "Tell me about a time you handled conflict on a project team.",
        "question_type": InterviewQuestionType.BEHAVIORAL,
        "difficulty": Difficulty.EASY,
        "experience_level": ExperienceLevel.JUNIOR,
        "expected_answer": "Use STAR: describe Situation, Task, Action (listening, clarifying goals, proposing a compromise or data-backed decision), and Result with reflection. Focus on professional disagreement, not personal attacks.",
        "explanation": "Guidance only — do not invent personal stories for the candidate.",
        "key_points": [
            "Situation context",
            "Task/ownership",
            "Actions taken",
            "Result and learning",
        ],
        "skills": ["Communication"],
        "roles": ["Data Engineer", "Python Developer"],
    },
    {
        "slug": "behavioral-failure",
        "question_text": "Describe a failure and what you learned from it.",
        "question_type": InterviewQuestionType.BEHAVIORAL,
        "difficulty": Difficulty.EASY,
        "experience_level": ExperienceLevel.JUNIOR,
        "expected_answer": "Pick a real professional miss, own it, explain root cause, corrective action, and lasting process change. Interviewers look for accountability and growth, not blame.",
        "explanation": "STAR + reflection.",
        "key_points": [
            "Clear ownership of the miss",
            "Root cause analysis",
            "Corrective action",
            "Process change / learning",
        ],
        "skills": ["Communication"],
        "roles": ["Data Engineer"],
    },
    {
        "slug": "hr-why-this-role",
        "question_text": "Why are you interested in this role?",
        "question_type": InterviewQuestionType.HR,
        "difficulty": Difficulty.EASY,
        "experience_level": ExperienceLevel.FRESHER,
        "expected_answer": "Connect your skills and interests to the role's responsibilities and the team's domain. Be specific about problems you want to solve; avoid generic praise. There is no single perfect script.",
        "explanation": "Preparation guidance, not a mandatory script.",
        "key_points": [
            "Link skills to role needs",
            "Specific motivations",
            "Team/domain fit",
            "Avoid generic statements",
        ],
        "skills": ["Communication"],
        "roles": ["Data Engineer", "Python Developer"],
        "companies": ["TCS", "Infosys", "Cognizant"],
    },
    {
        "slug": "troubleshooting-pipeline-latency",
        "question_text": "Your streaming pipeline latency spiked after a deployment. How do you investigate?",
        "question_type": InterviewQuestionType.TROUBLESHOOTING,
        "difficulty": Difficulty.HARD,
        "experience_level": ExperienceLevel.SENIOR,
        "expected_answer": "Compare pre/post metrics, check consumer lag, GC, backpressure, network, schema changes, and recent config. Bisect deployment, verify checkpoints/sinks, and roll back if needed while capturing evidence.",
        "explanation": None,
        "key_points": [
            "Establish baseline vs spike",
            "Lag/backpressure/resources",
            "Change correlation",
            "Mitigate and document",
        ],
        "skills": ["Data Engineering", "Apache Flink"],
        "roles": ["Data Engineer"],
    },
]

PACKS: list[dict] = [
    {
        "slug": "sql-interview-essentials",
        "title": "SQL Interview Essentials",
        "description": "Core SQL interview topics for analysts and engineers.",
        "experience_level": ExperienceLevel.JUNIOR,
        "role": "SQL Developer",
        "question_slugs": [
            "sql-window-functions-rank",
            "sql-indexing-tradeoffs",
            "de-etl-vs-elt",
        ],
    },
    {
        "slug": "data-engineer-intermediate",
        "title": "Data Engineer — Intermediate",
        "description": "ETL/ELT, cloud lake, and warehouse fundamentals.",
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "role": "Data Engineer",
        "question_slugs": [
            "de-etl-vs-elt",
            "snowflake-micro-partitions",
            "aws-s3-data-lake-design",
            "sql-window-functions-rank",
            "flink-checkpointing",
        ],
    },
    {
        "slug": "flink-fundamentals",
        "title": "Flink Fundamentals",
        "description": "Checkpointing and streaming troubleshooting.",
        "experience_level": ExperienceLevel.SENIOR,
        "role": "Data Engineer",
        "question_slugs": [
            "flink-checkpointing",
            "troubleshooting-pipeline-latency",
            "de-etl-vs-elt",
        ],
    },
    {
        "slug": "python-backend-interview",
        "title": "Python Backend Interview",
        "description": "Concurrency and Python fundamentals.",
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "role": "Python Developer",
        "question_slugs": [
            "python-gil-concurrency",
            "sql-window-functions-rank",
            "sql-indexing-tradeoffs",
        ],
    },
    {
        "slug": "genai-rag-essentials",
        "title": "GenAI & RAG Essentials",
        "description": "Chunking and agent tool safety.",
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "role": "GenAI Engineer",
        "question_slugs": [
            "rag-chunking-strategy",
            "agents-tool-calling-safety",
            "python-gil-concurrency",
        ],
    },
    {
        "slug": "devops-engineer-basics",
        "title": "DevOps Engineer Basics",
        "description": "Deployment strategies for interviews.",
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "role": "DevOps Engineer",
        "question_slugs": [
            "devops-blue-green",
            "aws-s3-data-lake-design",
            "troubleshooting-pipeline-latency",
        ],
    },
    {
        "slug": "soc-analyst-essentials",
        "title": "SOC Analyst Essentials",
        "description": "Alert triage and investigation framing.",
        "experience_level": ExperienceLevel.JUNIOR,
        "role": "SOC Analyst",
        "question_slugs": [
            "soc-triage-alert",
            "behavioral-conflict",
            "troubleshooting-pipeline-latency",
        ],
    },
    {
        "slug": "behavioral-essentials",
        "title": "Behavioral Essentials",
        "description": "STAR-oriented behavioral preparation.",
        "experience_level": ExperienceLevel.JUNIOR,
        "role": None,
        "question_slugs": [
            "behavioral-conflict",
            "behavioral-failure",
            "hr-why-this-role",
        ],
    },
    {
        "slug": "hr-final-round",
        "title": "HR Final Round",
        "description": "Common HR questions with preparation guidance.",
        "experience_level": ExperienceLevel.FRESHER,
        "role": None,
        "question_slugs": [
            "hr-why-this-role",
            "behavioral-conflict",
            "behavioral-failure",
        ],
    },
    {
        "slug": "tcs-skills-prep",
        "title": "TCS — Skills-Oriented Prep",
        "description": "Commonly relevant skills practice. Not affiliated with TCS.",
        "experience_level": ExperienceLevel.FRESHER,
        "role": None,
        "company": "TCS",
        "question_slugs": [
            "hr-why-this-role",
            "sql-window-functions-rank",
            "behavioral-conflict",
        ],
    },
    {
        "slug": "accenture-skills-prep",
        "title": "Accenture — Skills-Oriented Prep",
        "description": "Cloud/data skills commonly relevant in consulting interviews.",
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "role": "Data Engineer",
        "company": "Accenture",
        "question_slugs": [
            "aws-s3-data-lake-design",
            "de-etl-vs-elt",
            "snowflake-micro-partitions",
        ],
    },
    {
        "slug": "ai-agents-pack",
        "title": "AI Agents",
        "description": "Tool calling safety for agent interviews.",
        "experience_level": ExperienceLevel.SENIOR,
        "role": "AI Agent Engineer",
        "question_slugs": [
            "agents-tool-calling-safety",
            "rag-chunking-strategy",
            "python-gil-concurrency",
        ],
    },
]


async def _ensure_skill(session, name: str) -> Skill:
    slug = _slugify(name)
    row = (await session.execute(select(Skill).where(Skill.slug == slug))).scalar_one_or_none()
    if row:
        return row
    row = Skill(id=uuid4(), name=name, slug=slug)
    session.add(row)
    await session.flush()
    return row


async def _ensure_role(session, name: str) -> JobRole:
    slug = _slugify(name)
    row = (await session.execute(select(JobRole).where(JobRole.slug == slug))).scalar_one_or_none()
    if row:
        return row
    row = JobRole(id=uuid4(), name=name, slug=slug)
    session.add(row)
    await session.flush()
    return row


async def _ensure_company(session, name: str) -> Company:
    slug = _slugify(name)
    row = (await session.execute(select(Company).where(Company.slug == slug))).scalar_one_or_none()
    if row:
        return row
    row = Company(id=uuid4(), name=name, slug=slug)
    session.add(row)
    await session.flush()
    return row


async def seed_build8_content() -> None:
    async with AsyncSessionLocal() as session:
        q_by_slug: dict[str, InterviewQuestion] = {}
        for item in QUESTIONS:
            existing = (
                await session.execute(select(InterviewQuestion).where(InterviewQuestion.slug == item["slug"]))
            ).scalar_one_or_none()
            if existing:
                q_by_slug[item["slug"]] = existing
                continue
            q = InterviewQuestion(
                id=uuid4(),
                slug=item["slug"],
                question_text=item["question_text"],
                question_type=item["question_type"],
                difficulty=item["difficulty"],
                experience_level=item["experience_level"],
                expected_answer=item["expected_answer"],
                explanation=item.get("explanation"),
                source_type=ContentSourceType.MANUAL,
                review_status=ContentReviewStatus.APPROVED,
                content_hash=_hash(item["question_text"]),
                is_active=True,
            )
            session.add(q)
            await session.flush()
            for i, point in enumerate(item["key_points"]):
                session.add(
                    InterviewAnswerPoint(
                        id=uuid4(), question_id=q.id, point_text=point, sort_order=i
                    )
                )
            for skill_name in item.get("skills", []):
                skill = await _ensure_skill(session, skill_name)
                session.add(InterviewQuestionSkill(question_id=q.id, skill_id=skill.id))
            for role_name in item.get("roles", []):
                role = await _ensure_role(session, role_name)
                session.add(InterviewQuestionRole(question_id=q.id, role_id=role.id))
            for company_name in item.get("companies", []):
                company = await _ensure_company(session, company_name)
                session.add(InterviewQuestionCompany(question_id=q.id, company_id=company.id))
            q_by_slug[item["slug"]] = q

        for pack_def in PACKS:
            existing = (
                await session.execute(select(InterviewPack).where(InterviewPack.slug == pack_def["slug"]))
            ).scalar_one_or_none()
            role_id = None
            company_id = None
            if pack_def.get("role"):
                role_id = (await _ensure_role(session, pack_def["role"])).id
            if pack_def.get("company"):
                company_id = (await _ensure_company(session, pack_def["company"])).id
            if existing is None:
                pack = InterviewPack(
                    id=uuid4(),
                    slug=pack_def["slug"],
                    title=pack_def["title"],
                    description=pack_def["description"],
                    experience_level=pack_def.get("experience_level"),
                    target_role_id=role_id,
                    target_company_id=company_id,
                    is_active=True,
                )
                session.add(pack)
                await session.flush()
            else:
                pack = existing
                pack.is_active = True
                pack.description = pack_def["description"]
                pack.target_role_id = role_id
                pack.target_company_id = company_id
            # Rebuild mappings idempotently
            existing_links = (
                await session.execute(
                    select(InterviewPackQuestion).where(InterviewPackQuestion.pack_id == pack.id)
                )
            ).scalars().all()
            for link in existing_links:
                await session.delete(link)
            await session.flush()
            for i, qslug in enumerate(pack_def["question_slugs"]):
                q = q_by_slug.get(qslug)
                if not q:
                    continue
                session.add(
                    InterviewPackQuestion(
                        pack_id=pack.id, question_id=q.id, sort_order=i, section_name=None
                    )
                )

        # Ensure common company catalog rows for Company Prep UI
        for name in ["TCS", "Accenture", "Infosys", "Cognizant", "Capgemini", "Deloitte"]:
            await _ensure_company(session, name)

        await session.commit()


if __name__ == "__main__":
    import asyncio

    asyncio.run(seed_build8_content())
    print("Build 8 interview seed complete")
