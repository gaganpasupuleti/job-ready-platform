from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.models.user import User
from app.services.sql_execution.executor import SqlSandboxExecutor, get_sql_executor
from app.services.sql_playground.service import SqlPlaygroundService

router = APIRouter(prefix="/sql/playground")


class PlaygroundRunIn(BaseModel):
    query: str = Field(..., min_length=1, max_length=20000)


def _service(executor: SqlSandboxExecutor = Depends(get_sql_executor)) -> SqlPlaygroundService:
    return SqlPlaygroundService(executor)


@router.get("/")
async def playground_catalog(service: SqlPlaygroundService = Depends(_service)) -> dict:
    return service.catalog()


@router.get("")
async def playground_catalog_alias(service: SqlPlaygroundService = Depends(_service)) -> dict:
    return service.catalog()


@router.get("/datasets/{dataset_id}")
async def playground_dataset(dataset_id: str, service: SqlPlaygroundService = Depends(_service)) -> dict:
    return service.dataset(dataset_id)


@router.post("/datasets/{dataset_id}/run")
async def playground_run(
    dataset_id: str,
    payload: PlaygroundRunIn,
    user: User = Depends(get_current_user),
    service: SqlPlaygroundService = Depends(_service),
) -> dict:
    return await service.run(user, dataset_id, payload.query)
