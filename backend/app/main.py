import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler, generic_exception_handler
from app.db.session import engine
from app.utils.database import check_database_connection
from app.utils.redis import check_redis_connection, close_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_ok = await check_database_connection(engine)
    redis_ok = await check_redis_connection()

    if db_ok:
        logger.info("PostgreSQL connection established")
    else:
        logger.warning("PostgreSQL connection failed — API will start but DB features unavailable")

    if redis_ok:
        logger.info("Redis connection established")
    else:
        logger.warning("Redis connection failed — caching features unavailable")

    yield

    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="Job Ready Platform API",
    description="Foundation API for the job-ready-platform product",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    return {
        "message": "Job Ready Platform API",
        "docs": "/docs",
        "health": f"{settings.api_v1_prefix}/health",
    }
