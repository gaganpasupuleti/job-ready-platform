"""Optional live Judge0 integration tests.

Enable with:
  JUDGE0_LIVE_TESTS=1
  JUDGE0_URL=http://localhost:2358
  JUDGE0_AUTH_TOKEN=...
  JUDGE0_ENABLED=true

Never run in default CI.
"""

from __future__ import annotations

import os

import pytest

from app.services.code_execution.interface import ExecutionRequest
from app.services.code_execution.judge0 import Judge0CodeExecutionService


def _live_enabled() -> bool:
    return os.environ.get("JUDGE0_LIVE_TESTS", "").lower() in {"1", "true", "yes"}


pytestmark = pytest.mark.skipif(
    not _live_enabled(),
    reason="Set JUDGE0_LIVE_TESTS=1 with a reachable Judge0 instance",
)


@pytest.fixture
def judge0() -> Judge0CodeExecutionService:
    return Judge0CodeExecutionService()


@pytest.mark.asyncio
async def test_live_python_accepted(judge0):
    result = await judge0.execute(
        ExecutionRequest(
            source_code="print(sum(map(int, input().split())))",
            language_id=71,
            stdin="2 3\n",
            expected_output="5\n",
            cpu_time_limit=2,
            wall_time_limit=5,
            memory_limit_kb=128000,
        )
    )
    assert result.status == "accepted", result


@pytest.mark.asyncio
async def test_live_python_wrong_answer(judge0):
    result = await judge0.execute(
        ExecutionRequest(
            source_code="print(0)",
            language_id=71,
            stdin="",
            expected_output="1\n",
            cpu_time_limit=2,
            wall_time_limit=5,
            memory_limit_kb=128000,
        )
    )
    assert result.status == "wrong_answer", result


@pytest.mark.asyncio
async def test_live_python_runtime_error(judge0):
    result = await judge0.execute(
        ExecutionRequest(
            source_code="print(1/0)",
            language_id=71,
            stdin="",
            cpu_time_limit=2,
            wall_time_limit=5,
            memory_limit_kb=128000,
        )
    )
    assert result.status == "runtime_error", result


@pytest.mark.asyncio
async def test_live_java_compile_run(judge0):
    source = """
public class Main {
  public static void main(String[] args) {
    System.out.println(42);
  }
}
"""
    result = await judge0.execute(
        ExecutionRequest(
            source_code=source,
            language_id=62,
            expected_output="42\n",
            cpu_time_limit=3,
            wall_time_limit=8,
            memory_limit_kb=256000,
        )
    )
    assert result.status in {"accepted", "wrong_answer"}, result
    assert result.status != "service_unavailable"


@pytest.mark.asyncio
async def test_live_cpp_run(judge0):
    source = '#include <iostream>\nint main(){std::cout<<7;return 0;}\n'
    result = await judge0.execute(
        ExecutionRequest(
            source_code=source,
            language_id=54,
            expected_output="7",
            cpu_time_limit=2,
            wall_time_limit=5,
            memory_limit_kb=128000,
        )
    )
    assert result.status in {"accepted", "wrong_answer"}, result


@pytest.mark.asyncio
async def test_live_javascript_run(judge0):
    result = await judge0.execute(
        ExecutionRequest(
            source_code="console.log(9)",
            language_id=63,
            expected_output="9\n",
            cpu_time_limit=2,
            wall_time_limit=5,
            memory_limit_kb=128000,
        )
    )
    assert result.status in {"accepted", "wrong_answer"}, result


@pytest.mark.asyncio
async def test_live_tle(judge0):
    result = await judge0.execute(
        ExecutionRequest(
            source_code="while True:\n    pass\n",
            language_id=71,
            cpu_time_limit=0.5,
            wall_time_limit=2,
            memory_limit_kb=64000,
        )
    )
    assert result.status in {"time_limit_exceeded", "runtime_error"}, result


@pytest.mark.asyncio
async def test_live_isolation_no_env_leak(judge0):
    """Student code should not see Job Ready secrets via process env."""
    result = await judge0.execute(
        ExecutionRequest(
            source_code=(
                "import os\n"
                "keys=sorted(os.environ)\n"
                "print('DATABASE_URL' in os.environ)\n"
                "print('JWT_SECRET_KEY' in os.environ)\n"
                "print('SQL_SANDBOX' in ''.join(keys))\n"
            ),
            language_id=71,
            cpu_time_limit=2,
            wall_time_limit=5,
            memory_limit_kb=64000,
        )
    )
    assert result.status == "accepted", result
    lines = (result.stdout or "").strip().splitlines()
    assert lines[:3] == ["False", "False", "False"]
