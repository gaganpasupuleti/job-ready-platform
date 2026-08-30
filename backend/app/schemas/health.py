from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class HealthChecks(BaseModel):
    database: str = "ok"
    redis: str = "skipped"
    sql_sandbox: str = "disabled"
    judge0: str = "disabled"


class DetailedHealthResponse(HealthResponse):
    checks: HealthChecks = Field(default_factory=HealthChecks)
