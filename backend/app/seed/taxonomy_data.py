"""Taxonomy seed definitions for Build 2 development."""

TAXONOMY = [
    {
        "name": "Placement",
        "slug": "placement",
        "categories": [
            {
                "name": "Aptitude",
                "slug": "aptitude",
                "topics": [
                    {"name": "Percentages", "slug": "percentages"},
                    {"name": "Profit and Loss", "slug": "profit-and-loss"},
                    {"name": "Time and Work", "slug": "time-and-work"},
                    {"name": "Time Speed Distance", "slug": "time-speed-distance"},
                    {"name": "Ratio and Proportion", "slug": "ratio-and-proportion"},
                    {"name": "Simple Interest", "slug": "simple-interest"},
                    {"name": "Compound Interest", "slug": "compound-interest"},
                    {"name": "Probability", "slug": "probability"},
                    {"name": "Permutations and Combinations", "slug": "permutations-and-combinations"},
                    {"name": "Series", "slug": "series"},
                    {"name": "Coding-Decoding", "slug": "coding-decoding"},
                    {"name": "Blood Relations", "slug": "blood-relations"},
                    {"name": "Directions", "slug": "directions"},
                    {"name": "Syllogisms", "slug": "syllogisms"},
                    {"name": "Seating Arrangement", "slug": "seating-arrangement"},
                    {"name": "Puzzles", "slug": "puzzles"},
                    {"name": "Grammar", "slug": "grammar"},
                    {"name": "Vocabulary", "slug": "vocabulary"},
                    {"name": "Sentence Correction", "slug": "sentence-correction"},
                    {"name": "Reading Comprehension", "slug": "reading-comprehension"},
                    {"name": "Para Jumbles", "slug": "para-jumbles"},
                    {"name": "Tables", "slug": "tables"},
                    {"name": "Charts", "slug": "charts"},
                    {"name": "Graphs", "slug": "graphs"},
                    {"name": "Caselets", "slug": "caselets"},
                ],
            }
        ],
    },
    {
        "name": "Technical",
        "slug": "technical",
        "categories": [
            {"name": "Python", "slug": "python", "topics": [{"name": "Fundamentals", "slug": "fundamentals"}]},
            {"name": "SQL", "slug": "sql", "topics": [
                {"name": "SQL Fundamentals", "slug": "sql-fundamentals"},
                {"name": "Aggregations", "slug": "aggregations"},
                {"name": "Joins", "slug": "joins"},
                {"name": "Subqueries", "slug": "subqueries"},
                {"name": "CTE", "slug": "cte"},
                {"name": "Window Functions", "slug": "window-functions"},
                {"name": "Conditional Logic", "slug": "conditional-logic"},
                {"name": "Date Functions", "slug": "date-functions"},
                {"name": "String Functions", "slug": "string-functions"},
                {"name": "Advanced SQL", "slug": "advanced-sql"},
                {"name": "Queries", "slug": "queries"},
            ]},
            {"name": "DBMS", "slug": "dbms", "topics": [{"name": "Concepts", "slug": "concepts"}]},
            {"name": "Operating Systems", "slug": "operating-systems", "topics": [{"name": "Core Concepts", "slug": "core-concepts"}]},
            {"name": "Computer Networks", "slug": "computer-networks", "topics": [{"name": "Fundamentals", "slug": "fundamentals"}]},
            {"name": "OOP", "slug": "oop", "topics": [{"name": "Principles", "slug": "principles"}]},
            {"name": "Git", "slug": "git", "topics": [{"name": "Workflow", "slug": "workflow"}]},
            {"name": "Linux", "slug": "linux", "topics": [{"name": "Commands", "slug": "commands"}]},
            {"name": "Data Analytics", "slug": "data-analytics", "topics": [{"name": "Fundamentals", "slug": "fundamentals"}]},
            {"name": "Machine Learning", "slug": "machine-learning", "topics": [{"name": "Fundamentals", "slug": "fundamentals"}]},
            {
                "name": "DSA",
                "slug": "dsa",
                "topics": [
                    {"name": "Basics", "slug": "basics"},
                    {"name": "Arrays", "slug": "arrays"},
                    {"name": "Strings", "slug": "strings"},
                ],
            },
        ],
    },
    {
        "name": "AI",
        "slug": "ai",
        "categories": [
            {
                "name": "Generative AI",
                "slug": "generative-ai",
                "topics": [
                    {"name": "LLM Fundamentals", "slug": "llm-fundamentals"},
                    {"name": "Embeddings", "slug": "embeddings"},
                    {"name": "RAG", "slug": "rag"},
                    {"name": "Retrieval", "slug": "retrieval"},
                    {"name": "Tool Calling", "slug": "tool-calling"},
                    {"name": "LLM Evaluation", "slug": "llm-evaluation"},
                    {"name": "AI Security", "slug": "ai-security"},
                ],
            },
            {
                "name": "Prompt Engineering",
                "slug": "prompt-engineering",
                "topics": [
                    {"name": "Zero-shot", "slug": "zero-shot"},
                    {"name": "Few-shot", "slug": "few-shot"},
                    {"name": "Structured Outputs", "slug": "structured-outputs"},
                    {"name": "Prompt Injection", "slug": "prompt-injection"},
                ],
            },
            {
                "name": "AI Agents",
                "slug": "ai-agents",
                "topics": [
                    {"name": "Tool Calling", "slug": "tool-calling"},
                    {"name": "Agent Loops", "slug": "agent-loops"},
                    {"name": "Multi-Agent Systems", "slug": "multi-agent-systems"},
                ],
            },
        ],
    },
    {
        "name": "Cloud",
        "slug": "cloud",
        "categories": [
            {"name": "Cloud Fundamentals", "slug": "cloud-fundamentals", "topics": [{"name": "Architecture", "slug": "architecture"}]},
            {"name": "AWS", "slug": "aws", "topics": [{"name": "Compute", "slug": "compute"}]},
            {"name": "Azure", "slug": "azure", "topics": [{"name": "Compute", "slug": "compute"}]},
            {"name": "GCP", "slug": "gcp", "topics": [{"name": "Compute", "slug": "compute"}]},
        ],
    },
    {
        "name": "DevOps",
        "slug": "devops",
        "categories": [
            {"name": "DevOps", "slug": "devops-core", "topics": [{"name": "CI/CD", "slug": "ci-cd"}]},
        ],
    },
    {
        "name": "Cybersecurity",
        "slug": "cybersecurity",
        "categories": [
            {
                "name": "Web Security",
                "slug": "web-security",
                "topics": [
                    {"name": "OWASP", "slug": "owasp"},
                    {"name": "SQL Injection", "slug": "sql-injection"},
                ],
            },
            {
                "name": "Security Fundamentals",
                "slug": "security-fundamentals",
                "topics": [{"name": "Cryptography", "slug": "cryptography"}],
            },
        ],
    },
]

SKILLS = [
    "vector similarity",
    "embeddings",
    "probability",
    "percentages",
    "sql joins",
    "python basics",
    "networking",
    "cloud architecture",
    "prompt design",
    "rag retrieval",
]

JOB_ROLES = [
    "GenAI Engineer",
    "AI Engineer",
    "RAG Engineer",
    "Software Engineer",
    "Data Analyst",
    "Cloud Engineer",
]

COMPANIES = ["Acme Labs", "TechCorp"]
