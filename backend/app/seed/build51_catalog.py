# ruff: noqa: E501
"""Build 5.1 guided project catalog — original Job Ready wording, no third-party copies."""

from __future__ import annotations

from typing import Any

from app.models.learn_enums import PathAvailability, PracticePathDifficulty

B = PracticePathDifficulty.BEGINNER
E = PracticePathDifficulty.EASY
M = PracticePathDifficulty.MEDIUM
H = PracticePathDifficulty.HARD


def _p(
    slug: str,
    title: str,
    category: str,
    tech: str,
    difficulty: PracticePathDifficulty,
    minutes: int,
    short: str,
    skills: list[str],
    prereqs: list[str],
    objective: str,
    *,
    description: str | None = None,
    featured: bool = False,
    coding: list[str] | None = None,
    sql: list[str] | None = None,
    topic: str | None = None,
    genai_skeleton: bool = False,
) -> dict[str, Any]:
    return {
        "slug": slug,
        "title": title,
        "category_key": category,
        "technology": tech,
        "difficulty": difficulty,
        "estimated_minutes": minutes,
        "short_description": short,
        "description": description or short,
        "skills": skills,
        "prerequisites": prereqs,
        "final_objective": objective,
        "featured": featured,
        "coding_slugs": coding or [],
        "sql_slugs": sql or [],
        "topic_slug": topic,
        "genai_skeleton": genai_skeleton,
        "availability": PathAvailability.AVAILABLE,
    }


