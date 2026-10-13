"""PUB-01 publication candidate planner: read-only, canonical eligibility, proposal only."""

import ast
import dataclasses
import hashlib
import json
import os
import random
import re
import subprocess
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.job import Job, JobPublicationDecision
from app.services import jobs_source_reader, jobs_source_sync, publication_candidates
from app.services.jobs_source_reader import (
    CatalogEntry,
    SourceCatalogSnapshot,
    fetch_source_catalog,
)
from app.services.jobs_source_sync import (
    SourceJob,
    decision_key,
    parse_reviewed_batch,
    plan_named_batch,
    source_identity,
)
from app.services.publication_candidates import (
    CANDIDATE_NOTICE,
    ApplicationRow,
    ApplicationState,
    PlanCategory,
    build_publication_plan,
    load_application_state,
    read_only_session,
    run_publication_planner,
    summary_lines,
    write_plan_artifacts,
)

NOW = datetime(2026, 10, 13, 12, 0, tzinfo=UTC)
SOURCE_TARGET = "host=source.internal port=5432 database=railway"
APPLICATION_TARGET = "host=app.internal port=5432 database=jobready_db"
BACKEND = Path(__file__).resolve().parents[1]
PLANNER_MODULE = BACKEND / "app" / "services" / "publication_candidates.py"
READER_MODULE = BACKEND / "app" / "services" / "jobs_source_reader.py"
SCRIPT = BACKEND / "scripts" / "sync_jobs_source.py"
CANDIDATE_FIELDS = {
    "source",
    "job_id",
    "title",
    "company",
    "role_family",
    "actual_role_name",
    "experience_bucket",
    "approved_status",
    "manual_review_needed",
    "has_jd_clean",
    "date_posted",
    "scraped_created_at",
    "link_status",
    "job_url",
    "apply_url",
}
WRITE_CALLS = {
    "record_publication_decision",
    "apply_plan",
    "apply_named_plan",
    "_upsert",
    "mark_withdrawn",
    "repair_archived_active_flags",
    "backfill_source_taxonomy",
    "add",
    "add_all",
    "commit",
    "flush",
    "delete",
    "merge",
    "executemany",
    "copy_records_to_table",
    "_apply_target_url",
}
SQL_WRITE = re.compile(r"\b(INSERT|UPDATE|DELETE|TRUNCATE|ALTER|CREATE|DROP|GRANT|MERGE|UPSERT)\b")


def _job(**overrides) -> SourceJob:
    payload = dict(
        job_id="CQJ-PLAN-0001",
        source="naukri",
        title="Data Engineer",
        company="Infosys",
        location="Hyderabad",
        job_url="https://example.com/jobs/data-engineer",
        apply_url="https://example.com/apply/data-engineer",
        link_status="active",
        approved_status="PENDING",
        manual_review_needed=False,
        date_posted=datetime(2026, 10, 1, tzinfo=UTC),
        scraped_created_at=datetime(2026, 10, 2, tzinfo=UTC),
        synced_at=datetime(2026, 10, 2, tzinfo=UTC),
        jd_summary=None,
        jd_clean="Build pipelines. Source description only.",
        jd_requirements=["SQL required"],
        jd_responsibilities=["Own the warehouse"],
        required_skills=["sql"],
        actual_role_name="Data Engineer",
        role_family="data-engineer",
        experience_bucket="Fresher",
        salary_min=Decimal("10"),
        salary_max=Decimal("12"),
        currency="INR",
    )
    payload.update(overrides)
    return SourceJob(**payload)


def _entry(**overrides) -> CatalogEntry:
    return CatalogEntry(job=_job(**overrides), has_jd_clean=True)


def _state(decisions=None, rows=(), has_decisions=True) -> ApplicationState:
    return ApplicationState(
        decisions=dict(decisions or {}),
        owned_rows=list(rows),
        has_publication_decisions=has_decisions,
    )


def _app_row(job_id: str, status: str = "active", is_active: bool = True) -> ApplicationRow:
    return ApplicationRow(external_id=source_identity(job_id), status=status, is_active=is_active)


