import asyncio
import re
from uuid import uuid4

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal, engine
from app.models.enums import Difficulty, QuestionType, UserRole
from app.models.question import Question, QuestionOption
from app.models.tagging import Company, JobRole, QuestionRole, QuestionSkill, Skill
from app.models.taxonomy import Category, Domain, Topic
from app.models.user import User
from app.seed.taxonomy_data import COMPANIES, JOB_ROLES, SKILLS, TAXONOMY


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


SAMPLE_QUESTIONS = [
    {
        "domain": "placement",
        "category": "aptitude",
        "topic": "percentages",
        "difficulty": "easy",
        "text": "If the price of an item increases from 200 to 250, what is the percentage increase?",
        "explanation": "Increase = 50. Percentage increase = (50/200) * 100 = 25%.",
        "options": [("20%", False), ("25%", True), ("30%", False), ("50%", False)],
        "skills": ["percentages"],
    },
    {
        "domain": "placement",
        "category": "aptitude",
        "topic": "time-and-work",
        "difficulty": "medium",
        "text": "A can complete a work in 10 days and B in 15 days. In how many days will they finish together?",
        "explanation": "Combined rate = 1/10 + 1/15 = 1/6. Time = 6 days.",
        "options": [("5 days", False), ("6 days", True), ("8 days", False), ("12 days", False)],
        "skills": ["probability"],
    },
    {
        "domain": "placement",
        "category": "aptitude",
        "topic": "probability",
        "difficulty": "medium",
        "text": "What is the probability of getting exactly one head in two coin tosses?",
        "explanation": "Outcomes with one head: HT, TH. Probability = 2/4 = 1/2.",
        "options": [("1/4", False), ("1/2", True), ("3/4", False), ("1", False)],
        "skills": ["probability"],
    },
    {
        "domain": "placement",
        "category": "aptitude",
        "topic": "series",
        "difficulty": "easy",
        "text": "Find the next number in the series: 2, 4, 8, 16, ?",
        "explanation": "Each term doubles. Next number is 32.",
        "options": [("24", False), ("28", False), ("32", True), ("64", False)],
        "skills": ["probability"],
    },
    {
        "domain": "placement",
        "category": "aptitude",
        "topic": "grammar",
        "difficulty": "easy",
        "text": "Choose the correct sentence.",
        "explanation": "Subject-verb agreement requires 'team members were'.",
        "options": [
            ("The team were ready.", False),
            ("The team members were ready.", True),
            ("The team members was ready.", False),
            ("Team members is ready.", False),
        ],
        "skills": ["percentages"],
    },
    {
        "domain": "technical",
        "category": "python",
        "topic": "fundamentals",
        "difficulty": "easy",
        "text": "What is the output of len([1, 2, [3, 4]]) in Python?",
        "explanation": "The list has three top-level elements.",
        "options": [("2", False), ("3", True), ("4", False), ("Error", False)],
        "skills": ["python basics"],
    },
    {
        "domain": "technical",
        "category": "sql",
        "topic": "queries",
        "difficulty": "medium",
        "text": "Which SQL clause is used to filter rows before aggregation?",
        "explanation": "WHERE filters rows before grouping/aggregation.",
        "options": [("HAVING", False), ("WHERE", True), ("ORDER BY", False), ("GROUP BY", False)],
        "skills": ["sql joins"],
    },
    {
        "domain": "technical",
        "category": "dbms",
        "topic": "concepts",
        "difficulty": "medium",
        "text": "Which normal form removes partial dependency on a composite key?",
        "explanation": "Second Normal Form (2NF) removes partial dependencies.",
        "options": [("1NF", False), ("2NF", True), ("3NF", False), ("BCNF", False)],
        "skills": ["sql joins"],
    },
    {
        "domain": "technical",
        "category": "operating-systems",
        "topic": "core-concepts",
        "difficulty": "medium",
        "text": "Which scheduling algorithm can cause starvation?",
        "explanation": "Priority scheduling may starve lower-priority processes.",
        "options": [
            ("FCFS", False),
            ("Round Robin", False),
            ("Priority Scheduling", True),
            ("SJF without aging", False),
        ],
        "skills": ["networking"],
    },
    {
        "domain": "technical",
        "category": "computer-networks",
        "topic": "fundamentals",
        "difficulty": "easy",
        "text": "Which layer of the OSI model handles routing?",
        "explanation": "Routing is a Network layer (Layer 3) responsibility.",
        "options": [("Data Link", False), ("Network", True), ("Transport", False), ("Session", False)],
        "skills": ["networking"],
    },
    {
        "domain": "technical",
        "category": "git",
        "topic": "workflow",
        "difficulty": "easy",
        "text": "Which command creates a new branch and switches to it?",
        "explanation": "git checkout -b or git switch -c creates and switches.",
        "options": [
            ("git branch new", False),
            ("git checkout -b feature", True),
            ("git merge feature", False),
            ("git pull origin", False),
        ],
        "skills": ["python basics"],
    },
    {
        "domain": "technical",
        "category": "machine-learning",
        "topic": "fundamentals",
        "difficulty": "medium",
        "text": "Which metric is most appropriate for imbalanced classification?",
        "explanation": "F1-score balances precision and recall for imbalance.",
        "options": [("Accuracy", False), ("F1-score", True), ("MSE", False), ("R2", False)],
        "skills": ["python basics"],
    },
    {
        "domain": "ai",
        "category": "generative-ai",
        "topic": "embeddings",
        "difficulty": "medium",
        "text": "What is cosine similarity commonly used for in embedding systems?",
        "explanation": "Cosine similarity measures directional similarity between vectors.",
        "options": [
            ("Token counting", False),
            ("Vector similarity search", True),
            ("Model fine-tuning", False),
            ("Prompt injection detection", False),
        ],
        "skills": ["vector similarity", "embeddings"],
        "roles": ["GenAI Engineer", "AI Engineer", "RAG Engineer"],
    },
    {
        "domain": "ai",
        "category": "generative-ai",
        "topic": "rag",
        "difficulty": "medium",
        "text": "What is the primary purpose of chunking in RAG pipelines?",
        "explanation": "Chunking splits documents into retrievable segments.",
        "options": [
            ("Reduce model size", False),
            ("Improve retrieval granularity", True),
            ("Encrypt documents", False),
            ("Generate embeddings faster only", False),
        ],
        "skills": ["rag retrieval", "embeddings"],
        "roles": ["RAG Engineer"],
    },
    {
        "domain": "ai",
        "category": "prompt-engineering",
        "topic": "zero-shot",
        "difficulty": "easy",
        "text": "Zero-shot prompting means:",
        "explanation": "Zero-shot uses instructions without labeled examples.",
        "options": [
            ("Providing many examples", False),
            ("No examples, only instruction", True),
            ("Fine-tuning the model", False),
            ("Using retrieval only", False),
        ],
        "skills": ["prompt design"],
    },
    {
        "domain": "ai",
        "category": "ai-agents",
        "topic": "agent-loops",
        "difficulty": "hard",
        "text": "In an agent loop, what typically happens after tool execution?",
        "explanation": "The agent observes tool output and decides the next action.",
        "options": [
            ("Immediate termination", False),
            ("Observation and next planning step", True),
            ("Automatic fine-tuning", False),
            ("Database migration", False),
        ],
        "skills": ["prompt design"],
    },
    {
        "domain": "cloud",
        "category": "cloud-fundamentals",
        "topic": "architecture",
        "difficulty": "medium",
        "text": "Which cloud principle improves fault tolerance across zones?",
        "explanation": "Multi-AZ deployment reduces single-zone failure impact.",
        "options": [
            ("Single instance scaling", False),
            ("Multi-AZ deployment", True),
            ("Local-only storage", False),
            ("Shared admin credentials", False),
        ],
        "skills": ["cloud architecture"],
    },
    {
        "domain": "devops",
        "category": "devops-core",
        "topic": "ci-cd",
        "difficulty": "easy",
        "text": "What is the main goal of Continuous Integration?",
        "explanation": "CI integrates code frequently with automated validation.",
        "options": [
            ("Manual monthly releases only", False),
            ("Frequent automated integration and testing", True),
            ("Remove all tests", False),
            ("Disable version control", False),
        ],
        "skills": ["cloud architecture"],
    },
    {
        "domain": "cybersecurity",
        "category": "web-security",
        "topic": "owasp",
        "difficulty": "medium",
        "text": "Broken Access Control in OWASP Top 10 primarily refers to:",
        "explanation": "Users accessing resources or actions beyond their permissions.",
        "options": [
            ("Slow page loads", False),
            ("Unauthorized access to resources", True),
            ("Outdated CSS", False),
            ("Missing favicon", False),
        ],
        "skills": ["networking"],
    },
    {
        "domain": "cybersecurity",
        "category": "web-security",
        "topic": "sql-injection",
        "difficulty": "medium",
        "text": "Best defense against SQL injection is:",
        "explanation": "Parameterized queries prevent untrusted input altering SQL structure.",
        "options": [
            ("String concatenation", False),
            ("Parameterized queries / prepared statements", True),
            ("Hiding error messages only", False),
            ("Using SELECT *", False),
        ],
        "skills": ["sql joins"],
    },
]