PROJECT_SPECS: list[dict[str, Any]] = [
    # Python beginner
    _p("python-calculator", "Calculator", "python", "Python", B, 60, "A command-line calculator that parses expressions and reports errors clearly.", ["Python", "Parsing"], ["Variables and functions"], "Ship a calculator that handles +, -, *, / and reports invalid input without crashing.", featured=True),
    _p("python-expense-tracker", "Expense Tracker", "python", "Python", B, 90, "Record daily spends, group them by category, and print a monthly summary.", ["Python", "Files"], ["Lists and dictionaries"], "Produce a CSV-backed tracker that totals expenses by category."),
    _p("python-student-result-analyzer", "Student Result Analyzer", "python", "Python", B, 75, "Load marks from a file and compute averages, ranks, and pass/fail flags.", ["Python", "CSV"], ["Loops"], "Print a ranked class report from a marks file."),
    _p("python-csv-data-cleaner", "CSV Data Cleaner", "python", "Python", B, 80, "Trim whitespace, fill missing values, and write a cleaned CSV.", ["Python", "Data cleaning"], ["File I/O"], "Emit a cleaned CSV plus a one-page change log."),
    _p("python-file-organizer", "File Organizer", "python", "Python", B, 70, "Sort files in a folder by extension into destination directories.", ["Python", "OS"], ["Paths"], "Organize a sample folder without deleting originals."),
    _p("python-cli-task-manager", "CLI Task Manager", "python", "Python", B, 90, "Add, list, complete, and persist tasks from the terminal.", ["Python", "CLI"], ["Functions"], "A tiny task list stored in JSON."),
    _p("python-contact-book", "Contact Book", "python", "Python", B, 80, "Search, add, and update contacts with validation on phone and email.", ["Python", "Validation"], ["Dictionaries"], "CRUD for contacts with duplicate detection."),
    _p("python-log-file-analyzer", "Log File Analyzer", "python", "Python", E, 90, "Count status codes and top endpoints from a sample access log.", ["Python", "Logs"], ["Strings"], "Summarize error rates from a log file."),
    _p("python-password-strength-checker", "Password Strength Checker", "python", "Python", B, 45, "Score passwords on length, classes of characters, and common words.", ["Python", "Security basics"], ["Strings"], "Print a strength label and improvement hints. Defensive only."),
    _p("python-mini-quiz-app", "Mini Quiz App", "python", "Python", B, 60, "Ask multiple-choice questions from a JSON bank and score the attempt.", ["Python", "Control flow"], ["Lists"], "Run a five-question quiz and print a score report."),
    # Python intermediate
    _p("python-rest-api-client", "REST API Client", "python", "Python", M, 120, "Call a local mock JSON file as if it were an API and retry failed reads.", ["Python", "HTTP concepts"], ["JSON"], "A client that loads fixtures, maps errors, and prints a typed summary."),
    _p("python-data-validation-pipeline", "Data Validation Pipeline", "python", "Python", M, 110, "Validate rows against a schema and quarantine failures.", ["Python", "Validation"], ["CSV"], "Pass/fail counts plus a rejected-rows file."),
    _p("python-etl-mini-pipeline", "ETL Mini Pipeline", "python", "Python", M, 130, "Extract from CSV, transform types, and load a clean table-shaped JSON.", ["Python", "ETL"], ["Data types"], "Document extract, transform, and load steps with sample output."),
    _p("python-fastapi-mini-backend", "FastAPI Mini Backend Concept", "python", "Python", M, 140, "Design routes, models, and error shapes for a tiny notes API — no live deploy required.", ["Python", "APIs"], ["REST"], "A written API contract plus stub handlers you could later implement."),
    _p("python-automation-script", "Automation Script Project", "python", "Python", M, 100, "Watch a folder and rename files using a date prefix and a dry-run flag.", ["Python", "Automation"], ["CLI"], "A script with dry-run and apply modes."),
    # Java
    _p("java-console-banking", "Console Banking App", "java", "Java", E, 150, "Accounts, deposits, withdrawals, and a transaction log in the console.", ["Java", "OOP"], ["Classes"], "A menu-driven bank with insufficient-funds handling.", featured=True),
    _p("java-student-management", "Student Management System", "java", "Java", E, 140, "Store students, courses, and grades with simple search.", ["Java", "Collections"], ["OOP"], "CRUD plus a class average report."),
    _p("java-inventory-tracker", "Inventory Tracker", "java", "Java", E, 130, "Track SKUs, stock levels, and restock alerts.", ["Java", "Data modeling"], ["Collections"], "Low-stock list from sample inventory."),
    _p("java-library-management", "Library Management", "java", "Java", M, 150, "Borrow and return books with due dates.", ["Java", "OOP"], ["Dates"], "Checkout flow that blocks double-borrow."),
    _p("java-task-scheduler", "Task Scheduler", "java", "Java", M, 140, "Queue jobs with priorities and print the next runnable task.", ["Java", "Queues"], ["OOP"], "A priority queue simulation with a log."),
    _p("java-file-processing-utility", "File Processing Utility", "java", "Java", E, 110, "Read a text file, count lines/words, and write a report.", ["Java", "I/O"], ["Strings"], "A summary file next to the input."),
    _p("java-basic-rest-backend", "Basic REST Backend Concept", "java", "Java", M, 160, "Sketch controllers and DTOs for a student API without running a server.", ["Java", "APIs"], ["REST"], "OpenAPI-style notes and sample JSON payloads."),
    # C++
    _p("cpp-cli-calculator", "CLI Calculator", "cpp", "C++", B, 70, "Evaluate integer expressions from stdin with operator precedence notes.", ["C++", "Parsing"], ["I/O"], "Correct results for a provided expression list."),
    _p("cpp-student-record-system", "Student Record System", "cpp", "C++", E, 120, "Structs for students and a file-backed roster.", ["C++", "Structs"], ["Files"], "Load, search, and save a roster."),
    _p("cpp-inventory-manager", "Inventory Manager", "cpp", "C++", E, 120, "Track quantities and print restock candidates.", ["C++", "STL"], ["Maps"], "A restock report from sample stock."),
    _p("cpp-mini-banking-system", "Mini Banking System", "cpp", "C++", M, 140, "Accounts and transfers with a simple ledger.", ["C++", "Classes"], ["STL"], "Balanced ledger after a scripted transfer sequence."),
    _p("cpp-file-parser", "File Parser", "cpp", "C++", E, 100, "Parse a delimiter-separated file into records and validate columns.", ["C++", "Parsing"], ["Strings"], "Skip bad rows and count them."),
    _p("cpp-ds-visual-practice", "Data Structure Visual Practice", "cpp", "C++", M, 130, "Print stack/queue/tree operations as text traces for interview warm-ups.", ["C++", "DSA"], ["STL"], "Trace output for push/pop and BFS on a tiny graph.", coding=["valid-parentheses"]),
    # JavaScript
    _p("js-todo-app", "To-do App", "javascript", "JavaScript", B, 90, "Add, complete, and filter tasks stored in localStorage.", ["JavaScript", "DOM"], ["Events"], "A working to-do list that survives a refresh.", featured=True),
    _p("js-quiz-app", "Quiz App", "javascript", "JavaScript", B, 80, "Multiple-choice quiz with a score screen from local JSON.", ["JavaScript", "DOM"], ["Arrays"], "Five questions and a percentage score."),
    _p("js-expense-tracker", "Expense Tracker", "javascript", "JavaScript", E, 100, "Capture expenses and chart category totals with simple DOM bars.", ["JavaScript", "UI"], ["localStorage"], "Category totals that match sample rows."),
    _p("js-weather-ui-mock", "Weather UI (Mock Data)", "javascript", "JavaScript", B, 70, "Render forecast cards from a local JSON fixture — no network calls.", ["JavaScript", "UI"], ["JSON"], "City cards and a 5-day strip from fixtures."),
    _p("js-form-validation-app", "Form Validation App", "javascript", "JavaScript", E, 80, "Validate name, email, and password on the client with inline errors.", ["JavaScript", "Forms"], ["Validation"], "Block submit until rules pass."),
    _p("js-notes-app", "Notes App", "javascript", "JavaScript", E, 90, "Create, edit, and search notes in localStorage.", ["JavaScript", "CRUD"], ["DOM"], "Search filters notes by title."),
    _p("js-dashboard-widgets", "Dashboard Widgets", "javascript", "JavaScript", M, 110, "KPI cards and a table from mock metrics JSON.", ["JavaScript", "UI"], ["Data display"], "Four widgets that stay in sync with the fixture."),
    # SQL
    _p("sql-ecommerce-analytics", "E-commerce Analytics", "sql", "SQL", M, 150, "Guided SQL path: catalog, orders, and revenue questions on sample retail data.", ["SQL", "Joins"], ["SELECT"], "Complete the linked SQL challenges in order.", featured=True, sql=["active-catalog-items", "customer-order-pairs", "top-customers-by-revenue"]),
    _p("sql-banking-transaction-analysis", "Banking Transaction Analysis", "sql", "SQL", M, 140, "Deposits, branches, and settled payments.", ["SQL", "Aggregation"], ["GROUP BY"], "Answer the banking SQL set with original sample data.", sql=["branch-deposit-totals", "settled-invoice-payments"]),
    _p("sql-employee-analytics", "Employee Analytics", "sql", "SQL", M, 140, "Headcount, salaries, and department rankings.", ["SQL", "Window functions"], ["HR data"], "Finish the employee SQL sequence.", sql=["engineering-headcount-roster", "department-salary-rankings", "top-earner-per-department"]),
    _p("sql-support-sla-analytics", "Support / SLA Analytics", "sql", "SQL", M, 130, "Open tickets, priorities, and SLA breaches.", ["SQL", "Filters"], ["Support"], "Complete ticket and SLA queries.", sql=["high-priority-open-tickets", "ticket-sla-breaches"]),
    _p("sql-marketing-funnel-analysis", "Marketing Funnel Analysis", "sql", "SQL", H, 150, "Channels, conversion, and checkout funnel rates.", ["SQL", "Funnels"], ["Ratios"], "Work the funnel SQL challenges in order.", sql=["channel-conversion-rates", "checkout-funnel-rates"]),
    _p("sql-subscription-retention", "Subscription Retention Analysis", "sql", "SQL", H, 150, "Monthly sales, cohorts, and weekly active retention.", ["SQL", "Retention"], ["Windows"], "Complete the retention SQL set.", sql=["monthly-subscription-sales", "weekly-active-retention", "first-purchase-cohort-revenue"]),
    # Data analysis
    _p("da-sales-dashboard", "Sales Dashboard Analysis", "data-analysis", "SQL + Python", M, 180, "Define KPIs, clean a sales extract, and plan dashboard widgets.", ["Analytics", "SQL"], ["Aggregates"], "A KPI sheet plus SQL that feeds three widgets.", sql=["store-average-basket", "daily-running-revenue"]),
    _p("da-customer-churn", "Customer Churn Analysis", "data-analysis", "SQL + Python", M, 180, "Frame churn, pick features, and write questions a dashboard should answer.", ["Analytics", "Churn"], ["SQL"], "Churn definition, cohort notes, and linked SQL practice.", sql=["cte-repeat-high-spenders", "above-average-spenders"]),
    _p("da-support-ticket-analysis", "Support Ticket Analysis", "data-analysis", "SQL", M, 150, "Volume, SLA, and backlog questions from ticket data.", ["Analytics", "Ops"], ["SQL"], "A ticket KPI pack backed by SQL tasks.", sql=["high-priority-open-tickets", "ticket-sla-breaches"]),
    _p("da-hr-attrition", "HR Attrition Analysis", "data-analysis", "SQL", M, 160, "Attrition framing, department risk, and interview-style business questions.", ["Analytics", "HR"], ["SQL"], "Attrition KPI list plus employee SQL practice.", sql=["engineering-headcount-roster", "department-salary-rankings"]),
    _p("da-marketing-campaign", "Marketing Campaign Analysis", "data-analysis", "SQL", M, 160, "Campaign lift questions using funnel and conversion SQL.", ["Analytics", "Marketing"], ["SQL"], "A campaign readout outline plus SQL drills.", sql=["channel-conversion-rates", "checkout-funnel-rates"]),
    _p("da-student-performance", "Student Performance Analysis", "data-analysis", "SQL + Python", E, 140, "Understand a marks extract, define pass rates, and plan charts.", ["Analytics", "Education"], ["Cleaning"], "Pass-rate KPI and a cleaning checklist."),
    # ML (no training infra)
    _p("ml-house-price", "House Price Prediction", "machine-learning", "ML concepts", M, 120, "Frame regression, features, leakage risks, and evaluation — no model training required.", ["ML", "Regression"], ["Train/test"], "A written experiment plan with metrics and overfitting notes."),
    _p("ml-customer-churn-model", "Customer Churn Model Path", "machine-learning", "ML concepts", M, 120, "Classification framing, class imbalance, and interpretation of a churn score.", ["ML", "Classification"], ["Evaluation"], "Metric choice memo plus feature list."),
    _p("ml-loan-default-risk", "Loan Default Risk", "machine-learning", "ML concepts", M, 130, "Credit-risk problem statement, fairness notes, and evaluation without deploying a model.", ["ML", "Risk"], ["Ethics"], "A risk scorecard design on paper."),
    _p("ml-spam-classification", "Spam Classification", "machine-learning", "ML concepts", E, 100, "Text features, train/test split, and precision vs recall for spam.", ["ML", "NLP basics"], ["Evaluation"], "A labeling guide and metric table."),
    _p("ml-customer-segmentation", "Customer Segmentation", "machine-learning", "ML concepts", M, 110, "Unsupervised grouping: features, cluster count, and business use.", ["ML", "Clustering"], ["Interpretation"], "Segment cards without running k-means."),
    _p("ml-sales-forecasting", "Sales Forecasting", "machine-learning", "ML concepts", M, 120, "Time-series framing, seasonality, and why a naive baseline matters.", ["ML", "Forecasting"], ["Baselines"], "A forecast checklist and holdout plan."),
    # GenAI skeletons
    _p("genai-faq-rag-assistant", "FAQ RAG Assistant", "generative-ai", "GenAI (later)", M, 90, "Architecture for retrieval-augmented FAQ answers. No live LLM in this build.", ["RAG", "Retrieval"], ["Documents"], "A RAG design doc and evaluation questions.", genai_skeleton=True),
    _p("genai-resume-skill-extractor", "Resume Skill Extractor", "generative-ai", "GenAI (later)", M, 90, "Prompt and schema for extracting skills from resumes — offline design only.", ["Prompts", "Extraction"], ["JSON schema"], "Extraction schema plus failure cases.", genai_skeleton=True),
    _p("genai-document-qa", "Document Q&A", "generative-ai", "GenAI (later)", M, 90, "Chunking, citations, and refusal when the answer is not in the doc.", ["RAG", "Citations"], ["Evaluation"], "Q&A rubric with citation rules.", genai_skeleton=True),
    _p("genai-prompt-classifier", "Prompt Classifier", "generative-ai", "GenAI (later)", E, 60, "Label prompts by intent for later routing. No model runtime yet.", ["Classification", "Prompts"], ["Taxonomy"], "Intent taxonomy and sample labels.", genai_skeleton=True),
    _p("genai-support-ticket-router", "Support Ticket Router", "generative-ai", "GenAI (later)", M, 80, "Route tickets to queues using a planned classifier — design only.", ["Routing", "Ops"], ["Taxonomy"], "Queue map and confidence policy.", genai_skeleton=True),
    _p("genai-ai-agent-workflow", "AI Agent Workflow", "generative-ai", "GenAI (later)", H, 100, "Tool-using agent sketch: planner, tools, and stop conditions. No agent runtime.", ["Agents", "Tools"], ["Safety"], "Workflow diagram and tool allow-list.", genai_skeleton=True),
    # DevOps
    _p("devops-dockerize-web-app", "Dockerize a Web App", "devops", "Docker", E, 90, "Write a Dockerfile and run notes for a sample web app — no cloud account.", ["Docker", "Images"], ["CLI"], "A Dockerfile checklist and local run steps."),
    _p("devops-cicd-pipeline-design", "CI/CD Pipeline Design", "devops", "CI/CD", M, 100, "Stages, tests, and artifacts for a pipeline on paper.", ["CI/CD", "Quality"], ["Git"], "A pipeline diagram with fail-fast tests."),
    _p("devops-compose-multi-service", "Docker Compose Multi-service App", "devops", "Compose", M, 110, "App + database compose file design without deploying remotely.", ["Compose", "Networking"], ["Volumes"], "A compose.yml sketch and healthcheck notes."),
    _p("devops-monitoring-basics", "Monitoring Basics", "devops", "Observability", E, 80, "Logs, metrics, and alerts you would add to a toy API.", ["Monitoring", "SLOs"], ["Logs"], "An alert list with thresholds."),
    _p("devops-deployment-checklist", "Deployment Checklist", "devops", "Release", E, 60, "Pre-prod checks: migrations, rollback, and config.", ["Release", "Risk"], ["Checklists"], "A go/no-go checklist."),
    _p("devops-infra-config-review", "Infrastructure Configuration Review", "devops", "IaC review", M, 90, "Review a sample config for secrets, ports, and least privilege.", ["Security", "Config"], ["Review"], "A review comment list — defensive only."),
    # Cloud
    _p("cloud-aws-static-website", "AWS Static Website Architecture", "cloud", "AWS (design)", E, 70, "S3 + CDN style static hosting diagram. No AWS API calls.", ["AWS", "Architecture"], ["Static sites"], "An architecture sketch and cost/risk notes."),
    _p("cloud-aws-web-app", "AWS Web App Architecture", "cloud", "AWS (design)", M, 90, "ALB, compute, and database boxes for a web app.", ["AWS", "Architecture"], ["Networking"], "A labeled diagram plus failure modes."),
    _p("cloud-aws-serverless-api", "AWS Serverless API Design", "cloud", "AWS (design)", M, 90, "API Gateway + function + table design without invoking AWS.", ["Serverless", "APIs"], ["IAM"], "Event flow and timeout notes."),
    _p("cloud-aws-iam-access", "AWS IAM Access Design", "cloud", "AWS (design)", M, 80, "Least-privilege roles for a sample app. Defensive IAM only.", ["IAM", "Security"], ["Roles"], "Role/policy table for three personas."),
    _p("cloud-azure-app-service", "Azure App Service Architecture", "cloud", "Azure (design)", M, 80, "App Service + database sketch. No Azure APIs.", ["Azure", "Architecture"], ["PaaS"], "A service map and scaling notes."),
    _p("cloud-azure-storage-function", "Azure Storage + Function Design", "cloud", "Azure (design)", M, 80, "Blob trigger and function contract on paper.", ["Azure", "Serverless"], ["Storage"], "Trigger/retry design."),
    _p("cloud-gcp-compute-storage", "GCP Compute/Storage Architecture", "cloud", "GCP (design)", M, 80, "Compute Engine or Cloud Run plus Cloud Storage sketch.", ["GCP", "Architecture"], ["Storage"], "A component diagram and IAM notes."),
    # Cybersecurity defensive
    _p("cyber-secure-web-app-review", "Secure Web App Review", "cybersecurity", "AppSec", M, 100, "Review a fictional app for auth, cookies, and input handling. Defensive only.", ["AppSec", "OWASP"], ["Review"], "A finding list with severity — no exploit steps."),
    _p("cyber-owasp-risk-identification", "OWASP Risk Identification", "cybersecurity", "AppSec", E, 80, "Map sample findings to OWASP categories and owners.", ["OWASP", "Risk"], ["Documentation"], "A risk register for a demo app."),
    _p("cyber-log-analysis", "Log Analysis", "cybersecurity", "Detection", M, 90, "Read a sanitized log excerpt and flag suspicious patterns.", ["Logs", "Detection"], ["IR"], "A timeline of notable events."),
    _p("cyber-incident-response-scenario", "Incident Response Scenario", "cybersecurity", "IR", M, 90, "Walk a tabletop: detect, contain, communicate. No offensive tooling.", ["IR", "Process"], ["Comms"], "An IR runbook for the scenario."),
    _p("cyber-iam-review", "IAM Review", "cybersecurity", "IAM", M, 80, "Spot over-privileged roles in a sample policy set.", ["IAM", "Least privilege"], ["Review"], "Remediation recommendations."),
    _p("cyber-api-security-review", "API Security Review", "cybersecurity", "API security", M, 90, "AuthN/Z, rate limits, and data exposure on a fictional API.", ["APIs", "Auth"], ["Review"], "A review memo with controls."),
    _p("cyber-cloud-security-checklist", "Cloud Security Checklist", "cybersecurity", "Cloud", E, 70, "Storage public access, keys, and logging checklist. No cloud APIs.", ["Cloud", "Checklist"], ["Hygiene"], "A scored checklist on a sample architecture."),
]