def _plan(entries, state=None):
    return build_publication_plan(
        entries,
        state or _state(),
        generated_at=NOW,
        source_target=SOURCE_TARGET,
        application_target=APPLICATION_TARGET,
    )


def _only_category(plan) -> str:
    present = [name for name, count in plan.report["categories"].items() if count]
    assert len(present) == 1, plan.report["categories"]
    assert plan.report["categories"][present[0]] == 1
    return present[0]


def test_active_valid_job_without_decision_or_row_is_a_candidate():
    plan = _plan([_entry()])
    assert _only_category(plan) == PlanCategory.PUBLISH_DECISION_MISSING_CONTENT_ELIGIBLE
    assert plan.batch_text == "naukri/CQJ-PLAN-0001\n"
    assert plan.report["candidate_count"] == 1
    assert plan.report["decisions"]["missing"] == 1
    record = plan.report["candidates"][0]
    assert CANDIDATE_FIELDS <= set(record)
    assert record["has_jd_clean"] is True
    assert record["warnings"] == []
    assert plan.report["notice"] == CANDIDATE_NOTICE


def test_existing_publish_decision_is_never_proposed():
    key = "CQJ-PLAN-0001"
    publish = {decision_key("naukri", key): "publish"}
    visible = _plan([_entry()], _state(publish, [_app_row(key)]))
    assert _only_category(visible) == PlanCategory.VISIBLE_OR_ALREADY_PUBLISHED
    missing_row = _plan([_entry()], _state(publish))
    assert _only_category(missing_row) == PlanCategory.DECISION_EXISTS_APP_ROW_MISSING
    archived = _plan([_entry()], _state(publish, [_app_row(key, "archived", False)]))
    assert _only_category(archived) == PlanCategory.OTHER
    assert archived.report["other_reasons"] == {"publish_decision_app_row_not_active": 1}
    for plan in (visible, missing_row, archived):
        assert plan.batch_text == ""
        assert plan.report["candidate_count"] == 0
        assert plan.report["decisions"]["publish"] == 1


def test_existing_withhold_decision_is_never_proposed():
    key = "CQJ-PLAN-0001"
    withhold = {decision_key("naukri", key): "withhold"}
    for rows in ([], [_app_row(key, "archived", False)]):
        plan = _plan([_entry()], _state(withhold, rows))
        assert _only_category(plan) == PlanCategory.WITHHELD
        assert plan.batch_text == ""
        assert plan.report["decisions"]["withhold"] == 1


def test_missing_description_is_content_blocked():
    plan = _plan(
        [_entry(jd_clean=None, jd_summary=None, jd_requirements=None, jd_responsibilities=None)]
    )
    assert _only_category(plan) == PlanCategory.PUBLISH_DECISION_MISSING_CONTENT_BLOCKED
    assert plan.report["content_exclusions_missing_decision"] == {"missing_source_description": 1}
    assert plan.batch_text == ""


def test_missing_company_is_content_blocked():
    plan = _plan([_entry(company="  ")])
    assert _only_category(plan) == PlanCategory.PUBLISH_DECISION_MISSING_CONTENT_BLOCKED
    assert plan.report["content_exclusions_missing_decision"] == {"missing_title_or_company": 1}
    assert plan.batch_text == ""


def test_manufacturing_qc_as_software_qa_is_content_blocked():
    plan = _plan(
        [
            _entry(
                title="Walk-in || Qc Inspector",
                company="SRI Bm Tools",
                actual_role_name="QA / Testing Engineer",
                role_family="qa-testing",
                jd_clean="Drawing quality check on the shop floor.",
            )
        ]
    )
    assert _only_category(plan) == PlanCategory.PUBLISH_DECISION_MISSING_CONTENT_BLOCKED
    assert plan.report["content_exclusions_missing_decision"] == {"classification_mismatch": 1}
    assert plan.batch_text == ""


