from pydantic import BaseModel


class PlatformModule(BaseModel):
    id: str
    name: str
    category: str
    enabled: bool
    route: str | None = None


class ModulesResponse(BaseModel):
    modules: list[PlatformModule]