def _expand_questions() -> list[dict]:
    expanded = list(SAMPLE_QUESTIONS)
    templates = [
        ("placement", "aptitude", "ratio-and-proportion", "If a:b = 2:3 and b:c = 3:4, find a:c."),
        ("placement", "aptitude", "simple-interest", "Find SI on 5000 at 10% for 2 years."),
        ("placement", "aptitude", "compound-interest", "What is CI on 1000 at 10% for 2 years compounded annually?"),
        ("placement", "aptitude", "directions", "A person walks 5 km north, then 3 km east. How far from start?"),
        ("placement", "aptitude", "syllogisms", "All cats are mammals. Some mammals are pets. Which conclusion follows?"),
        ("technical", "python", "fundamentals", "Which Python data type is mutable?"),
        ("technical", "linux", "commands", "Which command lists files including hidden ones?"),
        ("technical", "oop", "principles", "Which OOP principle restricts direct access to internal state?"),
        ("technical", "data-analytics", "fundamentals", "Which chart is best for part-to-whole comparison?"),
        ("ai", "generative-ai", "llm-fundamentals", "What does a token represent in LLMs?"),
        ("ai", "generative-ai", "tool-calling", "Why do agents use tool calling?"),
        ("ai", "prompt-engineering", "few-shot", "Few-shot prompting improves performance by:"),
        ("ai", "prompt-engineering", "prompt-injection", "Prompt injection attempts to:"),
        ("cloud", "aws", "compute", "Which AWS service provides virtual servers?"),
        ("cloud", "azure", "compute", "Azure VMs belong to which category?"),
        ("cloud", "gcp", "compute", "Google Compute Engine provides:"),
        ("cybersecurity", "security-fundamentals", "cryptography", "Symmetric encryption uses:"),
    ]
    options_cycle = [
        [("Option A", False), ("Option B", True), ("Option C", False), ("Option D", False)],
        [("True", True), ("False", False)],
    ]
    for index, (domain, category, topic, text) in enumerate(templates):
        expanded.append(
            {
                "domain": domain,
                "category": category,
                "topic": topic,
                "difficulty": "easy" if index % 2 == 0 else "medium",
                "text": text,
                "explanation": "Sample development question for engine testing.",
                "options": options_cycle[index % 2],
                "skills": ["python basics"],
            }
        )
    return expanded


