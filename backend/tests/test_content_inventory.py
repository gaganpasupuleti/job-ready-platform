"""Read-only content inventory: determinism, accounting, references, and honesty.

Tests that read the pinned commits skip with the missing SHA named when a shallow clone
lacks them; the inventory itself refuses to substitute another branch.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.content.hashing import content_hash
from app.content.inventory import analysis
from app.content.inventory.extract import ITEM_FIELDS, build_items, load_snapshot
from app.content.inventory.report import GENERATED_FILES, check, render
from app.content.inventory.sources import (
    MASTER,
    PINNED_REFS,
    CallExpr,
    GitReader,
    SourceRef,
    SourceUnavailable,
    module_values,
    repo_root,
)

REPO = repo_root()
EVIDENCE = REPO / "docs" / "audits" / "2026-10-11-content-inventory"
SPRINT = "2026-10-10-crt-dsa-sprint-001"


def _pinned_available() -> str | None:
    for ref in PINNED_REFS:
        proc = subprocess.run(
            ["git", "cat-file", "-e", f"{ref.sha}^{{commit}}"], cwd=REPO, capture_output=True
        )
        if proc.returncode != 0:
            return f"pinned source unavailable: {ref.label} {ref.sha}"
    return None


requires_pinned = pytest.mark.skipif(
    _pinned_available() is not None, reason=_pinned_available() or ""
)


@pytest.fixture(scope="module")
def real():
    snapshot = load_snapshot(REPO)
    items = build_items(snapshot)
    analysis.annotate(snapshot, items)
    return snapshot, items


@pytest.fixture(scope="module")
def rendered():
    return render(REPO)


def _tracked_state() -> tuple[str, str]:
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", "backend/app/seed", "backend/content"],
        cwd=REPO,
        capture_output=True,
        check=True,
    ).stdout.decode()
    tree = subprocess.run(
        ["git", "rev-parse", "HEAD:backend/content", "HEAD:backend/app/seed"],
        cwd=REPO,
        capture_output=True,
        check=True,
    ).stdout.decode()
    return status, tree


@requires_pinned
def test_output_is_deterministic_and_matches_committed_evidence(rendered):
    assert sorted(rendered) == sorted(GENERATED_FILES)
    assert check(rendered, EVIDENCE) == []
    for name, text in rendered.items():
        assert "\r" not in text, name
        assert "2026-10-11T" not in text, f"{name} contains a timestamp"


@requires_pinned
def test_output_is_stable_in_a_fresh_process_with_a_different_hash_seed():
    env = {**os.environ, "PYTHONHASHSEED": "12345"}
    proc = subprocess.run(
        [sys.executable, "-m", "app.content.inventory", "--out", str(EVIDENCE), "--check"],
        cwd=REPO / "backend",
        env=env,
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr.decode()


@requires_pinned
def test_generation_does_not_touch_sources(real):
    before = _tracked_state()
    render(REPO)
    assert _tracked_state() == before


@requires_pinned
def test_item_ids_and_keys_are_unique_within_their_scope(real):
    _, items = real
    ids = [item["item_id"] for item in items]
    assert len(ids) == len(set(ids))
    assert analysis.duplicate_keys(items) == []
    assert all(set(item) >= set(ITEM_FIELDS) for item in items)


@requires_pinned
def test_source_definition_counts(real):
    _, items = real

    def rows(label: str, collection: str, kind: str = "mcq") -> int:
        return sum(
            1
            for i in items
            if i["source_label"] == label and i["collection"] == collection and i["kind"] == kind
        )

    assert rows("master", "phase11-aptitude") == 110
    assert rows("master", "phase11-technical") == 110
    assert rows("master", "build6-ai") == 110
    assert rows("master", "build7-cloud") == 103
    assert rows("master", "build7-devops") == 97
    assert rows("master", "build7-cybersecurity") == 77
    assert rows("master", "runner-samples") == 20
    assert rows("master", "runner-templates") == 17
    assert rows("master", "PROBLEM_BANK", "coding_problem") == 21
    assert rows("master", "2026-09-14-syllabus-001", "syllabus_entry") == 19
    assert rows("quality-gate", SPRINT, "syllabus_entry") == 10
    master = analysis.methodology_counts(items, "master")
    assert master["1_definitions_in_source"] == {
        "mcq_rows": 750,
        "seed_mcq_rows": 644,
        "batch_mcq_rows": 106,
    }
    assert master["8_dsa_coding_definitions"] == 21


@requires_pinned
def test_sprint_adoptions_are_not_counted_as_new_questions(real):
    _, items = real
    for label in ("pr-18", "quality-gate"):
        accounting = analysis.sprint_accounting(items, label)
        assert accounting["rows"] == 70
        assert accounting["adopt"] == 50
        assert accounting["create"] == 20
        assert accounting["adopt_linked_to_phase11"] == 50
    master = analysis.methodology_counts(items, "master")
    gate = analysis.methodology_counts(items, "master+quality-gate")
    assert gate["3_adoption_references"] == 50
    assert gate["4_new_batch_questions"] - master["4_new_batch_questions"] == 20
    assert (
        gate["1_definitions_in_source"]["mcq_rows"] - master["1_definitions_in_source"]["mcq_rows"]
        == 70
    )
    assert (
        gate["2_unique_authored_keys"]["distinct_mcq_stem_fingerprints"]
        < gate["1_definitions_in_source"]["mcq_rows"]
    )


@requires_pinned
def test_version_reporting(real):
    snapshot, items = real
    gate = analysis.sprint_accounting(items, "quality-gate")
    assert gate["versions"] == {"1": 53, "2": 17}
    assert gate["with_revises"] == 11
    assert analysis.sprint_accounting(items, "pr-18")["versions"] == {"1": 70}
    digests = analysis.batch_digests(snapshot)
    sprint = analysis.version_comparison(items, digests, "pr-18", "quality-gate")
    assert len(sprint["changed_with_version_bump"]) == 17
    assert "changed_without_version_bump" not in sprint
    assert len(sprint["unchanged"]) == 74
    visual = analysis.version_comparison(items, digests, "master", "pr-17")
    assert len(visual["changed_with_version_bump"]) == 6
    assert "changed_without_version_bump" not in visual


@requires_pinned
def test_manifests_verify_against_checkout_bytes(real):
    snapshot, _ = real
    statuses = {finding["status"] for finding in analysis.manifest_checks(snapshot)}
    assert statuses == {"match"}


@requires_pinned
def test_production_status_is_reported_as_unknown(rendered, real):
    _, items = real
    for view in analysis.VIEWS:
        counts = analysis.methodology_counts(items, view)
        assert counts["6_actual_published_database_rows"] == "Production verification pending."
        assert counts["9_executable_coding_problems"]["runtime_execution"] == (
            "Production verification pending."
        )
    data = json.loads(rendered["SOURCE_COUNTS.json"])
    assert data["production_status"] == "Production verification pending."
    assert data["curriculum_target"]["status"] == "target, not an existing completion count"
    for measurement in data["historical_measurements"]:
        assert measurement["measured_on"] and measurement["source"]
        assert "not re-verified" in measurement["status"]
    assert all(
        row["student_ready"] == "not determined" for row in analysis.coverage(items, real[0])
    )


def test_unavailable_commit_stops_instead_of_substituting():
    missing = SourceRef("missing", "0" * 40, "nowhere", ("backend/content",), "test")
    with pytest.raises(SourceUnavailable, match="do not substitute"):
        GitReader(REPO, missing)
    with pytest.raises(SourceUnavailable):
        load_snapshot(REPO, (MASTER, missing))


@requires_pinned
def test_reader_refuses_undeclared_paths():
    reader = GitReader(REPO, PINNED_REFS[1])
    with pytest.raises(ValueError, match="not a declared input"):
        reader.read_bytes("backend/app/core/config.py")


def test_seed_parsing_never_executes_code(tmp_path: Path):
    marker = tmp_path / "executed"
    source = f"ROWS = [__import__('pathlib').Path({str(marker)!r}).touch()]\nX = ('a', -1)\n"
    values = module_values(source)
    assert not marker.exists()
    assert isinstance(values["ROWS"][0], CallExpr)
    assert values["X"] == ("a", -1)


def _synthetic_snapshot() -> dict:
    ref = MASTER
    taxonomy = (
        "TAXONOMY = [{'slug': 'placement', 'categories': [{'slug': 'aptitude', "
        "'topics': [{'slug': 'percentages'}]}]}]\n"
    )
    seed_row = (
        "('placement', 'aptitude', 'percentages', 'easy', 'What is 10% of 50?', 'Five.', "
        "'5', '10', '15', '20')"
    )
    seed = {
        name: {}
        for name in (
            "phase11_technical_mcq.py",
            "build6_mcq.py",
            "build7_mcq.py",
            "build6_challenges.py",
            "build7_scenarios.py",
            "sql_problems_bank.py",
            "build51_catalog.py",
        )
    }
    seed["phase11_aptitude_mcq.py"] = module_values(
        f"APTITUDE_MCQS = [{seed_row}, ('placement', 'aptitude')]"
    )
    question = {
        "key": "q1",
        "stem": "Pick one",
        "mode": "single",
        "skill": "quantitative",
        "explanation": "Steps\n\nRelated lesson\nlesson-that-does-not-exist",
        "options": [
            {"key": "A", "text": "x", "correct": True},
            {"key": "B", "text": "x", "correct": True},
        ],
    }
    batch = {
        "files": {"articles/present.md": "0" * 64},
        "manifest": {"items": [{"path": "questions.json", "sha256": "f" * 64}]},
        "checkout_eol": "unspecified",
        "questions": [question, dict(question)],
        "materials": [{"key": "present", "body_file": "articles/absent.md", "version": 1}],
        "packs": [{"key": "pack", "question_keys": ["q1", "ghost"]}],
        "entries": [
            {
                "key": "entry",
                "status": "published",
                "question_keys": ["q1"],
                "track": "crt",
                "unit": "quantitative",
            },
            {
                "key": "entry2",
                "status": "published",
                "material_key": "missing-material",
                "question_keys": [],
                "track": "crt",
                "unit": "quantitative",
            },
        ],
    }
    return {
        "refs": {ref.label: ref},
        "seed": seed,
        "sources": {
            "runner.py": "SAMPLE_QUESTIONS = []\ndef _expand_questions():\n    templates = []\n",
            "problems_bank.py": "PROBLEM_BANK = []\n",
            "build8_seed.py": (
                "QUESTIONS = []\nPACKS = [{'slug': 'p', 'question_slugs': ['nope']}]\n"
            ),
            "learn_data.py": (
                "BEGINNER_DSA_PATHS = [('b', 'B', 'graphs', 'd')]\n"
                "DATA_STRUCTURE_PATHS = []\nALGORITHM_PATHS = []\nPYTHON_COURSE_MODULES = []\n"
            ),
            "build51_catalog.py": "",
            "taxonomy_data.py": taxonomy,
            "coding_data.py": "EXTRA_TOPICS = []\n",
        },
        "generated": {},
        "batches": {ref.label: {"synthetic-batch": batch}},
    }


def test_missing_and_malformed_references_are_flagged():
    snapshot = _synthetic_snapshot()
    items = build_items(snapshot)
    analysis.annotate(snapshot, items)
    flags = {item["item_id"]: item["flags"] for item in items}

    assert "malformed-row" in flags["master/phase11-aptitude/#002"]
    assert "related-lesson-unresolved" in flags["master/synthetic-batch/q1"]
    assert "single-answer-correct-count" in flags["master/synthetic-batch/q1"]
    assert "duplicate-option-text" in flags["master/synthetic-batch/q1"]
    assert "unresolved-question-reference:ghost" in flags["master/synthetic-batch/pack"]
    assert "published-without-material" in flags["master/synthetic-batch/entry"]
    assert (
        "unresolved-material-reference:missing-material" in flags["master/synthetic-batch/entry2"]
    )
    assert "material-body-missing" in flags["master/synthetic-batch/present"]
    assert "path-topic-has-no-coding-problems" in flags["master/BEGINNER_DSA_PATHS/b"]
    assert "unresolved-interview-reference:nope" in flags["master/build8-PACKS/p"]
    assert analysis.duplicate_keys(items) == [
        {"scope": "master/synthetic-batch", "kind": "mcq", "key": "q1", "count": 2}
    ]
    assert analysis.manifest_checks(snapshot)[0]["status"] == "missing"


def test_adoption_without_a_source_is_flagged_not_invented():
    snapshot = _synthetic_snapshot()
    question = snapshot["batches"]["master"]["synthetic-batch"]["questions"][0]
    question["adoption"] = "required"
    question["stem"] = "A stem that no Phase 11 row has"
    snapshot["batches"]["master"]["synthetic-batch"]["questions"] = [question]
    items = build_items(snapshot)
    analysis.annotate(snapshot, items)
    adopted = next(i for i in items if i["content_key"] == "q1")
    assert adopted["adopts"] is None
    assert "adoption-source-not-found" in adopted["flags"]

    question["stem"] = "What is 10% of 50?"
    items = build_items(copy.deepcopy(snapshot))
    analysis.annotate(snapshot, items)
    adopted = next(i for i in items if i["content_key"] == "q1")
    assert adopted["adopts"] == "master/phase11-aptitude/#001"
    assert adopted["stem_fingerprint"] == content_hash("What is 10% of 50?")


@requires_pinned
def test_source_counts_report_overlapping_views_separately(rendered):
    data = json.loads(rendered["SOURCE_COUNTS.json"])
    views = data["methodology_counts"]
    assert set(views) == set(analysis.VIEWS)
    master = views["master"]["1_definitions_in_source"]["mcq_rows"]
    for view in ("master+pr-18", "master+quality-gate"):
        assert views[view]["3_adoption_references"] == 50
        assert views[view]["1_definitions_in_source"]["mcq_rows"] == master + 70
    assert set(data) >= {"methodology_counts", "production_status", "historical_measurements"}
