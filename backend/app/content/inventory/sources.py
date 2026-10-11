"""Pinned inputs and side-effect-free readers for the content inventory."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SPRINT_BATCH = "backend/content/batches/2026-10-10-crt-dsa-sprint-001"
VISUAL_BATCH = "backend/content/batches/2026-10-10-visual-learning-001"


@dataclass(frozen=True)
class SourceRef:
    label: str
    sha: str
    branch: str
    paths: tuple[str, ...]
    status: str


MASTER = SourceRef(
    "master",
    "bc4e80b8ade331d592b95d885369c19c0f6d0af5",
    "master",
    ("backend/app/seed", "backend/content", "backend/app/content/studio_batch.py"),
    "merged baseline",
)
PR17 = SourceRef(
    "pr-17",
    "df02a59eda4e0fe08fe46e070383d78168950e04",
    "feature/visual-learning-phase1",
    (VISUAL_BATCH,),
    "open pull request #17, unmerged",
)
PR18 = SourceRef(
    "pr-18",
    "4d129fed88383e32777765c3eb446a3ceeab54ce",
    "feature/crt-dsa-content-sprint-1",
    (SPRINT_BATCH,),
    "open pull request #18, unmerged",
)
QUALITY_GATE = SourceRef(
    "quality-gate",
    "666941b5bb44ebd5da3747d5ff217bebb412f6c8",
    "content/sprint1-quality-gate",
    (SPRINT_BATCH,),
    "candidate branch, no pull request, awaiting human content approval",
)
PINNED_REFS: tuple[SourceRef, ...] = (MASTER, PR17, PR18, QUALITY_GATE)


class SourceUnavailable(RuntimeError):
    """A pinned commit or file is missing. Never substitute another ref."""


class GitReader:
    """Reads files from one pinned commit. It never touches the working tree."""

    def __init__(self, repo_root: Path, ref: SourceRef) -> None:
        self.repo_root = repo_root
        self.ref = ref
        if self._git("cat-file", "-e", f"{ref.sha}^{{commit}}").returncode != 0:
            raise SourceUnavailable(
                f"{ref.label}: commit {ref.sha} ({ref.branch}) is not in this clone. "
                "Fetch it; do not substitute another branch."
            )

    def _git(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(["git", *args], cwd=self.repo_root, capture_output=True, check=False)

    def _require_declared(self, path: str) -> None:
        if not any(path == root or path.startswith(root + "/") for root in self.ref.paths):
            raise ValueError(f"{path} is not a declared input of {self.ref.label}")

    def read_bytes(self, path: str) -> bytes:
        self._require_declared(path)
        proc = self._git("show", f"{self.ref.sha}:{path}")
        if proc.returncode != 0:
            raise SourceUnavailable(f"{self.ref.label}: {path} is missing at {self.ref.sha}")
        return proc.stdout

    def checkout_eols(self, paths: list[str]) -> dict[str, str]:
        """The eol attribute this commit declares per path, as a checkout would apply it."""
        if not paths:
            return {}
        proc = self._git("check-attr", f"--source={self.ref.sha}", "eol", "--", *paths)
        if proc.returncode != 0:
            raise SourceUnavailable(f"{self.ref.label}: cannot read eol attributes")
        eols = {}
        for line in proc.stdout.decode("utf-8").splitlines():
            path, _attr, value = line.rsplit(": ", 2)
            eols[path] = value.strip()
        return eols

    def read_text(self, path: str) -> str:
        return self.read_bytes(path).decode("utf-8")

    def read_json(self, path: str) -> Any:
        return json.loads(self.read_text(path))

    def list_files(self, path: str) -> list[str]:
        self._require_declared(path)
        proc = self._git("ls-tree", "-r", "--name-only", self.ref.sha, "--", path)
        if proc.returncode != 0:
            raise SourceUnavailable(f"{self.ref.label}: cannot list {path} at {self.ref.sha}")
        return sorted(line for line in proc.stdout.decode("utf-8").splitlines() if line)


def checkout_bytes(data: bytes, eol: str) -> bytes:
    """File bytes as a checkout produces them; batch manifests hash these, not the blob."""
    if eol == "crlf":
        return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return data


def repo_root() -> Path:
    here = Path(__file__).resolve().parent
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=here, capture_output=True, check=False
    )
    if proc.returncode != 0:
        raise SourceUnavailable("the inventory must run inside a git clone of the repository")
    return Path(proc.stdout.decode("utf-8").strip())


@dataclass(frozen=True)
class Symbol:
    """A name, attribute, or expression that the inventory does not execute."""

    text: str


@dataclass(frozen=True)
class CallExpr:
    func: str
    args: tuple[Any, ...]
    kwargs: tuple[tuple[str, Any], ...]


def evaluate(node: ast.AST) -> Any:
    """Turn literal source syntax into data without running any code."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [evaluate(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(evaluate(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return {
            evaluate(key): evaluate(value)
            for key, value in zip(node.keys, node.values, strict=True)
            if key is not None
        }
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = evaluate(node.operand)
        if isinstance(value, int | float):
            return -value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = evaluate(node.left), evaluate(node.right)
        if isinstance(left, str) and isinstance(right, str):
            return left + right
        if isinstance(left, list) and isinstance(right, list):
            return left + right
    if isinstance(node, ast.Call):
        return CallExpr(
            ast.unparse(node.func),
            tuple(evaluate(arg) for arg in node.args),
            tuple((kw.arg or "**", evaluate(kw.value)) for kw in node.keywords),
        )
    return Symbol(ast.unparse(node))


def _assignments(body: list[ast.stmt]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for node in body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    values[target.id] = evaluate(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                values[node.target.id] = evaluate(node.value)
    return values


def module_values(source: str) -> dict[str, Any]:
    return _assignments(ast.parse(source).body)


def function_values(source: str, name: str) -> dict[str, Any]:
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name:
            return _assignments(node.body)
    raise SourceUnavailable(f"function {name} not found")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
