"""Disposable-database checks for reworded Sprint 1 questions that keep their identity."""

import hashlib
import itertools
import json
import shutil
from pathlib import Path

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.content import studio_batch
from app.content.revised_seed_stems import REVISED_SEED_STEMS, superseded_by_revision
from app.content.studio_batch import SPRINT_BATCH_ID, apply_batch, load_batch
from app.db.session import AsyncSessionLocal
from app.models.practice import Bookmark
from app.models.question import Question, QuestionOption
from app.models.studio import ContentBatchItem
from app.models.user import User
from app.seed.phase11_activate import seed_phase11_mcqs
from app.seed.phase11_aptitude_mcq import APTITUDE_MCQS
from tests.test_crt_dsa_sprint import BATCH, SATURDAY, _seed_required

SYL = "sprint1-syl-03"
CX = "sprint1-cx-02"


def _row(key: str) -> dict:
    return next(row for row in load_batch(BATCH)["questions"] if row["key"] == key)


SYL_ROW = _row(SYL)
CX_ROW = _row(CX)
SYL_PRIOR = SYL_ROW["revises"]["stem"]
CX_PRIOR = CX_ROW["revises"]["stem"]


def _necessary_options(premises, options: dict) -> set[str]:
    """Options true in every model of the premises, over all sets of phone/laptop/gadget kinds."""
    kinds = list(itertools.product([False, True], repeat=3))
    necessary = set(options)
    for size in range(len(kinds) + 1):
        for model in itertools.combinations(kinds, size):
            if all(premise(model) for premise in premises):
                necessary &= {text for text, holds in options.items() if holds(model)}
    return necessary


def NO_PHONE_IS_LAPTOP(model) -> bool:
    return not any(phone and laptop for phone, laptop, _ in model)


def SOME_LAPTOP(model) -> bool:
    return any(laptop for _, laptop, _ in model)


def LAPTOPS_ARE_GADGETS(model) -> bool:
    return all(gadget for _, laptop, gadget in model if laptop)


SYL_OPTIONS = {
    "Some gadgets are not phones": lambda model: any(
        gadget and not phone for phone, _, gadget in model
    ),
    "No gadget is a phone": lambda model: not any(gadget and phone for phone, _, gadget in model),
    "All gadgets are laptops": lambda model: all(laptop for _, laptop, gadget in model if gadget),
    "All phones are laptops": lambda model: all(laptop for phone, laptop, _ in model if phone),
}


def test_revised_syllogism_has_exactly_one_necessary_answer():
    assert [opt["text"] for opt in SYL_ROW["options"]] == list(SYL_OPTIONS)
    correct = [opt["text"] for opt in SYL_ROW["options"] if opt["correct"]]
    revised = _necessary_options(
        [NO_PHONE_IS_LAPTOP, SOME_LAPTOP, LAPTOPS_ARE_GADGETS], SYL_OPTIONS
    )
    original = _necessary_options([NO_PHONE_IS_LAPTOP, LAPTOPS_ARE_GADGETS], SYL_OPTIONS)
    assert revised == set(correct) == {"Some gadgets are not phones"}
    assert original == set()
    assert "At least one laptop exists" in SYL_ROW["stem"]


def test_revised_halving_loop_count_and_bounds():
    assert "n ≥ 2" in CX_ROW["stem"] and "tightest" in CX_ROW["stem"]
    assert [opt["text"] for opt in CX_ROW["options"] if opt["correct"]] == ["O(log n)"]
    for n in range(1, 5000):
        x, iterations = n, 0
        while x > 0:
            x //= 2
            iterations += 1
        assert iterations == n.bit_length() == (n.bit_length() - 1) + 1
        assert iterations <= n <= n * n
    assert [n.bit_length() for n in (2, 3, 8, 1024)] == [2, 2, 4, 11]
    why = {opt["text"]: opt["why"] for opt in CX_ROW["options"]}
    assert "valid upper bound" in why["O(n)"] and "not the tightest" in why["O(n)"]
    assert "valid upper bound" in why["O(n²)"]
    assert "Not a valid bound" in why["O(1) for every n > 1"]


