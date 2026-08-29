"""Judge0 HTTP client — auth, poll, batch, retries. Never runs student code locally."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from app.core.config import settings
from app.services.code_execution.interface import (
    CodeExecutionService,
    ExecutionRequest,
    ExecutionResult,
)
from app.services.code_execution.languages import apply_judge0_language_catalog
from app.services.code_execution.sanitize import sanitize_execution_message

logger = logging.getLogger(__name__)

JUDGE0_STATUS_MAP = {
    1: "in_queue",
    2: "processing",
    3: "accepted",
    4: "wrong_answer",
    5: "time_limit_exceeded",
    6: "compilation_error",
    7: "runtime_error",  # SIGSEGV
    8: "runtime_error",  # SIGXFSZ
    9: "runtime_error",  # SIGFPE
    10: "runtime_error",  # SIGABRT
    11: "runtime_error",  # NZEC
    12: "runtime_error",  # Other
    13: "internal_error",
    14: "exec_format_error",
    15: "runtime_error",  # Runtime Error (SIGPIPE) on some builds
}

_TERMINAL = {
    "accepted",
    "wrong_answer",
    "time_limit_exceeded",
    "compilation_error",
    "runtime_error",
    "internal_error",
    "exec_format_error",
    "memory_limit_exceeded",
}


class Judge0CodeExecutionService(CodeExecutionService):
    """Delegates code execution to an isolated Judge0 instance over HTTP."""

    def __init__(
        self,
        base_url: str | None = None,
        auth_token: str | None = None,
        auth_header: str | None = None,
    ):
        self.base_url = (base_url or settings.judge0_url).rstrip("/")
        token = auth_token
        if token is None:
            token = settings.judge0_auth_token or settings.judge0_api_key
        self.auth_token = token
        self.auth_header = auth_header or settings.judge0_auth_header or "X-Auth-Token"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.auth_token:
            headers[self.auth_header] = self.auth_token
        return headers

    def _client_timeout(self) -> httpx.Timeout:
        return httpx.Timeout(float(settings.judge0_timeout_seconds))

    def _build_payload(self, request: ExecutionRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source_code": request.source_code,
            "language_id": request.language_id,
            "stdin": request.stdin or "",
        }
        if request.expected_output is not None:
            payload["expected_output"] = request.expected_output
        if request.cpu_time_limit is not None:
            payload["cpu_time_limit"] = request.cpu_time_limit
        if request.wall_time_limit is not None:
            payload["wall_time_limit"] = request.wall_time_limit
        if request.memory_limit_kb is not None:
            payload["memory_limit"] = request.memory_limit_kb
        return payload

    def _parse_result(self, data: dict[str, Any]) -> ExecutionResult:
        status_id = (data.get("status") or {}).get("id", 13)
        status = JUDGE0_STATUS_MAP.get(status_id, "internal_error")
        # Some Judge0 builds report MLE as status id overlapping RE — check description
        desc = ((data.get("status") or {}).get("description") or "").lower()
        if "memory limit" in desc:
            status = "memory_limit_exceeded"

        compile_output = sanitize_execution_message(data.get("compile_output"))
        stderr = sanitize_execution_message(data.get("stderr"))
        if status == "compilation_error" and compile_output and not stderr:
            stderr = compile_output
        elif compile_output and status == "compilation_error":
            stderr = compile_output

        time_val = data.get("time")
        memory_val = data.get("memory")
        return ExecutionResult(
            stdout=data.get("stdout") or "",
            stderr=stderr,
            status=status,
            time=float(time_val) if time_val not in (None, "") else None,
            memory=int(memory_val) if memory_val is not None else None,
            compile_output=compile_output or None,
        )

    async def _request_with_retries(
        self,
        method: str,
        url: str,
        *,
        json: dict | list | None = None,
        params: dict | None = None,
    ) -> httpx.Response:
        retries = max(0, settings.judge0_retry_count)
        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._client_timeout()) as client:
                    response = await client.request(
                        method,
                        url,
                        json=json,
                        params=params,
                        headers=self._headers(),
                    )
                if response.status_code in {502, 503, 504} and attempt < retries:
                    await asyncio.sleep(0.3 * (attempt + 1))
                    continue
                return response
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                if attempt < retries:
                    await asyncio.sleep(0.3 * (attempt + 1))
                    continue
                raise
        assert last_exc is not None
        raise last_exc

    async def health_check(self) -> bool:
        try:
            response = await self._request_with_retries(
                "GET", f"{self.base_url}/about"
            )
            if response.status_code == 200:
                return True
            # Some installs only expose /languages
            response = await self._request_with_retries(
                "GET", f"{self.base_url}/languages"
            )
            return response.status_code == 200
        except Exception:
            logger.warning("Judge0 health check failed", exc_info=True)
            return False

    async def refresh_languages(self) -> bool:
        try:
            response = await self._request_with_retries(
                "GET", f"{self.base_url}/languages"
            )
            if response.status_code != 200:
                return False
            data = response.json()
            if isinstance(data, list):
                apply_judge0_language_catalog(data)
                return True
            return False
        except Exception:
            logger.warning("Judge0 language discovery failed", exc_info=True)
            return False

    async def _poll_until_done(self, token: str) -> dict[str, Any]:
        deadline = time.monotonic() + float(settings.judge0_max_poll_seconds)
        interval = max(50, settings.judge0_poll_interval_ms) / 1000.0
        url = f"{self.base_url}/submissions/{token}"
        while time.monotonic() < deadline:
            response = await self._request_with_retries(
                "GET",
                url,
                params={"base64_encoded": "false"},
            )
            if response.status_code >= 500:
                raise httpx.HTTPStatusError(
                    "Judge0 poll failed",
                    request=response.request,
                    response=response,
                )
            response.raise_for_status()
            data = response.json()
            status_id = (data.get("status") or {}).get("id", 2)
            mapped = JUDGE0_STATUS_MAP.get(status_id, "processing")
            if mapped in _TERMINAL or status_id not in (1, 2):
                return data
            await asyncio.sleep(interval)
        logger.warning("Judge0 poll timeout token=%s...", token[:8])
        raise TimeoutError("Judge0 poll timeout")

    async def _poll_batch(self, tokens: list[str]) -> list[dict[str, Any]]:
        deadline = time.monotonic() + float(settings.judge0_max_poll_seconds)
        interval = max(50, settings.judge0_poll_interval_ms) / 1000.0
        token_csv = ",".join(tokens)
        url = f"{self.base_url}/submissions/batch"
        while time.monotonic() < deadline:
            response = await self._request_with_retries(
                "GET",
                url,
                params={"tokens": token_csv, "base64_encoded": "false"},
            )
            response.raise_for_status()
            payload = response.json()
            submissions = payload.get("submissions") if isinstance(payload, dict) else payload
            if not isinstance(submissions, list):
                raise ValueError("Unexpected Judge0 batch response")
            done = True
            for item in submissions:
                if item is None:
                    done = False
                    break
                status_id = (item.get("status") or {}).get("id", 2)
                mapped = JUDGE0_STATUS_MAP.get(status_id, "processing")
                if mapped not in _TERMINAL and status_id in (1, 2):
                    done = False
                    break
            if done:
                return submissions
            await asyncio.sleep(interval)
        raise TimeoutError("Judge0 batch poll timeout")

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        results = await self.execute_many([request])
        return results[0]

    async def execute_many(self, requests: list[ExecutionRequest]) -> list[ExecutionResult]:
        if not requests:
            return []

        unavailable = ExecutionResult(
            stdout="",
            stderr="Code execution is currently unavailable",
            status="service_unavailable",
        )

        try:
            # Prefer batch when multiple cases
            if len(requests) == 1:
                return [await self._execute_single(requests[0])]

            batch_size = max(1, settings.judge0_batch_size)
            out: list[ExecutionResult] = []
            for i in range(0, len(requests), batch_size):
                chunk = requests[i : i + batch_size]
                out.extend(await self._execute_batch(chunk))
            return out
        except TimeoutError:
            logger.warning("Judge0 execution timed out (API/poll)")
            return [unavailable for _ in requests]
        except httpx.HTTPError:
            logger.exception("Judge0 HTTP failure")
            return [unavailable for _ in requests]
        except Exception:
            logger.exception("Judge0 unexpected failure")
            return [unavailable for _ in requests]

    async def _execute_single(self, request: ExecutionRequest) -> ExecutionResult:
        payload = self._build_payload(request)
        # Async submit + poll (wait=true can hang; we bound poll ourselves)
        response = await self._request_with_retries(
            "POST",
            f"{self.base_url}/submissions",
            json=payload,
            params={"base64_encoded": "false", "wait": "false"},
        )
        if response.status_code >= 500:
            return ExecutionResult(
                stdout="",
                stderr="Code execution is currently unavailable",
                status="service_unavailable",
            )
        response.raise_for_status()
        token = response.json().get("token")
        if not token:
            return ExecutionResult(
                stdout="",
                stderr="Code execution is currently unavailable",
                status="service_unavailable",
            )
        data = await self._poll_until_done(token)
        return self._parse_result(data)

    async def _execute_batch(self, requests: list[ExecutionRequest]) -> list[ExecutionResult]:
        payloads = [self._build_payload(req) for req in requests]
        response = await self._request_with_retries(
            "POST",
            f"{self.base_url}/submissions/batch",
            json={"submissions": payloads},
            params={"base64_encoded": "false"},
        )
        if response.status_code >= 500:
            return [
                ExecutionResult(
                    stdout="",
                    stderr="Code execution is currently unavailable",
                    status="service_unavailable",
                )
                for _ in requests
            ]
        response.raise_for_status()
        created = response.json()
        if not isinstance(created, list):
            # Some versions wrap
            created = created.get("submissions", created)
        tokens: list[str] = []
        for item in created:
            if not item or not item.get("token"):
                return [
                    ExecutionResult(
                        stdout="",
                        stderr="Code execution is currently unavailable",
                        status="service_unavailable",
                    )
                    for _ in requests
                ]
            tokens.append(item["token"])

        submissions = await self._poll_batch(tokens)
        # Preserve order relative to tokens
        by_token = {
            item.get("token"): item for item in submissions if item and item.get("token")
        }
        results: list[ExecutionResult] = []
        for token in tokens:
            data = by_token.get(token)
            if not data:
                results.append(
                    ExecutionResult(
                        stdout="",
                        stderr="Code execution is currently unavailable",
                        status="service_unavailable",
                    )
                )
            else:
                results.append(self._parse_result(data))
        return results