def test_inactive_link_is_not_a_candidate():
    key = "CQJ-PLAN-0001"
    no_decision = _plan([_entry(link_status="expired")])
    assert _only_category(no_decision) == PlanCategory.LINK_INACTIVE
    published = _plan(
        [_entry(link_status="expired")],
        _state({decision_key("naukri", key): "publish"}, [_app_row(key, "archived", False)]),
    )
    assert _only_category(published) == PlanCategory.LINK_INACTIVE
    for plan in (no_decision, published):
        assert plan.batch_text == ""
        assert plan.report["active_catalog_count"] == 0
        assert plan.report["content_exclusions"]["link_not_active"] == 1


def test_existing_jobs_server_row_is_not_a_new_candidate():
    key = "CQJ-PLAN-0001"
    for status, is_active in (("active", True), ("archived", False)):
        plan = _plan([_entry()], _state(rows=[_app_row(key, status, is_active)]))
        assert _only_category(plan) == PlanCategory.OTHER
        assert plan.report["other_reasons"] == {"application_row_without_decision": 1}
        assert plan.batch_text == ""


def test_duplicate_or_unsafe_identity_is_refused_deterministically():
    entries = [
        _entry(job_id="CQJ-DUP-SAME"),
        _entry(job_id="CQJ-DUP-SAME", title="Second copy"),
        _entry(job_id="CQJ-DUP-BOARD", source="indeed"),
        _entry(job_id="CQJ-DUP-BOARD", source="linkedin"),
        _entry(job_id="CQJ/SLASH"),
        _entry(job_id="CQJ #SPACE"),
        _entry(job_id="CQJ#HASH"),
        _entry(job_id=" CQJ-PADDED"),
        _entry(job_id=""),
        _entry(job_id="CQJ-" + "X" * 80),
        _entry(job_id="CQJ-BLANK-SOURCE", source=" "),
        _entry(job_id="CQJ-DUP-APP"),
        _entry(job_id="CQJ-SAFE"),
    ]
    state = _state(rows=[_app_row("CQJ-DUP-APP"), _app_row("CQJ-DUP-APP", "archived", False)])
    first = _plan(entries, state)
    second = _plan(list(reversed(entries)), state)
    assert first.report == second.report
    assert first.batch_text == second.batch_text == "naukri/CQJ-SAFE\n"
    assert first.report["categories"][PlanCategory.IDENTITY_CONFLICT] == 12
    assert first.report["identity_conflicts"] == {
        "blank_job_id": 1,
        "blank_source": 1,
        "duplicate_application_external_id": 1,
        "duplicate_catalog_job_id": 4,
        "job_id_not_batch_safe": 3,
        "job_id_surrounding_whitespace": 1,
        "job_id_too_long_for_decision": 1,
    }


def test_input_order_does_not_change_batch_or_hash():
    boards = ["naukri", "linkedin", "indeed", "foundit", "LinkedIn"]
    entries = [
        _entry(job_id=f"CQJ-2026101{index % 3}-{index:04d}", source=boards[index % len(boards)])
        for index in range(30)
    ]
    baseline = _plan(entries)
    lines = baseline.batch_text.splitlines()
    pairs = [tuple(line.split("/", 1)) for line in lines]
    assert pairs == sorted(pairs)
    assert {source for source, _ in pairs} == {"foundit", "indeed", "linkedin", "naukri"}
    assert baseline.candidate_set_sha256 == hashlib.sha256(baseline.batch_text.encode()).hexdigest()
    assert baseline.report["candidate_set_sha256"] == baseline.candidate_set_sha256
    for seed in range(5):
        shuffled = list(entries)
        random.Random(seed).shuffle(shuffled)
        again = _plan(shuffled)
        assert again.batch_text == baseline.batch_text
        assert again.candidate_set_sha256 == baseline.candidate_set_sha256
        assert json.dumps(again.report, sort_keys=True) == json.dumps(
            baseline.report, sort_keys=True
        )


