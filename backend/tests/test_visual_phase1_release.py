"""Disposable-database proof for the one-time Visual Learning Phase 1 publication."""

import subprocess
import sys
from pathlib import Path

import pytest

from app.content.studio_batch import apply_batch, load_batch
from app.content.visual_phase1_release import (
    CONFIRM_KEYS,
    DIAGRAMS,
    LESSON_KEYS,
    PUBLISH_AUTHORIZATION,
    ROLLBACK_AUTHORIZATION,
    SYLLABUS,
    VISUAL_BATCH,
    inspect_visual_batch,
    prepare_visual_phase1,
    publish_visual_phase1,
    rollback_visual_phase1,
    stage_visual_phase1,
)

BACKEND = Path(__file__).resolve().parents[1]
SYLLABUS_BATCH = BACKEND / "content" / "batches" / "2026-09-14-syllabus-001"


def test_general_importer_still_refuses_a_production_target():
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/content_batch.py",
            "--batch",
            "content/batches/2026-10-10-visual-learning-001",
            "--apply",
            "--target",
            "production",
        ],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0
    assert "does not publish production" in completed.stderr + completed.stdout
    release_source = (BACKEND / "app" / "content" / "visual_phase1_release.py").read_text(encoding="utf-8")
    assert "apply_batch" not in release_source


def test_visual_batch_is_exactly_six_version_two_lessons():
    batch = load_batch(VISUAL_BATCH)
    assert inspect_visual_batch(batch) == []
    mutated = {**batch, "materials": [*batch["materials"], {**batch["materials"][0], "key": "crt-extra"}]}
    assert any("exactly the six" in item for item in inspect_visual_batch(mutated))


