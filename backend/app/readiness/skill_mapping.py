"""Map taxonomy tags/categories to canonical skill slugs."""

from __future__ import annotations

CATEGORY_SLUG_TO_SKILL: dict[str, str] = {
    "sql": "sql",
    "python": "python",
    "dsa": "python",
    "generative-ai": "rag",
    "prompt-engineering": "prompt-engineering",
    "ai-agents": "agents",
    "cloud": "aws",
    "devops": "docker",
    "cybersecurity": "soc",
    "data-analytics": "sql",
    "machine-learning": "python",
}

TAG_TO_SKILL: dict[str, str] = {
    "aws": "aws",
    "azure": "azure",
    "gcp": "gcp",
    "snowflake": "snowflake",
    "spark": "spark",
    "flink": "spark",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "terraform": "terraform",
    "linux": "linux",
    "iam": "iam",
    "rag": "rag",
    "agents": "agents",
    "mcp": "mcp",
    "etl": "sql",
    "data-engineering": "sql",
    "sql": "sql",
    "python": "python",
    "devops": "docker",
    "soc": "soc",
    "security": "soc",
    "prompt": "prompt-engineering",
}

SKILL_ALIASES: dict[str, str] = {
    "postgresql": "sql",
    "postgres": "sql",
    "mysql": "sql",
    "powerbi": "sql",
    "power-bi": "sql",
    "apache-spark": "spark",
    "apache flink": "spark",
    "generative ai": "rag",
    "prompt engineering": "prompt-engineering",
    "ai agents": "agents",
    "data engineering": "sql",
    "data modeling": "sql",
    "etl": "sql",
    "communication": "python",
}


def normalize_skill_key(name: str) -> str:
    key = name.strip().lower().replace("_", "-")
    if key in SKILL_ALIASES:
        return SKILL_ALIASES[key]
    return key.replace(" ", "-")


def skill_slug_from_category(category_slug: str | None) -> str | None:
    if not category_slug:
        return None
    return CATEGORY_SLUG_TO_SKILL.get(category_slug.lower())


def skill_slug_from_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    slugs: list[str] = []
    for tag in tags:
        key = normalize_skill_key(str(tag))
        mapped = TAG_TO_SKILL.get(key, key)
        if mapped not in slugs:
            slugs.append(mapped)
    return slugs