def test_written_batch_round_trips_through_existing_reviewed_batch_path(tmp_path):
    entries = [
        _entry(job_id="CQJ-20261013-0002", source="linkedin"),
        _entry(job_id="CQJ-20261013-0001", source="indeed"),
        _entry(job_id="CQJ-20261013-0003", source="naukri", link_status="expired"),
    ]
    plan = _plan(entries)
    result = write_plan_artifacts(plan, tmp_path / "plans")
    raw = result.batch_path.read_bytes()
    assert raw == b"indeed/CQJ-20261013-0001\nlinkedin/CQJ-20261013-0002\n"
    assert hashlib.sha256(raw).hexdigest() == plan.candidate_set_sha256
    assert result.batch_path.name == "publication_candidates_20261013T120000Z.txt"
    report = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert report["candidate_batch_path"] == str(result.batch_path.resolve())
    assert report["candidate_set_sha256"] == plan.candidate_set_sha256
    assert report["notice"] == CANDIDATE_NOTICE
    names = parse_reviewed_batch(raw.decode("utf-8"))
    granted = {decision_key(name.source, name.job_id): "publish" for name in names}
    named = plan_named_batch([entry.job for entry in entries], {}, granted, names)
    assert named.rejected == []
    assert named.archive_ids == []
    assert [row.job_id for row in named.inserts] == ["CQJ-20261013-0001", "CQJ-20261013-0002"]
    with pytest.raises(FileExistsError):
        write_plan_artifacts(plan, tmp_path / "plans")


def test_quality_warnings_are_metadata_not_exclusions():
    plan = _plan(
        [
            _entry(
                role_family="other-review",
                manual_review_needed=True,
                approved_status="NEEDS_REVIEW",
                experience_bucket="Experienced",
                date_posted=None,
            )
        ]
    )
    assert _only_category(plan) == PlanCategory.PUBLISH_DECISION_MISSING_CONTENT_ELIGIBLE
    assert plan.report["candidates"][0]["warnings"] == [
        "role_family_other_review",
        "manual_review_needed",
        "experienced_role",
        "missing_date_posted",
    ]
    assert plan.report["quality_warnings"] == {
        "role_family_other_review": 1,
        "manual_review_needed": 1,
        "experienced_role": 1,
        "missing_date_posted": 1,
    }
    breakdown = plan.report["candidate_breakdown"]
    assert breakdown["by_approved_status"] == {"NEEDS_REVIEW": 1}
    assert breakdown["by_manual_review_needed"] == {"true": 1}
    assert breakdown["by_experience_bucket"] == {"Experienced": 1}


def test_every_catalog_row_lands_in_exactly_one_category():
    entries = [
        _entry(job_id="CQJ-VISIBLE"),
        _entry(job_id="CQJ-CANDIDATE"),
        _entry(job_id="CQJ-BLOCKED", company=None),
        _entry(job_id="CQJ-NO-ROW"),
        _entry(job_id="CQJ-HELD"),
        _entry(job_id="CQJ-EXPIRED", link_status="expired"),
        _entry(job_id="CQJ/CONFLICT"),
        _entry(job_id="CQJ-ODD"),
    ]
    state = _state(
        {
            decision_key("naukri", "CQJ-VISIBLE"): "publish",
            decision_key("naukri", "CQJ-NO-ROW"): "publish",
            decision_key("naukri", "CQJ-HELD"): "withhold",
            decision_key("naukri", "CQJ-ODD"): "maybe",
        },
        [_app_row("CQJ-VISIBLE"), _app_row("CQJ-GONE", "archived", False)],
    )
    plan = _plan(entries, state)
    assert plan.report["categories"] == {category.value: 1 for category in PlanCategory}
    assert sum(plan.report["categories"].values()) == plan.report["catalog_count"] == 8
    assert plan.report["other_reasons"] == {"unrecognized_decision": 1}
    assert plan.report["decisions"] == {
        "publish": 2,
        "withhold": 1,
        "missing": 4,
        "unrecognized": 1,
        "table_total": 4,
        "table_publish": 2,
        "table_withhold": 1,
    }
    assert plan.report["application"] == {
        "integration_owned_rows": 2,
        "active_rows": 1,
        "archived_rows": 1,
        "other_status_rows": 0,
        "owned_rows_without_catalog_job": 1,
    }
    assert plan.batch_text == "naukri/CQJ-CANDIDATE\n"


