import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExecutionRequest:
    source_code: str
    language_id: int
    stdin: str = ""
    expected_output: str | None = None
    stdout_override: str | None = None


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


def get_code_execution_service() -> CodeExecutionService:
    from app.core.config import settings
    from app.services.code_execution.disabled import DisabledCodeExecutionService
    from app.services.code_execution.judge0 import Judge0CodeExecutionService

    if not settings.judge0_enabled:
        return DisabledCodeExecutionService()
    return Judge0CodeExecutionService()