async def seed_all() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(User).where(User.email == "admin@jobready.dev"))
        if existing.scalar_one_or_none():
            print("Seed data already exists. Skipping.")
            return

        admin = User(
            email="admin@jobready.dev",
            username="admin",
            full_name="Platform Admin",
            password_hash=hash_password("Admin123!"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin)

        domain_map: dict[str, Domain] = {}
        category_map: dict[str, Category] = {}
        topic_map: dict[str, Topic] = {}

        for domain_data in TAXONOMY:
            domain = Domain(
                name=domain_data["name"],
                slug=domain_data["slug"],
                description=f"{domain_data['name']} domain",
                is_active=True,
            )
            session.add(domain)
            await session.flush()
            domain_map[domain.slug] = domain
            for category_data in domain_data["categories"]:
                category = Category(
                    domain_id=domain.id,
                    name=category_data["name"],
                    slug=category_data["slug"],
                    is_active=True,
                )
                session.add(category)
                await session.flush()
                category_map[f"{domain.slug}:{category.slug}"] = category
                for topic_data in category_data["topics"]:
                    topic = Topic(
                        category_id=category.id,
                        name=topic_data["name"],
                        slug=topic_data["slug"],
                        is_active=True,
                    )
                    session.add(topic)
                    await session.flush()
                    topic_map[f"{domain.slug}:{category.slug}:{topic.slug}"] = topic

        skill_map: dict[str, Skill] = {}
        for skill_name in SKILLS:
            skill = Skill(name=skill_name, slug=slugify(skill_name))
            session.add(skill)
            await session.flush()
            skill_map[skill_name] = skill

        role_map: dict[str, JobRole] = {}
        for role_name in JOB_ROLES:
            role = JobRole(name=role_name, slug=slugify(role_name))
            session.add(role)
            await session.flush()
            role_map[role_name] = role

        for company_name in COMPANIES:
            session.add(Company(name=company_name, slug=slugify(company_name)))
        await session.flush()

        for item in _expand_questions():
            domain = domain_map[item["domain"]]
            category = category_map[f"{item['domain']}:{item['category']}"]
            topic = topic_map[f"{item['domain']}:{item['category']}:{item['topic']}"]
            question = Question(
                question_type=QuestionType.SINGLE_CHOICE,
                question_text=item["text"],
                explanation=item["explanation"],
                difficulty=Difficulty(item["difficulty"]),
                domain_id=domain.id,
                category_id=category.id,
                topic_id=topic.id,
                marks=1.0,
                negative_marks=0.25,
                estimated_time_seconds=60,
                is_active=True,
                is_premium=False,
                is_sample=True,
                created_by=admin.id,
                options=[
                    QuestionOption(
                        id=uuid4(),
                        option_text=text,
                        is_correct=correct,
                        sort_order=idx,
                    )
                    for idx, (text, correct) in enumerate(item["options"])
                ],
            )
            session.add(question)
            await session.flush()
            for skill_name in item.get("skills", []):
                skill = skill_map.get(skill_name)
                if skill:
                    session.add(QuestionSkill(question_id=question.id, skill_id=skill.id))
            for role_name in item.get("roles", []):
                role = role_map.get(role_name)
                if role:
                    session.add(QuestionRole(question_id=question.id, role_id=role.id))

        await session.commit()
        print("Seed completed successfully.")


async def seed_coding_problems() -> None:
    from app.seed.coding_data import seed_coding_problems as _seed_coding

    await _seed_coding()


async def seed_sql_problems() -> None:
    from app.seed.sql_data import seed_sql_problems as _seed_sql

    await _seed_sql()


async def seed_learn_content() -> None:
    from app.seed.learn_data import seed_learn_content as _seed_learn

    await _seed_learn()


def run_seed() -> None:
    asyncio.run(_run())


async def ensure_content_factory_catalog() -> None:
    """Idempotent extra skills/roles for interview Q&A tagging."""
    from app.models.interview import JobListing

    async with AsyncSessionLocal() as session:
        for skill_name in SKILLS:
            existing = await session.execute(select(Skill).where(Skill.slug == slugify(skill_name)))
            if existing.scalar_one_or_none() is None:
                session.add(Skill(name=skill_name, slug=slugify(skill_name)))
        for role_name in JOB_ROLES:
            existing = await session.execute(select(JobRole).where(JobRole.slug == slugify(role_name)))
            if existing.scalar_one_or_none() is None:
                session.add(JobRole(name=role_name, slug=slugify(role_name)))
        for company_name in COMPANIES:
            existing = await session.execute(select(Company).where(Company.slug == slugify(company_name)))
            if existing.scalar_one_or_none() is None:
                session.add(Company(name=company_name, slug=slugify(company_name)))
        await session.flush()
        demo_job_slug = "acme-data-engineer"
        job = await session.execute(select(JobListing).where(JobListing.slug == demo_job_slug))
        if job.scalar_one_or_none() is None:
            company = (
                await session.execute(select(Company).where(Company.slug == slugify("Acme Labs")))
            ).scalar_one_or_none()
            session.add(
                JobListing(
                    slug=demo_job_slug,
                    title="Acme Data Engineer",
                    company_id=company.id if company else None,
                    is_active=True,
                )
            )
        await session.commit()


async def _run() -> None:
    await seed_all()
    await ensure_content_factory_catalog()
    await seed_coding_problems()
    await seed_sql_problems()
    await seed_learn_content()
    await engine.dispose()
