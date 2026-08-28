from fastapi import APIRouter

from app.api.v1 import admin, auth, health, modules, practice

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(modules.router, tags=["modules"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(practice.router, tags=["practice"])
api_router.include_router(admin.router, tags=["admin"])