def _called_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                names.add(node.func.attr)
    return names


def _imported_names(tree: ast.AST) -> set[str]:
    return {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }


def _string_constants(tree: ast.AST) -> list[str]:
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


def _function(tree: ast.Module, name: str) -> ast.AST:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} not found")


def test_planner_has_no_decision_or_job_write_path():
    planner = ast.parse(PLANNER_MODULE.read_text(encoding="utf-8"))
    assert not _called_names(planner) & WRITE_CALLS
    assert not _imported_names(planner) & WRITE_CALLS
    for value in _string_constants(planner):
        assert not SQL_WRITE.search(value), value
    assert "JOBS_APPLY_DATABASE_URL" not in PLANNER_MODULE.read_text(encoding="utf-8")

    reader = ast.parse(READER_MODULE.read_text(encoding="utf-8"))
    catalog_fetch = _function(reader, "fetch_source_catalog")
    assert not _called_names(catalog_fetch) & WRITE_CALLS
    for value in _string_constants(reader):
        assert not SQL_WRITE.search(value), value

    script = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    for name in ("_plan_publication_candidates", "_plan_application_url"):
        node = _function(script, name)
        assert not _called_names(node) & WRITE_CALLS
        assert "JOBS_APPLY_DATABASE_URL" not in _string_constants(node)
        assert "APPLY_TARGET_ENV" not in {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _snapshot(entries, *, validated=True, source_decisions=False) -> SourceCatalogSnapshot:
    return SourceCatalogSnapshot(
        entries=list(entries),
        has_validated_jobs=validated,
        has_publication_decisions=source_decisions,
    )


def _fakes(snapshot, state):
    seen: list[str] = []

    async def fetch(dsn: str) -> SourceCatalogSnapshot:
        seen.append("source")
        return snapshot

    async def load(dsn: str) -> ApplicationState:
        seen.append("application")
        return state

    return fetch, load, seen


async def test_planner_runs_with_every_write_function_disabled(tmp_path, monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("planner reached a write path")

    for name in (
        "record_publication_decision",
        "apply_plan",
        "apply_named_plan",
        "_upsert",
        "mark_withdrawn",
        "repair_archived_active_flags",
        "backfill_source_taxonomy",
    ):
        monkeypatch.setattr(jobs_source_sync, name, refuse)
        monkeypatch.setattr(publication_candidates, name, refuse, raising=False)
    secret = "runtime-planner-secret"
    fetch, load, seen = _fakes(
        _snapshot([_entry(job_id="CQJ-RUN-0001"), _entry(job_id="CQJ-RUN-0002", source="indeed")]),
        _state(),
    )
    result = await run_publication_planner(
        source_dsn=f"postgresql://source:{secret}@source.internal:5432/railway",
        application_dsn=f"postgresql+asyncpg://appuser:{secret}@app.internal:5432/jobready_db",
        output_dir=tmp_path,
        now=NOW,
        fetch_catalog=fetch,
        load_application=load,
    )
    assert seen == ["application", "source"]
    assert (
        result.batch_path.read_text(encoding="utf-8")
        == "indeed/CQJ-RUN-0002\nnaukri/CQJ-RUN-0001\n"
    )
    blob = result.report_path.read_text(encoding="utf-8") + "\n".join(summary_lines(result))
    assert secret not in blob
    assert "postgresql" not in blob
    assert "appuser" not in blob
    assert result.report["targets"] == {
        "source": SOURCE_TARGET,
        "application": APPLICATION_TARGET,
    }
    assert "NO_WRITES publication planning only" in summary_lines(result)


@pytest.mark.parametrize(
    ("snapshot", "state", "message"),
    [
        (_snapshot([_entry()], source_decisions=True), _state(), "source target has application"),
        (_snapshot([_entry()], validated=False), _state(), "no validated_jobs"),
        (_snapshot([_entry()]), _state(has_decisions=False), "no publication decisions"),
        (_snapshot([]), _state(), "empty source catalog"),
    ],
)
async def test_planner_refuses_wrong_roles_or_empty_catalog(tmp_path, snapshot, state, message):
    fetch, load, _ = _fakes(snapshot, state)
    with pytest.raises(SystemExit, match=message) as refused:
        await run_publication_planner(
            source_dsn="postgresql://source:pw@source.internal:5432/railway",
            application_dsn="postgresql://app:pw@app.internal:5432/jobready_db",
            output_dir=tmp_path / "plans",
            now=NOW,
            fetch_catalog=fetch,
            load_application=load,
        )
    assert str(refused.value.code).startswith("PLAN_REFUSED")
    assert not (tmp_path / "plans").exists()


async def test_planner_refuses_same_source_and_application_database(tmp_path):
    fetch, load, seen = _fakes(_snapshot([_entry()]), _state())
    with pytest.raises(SystemExit, match="same database"):
        await run_publication_planner(
            source_dsn="postgresql://source:pw@db.internal:5432/railway",
            application_dsn="postgresql+asyncpg://app:pw@db.internal:5432/railway",
            output_dir=tmp_path,
            fetch_catalog=fetch,
            load_application=load,
        )
    assert seen == []


class _FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_exc):
        return False


class _FakeSourceConnection:
    def __init__(self, read_only: str, row: dict):
        self.read_only = read_only
        self.row = row
        self.statements: list[str] = []
        self.transactions: list[dict] = []
        self.closed = False

    async def execute(self, sql: str):
        self.statements.append(sql)

    def transaction(self, **kwargs):
        self.transactions.append(kwargs)
        return _FakeTransaction()

    async def fetchval(self, sql: str):
        self.statements.append(sql)
        return self.read_only

    async def fetchrow(self, sql: str):
        self.statements.append(sql)
        return (True, False)

    async def fetch(self, sql: str):
        self.statements.append(sql)
        return [self.row]

    async def close(self):
        self.closed = True


async def test_source_catalog_is_fetched_in_a_verified_read_only_transaction(monkeypatch):
    row = {**dataclasses.asdict(_job()), "has_jd_clean": True}
    connections: list[_FakeSourceConnection] = []

    async def connect(_dsn, **_kwargs):
        connection = _FakeSourceConnection("on", row)
        connections.append(connection)
        return connection

    monkeypatch.setattr(jobs_source_reader.asyncpg, "connect", connect)
    snapshot = await fetch_source_catalog("postgresql://source:pw@source.internal:5432/railway")
    connection = connections[0]
    assert connection.statements[0] == "SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY"
    assert connection.transactions == [{"isolation": "repeatable_read", "readonly": True}]
    assert connection.statements[1] == "SHOW transaction_read_only"
    for sql in connection.statements:
        assert sql.strip().split()[0] in {"SET", "SHOW", "SELECT"}
        assert not SQL_WRITE.search(sql)
    assert connection.closed
    assert snapshot.has_validated_jobs is True
    assert snapshot.has_publication_decisions is False
    assert snapshot.entries == [CatalogEntry(job=_job(), has_jd_clean=True)]

    async def writable(_dsn, **_kwargs):
        connection = _FakeSourceConnection("off", row)
        connections.append(connection)
        return connection

    monkeypatch.setattr(jobs_source_reader.asyncpg, "connect", writable)
    with pytest.raises(RuntimeError, match="not read-only"):
        await fetch_source_catalog("postgresql://source:pw@source.internal:5432/railway")
    assert connections[-1].closed
    assert not any("FROM public.validated_jobs" in sql for sql in connections[-1].statements)
    assert any("FROM public.validated_jobs" in sql for sql in connection.statements)


async def _counts() -> tuple[int, int]:
    async with AsyncSessionLocal() as db:
        jobs = await db.scalar(select(func.count()).select_from(Job))
        decisions = await db.scalar(select(func.count()).select_from(JobPublicationDecision))
    return int(jobs or 0), int(decisions or 0)


async def test_application_state_is_read_in_a_verified_read_only_session():
    key = f"CQJ-PLANRO-{uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        db.add(
            JobPublicationDecision(
                id=uuid4(), source="indeed", source_job_id=key, decision="publish"
            )
        )
        await db.commit()
    before = await _counts()
    state = await load_application_state(settings.database_url)
    assert state.has_publication_decisions is True
    assert state.decisions[decision_key("indeed", key)] == "publish"
    assert all(row.external_id.startswith("jobs-server:") for row in state.owned_rows)
    async with read_only_session(settings.database_url) as db:
        with pytest.raises(DBAPIError, match="read-only transaction"):
            await db.execute(
                text(
                    "INSERT INTO job_publication_decisions "
                    "(id, source, source_job_id, decision, created_at, updated_at) "
                    "VALUES (gen_random_uuid(), 'indeed', :key, 'publish', now(), now())"
                ),
                {"key": f"{key}-write"},
            )
    async with read_only_session(settings.database_url) as db:
        with pytest.raises(DBAPIError, match="read-only transaction"):
            await db.execute(text("UPDATE jobs SET is_active = is_active"))
    assert await _counts() == before


