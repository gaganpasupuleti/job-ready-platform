from app.schemas.modules import ModulesResponse, PlatformModule


class ModulesService:
    """Returns the catalog of platform modules.

    In later builds this may be driven by feature flags or database config.
    """

    _MODULES: list[PlatformModule] = [
        # Practice
        PlatformModule(id="aptitude", name="Aptitude / CRT", category="practice", enabled=True, route="/practice/aptitude"),
        PlatformModule(id="dsa", name="DSA", category="practice", enabled=True, route="/practice/dsa"),
        PlatformModule(id="coding", name="Coding Practice", category="practice", enabled=True, route="/practice/coding"),
        PlatformModule(id="sql", name="SQL Practice", category="practice", enabled=True, route="/practice/sql"),
        PlatformModule(id="mcq", name="Technical MCQs", category="practice", enabled=True, route="/practice/mcq"),
        # AI Era
        PlatformModule(id="ai-ml", name="AI / ML", category="ai", enabled=True, route="/ai/ml"),
        PlatformModule(id="genai", name="Generative AI", category="ai", enabled=True, route="/ai/genai"),
        PlatformModule(id="prompt-engineering", name="Prompt Engineering", category="ai", enabled=True, route="/ai/prompt-engineering"),
        PlatformModule(id="ai-agents", name="AI Agents", category="ai", enabled=True, route="/ai/agents"),
        # Infrastructure
        PlatformModule(id="cloud", name="Cloud", category="infrastructure", enabled=True, route="/cloud"),
        PlatformModule(id="devops", name="DevOps", category="infrastructure", enabled=True, route="/devops"),
        PlatformModule(id="cybersecurity", name="Cybersecurity", category="infrastructure", enabled=True, route="/cybersecurity"),
        # Career
        PlatformModule(id="interviews", name="Interview Preparation", category="career", enabled=True, route="/interviews"),
        PlatformModule(id="company-prep", name="Company-specific Preparation", category="career", enabled=True, route="/company-prep"),
        PlatformModule(id="assessments", name="Assessments", category="career", enabled=True, route="/assessments"),
        PlatformModule(id="contests", name="Contests", category="career", enabled=True, route="/contests"),
        # Jobs
        PlatformModule(id="jobs", name="Jobs Portal", category="jobs", enabled=True, route="/jobs"),
        PlatformModule(id="saved-jobs", name="Saved Jobs", category="jobs", enabled=True, route="/jobs/saved"),
        PlatformModule(id="applications", name="Application Tracking", category="jobs", enabled=True, route="/jobs/applications"),
        # Progress
        PlatformModule(id="readiness", name="Job Readiness Scoring", category="progress", enabled=True, route="/readiness"),
    ]

    def get_modules(self, enabled_only: bool = True) -> ModulesResponse:
        modules = self._MODULES
        if enabled_only:
            modules = [m for m in modules if m.enabled]
        return ModulesResponse(modules=modules)
