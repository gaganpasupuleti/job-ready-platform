from fastapi import APIRouter

from app.api.v1 import (
    admin,
    admin_ai,
    admin_content,
    admin_infra,
    admin_interviews,
    admin_learn,
    admin_readiness,
    ai,
    admin_jobs,
    applications,
    auth,
    coding,
    health,
    infra,
    interview,
    interviews,
    jobs,
    learn,
    mistakes,
    modules,
    practice,
    readiness,
    sql_practice,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(modules.router, tags=["modules"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(practice.router, tags=["practice"])
api_router.include_router(coding.router, tags=["coding"])
api_router.include_router(sql_practice.router, tags=["sql"])
api_router.include_router(interview.router, tags=["interview"])
api_router.include_router(interviews.router, tags=["interviews"])
api_router.include_router(jobs.router, tags=["jobs"])
api_router.include_router(applications.router, tags=["applications"])
api_router.include_router(readiness.router, tags=["readiness"])
api_router.include_router(mistakes.router, tags=["mistakes"])
api_router.include_router(learn.router, tags=["learn"])
api_router.include_router(ai.router, tags=["ai"])
api_router.include_router(infra.router, tags=["infra"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(admin_ai.router, tags=["admin-ai"])
api_router.include_router(admin_infra.router, tags=["admin-infra"])
api_router.include_router(admin_content.router, tags=["admin-content"])
api_router.include_router(admin_interviews.router, tags=["admin-interviews"])
api_router.include_router(admin_jobs.router, tags=["admin-jobs"])
api_router.include_router(admin_readiness.router, tags=["admin-readiness"])
api_router.include_router(admin_learn.router, tags=["admin-learn"])
