import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.services.code_execution.interface import (
    CodeExecutionService,
    ExecutionRequest,
    ExecutionResult,
)

logger = logging.getLogger(__name__)

JUDGE0_STATUS_MAP = {
    1: "in_queue",
    2: "processing",
    3: "accepted",
    4: "wrong_answer",
    5: "time_limit_exceeded",
    6: "compilation_error",
    7: "runtime_error",
    8: "runtime_error",
    9: "runtime_error",
    10: "runtime_error",
    11: "runtime_error",
    12: "runtime_error",
    13: "internal_error",
    14: "exec_format_error",
}


@dataclass
class Judge0SubmissionResponse:
    stdout: str | None
    stderr: str | None
    status_id: int
    time: str | None
    memory: int | None
    compile_output: str | None = None


class Judge0CodeExecutionService(CodeExecutionService):
    """Delegates code execution to an isolated Judge0 instance."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or settings.judge0_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.judge0_api_key

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Auth-Token"] = self.api_key
        return headers

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        payload: dict = {
            "source_code": request.source_code,
            "language_id": request.language_id,
            "stdin": request.stdin,
        }
        if request.expected_output is not None:
            payload["expected_output"] = request.expected_output

        url = f"{self.base_url}/submissions?base64_encoded=false&wait=true"
        timeout = float(settings.judge0_timeout_seconds)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload, headers=self._headers())
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException:
            logger.warning("Judge0 request timed out")
            return ExecutionResult(stdout="", stderr="", status="service_unavailable")
        except httpx.HTTPError as exc:
            logger.exception("Judge0 request failed")
            return ExecutionResult(
                stdout="",
                stderr="Code execution is currently unavailable",
                status="service_unavailable",
            )

        status_id = data.get("status", {}).get("id", 13)
        status = JUDGE0_STATUS_MAP.get(status_id, "internal_error")
        stderr = data.get("stderr") or data.get("compile_output") or ""
        return ExecutionResult(
            stdout=data.get("stdout") or "",
            stderr=stderr,
            status=status,
            time=float(data["time"]) if data.get("time") else None,
            memory=int(data["memory"]) if data.get("memory") is not None else None,
        )
