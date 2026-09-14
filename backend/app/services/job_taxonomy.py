"""Source taxonomy for Jobs listings.

These ids are the collector's. Do not infer a family from a title, and do
not rewrite an unknown source value into one of these ids.
"""

from __future__ import annotations

JOB_FAMILIES: tuple[tuple[str, str, str], ...] = (
    ("java-backend", "Java Backend Developer", "ROLE_JAVA_BACKEND"),
    ("python-dev", "Python Developer", "ROLE_PYTHON_DEV"),
    ("frontend-react", "Frontend React Developer", "ROLE_FRONTEND_REACT"),
    ("fullstack-web", "Full Stack Web Developer", "ROLE_FULLSTACK_WEB"),
    ("qa-testing", "QA / Testing Engineer", "ROLE_QA_TESTING"),
    ("data-analyst", "Data Analyst", "ROLE_DATA_ANALYST"),
    ("powerbi-analyst", "Power BI Analyst", "ROLE_POWERBI_ANALYST"),
    ("data-engineer", "Data Engineer", "ROLE_DATA_ENGINEER"),
    ("ml-ai", "ML / Data Science Engineer", "ROLE_ML_AI"),
    ("gen-ai", "Generative AI / LLM Engineer", "ROLE_GEN_AI"),
    ("agentic-ai", "Agentic AI Engineer", "ROLE_AGENTIC_AI"),
    ("it-support", "IT Support / Helpdesk", "ROLE_IT_SUPPORT"),
    ("servicenow", "ServiceNow Developer / Admin", "ROLE_SERVICENOW"),
    ("business-analyst", "Business Analyst", "ROLE_BUSINESS_ANALYST"),
    ("cyber-security", "Cyber Security Analyst", "ROLE_CYBER_SECURITY"),
    ("salesforce-crm", "Salesforce Developer / Admin", "ROLE_SALESFORCE"),
    ("dynamics-crm", "Microsoft Dynamics 365 CRM", "ROLE_DYNAMICS_CRM"),
    ("power-platform", "Power Platform Developer", "ROLE_POWER_PLATFORM"),
    ("other-review", "Other (needs review)", "ROLE_OTHER_REVIEW"),
)

EXPERIENCE_BUCKETS: tuple[str, ...] = (
    "Internship",
    "Fresher",
    "Entry (1-2 yrs)",
    "Experienced",
)

MISSING_COMPANY_LABEL = "Company not provided"

_PLACEHOLDERS = frozenset({"nan", "none", "null", "n/a", "na", "-", "undefined", "unknown"})


def catalog_text(value: object) -> str | None:
    """Return a displayable catalog value, or None for empty placeholders."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in _PLACEHOLDERS:
        return None
    return text


def stored_source_value(value: object) -> str | None:
    """Keep the source value. A missing placeholder is not a family or bucket."""
    return catalog_text(value)


def family_label(family_id: str) -> str | None:
    for slug, label, _role_id in JOB_FAMILIES:
        if slug == family_id:
            return label
    return None