PATH_STRUCTURE_UPDATES: list[dict[str, Any]] = [
    # beginner dsa — Learn / Practice / Checkpoint labels (items filled in seeder)
    {"slug": "beginner-arrays", "topic": "arrays", "learn": "How arrays store contiguous values and why index math matters."},
    {"slug": "beginner-strings", "topic": "strings", "learn": "Strings as sequences: scans, slices, and immutable copies."},
    {"slug": "beginner-basic-math", "topic": "basics", "learn": "Digits, divisibility, and overflow-aware arithmetic."},
    {"slug": "beginner-sorting", "topic": "sorting", "learn": "When sorting first collapses a nested loop into a linear pass."},
    {"slug": "beginner-searching", "topic": "searching", "learn": "Linear scan versus binary search preconditions."},
    {"slug": "beginner-hashing", "topic": "hash-maps", "learn": "Sets and maps as O(1) membership tests."},
    {"slug": "beginner-two-pointers", "topic": "two-pointers", "learn": "Opposite ends and slow/fast pointer patterns."},
]


NEW_DS_PATHS = [
    ("ds-matrices", "Matrices", "2D arrays, traversal order, and in-place tricks."),
    ("ds-bst", "Binary Search Trees", "Search, insert, and inorder as a sorted view."),
    ("ds-dsu", "Disjoint Set Union", "Union-find for connectivity questions."),
]

NEW_ALGO_PATHS = [
    ("algo-searching", "Searching", "Linear and binary search as algorithm families."),
    ("algo-number-theory", "Number Theory", "GCD, primes, and modular arithmetic used in contests."),
]

COMPANY_DISCLAIMER = (
    "Preparation path based on commonly relevant skills and hiring patterns. "
    "Questions and problems are original Job Ready content. This path is not affiliated with, "
    "endorsed by, or sponsored by the company, and it does not claim any item was asked in a real interview."
)
