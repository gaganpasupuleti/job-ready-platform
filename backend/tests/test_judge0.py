"""Unit tests for Judge0 client, sanitization, language mapping — no live Judge0."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.services.code_execution.interface import ExecutionRequest
from app.services.code_execution.judge0 import JUDGE0_STATUS_MAP, Judge0CodeExecutionService
from app.services.code_execution.languages import (
    apply_judge0_language_catalog,
    get_language,
    validate_language_id,
)
from app.services.code_execution.sanitize import sanitize_execution_message


def test_status_map_covers_core_outcomes():
    assert JUDGE0_STATUS_MAP[3] == "accepted"
    assert JUDGE0_STATUS_MAP[4] == "wrong_answer"
    assert JUDGE0_STATUS_MAP[5] == "time_limit_exceeded"
    assert JUDGE0_STATUS_MAP[6] == "compilation_error"
    assert JUDGE0_STATUS_MAP[11] == "runtime_error"


def test_sanitize_strips_paths_and_hosts():
    raw = (
        'File "/box/script.py", line 3\n'
        "Connection to 10.0.0.5:5432 failed\n"
        "X-Auth-Token: secret"
    )
    clean = sanitize_execution_message(raw)
    assert "/box/" not in clean
    assert "10.0.0.5" not in clean
    assert "secret" not in clean
    assert "[path]" in clean or "[host]" in clean or "[redacted]" in clean


def test_language_catalog_marks_missing_unavailable():
    apply_judge0_language_catalog(
        [
            {"id": 71, "name": "Python (3.8.1)"},
            {"id": 63, "name": "JavaScript (Node.js 12.14.0)"},
        ]
    )
    assert get_language(71).available is True
    assert get_language(71).name == "Python (3.8.1)"
    assert get_language(62).available is False
    with pytest.raises(ValueError):
        validate_language_id(62)
    # restore defaults for other tests
    apply_judge0_language_catalog(
        [
            {"id": 71, "name": "Python (3.8.1)"},
            {"id": 62, "name": "Java (OpenJDK 13.0.1)"},
            {"id": 54, "name": "C++ (GCC 9.2.0)"},
            {"id": 63, "name": "JavaScript (Node.js 12.14.0)"},
        ]
    )


def test_auth_header_included():
    svc = Judge0CodeExecutionService(
        base_url="http://judge.example",
        auth_token="tok-123",
        auth_header="X-Auth-Token",
    )
    headers = svc._headers()
    assert headers["X-Auth-Token"] == "tok-123"
    assert "tok-123" not in str(svc.base_url)


@pytest.mark.asyncio
async def test_execute_accepted_via_poll(monkeypatch):
    svc = Judge0CodeExecutionService(base_url="http://judge.test", auth_token="t")

    post_resp = MagicMock()
    post_resp.status_code = 201
    post_resp.raise_for_status = MagicMock()
    post_resp.json.return_value = {"token": "abc"}

    get_resp = MagicMock()
    get_resp.status_code = 200
    get_resp.raise_for_status = MagicMock()
    get_resp.json.return_value = {
        "stdout": "2\n",
        "stderr": None,
        "compile_output": None,
        "status": {"id": 3, "description": "Accepted"},
        "time": "0.01",
        "memory": 2048,
        "token": "abc",
    }

    async def fake_request(method, url, **kwargs):
        if method == "POST":
            return post_resp
        return get_resp

    monkeypatch.setattr(svc, "_request_with_retries", fake_request)
    result = await svc.execute(
        ExecutionRequest(source_code="print(2)", language_id=71, expected_output="2")
    )
    assert result.status == "accepted"
    assert result.stdout.strip() == "2"


@pytest.mark.asyncio
async def test_compile_error_sanitized(monkeypatch):
    svc = Judge0CodeExecutionService(base_url="http://judge.test", auth_token="t")

    post_resp = MagicMock()
    post_resp.status_code = 201
    post_resp.raise_for_status = MagicMock()
    post_resp.json.return_value = {"token": "ce1"}

    get_resp = MagicMock()
    get_resp.status_code = 200
    get_resp.raise_for_status = MagicMock()
    get_resp.json.return_value = {
        "stdout": None,
        "stderr": None,
        "compile_output": "/box/Main.java:6: error: expected ';'",
        "status": {"id": 6, "description": "Compilation Error"},
        "time": None,
        "memory": None,
        "token": "ce1",
    }

    async def fake_request(method, url, **kwargs):
        return post_resp if method == "POST" else get_resp

    monkeypatch.setattr(svc, "_request_with_retries", fake_request)
    result = await svc.execute(ExecutionRequest(source_code="class X {}", language_id=62))
    assert result.status == "compilation_error"
    assert "/box/" not in (result.stderr or "")


@pytest.mark.asyncio
async def test_poll_timeout_returns_unavailable(monkeypatch):
    svc = Judge0CodeExecutionService(base_url="http://judge.test", auth_token="t")

    post_resp = MagicMock()
    post_resp.status_code = 201
    post_resp.raise_for_status = MagicMock()
    post_resp.json.return_value = {"token": "slow"}

    async def fake_request(method, url, **kwargs):
        if method == "POST":
            return post_resp
        raise TimeoutError("Judge0 poll timeout")

    monkeypatch.setattr(svc, "_request_with_retries", fake_request)
    monkeypatch.setattr(svc, "_poll_until_done", AsyncMock(side_effect=TimeoutError("poll")))
    result = await svc.execute(ExecutionRequest(source_code="print(1)", language_id=71))
    assert result.status == "service_unavailable"


@pytest.mark.asyncio
async def test_connection_failure_unavailable(monkeypatch):
    svc = Judge0CodeExecutionService(base_url="http://judge.test", auth_token="t")

    async def boom(*args, **kwargs):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(svc, "_request_with_retries", boom)
    results = await svc.execute_many(
        [ExecutionRequest(source_code="print(1)", language_id=71)]
    )
    assert results[0].status == "service_unavailable"


@pytest.mark.asyncio
async def test_runtime_and_tle_mapping(monkeypatch):
    svc = Judge0CodeExecutionService(base_url="http://judge.test", auth_token="t")

    async def run_status(status_id: int, desc: str):
        post_resp = MagicMock(status_code=201)
        post_resp.raise_for_status = MagicMock()
        post_resp.json.return_value = {"token": "t1"}
        get_resp = MagicMock(status_code=200)
        get_resp.raise_for_status = MagicMock()
        get_resp.json.return_value = {
            "stdout": "",
            "stderr": "IndexError",
            "compile_output": None,
            "status": {"id": status_id, "description": desc},
            "time": "0.1",
            "memory": 1000,
            "token": "t1",
        }

        async def fake_request(method, url, **kwargs):
            return post_resp if method == "POST" else get_resp

        monkeypatch.setattr(svc, "_request_with_retries", fake_request)
        return await svc.execute(ExecutionRequest(source_code="x", language_id=71))

    re = await run_status(11, "Runtime Error (NZEC)")
    assert re.status == "runtime_error"
    tle = await run_status(5, "Time Limit Exceeded")
    assert tle.status == "time_limit_exceeded"


@pytest.mark.asyncio
async def test_batch_execute(monkeypatch):
    svc = Judge0CodeExecutionService(base_url="http://judge.test", auth_token="t")

    post_resp = MagicMock(status_code=201)
    post_resp.raise_for_status = MagicMock()
    post_resp.json.return_value = [{"token": "a"}, {"token": "b"}]

    async def fake_request(method, url, **kwargs):
        assert "batch" in url or method == "GET"
        if method == "POST":
            return post_resp
        get_resp = MagicMock(status_code=200)
        get_resp.raise_for_status = MagicMock()
        get_resp.json.return_value = {
            "submissions": [
                {
                    "token": "a",
                    "stdout": "1",
                    "stderr": None,
                    "status": {"id": 3},
                    "time": "0.01",
                    "memory": 1,
                },
                {
                    "token": "b",
                    "stdout": "2",
                    "stderr": None,
                    "status": {"id": 4},
                    "time": "0.01",
                    "memory": 1,
                },
            ]
        }
        return get_resp

    monkeypatch.setattr(svc, "_request_with_retries", fake_request)
    results = await svc.execute_many(
        [
            ExecutionRequest(source_code="print(1)", language_id=71, expected_output="1"),
            ExecutionRequest(source_code="print(0)", language_id=71, expected_output="1"),
        ]
    )
    assert results[0].status == "accepted"
    assert results[1].status == "wrong_answer"


@pytest.mark.asyncio
async def test_execution_status_shape(client):
    response = await client.get("/api/v1/coding/execution-status")
    assert response.status_code == 200
    body = response.json()
    assert "available" in body
    assert "enabled" in body
    assert "provider" in body