def _run_cli(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def test_planner_cli_refuses_unsafe_use_and_never_prints_credentials(tmp_path):
    secret = "planner-cli-secret"
    env = os.environ.copy()
    env.pop("JOBS_PLAN_APPLICATION_DATABASE_URL", None)
    env["JOBS_SOURCE_DATABASE_URL"] = f"postgresql://source:{secret}@127.0.0.1:1/railway"
    env["DATABASE_URL"] = f"postgresql://appuser:{secret}@127.0.0.1:2/jobready_db"
    env["JOBS_APPLY_DATABASE_URL"] = f"postgresql://apply:{secret}@127.0.0.1:3/jobready_db"
    out = tmp_path / "plans"
    batch = tmp_path / "reviewed.txt"
    batch.write_text("indeed/CQJ-REVIEWED\n", encoding="utf-8")
    same_env = {
        **env,
        "JOBS_PLAN_APPLICATION_DATABASE_URL": f"postgresql://app:{secret}@127.0.0.1:1/railway",
    }

    unreachable = _run_cli(["--plan-publication-candidates", "--output-dir", str(out)], env)
    combined = _run_cli(
        [
            "--plan-publication-candidates",
            "--output-dir",
            str(out),
            "--apply-reviewed-batch",
            "--batch",
            str(batch),
            "--confirm-target",
            "127.0.0.1:2/jobready_db",
        ],
        env,
    )
    no_output_dir = _run_cli(["--plan-publication-candidates"], env)
    stray_output_dir = _run_cli(["--output-dir", str(out)], env)
    same_target = _run_cli(["--plan-publication-candidates", "--output-dir", str(out)], same_env)

    assert unreachable.returncode == 1
    assert "SOURCE_TARGET host=127.0.0.1 port=1 database=railway" in unreachable.stdout
    assert "APPLICATION_TARGET host=127.0.0.1 port=2 database=jobready_db" in unreachable.stdout
    assert "PLAN_FAILED" in unreachable.stdout
    assert "planning cannot be combined" in combined.stdout
    assert "--output-dir is required" in no_output_dir.stdout
    assert "only used with --plan-publication-candidates" in stray_output_dir.stdout
    assert "same database" in same_target.stdout
    for result in (combined, no_output_dir, stray_output_dir, same_target):
        assert result.returncode == 2
    for result in (unreachable, combined, no_output_dir, stray_output_dir, same_target):
        blob = result.stdout + result.stderr
        assert secret not in blob
        assert "postgresql://" not in blob
        assert "appuser" not in blob
        assert "APPLIED" not in blob
    assert not out.exists() or not any(out.iterdir())
