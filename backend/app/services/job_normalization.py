"""Deterministic job normalization: hashing, skills, roles, URLs, experience."""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from typing import Any

from app.models.job_enums import EmploymentType, JobRoleMappingSource, JobSkillImportance, WorkMode

_SKILL_ALIASES: dict[str, str] = {
    "postgresql": "SQL",
    "postgres": "SQL",
    "mysql": "SQL",
    "aws": "AWS",
    "amazon web services": "AWS",
    "apache flink": "Apache Flink",
    "flink": "Apache Flink",
    "powerbi": "Power BI",
    "power bi": "Power BI",
    "genai": "Generative AI",
    "generative ai": "Generative AI",
    "rag": "RAG",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "python": "Python",
    "sql": "SQL",
    "spark": "Spark",
    "snowflake": "Snowflake",
    "databricks": "Databricks",
    "devops": "DevOps",
    "soc": "SOC",
}

_ROLE_RULES: list[tuple[str, list[str]]] = [
    ("Data Engineer", ["data engineer", "etl developer", "pipeline engineer", "data engineering"]),
    ("Data Analyst", ["data analyst", "bi analyst", "business intelligence analyst"]),
    ("Python Developer", ["python developer", "python engineer", "backend python"]),
    ("SQL Developer", ["sql developer", "database developer"]),
    ("DevOps Engineer", ["devops", "site reliability", "sre", "platform engineer"]),
    ("Cloud Engineer", ["cloud engineer", "cloud architect"]),
    ("GenAI Engineer", ["genai engineer", "generative ai engineer"]),
    ("AI Engineer", ["ai engineer", "machine learning engineer", "ml engineer"]),
    ("SOC Analyst", ["soc analyst", "security analyst"]),
    ("Cybersecurity Analyst", ["cybersecurity analyst", "cyber security"]),
]


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.lower().strip())


def slugify_job(title: str, company: str, suffix: str = "") -> str:
    base = re.sub(r"[^a-z0-9]+", "-", f"{title}-{company}".lower()).strip("-")
    if suffix:
        base = f"{base}-{suffix[:8]}"
    return base[:170]


def validate_url(url: str | None) -> str | None:
    if not url or not url.strip():
        return None
    u = url.strip()
    lower = u.lower()
    if lower.startswith("javascript:") or lower.startswith("data:"):
        raise ValueError("URL scheme not allowed")
    if not (lower.startswith("http://") or lower.startswith("https://")):
        raise ValueError("URL must use http or https")
    return u


def parse_experience(text: str | None) -> tuple[int | None, int | None]:
    if not text:
        return None, None
    t = text.lower()
    m = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*year", t)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d+)\s*\+\s*year", t)
    if m:
        v = int(m.group(1))
        return v, None
    m = re.search(r"minimum\s+(\d+)\s*year", t)
    if m:
        v = int(m.group(1))
        return v, None
    m = re.search(r"(\d+)\s+year", t)
    if m:
        v = int(m.group(1))
        return v, v
    return None, None


def normalize_work_mode(value: str | None, is_remote: bool | None = None) -> WorkMode | None:
    if not value:
        if is_remote:
            return WorkMode.REMOTE
        return None
    v = value.lower().strip()
    if "remote" in v and "hybrid" not in v:
        return WorkMode.REMOTE
    if "hybrid" in v:
        return WorkMode.HYBRID
    if "onsite" in v or "on-site" in v or "office" in v:
        return WorkMode.ONSITE
    return WorkMode.UNKNOWN


def normalize_employment_type(value: str | None) -> EmploymentType | None:
    if not value:
        return None
    v = value.lower().strip()
    if "full" in v:
        return EmploymentType.FULL_TIME
    if "part" in v:
        return EmploymentType.PART_TIME
    if "contract" in v:
        return EmploymentType.CONTRACT
    if "intern" in v:
        return EmploymentType.INTERNSHIP
    return EmploymentType.UNKNOWN


def job_content_hash(
    *,
    normalized_title: str,
    company: str,
    location: str | None,
    description_snippet: str,
    external_id: str | None = None,
    source_slug: str | None = None,
) -> str:
    parts = [
        normalized_title,
        company.lower().strip(),
        (location or "").lower().strip(),
        description_snippet[:500].lower().strip(),
        (external_id or "").strip(),
        (source_slug or "").strip(),
    ]
    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def extract_skill_names(
    text: str,
    known_skills: dict[str, str],
) -> list[tuple[str, JobSkillImportance]]:
    """Return (skill_name, importance) from known skill catalog."""
    if not text:
        return []
    lower = text.lower()
    found: dict[str, JobSkillImportance] = {}
    for alias, canonical in _SKILL_ALIASES.items():
        if canonical not in known_skills:
            continue
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, lower):
            found[canonical] = JobSkillImportance.MENTIONED
    for name in known_skills:
        pattern = r"\b" + re.escape(name.lower()) + r"\b"
        if re.search(pattern, lower):
            found[name] = JobSkillImportance.MENTIONED
    return list(found.items())


def infer_roles(title: str, description: str | None = None) -> list[tuple[str, JobRoleMappingSource]]:
    blob = f"{title} {description or ''}".lower()
    matches: list[tuple[str, JobRoleMappingSource]] = []
    for role_name, patterns in _ROLE_RULES:
        for p in patterns:
            if p in blob:
                matches.append((role_name, JobRoleMappingSource.RULE))
                break
    return matches


def parse_csv_skills(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [s.strip() for s in re.split(r"[;,|]", raw) if s.strip()]