@pytest.mark.asyncio
async def test_phase1_publication_is_gated_idempotent_and_reversible(client, student_auth, tmp_path):
    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models.studio import ContentBatchItem, LearningMaterial, LearningMaterialRead, LearningSyllabusEntry
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        materials = (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key.in_(LESSON_KEYS)))).scalars().all()
        material_ids = [row.id for row in materials]
        if material_ids:
            reads = (await db.execute(select(LearningMaterialRead).where(LearningMaterialRead.material_id.in_(material_ids)))).scalars().all()
            for read in reads:
                await db.delete(read)
            await db.flush()
            for row in materials:
                await db.delete(row)
        items = (await db.execute(select(ContentBatchItem).where(ContentBatchItem.item_key.in_(LESSON_KEYS)))).scalars().all()
        for item in items:
            await db.delete(item)
        await db.commit()

    async with AsyncSessionLocal() as db:
        original = await apply_batch(db, SYLLABUS_BATCH)
        assert not original.get("refused"), original

    headers = student_auth[0]
    before = await client.get("/api/v1/studio/syllabus/syl-crt-quant-percentages", headers=headers)
    assert before.status_code == 200, before.text
    question_stem = before.json()["practice"][0]["stem"]
    marked = await client.post("/api/v1/studio/materials/crt-quant-percentages/read", headers=headers)
    assert marked.status_code == 200, marked.text

    async with AsyncSessionLocal() as db:
        prepared = await prepare_visual_phase1(db)
        assert prepared["rejected"] == []
        assert prepared["counts"]["update"] == 6
        await db.rollback()
        material = (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key == "crt-quant-percentages"))).scalar_one()
        material_id = material.id
        assert material.version == 1
        student = (await db.execute(select(User).where(User.email == student_auth[1]))).scalar_one()
        read = (
            await db.execute(
                select(LearningMaterialRead).where(
                    LearningMaterialRead.material_id == material_id,
                    LearningMaterialRead.user_id == student.id,
                )
            )
        ).scalar_one()
        read_at = read.read_at
        fingerprint = prepared["database"]

    async with AsyncSessionLocal() as db:
        refused = await publish_visual_phase1(
            db,
            authorization=None,
            confirm_database=fingerprint,
            confirm_keys=CONFIRM_KEYS,
            backup_path=tmp_path / "should-not-be-written.json",
        )
        assert refused["refused"] is True
        assert "authorization rejected" in refused["rejected"]
        wrong_database = await publish_visual_phase1(
            db,
            authorization=PUBLISH_AUTHORIZATION,
            confirm_database="production.internal:5432/railway",
            confirm_keys=CONFIRM_KEYS,
            backup_path=tmp_path / "wrong-database.json",
        )
        assert wrong_database["refused"] is True
        assert any("database confirmation" in item for item in wrong_database["rejected"])

    async with AsyncSessionLocal() as db:
        staged = await prepare_visual_phase1(db)
        await stage_visual_phase1(db, staged)
        await db.rollback()
    async with AsyncSessionLocal() as db:
        material = (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key == "crt-quant-percentages"))).scalar_one()
        assert material.version == 1
        assert material.id == material_id

    async with AsyncSessionLocal() as db:
        material = (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key == "dsa-complexity"))).scalar_one()
        item = (await db.execute(select(ContentBatchItem).where(ContentBatchItem.item_key == "dsa-complexity"))).scalar_one()
        saved = (material.version, material.content_hash, item.version, item.content_hash, item.batch_id)
        material.version = 2
        material.content_hash = "not-the-reviewed-version"
        item.version = 2
        item.content_hash = "not-the-reviewed-version"
        await db.commit()
    async with AsyncSessionLocal() as db:
        unexpected = await prepare_visual_phase1(db)
        assert unexpected["rejected"]
        await db.rollback()
    async with AsyncSessionLocal() as db:
        material = (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key == "dsa-complexity"))).scalar_one()
        item = (await db.execute(select(ContentBatchItem).where(ContentBatchItem.item_key == "dsa-complexity"))).scalar_one()
        material.version, material.content_hash, item.version, item.content_hash, item.batch_id = saved
        await db.commit()

    backup = tmp_path / "visual-phase1-backup.json"
    async with AsyncSessionLocal() as db:
        published = await publish_visual_phase1(
            db,
            authorization=PUBLISH_AUTHORIZATION,
            confirm_database=fingerprint,
            confirm_keys=CONFIRM_KEYS,
            backup_path=backup,
        )
        assert published["refused"] is False, published
        assert published["counts"]["update"] == 6
    assert backup.is_file()

    async with AsyncSessionLocal() as db:
        repeated = await publish_visual_phase1(
            db,
            authorization=PUBLISH_AUTHORIZATION,
            confirm_database=fingerprint,
            confirm_keys=CONFIRM_KEYS,
            backup_path=tmp_path / "second-backup-not-needed.json",
        )
        assert repeated["idempotent"] is True
        assert repeated["counts"]["update"] == 0
        material = (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key == "crt-quant-percentages"))).scalar_one()
        assert material.id == material_id
        assert material.version == 2
        assert DIAGRAMS["crt-quant-percentages"] in material.body_md
        student = (await db.execute(select(User).where(User.email == student_auth[1]))).scalar_one()
        read = (
            await db.execute(
                select(LearningMaterialRead).where(
                    LearningMaterialRead.material_id == material.id,
                    LearningMaterialRead.user_id == student.id,
                )
            )
        ).scalar_one()
        assert read.read_at == read_at
        for syllabus_key, (material_key, question_keys) in SYLLABUS.items():
            entry = (await db.execute(select(LearningSyllabusEntry).where(LearningSyllabusEntry.content_key == syllabus_key))).scalar_one()
            assert entry.version == 1
            assert entry.material_key == material_key
            assert entry.question_keys == question_keys

    after = await client.get("/api/v1/studio/syllabus/syl-crt-quant-percentages", headers=headers)
    assert after.json()["practice"][0]["stem"] == question_stem
    for material_key, diagram in DIAGRAMS.items():
        syllabus_key = next(key for key, (linked, _) in SYLLABUS.items() if linked == material_key)
        lesson = await client.get(f"/api/v1/studio/syllabus/{syllabus_key}", headers=headers)
        assert diagram in lesson.json()["material"]["body_md"]

    async with AsyncSessionLocal() as db:
        restored = await rollback_visual_phase1(
            db,
            authorization=ROLLBACK_AUTHORIZATION,
            confirm_database=fingerprint,
            confirm_keys=CONFIRM_KEYS,
            backup_path=backup,
        )
        assert restored["refused"] is False, restored
    async with AsyncSessionLocal() as db:
        material = (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key == "crt-quant-percentages"))).scalar_one()
        assert material.id == material_id
        assert material.version == 1
        assert "/learning-visuals/" not in material.body_md
        student = (await db.execute(select(User).where(User.email == student_auth[1]))).scalar_one()
        read = (
            await db.execute(
                select(LearningMaterialRead).where(
                    LearningMaterialRead.material_id == material.id,
                    LearningMaterialRead.user_id == student.id,
                )
            )
        ).scalar_one()
        assert read.read_at == read_at

    async with AsyncSessionLocal() as db:
        republished = await publish_visual_phase1(
            db,
            authorization=PUBLISH_AUTHORIZATION,
            confirm_database=fingerprint,
            confirm_keys=CONFIRM_KEYS,
            backup_path=tmp_path / "visual-phase1-republish.json",
        )
        assert republished["counts"]["update"] == 6
        material = (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key == "dsa-arrays-strings"))).scalar_one()
        assert DIAGRAMS["dsa-arrays-strings"] in material.body_md
