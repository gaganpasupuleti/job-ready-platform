"""One-time publication of the six Visual Learning Phase 1 lessons.

This is not the general content importer. `scripts/content_batch.py` still
accepts only a local target. This module updates the six lesson rows directly.

Plan reads the connected database and writes nothing. Apply and rollback each
require three independent confirmations: an authorization value, the exact
database fingerprint, and the exact six lesson keys. Apply updates only
existing rows for those keys, inside one transaction.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.studio_batch import load_batch, plan
from app.models.question import Question
from app.models.studio import ContentBatchItem, LearningMaterial, LearningMaterialRead, LearningSyllabusEntry

BATCH_ID = "2026-10-10-visual-learning-001"
HISTORICAL_BATCH_ID = "2026-09-14-syllabus-001"
PUBLISH_AUTHORIZATION = "PUBLISH-2026-10-10-VISUAL-LEARNING-001"
ROLLBACK_AUTHORIZATION = "ROLLBACK-2026-10-10-VISUAL-LEARNING-001"
LESSON_KEYS = (
    "crt-di-tables",
    "crt-logical-patterns",
    "crt-quant-percentages",
    "crt-verbal-meaning",
    "dsa-arrays-strings",
    "dsa-complexity",
)
CONFIRM_KEYS = ",".join(LESSON_KEYS)
DIAGRAMS = {
    "crt-di-tables": "/learning-visuals/crt/data-interpretation.svg",
    "crt-logical-patterns": "/learning-visuals/crt/number-pattern.svg",
    "crt-quant-percentages": "/learning-visuals/crt/percentages-quarter.svg",
    "crt-verbal-meaning": "/learning-visuals/crt/verbal-claim.svg",
    "dsa-arrays-strings": "/learning-visuals/dsa/array-reversal.svg",
    "dsa-complexity": "/learning-visuals/dsa/complexity-growth.svg",
}
SYLLABUS = {
    "syl-crt-di-tables": ("crt-di-tables", ["syl-crt-q04"]),
    "syl-crt-logical-patterns": ("crt-logical-patterns", ["syl-crt-q02"]),
    "syl-crt-quant-percentages": ("crt-quant-percentages", ["syl-crt-q01"]),
    "syl-crt-verbal-meaning": ("crt-verbal-meaning", ["syl-crt-q03"]),
    "syl-dsa-arrays-strings": ("dsa-arrays-strings", ["syl-dsa-q02"]),
    "syl-dsa-complexity": ("dsa-complexity", ["syl-dsa-q01"]),
}
MATERIAL_FIELDS = (
    "version",
    "title",
    "summary",
    "kind",
    "level",
    "audience",
    "estimated_minutes",
    "objectives",
    "prerequisites",
    "body_md",
    "examples",
    "exercises",
    "summary_md",
    "sources",
    "families",
    "skill_tags",
    "download_relpath",
    "content_hash",
    "is_published",
)

_ROOT = Path(__file__).resolve().parents[2] / "content" / "batches"
VISUAL_BATCH = _ROOT / BATCH_ID
HISTORICAL_BATCH = _ROOT / HISTORICAL_BATCH_ID


def database_fingerprint(db: AsyncSession) -> str:
    bind = db.get_bind()
    url = getattr(bind, "url", None)
    if url is None:
        return ""
    host = (url.host or "").lower()
    port = url.port or 5432
    name = url.database or ""
    return f"{host}:{port}/{name}"


def _material_hashes(path: Path) -> dict[str, str]:
    batch = load_batch(path)
    if batch["rejected"]:
        raise RuntimeError(batch["rejected"])
    planned = plan(batch, {})
    return {
        action["key"]: action["hash"]
        for action in planned["actions"]
        if action["type"] == "material" and action["key"] in LESSON_KEYS
    }


def inspect_visual_batch(batch: dict) -> list[str]:
    rejected: list[str] = []
    if batch.get("batch_id") != BATCH_ID:
        rejected.append("unexpected batch id")
    rejected.extend(batch.get("rejected") or [])
    if batch.get("questions") or batch.get("syllabus") or batch.get("assignments") or batch.get("packs") or batch.get("project"):
        rejected.append("batch includes more than the six lesson articles")
    keys = [row["key"] for row in batch.get("materials") or []]
    if tuple(sorted(keys)) != LESSON_KEYS:
        rejected.append("batch does not contain exactly the six lesson keys")
    by_key = {row["key"]: row for row in batch.get("materials") or []}
    for key in LESSON_KEYS:
        row = by_key.get(key)
        if row is None:
            continue
        if int(row.get("version") or 0) != 2:
            rejected.append(f"{key} is not version 2")
        body = row.get("body_md") or ""
        if DIAGRAMS[key] not in body:
            rejected.append(f"{key} is missing its diagram")
        lowered = body.lower()
        if "javascript:" in lowered or "data:" in lowered:
            rejected.append(f"{key} contains an unsafe URL")
    return rejected


def _snapshot_material(row: LearningMaterial) -> dict:
    payload = {"id": str(row.id), "content_key": row.content_key}
    for field in MATERIAL_FIELDS:
        payload[field] = getattr(row, field)
    return payload


def _snapshot_item(row: ContentBatchItem) -> dict:
    return {
        "item_key": row.item_key,
        "content_type": row.content_type,
        "version": row.version,
        "content_hash": row.content_hash,
        "batch_id": row.batch_id,
        "applied_at": row.applied_at.isoformat(),
    }


async def _syllabus_state(db: AsyncSession) -> dict[str, dict]:
    rows = (await db.execute(select(LearningSyllabusEntry).where(LearningSyllabusEntry.content_key.in_(SYLLABUS)))).scalars().all()
    return {
        row.content_key: {
            "version": row.version,
            "material_key": row.material_key,
            "question_keys": list(row.question_keys or []),
        }
        for row in rows
    }


async def _question_stems(db: AsyncSession) -> dict[str, str]:
    keys = [question_key for _, question_keys in SYLLABUS.values() for question_key in question_keys]
    rows = (await db.execute(select(Question).where(Question.content_key.in_(keys)))).scalars().all()
    return {row.content_key: row.question_text for row in rows}


def _syllabus_errors(state: dict[str, dict]) -> list[str]:
    rejected = []
    for syllabus_key, (material_key, question_keys) in SYLLABUS.items():
        row = state.get(syllabus_key)
        if row is None:
            rejected.append(f"missing syllabus row {syllabus_key}")
            continue
        if row["version"] != 1 or row["material_key"] != material_key or row["question_keys"] != question_keys:
            rejected.append(f"unexpected syllabus row {syllabus_key}")
    return rejected


async def prepare_visual_phase1(db: AsyncSession) -> dict:
    batch = load_batch(VISUAL_BATCH)
    rejected = inspect_visual_batch(batch)
    version_one = _material_hashes(HISTORICAL_BATCH) if not rejected else {}
    version_two = {
        action["key"]: action["hash"]
        for action in plan(batch, {}).get("actions", [])
        if action["type"] == "material" and action["key"] in LESSON_KEYS
    }
    materials = {
        row.content_key: row
        for row in (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key.in_(LESSON_KEYS)))).scalars().all()
    }
    items = {
        row.item_key: row
        for row in (await db.execute(select(ContentBatchItem).where(ContentBatchItem.item_key.in_(LESSON_KEYS)))).scalars().all()
    }
    by_file = {row["key"]: row for row in batch.get("materials") or []}
    actions = []
    for key in LESSON_KEYS:
        current = materials.get(key)
        item = items.get(key)
        if current is None or item is None:
            rejected.append(f"{key} is not an existing published lesson")
            continue
        if item.content_hash != current.content_hash or item.version != current.version:
            rejected.append(f"{key} publication record does not match the lesson")
        expected_v2 = version_two.get(key)
        expected_v1 = version_one.get(key)
        if current.version == 2 and current.content_hash == expected_v2 and DIAGRAMS[key] in (current.body_md or ""):
            action = "unchanged"
        elif current.version == 1 and current.content_hash == expected_v1 and item.version == 1 and item.batch_id == HISTORICAL_BATCH_ID:
            action = "update"
        else:
            action = "rejected"
            rejected.append(f"{key} is not the published version 1 lesson or the already published version 2 lesson")
        actions.append(
            {
                "key": key,
                "material_id": str(current.id),
                "action": action,
                "from_version": current.version,
                "to_version": 2,
                "diagram": DIAGRAMS[key],
            }
        )
    update_count = sum(1 for row in actions if row["action"] == "update")
    unchanged_count = sum(1 for row in actions if row["action"] == "unchanged")
    if update_count and unchanged_count:
        rejected.append("partial publication of visual learning phase 1")
    rejected.extend(_syllabus_errors(await _syllabus_state(db)))
    if len(await _question_stems(db)) != len(SYLLABUS):
        rejected.append("missing associated syllabus question")
    return {
        "batch_id": BATCH_ID,
        "database": database_fingerprint(db),
        "applied": False,
        "actions": actions,
        "rejected": rejected,
        "counts": {"update": update_count, "unchanged": unchanged_count, "rejected": len(rejected)},
        "_batch_materials": by_file,
        "_version_two": version_two,
    }


def authorization_errors(*, mode: str, authorization: str | None, confirm_database: str | None, confirm_keys: str | None, fingerprint: str) -> list[str]:
    expected = PUBLISH_AUTHORIZATION if mode == "apply" else ROLLBACK_AUTHORIZATION
    errors = []
    if authorization != expected:
        errors.append("authorization rejected")
    if confirm_database != fingerprint:
        errors.append("database confirmation does not match the connected database")
    if confirm_keys != CONFIRM_KEYS:
        errors.append("key confirmation does not match the six lesson keys")
    return errors


def _payload(row: dict, version_hash: str) -> dict:
    return {
        "version": 2,
        "title": row["title"],
        "summary": row["summary"],
        "kind": row["kind"],
        "level": row["level"],
        "audience": row.get("audience"),
        "estimated_minutes": row["minutes"],
        "objectives": row["objectives"],
        "prerequisites": row["prerequisites"],
        "body_md": row["body_md"],
        "examples": row["examples"],
        "exercises": row["exercises"],
        "summary_md": row["summary"],
        "sources": row["sources"],
        "families": row["families"],
        "skill_tags": row["skills"],
        "download_relpath": row["body_file"],
        "content_hash": version_hash,
        "is_published": True,
    }


async def _backup_document(db: AsyncSession) -> dict:
    materials = (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key.in_(LESSON_KEYS)))).scalars().all()
    items = (await db.execute(select(ContentBatchItem).where(ContentBatchItem.item_key.in_(LESSON_KEYS)))).scalars().all()
    reads = (
        await db.execute(
            select(LearningMaterialRead).where(LearningMaterialRead.material_id.in_([row.id for row in materials]))
        )
    ).scalars().all()
    return {
        "batch_id": BATCH_ID,
        "database": database_fingerprint(db),
        "materials": [_snapshot_material(row) for row in sorted(materials, key=lambda row: row.content_key)],
        "batch_items": [_snapshot_item(row) for row in sorted(items, key=lambda row: row.item_key)],
        "read_ids": [str(row.id) for row in reads],
        "syllabus": await _syllabus_state(db),
        "question_stems": await _question_stems(db),
    }


def _write_backup(path: Path, document: dict) -> None:
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, default=str) + "\n", encoding="utf-8")
    reread = json.loads(path.read_text(encoding="utf-8"))
    if [row["content_key"] for row in reread["materials"]] != list(LESSON_KEYS):
        path.unlink(missing_ok=True)
        raise RuntimeError("backup reread did not contain the six lessons")


async def stage_visual_phase1(db: AsyncSession, prepared: dict) -> None:
    now = datetime.now(UTC)
    materials = {
        row.content_key: row
        for row in (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key.in_(LESSON_KEYS)))).scalars().all()
    }
    items = {
        row.item_key: row
        for row in (await db.execute(select(ContentBatchItem).where(ContentBatchItem.item_key.in_(LESSON_KEYS)))).scalars().all()
    }
    for action in prepared["actions"]:
        if action["action"] != "update":
            continue
        key = action["key"]
        current = materials[key]
        if str(current.id) != action["material_id"]:
            raise RuntimeError(f"{key} changed identity before publication")
        for field, value in _payload(prepared["_batch_materials"][key], prepared["_version_two"][key]).items():
            setattr(current, field, value)
        item = items[key]
        item.content_type = "material"
        item.version = 2
        item.content_hash = prepared["_version_two"][key]
        item.batch_id = BATCH_ID
        item.applied_at = now
    await db.flush()


async def publish_visual_phase1(
    db: AsyncSession,
    *,
    authorization: str | None,
    confirm_database: str | None,
    confirm_keys: str | None,
    backup_path: Path | None,
    commit: bool = True,
) -> dict:
    prepared = await prepare_visual_phase1(db)
    public = {key: value for key, value in prepared.items() if not key.startswith("_")}
    gate = authorization_errors(
        mode="apply",
        authorization=authorization,
        confirm_database=confirm_database,
        confirm_keys=confirm_keys,
        fingerprint=public["database"],
    )
    if gate or prepared["rejected"]:
        await db.rollback()
        return {**public, "applied": False, "refused": True, "rejected": [*gate, *prepared["rejected"]]}
    if prepared["counts"]["update"] == 0:
        await db.rollback()
        return {**public, "applied": True, "refused": False, "idempotent": True}
    if backup_path is None:
        await db.rollback()
        return {**public, "applied": False, "refused": True, "rejected": ["a new backup path is required before publication"]}
    before_syllabus = await _syllabus_state(db)
    before_questions = await _question_stems(db)
    try:
        _write_backup(backup_path, await _backup_document(db))
        await stage_visual_phase1(db, prepared)
        if await _syllabus_state(db) != before_syllabus or await _question_stems(db) != before_questions:
            raise RuntimeError("publication changed syllabus or questions")
    except Exception:
        await db.rollback()
        raise
    if commit:
        await db.commit()
    public["counts"] = {"update": prepared["counts"]["update"], "unchanged": 0, "rejected": 0}
    return {**public, "applied": True, "refused": False, "idempotent": False, "backup": str(backup_path)}


def _parse_backup_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


async def rollback_visual_phase1(
    db: AsyncSession,
    *,
    authorization: str | None,
    confirm_database: str | None,
    confirm_keys: str | None,
    backup_path: Path,
    commit: bool = True,
) -> dict:
    fingerprint = database_fingerprint(db)
    gate = authorization_errors(
        mode="rollback",
        authorization=authorization,
        confirm_database=confirm_database,
        confirm_keys=confirm_keys,
        fingerprint=fingerprint,
    )
    document = json.loads(backup_path.read_text(encoding="utf-8"))
    rejected = list(gate)
    if document.get("batch_id") != BATCH_ID or document.get("database") != fingerprint:
        rejected.append("backup was not taken from the connected database for this batch")
    if [row["content_key"] for row in document.get("materials", [])] != list(LESSON_KEYS):
        rejected.append("backup does not contain exactly the six lessons")
    version_two = _material_hashes(VISUAL_BATCH)
    materials = {
        row.content_key: row
        for row in (await db.execute(select(LearningMaterial).where(LearningMaterial.content_key.in_(LESSON_KEYS)))).scalars().all()
    }
    items = {
        row.item_key: row
        for row in (await db.execute(select(ContentBatchItem).where(ContentBatchItem.item_key.in_(LESSON_KEYS)))).scalars().all()
    }
    for row in document.get("materials", []):
        current = materials.get(row["content_key"])
        if current is None or str(current.id) != row["id"]:
            rejected.append(f"{row['content_key']} identity does not match the backup")
            continue
        if current.version != 2 or current.content_hash != version_two.get(row["content_key"]):
            rejected.append(f"{row['content_key']} is not the published version 2 lesson")
    if await _syllabus_state(db) != document.get("syllabus") or await _question_stems(db) != document.get("question_stems"):
        rejected.append("syllabus or questions changed after the backup")
    if rejected:
        await db.rollback()
        return {"applied": False, "refused": True, "rejected": rejected, "database": fingerprint}
    for row in document["materials"]:
        current = materials[row["content_key"]]
        for field in MATERIAL_FIELDS:
            setattr(current, field, row[field])
    for row in document["batch_items"]:
        item = items[row["item_key"]]
        item.content_type = row["content_type"]
        item.version = row["version"]
        item.content_hash = row["content_hash"]
        item.batch_id = row["batch_id"]
        item.applied_at = _parse_backup_time(row["applied_at"])
    await db.flush()
    if commit:
        await db.commit()
    return {"applied": True, "refused": False, "rejected": [], "database": fingerprint, "restored": list(LESSON_KEYS)}