def test_revision_metadata_is_scoped_to_two_rows():
    revised = {row["key"]: row for row in load_batch(BATCH)["questions"] if row.get("revises")}
    assert set(revised) == {SYL, CX}
    assert all(row["version"] == 2 and row["revises"]["version"] == 1 for row in revised.values())
    seed_texts = {row[4] for row in APTITUDE_MCQS}
    assert SYL_PRIOR in seed_texts
    assert REVISED_SEED_STEMS == {
        row["revises"]["stem"]: key for key, row in revised.items() if row["adoption"] == "required"
    }
    assert superseded_by_revision(SYL_PRIOR, {SYL}) is True
    assert superseded_by_revision(SYL_PRIOR, set()) is False


def test_revises_is_refused_outside_the_sprint_batch(tmp_path):
    target = tmp_path / SATURDAY.name
    shutil.copytree(SATURDAY, target)
    data = json.loads((target / "questions.json").read_text(encoding="utf-8"))
    first = data["questions"][0]
    first["revises"] = {"stem": first["stem"] + " (old)", "version": int(first.get("version") or 1)}
    first["version"] = int(first.get("version") or 1) + 1
    _write_questions(target, data)
    assert any("outside the sprint batch" in item for item in load_batch(target)["rejected"])


def _write_questions(target: Path, data: dict) -> None:
    (target / "questions.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    for item in manifest["items"]:
        item["sha256"] = hashlib.sha256((target / item["path"]).read_bytes()).hexdigest()
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _previous_version(tmp_path: Path) -> Path:
    """The version-1 identity of the two rows: original stems, version 1, no revision record."""
    target = tmp_path / "previous"
    shutil.copytree(BATCH, target)
    data = json.loads((target / "questions.json").read_text(encoding="utf-8"))
    for row in data["questions"]:
        prior = row.pop("revises", None)
        if prior:
            row["stem"], row["version"] = prior["stem"], prior["version"]
    _write_questions(target, data)
    return target


async def _reset_sprint(db) -> None:
    """Return the shared test database to the state before any Sprint batch was applied."""
    rows = {row["key"]: row for row in load_batch(BATCH)["questions"]}
    await db.execute(delete(ContentBatchItem).where(ContentBatchItem.batch_id == SPRINT_BATCH_ID))
    keyed = (
        (await db.execute(select(Question).where(Question.content_key.in_(rows)))).scalars().all()
    )
    for question in keyed:
        row = rows[question.content_key]
        question.content_key = None
        if row["adoption"] == "required":
            question.question_text = (row.get("revises") or {}).get("stem") or row["stem"]
        else:
            question.question_text = f"RETIRED {question.id}"
            question.is_active = False
    await db.commit()


async def _fresh_syllogism() -> dict:
    async with AsyncSessionLocal() as db:
        await _reset_sprint(db)
        await _seed_required(db)
        row = (
            await db.execute(
                select(Question)
                .options(selectinload(Question.options))
                .where(Question.question_text == SYL_PRIOR)
            )
        ).scalar_one()
        options = sorted(row.options, key=lambda item: item.sort_order)
        return {
            "id": row.id,
            "option_ids": [str(opt.id) for opt in options],
            "correct_id": str(next(opt.id for opt in options if opt.is_correct)),
            "wrong_id": str(next(opt.id for opt in options if not opt.is_correct)),
        }


async def _assert_nothing_applied(syl_id) -> None:
    async with AsyncSessionLocal() as db:
        ledger = await db.scalar(
            select(func.count())
            .select_from(ContentBatchItem)
            .where(ContentBatchItem.batch_id == SPRINT_BATCH_ID)
        )
        keys = [row["key"] for row in load_batch(BATCH)["questions"]]
        keyed = await db.scalar(
            select(func.count()).select_from(Question).where(Question.content_key.in_(keys))
        )
        syl = await db.get(Question, syl_id)
        new_stems = await db.scalar(
            select(func.count())
            .select_from(Question)
            .where(Question.question_text.in_([SYL_ROW["stem"], CX_ROW["stem"]]))
        )
        assert ledger == 0
        assert keyed == 0
        assert new_stems == 0
        assert syl.content_key is None
        assert syl.explanation == "SHORT SEED"


@pytest.mark.asyncio
async def test_unexpected_original_stem_refuses_adoption(client):
    seeded = await _fresh_syllogism()
    async with AsyncSessionLocal() as db:
        row = await db.get(Question, seeded["id"])
        row.question_text = SYL_PRIOR + " Choose one."
        await db.commit()
        refused = await apply_batch(db, BATCH, allow_remote=False)
    assert refused["refused"] is True
    assert any(item.startswith(SYL) and "found 0" in item for item in refused["rejected"])
    await _assert_nothing_applied(seeded["id"])
    async with AsyncSessionLocal() as db:
        row = await db.get(Question, seeded["id"])
        assert row.question_text == SYL_PRIOR + " Choose one."
        row.question_text = SYL_PRIOR
        await db.commit()


@pytest.mark.asyncio
async def test_drifted_options_refuse_adoption(client):
    seeded = await _fresh_syllogism()
    async with AsyncSessionLocal() as db:
        option = await db.get(QuestionOption, seeded["wrong_id"])
        original = option.option_text
        option.option_text = "Some phones are gadgets"
        await db.commit()
        refused = await apply_batch(db, BATCH, allow_remote=False)
    assert refused["refused"] is True
    assert any(item.startswith(SYL) and "option text" in item for item in refused["rejected"])
    await _assert_nothing_applied(seeded["id"])
    async with AsyncSessionLocal() as db:
        option = await db.get(QuestionOption, seeded["wrong_id"])
        option.option_text = original
        correct = await db.get(QuestionOption, seeded["correct_id"])
        correct.is_correct = False
        await db.commit()
        flipped = await apply_batch(db, BATCH, allow_remote=False)
        assert flipped["refused"] is True
        correct = await db.get(QuestionOption, seeded["correct_id"])
        correct.is_correct = True
        await db.commit()
    await _assert_nothing_applied(seeded["id"])


@pytest.mark.asyncio
@pytest.mark.parametrize("stem", [SYL_PRIOR, SYL_ROW["stem"]])
async def test_duplicate_original_or_revised_stem_refuses_adoption(client, stem):
    seeded = await _fresh_syllogism()
    async with AsyncSessionLocal() as db:
        original = await db.get(Question, seeded["id"])
        extra = Question(
            question_type=original.question_type,
            question_text=stem,
            explanation="SECOND COPY",
            difficulty=original.difficulty,
            domain_id=original.domain_id,
            category_id=original.category_id,
            topic_id=original.topic_id,
            marks=3,
            negative_marks=1,
            is_active=True,
        )
        db.add(extra)
        await db.commit()
        extra_id = extra.id
        refused = await apply_batch(db, BATCH, allow_remote=False)
    assert refused["refused"] is True
    assert any(item.startswith(SYL) for item in refused["rejected"])
    async with AsyncSessionLocal() as db:
        kept = await db.get(Question, extra_id)
        assert kept.content_key is None and kept.explanation == "SECOND COPY"
        await db.delete(kept)
        await db.commit()
    await _assert_nothing_applied(seeded["id"])


@pytest.mark.asyncio
async def test_failed_apply_commits_nothing(client, monkeypatch):
    seeded = await _fresh_syllogism()
    record = studio_batch._identity_record

    def fail_after_revision(key, how, question, **kwargs):
        if key == CX:
            raise RuntimeError("apply interrupted")
        return record(key, how, question, **kwargs)

    monkeypatch.setattr(studio_batch, "_identity_record", fail_after_revision)
    async with AsyncSessionLocal() as db:
        with pytest.raises(RuntimeError, match="apply interrupted"):
            await apply_batch(db, BATCH, allow_remote=False)
    await _assert_nothing_applied(seeded["id"])
    async with AsyncSessionLocal() as db:
        syl = await db.get(Question, seeded["id"])
        assert syl.question_text == SYL_PRIOR


@pytest.mark.asyncio
async def test_upgrade_from_version_one_keeps_ids_and_old_batch_cannot_downgrade(client, tmp_path):
    seeded = await _fresh_syllogism()
    previous = _previous_version(tmp_path)
    async with AsyncSessionLocal() as db:
        first = await apply_batch(db, previous, allow_remote=False)
    assert first["refused"] is False, first
    v1 = {row["key"]: row for row in first["identity"]}
    assert v1[SYL]["row"] == "adopted" and v1[SYL]["question_id"] == str(seeded["id"])
    assert v1[CX]["row"] == "created"

    async with AsyncSessionLocal() as db:
        upgraded = await apply_batch(db, BATCH, allow_remote=False)
    assert upgraded["refused"] is False, upgraded
    assert upgraded["counts"]["question"] == {
        "create": 0,
        "update": 2,
        "unchanged": 68,
        "rejected": 0,
    }
    v2 = {row["key"]: row for row in upgraded["identity"]}
    for key in (SYL, CX):
        assert v2[key]["row"] == "revised"
        assert v2[key]["stem_changed"] is True
        assert v2[key]["question_id"] == v1[key]["question_id"]
        assert v2[key]["option_ids"] == v1[key]["option_ids"]
        assert v2[key]["option_ids_changed"] is False and v2[key]["option_text_changed"] is False
    assert [row["key"] for row in upgraded["identity"] if row["stem_changed"]] == [SYL, CX]

    async with AsyncSessionLocal() as db:
        replay = await apply_batch(db, previous, allow_remote=False)
    assert replay["refused"] is True
    assert f"{SYL} changed without a version bump" in replay["rejected"]
    assert f"{CX} changed without a version bump" in replay["rejected"]
    async with AsyncSessionLocal() as db:
        for key, row in ((SYL, SYL_ROW), (CX, CX_ROW)):
            saved = (
                await db.execute(select(Question).where(Question.content_key == key))
            ).scalar_one()
            assert saved.question_text == row["stem"]
            assert saved.explanation == row["explanation"]
        ledger = (
            (
                await db.execute(
                    select(ContentBatchItem).where(ContentBatchItem.item_key.in_([SYL, CX]))
                )
            )
            .scalars()
            .all()
        )
        assert {item.version for item in ledger} == {2}

    async with AsyncSessionLocal() as db:
        drifted = (
            await db.execute(select(Question).where(Question.content_key == SYL))
        ).scalar_one()
        drifted.question_text = SYL_PRIOR
        await db.commit()
        refused = await apply_batch(db, BATCH, allow_remote=False)
        assert refused["refused"] is True
        assert any(item.startswith(SYL) for item in refused["rejected"])
        drifted.question_text = SYL_ROW["stem"]
        drifted.content_key = None
        await db.commit()
        missing = await apply_batch(db, BATCH, allow_remote=False)
        assert missing["refused"] is True
        assert f"{SYL} recorded as applied but its keyed row is missing" in missing["rejected"]
        drifted.content_key = SYL
        await db.commit()


@pytest.mark.asyncio
async def test_revision_preserves_ids_history_snapshots_and_scoring(client, student_auth):
    headers, email = student_auth
    seeded = await _fresh_syllogism()
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one()
        bookmark = Bookmark(user_id=user.id, question_id=seeded["id"])
        db.add(bookmark)
        await db.commit()
        bookmark_id = bookmark.id
        saturday_before = {
            (item.item_key, item.version, item.content_hash)
            for item in (
                await db.execute(
                    select(ContentBatchItem).where(ContentBatchItem.batch_id != SPRINT_BATCH_ID)
                )
            ).scalars()
        }

    answered = await client.post(
        "/api/v1/practice/sessions/retry",
        headers=headers,
        json={"question_ids": [str(seeded["id"])]},
    )
    answered_id = answered.json()["id"]
    first = await client.post(
        f"/api/v1/practice/sessions/{answered_id}/questions/1/answer",
        headers=headers,
        json={"selected_option_ids": [seeded["correct_id"]], "time_spent_seconds": 3},
    )
    assert first.json()["feedback"]["marks_awarded"] == 2.0
    completed = await client.post(
        f"/api/v1/practice/sessions/{answered_id}/complete", headers=headers
    )
    assert completed.status_code == 200, completed.text
    score_before = completed.json()["session"]["score"]
    pending = await client.post(
        "/api/v1/practice/sessions/retry",
        headers=headers,
        json={"question_ids": [str(seeded["id"])]},
    )
    pending_id = pending.json()["id"]

    async with AsyncSessionLocal() as db:
        result = await apply_batch(db, BATCH, allow_remote=False)
    assert result["refused"] is False, result
    identity = {row["key"]: row for row in result["identity"]}
    assert identity[SYL]["row"] == "revised" and identity[SYL]["stem_changed"] is True
    assert identity[SYL]["question_id"] == str(seeded["id"])
    assert identity[SYL]["option_ids"] == seeded["option_ids"]
    assert identity[CX]["row"] == "created" and identity[CX]["stem_changed"] is False
    assert sum(row["row"] == "adopted" for row in result["identity"]) == 49
    assert all(
        row["option_ids_changed"] is False and row["option_text_changed"] is False
        for row in result["identity"]
    )

    async with AsyncSessionLocal() as db:
        saved = (
            await db.execute(
                select(Question)
                .options(selectinload(Question.options))
                .where(Question.id == seeded["id"])
            )
        ).scalar_one()
        assert saved.question_text == SYL_ROW["stem"]
        assert saved.content_key == SYL
        assert (saved.marks, saved.negative_marks) == (2.0, 0.5)
        options = sorted(saved.options, key=lambda item: item.sort_order)
        assert [str(opt.id) for opt in options] == seeded["option_ids"]
        assert [(opt.option_text, opt.is_correct) for opt in options] == [
            (opt["text"], opt["correct"]) for opt in SYL_ROW["options"]
        ]
        assert (await db.get(Bookmark, bookmark_id)).question_id == seeded["id"]
        assert (
            await db.scalar(
                select(func.count())
                .select_from(Question)
                .where(Question.question_text == SYL_PRIOR)
            )
            == 0
        )
        assert (
            await db.scalar(
                select(func.count())
                .select_from(Question)
                .where(Question.question_text == SYL_ROW["stem"])
            )
            == 1
        )
        saturday_after = {
            (item.item_key, item.version, item.content_hash)
            for item in (
                await db.execute(
                    select(ContentBatchItem).where(ContentBatchItem.batch_id != SPRINT_BATCH_ID)
                )
            ).scalars()
        }
        assert saturday_after == saturday_before

    old_results = await client.get(
        f"/api/v1/practice/sessions/{answered_id}/results", headers=headers
    )
    assert old_results.json()["session"]["score"] == score_before
    assert old_results.json()["questions"][0]["question_text"] == SYL_PRIOR
    assert old_results.json()["questions"][0]["explanation"] == "SHORT SEED"

    old_view = await client.get(
        f"/api/v1/practice/sessions/{pending_id}/questions/1", headers=headers
    )
    assert old_view.json()["question"]["question_text"] == SYL_PRIOR
    assert [opt["id"] for opt in old_view.json()["question"]["options"]] == seeded["option_ids"]
    old_answer = await client.post(
        f"/api/v1/practice/sessions/{pending_id}/questions/1/answer",
        headers=headers,
        json={"selected_option_ids": [seeded["wrong_id"]], "time_spent_seconds": 2},
    )
    assert old_answer.json()["feedback"]["is_correct"] is False
    assert old_answer.json()["feedback"]["marks_awarded"] == -0.5
    assert old_answer.json()["feedback"]["explanation"] == "SHORT SEED"

    fresh = await client.post(
        "/api/v1/practice/sessions/retry",
        headers=headers,
        json={"question_ids": [str(seeded["id"])]},
    )
    fresh_view = await client.get(
        f"/api/v1/practice/sessions/{fresh.json()['id']}/questions/1", headers=headers
    )
    assert fresh_view.json()["question"]["question_text"] == SYL_ROW["stem"]
    fresh_answer = await client.post(
        f"/api/v1/practice/sessions/{fresh.json()['id']}/questions/1/answer",
        headers=headers,
        json={"selected_option_ids": [seeded["correct_id"]], "time_spent_seconds": 2},
    )
    assert fresh_answer.json()["feedback"]["is_correct"] is True
    assert fresh_answer.json()["feedback"]["explanation"] == SYL_ROW["explanation"]

    async with AsyncSessionLocal() as db:
        again = await apply_batch(db, BATCH, allow_remote=False)
    assert again["refused"] is False
    assert again["counts"]["question"]["unchanged"] == 70
    assert {row["key"]: row for row in again["identity"]}[SYL]["question_id"] == str(seeded["id"])

    await seed_phase11_mcqs()
    async with AsyncSessionLocal() as db:
        assert (
            await db.scalar(
                select(func.count())
                .select_from(Question)
                .where(Question.question_text == SYL_PRIOR)
            )
            == 0
        )
        after_seed = await apply_batch(db, BATCH, allow_remote=False)
    assert after_seed["refused"] is False, after_seed
    assert after_seed["counts"]["question"]["unchanged"] == 70
