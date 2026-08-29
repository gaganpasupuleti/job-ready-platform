from app.services.code_execution.interface import (
    CodeExecutionService,
    ExecutionRequest,
    ExecutionResult,
)


class DisabledCodeExecutionService(CodeExecutionService):
    """Returned when Judge0 is disabled or unavailable."""

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        return ExecutionResult(
            stdout="",
            stderr="Code execution is currently unavailable",
            status="service_unavailable",
        )

    async def health_check(self) -> bool:
        return False
