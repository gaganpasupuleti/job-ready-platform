from app.services.code_execution.interface import (
    CodeExecutionService,
    ExecutionRequest,
    ExecutionResult,
)


class MockCodeExecutionService(CodeExecutionService):
    """In-process mock for tests — never executes untrusted code."""

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if request.expected_output is None:
            return ExecutionResult(
                stdout="",
                stderr="Mock execution requires expected_output",
                status="internal_error",
            )

        actual = (request.stdout_override if request.stdout_override is not None else request.source_code)
        # For mock: treat source_code containing "print(" as simulating stdout from a simple echo
        # Tests will use predictable Python solutions; we compare against expected via stdin simulation
        stdout = self._simulate_stdout(request)
        expected = request.expected_output.strip()
        actual_out = stdout.strip()

        if request.source_code.strip().startswith("# COMPILE_ERROR"):
            return ExecutionResult(stdout="", stderr="SyntaxError", status="compilation_error")
        if request.source_code.strip().startswith("# RUNTIME_ERROR"):
            return ExecutionResult(stdout="", stderr="RuntimeError", status="runtime_error")
        if request.source_code.strip().startswith("# TLE"):
            return ExecutionResult(stdout="", stderr="", status="time_limit_exceeded")

        status = "accepted" if actual_out == expected else "wrong_answer"
        return ExecutionResult(
            stdout=stdout,
            stderr="",
            status=status,
            time=0.01,
            memory=1024,
        )

    def _simulate_stdout(self, request: ExecutionRequest) -> str:
        """Simple deterministic mock: if code contains 'return ' use eval pattern for sum problems."""
        code = request.source_code
        stdin = request.stdin.strip()

        if "two_sum" in code.lower() or "Two Sum" in code:
            nums_line, target_line = stdin.split("\n", 1)
            nums = [int(x.strip()) for x in nums_line.strip("[]").split(",") if x.strip()]
            target = int(target_line.strip())
            for i, a in enumerate(nums):
                for j in range(i + 1, len(nums)):
                    if a + nums[j] == target:
                        return f"[{i}, {j}]"

        if "reverse_string" in code.lower() or "reverse" in code.lower():
            return stdin[::-1]

        if "add" in code.lower() and stdin:
            parts = stdin.split()
            if len(parts) == 2:
                return str(int(parts[0]) + int(parts[1]))

        # Fallback: echo stdin (lets tests pass trivial echo solutions)
        if "print(input())" in code or "print(input(" in code:
            return stdin

        return stdin
