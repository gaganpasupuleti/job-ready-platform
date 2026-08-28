import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ExecutionRequest:
    source_code: str
    language_id: int
    stdin: str = ""


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    status: str
    time: float | None = None
    memory: int | None = None


class CodeExecutionService(ABC):
    """Abstract interface for isolated code execution.

    Student code MUST NEVER run inside the FastAPI container.
    Future implementations will delegate to Judge0 or similar services.
    """

    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        ...


class Judge0CodeExecutionService(CodeExecutionService):
    """Placeholder for future Judge0 integration."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = base_url or settings.judge0_url
        self.api_key = api_key or settings.judge0_api_key

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        raise NotImplementedError(
            "Judge0 integration is not available in Build 1. "
            "Configure JUDGE0_URL and deploy Judge0 before enabling code execution."
        )


def get_code_execution_service() -> CodeExecutionService:
    return Judge0CodeExecutionService()
