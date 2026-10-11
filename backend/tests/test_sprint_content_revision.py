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
from app.seed.phase11_technical_mcq import TECHNICAL_MCQS
from tests.test_crt_dsa_sprint import BATCH, SATURDAY, _seed_required

SYL = "sprint1-syl-03"
CX = "sprint1-cx-02"
QUESTIONS = load_batch(BATCH)["questions"]
ROWS = {row["key"]: row for row in QUESTIONS}
REWORDED = [row["key"] for row in QUESTIONS if row.get("revises")]
VERSIONED = [row["key"] for row in QUESTIONS if row["version"] > 1]
EXPLANATION_ONLY = [key for key in VERSIONED if key not in REWORDED]
ADOPTED_REWORDED = [key for key in REWORDED if ROWS[key]["adoption"] == "required"]
REVISED_STEMS = [ROWS[key]["stem"] for key in REWORDED]


def _row(key: str) -> dict:
    return ROWS[key]


SYL_ROW = _row(SYL)
CX_ROW = _row(CX)
SYL_PRIOR = SYL_ROW["revises"]["stem"]
CX_PRIOR = CX_ROW["revises"]["stem"]

# Reviewer classification of every option on a question whose options are asymptotic bounds.
# tight: the tightest bound. loose: a true upper bound that is not tight. invalid: false.
BOUNDS = {
    "sprint1-arr-02": {
        "O(n)": "tight",
        "O(1)": "invalid",
        "O(log n)": "invalid",
        "O(n²) always": "loose",
    },
    "sprint1-arr-03": {
        "Θ(n) comparisons": "tight",
        "Θ(1)": "invalid",
        "Θ(log n)": "invalid",
        "Θ(n²) minimum always": "invalid",
    },
    "sprint1-arr-04": {"O(n)": "tight", "O(1)": "invalid", "O(n²)": "loose", "O(2ⁿ)": "loose"},
    "sprint1-arr-05": {
        "O(n)": "tight",
        "O(n²) required always": "invalid",
        "O(log n)": "invalid",
        "O(n!)": "loose",
    },
    "sprint1-arr-06": {
        "O(n) average time": "tight",
        "O(n²) unavoidable": "invalid",
        "O(1) time always": "invalid",
        "O(n log n) space minimum": "invalid",
    },
    "sprint1-arr-07": {
        "O(1) auxiliary": "tight",
        "O(n) auxiliary required": "invalid",
        "O(n²) auxiliary": "loose",
        "O(log n) auxiliary required": "invalid",
    },
    "sprint1-arr-08": {
        "O(n) time and O(1) extra space": "tight",
        "Only O(n²) time": "invalid",
        "Only with O(n) extra always": "invalid",
        "O(log n) time": "invalid",
    },
    "sprint1-arr-09": {
        "O(1) per query after O(n) preprocess": "tight",
        "O(n) per query always with no benefit": "invalid",
        "O(n²) preprocess mandatory": "invalid",
        "O(log n) preprocess only": "invalid",
    },
    "sprint1-arr-10": {
        "O(n) time, O(1) space": "tight",
        "O(n log n) time required": "invalid",
        "O(n²) time": "loose",
        "O(n) space required": "invalid",
    },
    "sprint1-str-09": {
        "O(1) extra memory": "tight",
        "O(n) extra memory required": "invalid",
        "O(n²) extra memory": "loose",
        "O(2ⁿ) extra memory": "loose",
    },
    "sprint1-str-10": {
        "O(n) extra memory": "tight",
        "O(1) extra memory": "invalid",
        "O(log n) extra memory": "invalid",
        "O(n²) extra memory": "loose",
    },
    "sprint1-cx-01": {
        "O(n²)": "tight",
        "O(n)": "invalid",
        "O(log n)": "invalid",
        "O(1)": "invalid",
    },
    "sprint1-cx-02": {
        "O(log n)": "tight",
        "O(n)": "loose",
        "O(n²)": "loose",
        "O(1) for every n > 1": "invalid",
    },
    "sprint1-cx-03": {"O(n²)": "tight", "O(n)": "invalid", "O(n³)": "loose", "O(1)": "invalid"},
    "sprint1-cx-04": {
        "O(n)": "tight",
        "O(1)": "invalid",
        "O(n + 20) as a different class from O(n)": "invalid",
        "O(20ⁿ)": "loose",
    },
    "sprint1-cx-05": {
        "The formula n(n+1)/2 is O(1); adding the integers one by one is O(n)": "tight",
        "Both methods are O(1)": "invalid",
        "Both methods are O(n²)": "loose",
        "The formula is O(n!)": "loose",
    },
    "sprint1-sea-03": {
        "Θ(n)": "tight",
        "Θ(1)": "invalid",
        "Θ(log n)": "invalid",
        "Θ(n²)": "invalid",
    },
}


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


def test_revision_metadata_matches_the_reviewed_list():
    assert REWORDED == [
        "sprint1-syl-03",
        "sprint1-arr-02",
        "sprint1-arr-04",
        "sprint1-arr-05",
        "sprint1-arr-07",
        "sprint1-arr-10",
        "sprint1-str-09",
        "sprint1-str-10",
        "sprint1-cx-02",
        "sprint1-cx-04",
        "sprint1-cx-05",
    ]
    assert EXPLANATION_ONLY == [
        "sprint1-pct-04",
        "sprint1-ser-03",
        "sprint1-ch-01",
        "sprint1-arr-03",
        "sprint1-str-08",
        "sprint1-sea-02",
    ]
    assert all(ROWS[key]["version"] == 2 for key in VERSIONED)
    assert all(ROWS[key]["revises"]["version"] == 1 for key in REWORDED)
    assert all(row["version"] == 1 for row in QUESTIONS if row["key"] not in VERSIONED)
    seed_texts = {row[4] for row in APTITUDE_MCQS} | {row[4] for row in TECHNICAL_MCQS}
    assert all(ROWS[key]["revises"]["stem"] in seed_texts for key in ADOPTED_REWORDED)
    assert all(ROWS[key]["stem"] not in seed_texts for key in REWORDED)
    assert REVISED_SEED_STEMS == {ROWS[key]["revises"]["stem"]: key for key in ADOPTED_REWORDED}
    assert superseded_by_revision(SYL_PRIOR, {SYL}) is True
    assert superseded_by_revision(SYL_PRIOR, set()) is False


def test_bound_questions_have_one_tightest_answer_and_honest_explanations():
    bound_rows = [
        row
        for row in QUESTIONS
        if any("O(" in opt["text"] or "Θ(" in opt["text"] for opt in row["options"])
    ]
    assert {row["key"] for row in bound_rows} == set(BOUNDS)
    for row in bound_rows:
        labels = BOUNDS[row["key"]]
        assert set(labels) == {opt["text"] for opt in row["options"]}, row["key"]
        assert [opt["text"] for opt in row["options"] if opt["correct"]] == [
            text for text, label in labels.items() if label == "tight"
        ], row["key"]
        if "loose" in labels.values():
            assert "tightest" in row["stem"], row["key"]
        for opt in row["options"]:
            label = labels[opt["text"]]
            if label == "loose":
                assert "upper bound" in opt["why"], row["key"]
                assert any(
                    word in opt["why"] for word in ("not the tightest", "loose", "far from tight")
                )
            elif label == "invalid":
                assert "valid upper bound" not in opt["why"].lower(), (row["key"], opt["text"])


def _kadane(values: list[int]) -> tuple[list[int], list[int]]:
    ending = best = values[0]
    endings, bests = [ending], [best]
    for value in values[1:]:
        ending = max(value, ending + value)
        best = max(best, ending)
        endings.append(ending)
        bests.append(best)
    return endings, bests


def _signed(values: list[int]) -> str:
    return ", ".join(str(value).replace("-", "−") for value in values)


def test_corrected_explanations_match_checked_values():
    kadane = ROWS["sprint1-arr-05"]["explanation"]
    endings, bests = _kadane([1, -2, 3])
    assert (endings, bests) == ([1, -1, 3], [1, 1, 3])
    assert "ending 1, then −1, then 3; best 1, then 1, then 3. The answer is 3." in kadane
    assert "ending 1, then 1, then 3" not in kadane
    endings, bests = _kadane([-2, 1, -3, 4, -1, 2, 1])
    assert f"the ending sums are {_signed(endings)}. The best is {bests[-1]}" in kadane
    assert sum([4, -1, 2, 1]) == bests[-1] == 6

    squares = ROWS["sprint1-ser-03"]["explanation"]
    assert "4²+4" not in squares and 4**2 + 4 == 20
    assert [k * k for k in range(1, 6)] == [1, 4, 9, 16, 25]
    assert "consecutive perfect squares" in squares and "5² = 25" in squares
    assert "gaps 3, 5, 7, 9" in squares

    assert 100 / 640 * 100 == 15.625
    assert "100 is 15.625% of 640" in ROWS["sprint1-pct-04"]["explanation"]
    assert 500 - 300 == 200 == 2 * 100
    assert "100 is only half the gap" in ROWS["sprint1-ch-01"]["explanation"]
    assert len("ab" + "c") == 3 and '"abc" has 3' in ROWS["sprint1-str-08"]["explanation"]

    maximum = ROWS["sprint1-arr-03"]["explanation"]
    assert "candidate ← A[0]" in maximum and "candidate ← A[1]" not in maximum
    assert "exactly n−1 comparisons" in maximum

    values, target, low, high, middles = [2, 4, 6, 8, 10], 6, 0, 4, []
    while low <= high:
        mid = low + (high - low) // 2
        middles.append(mid)
        if values[mid] == target:
            break
        low, high = (mid + 1, high) if values[mid] < target else (low, mid - 1)
    assert middles == [2]
    search = ROWS["sprint1-sea-02"]["explanation"]
    assert "The first middle is not the answer" not in search
    assert "The first middle, index 2, already holds 6" in search

    setup = ROWS["sprint1-cx-04"]["explanation"]
    assert 20 + 5 == 25 and 20 + 50 == 70
    assert "20 setup steps and 5 additions, 25 steps in total" in setup

    sums = ROWS["sprint1-cx-05"]
    assert "Count each arithmetic operation as one step" in sums["stem"]
    assert all(n * (n + 1) // 2 == sum(range(1, n + 1)) for n in range(200))


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
    """The version-1 identity of the revised rows: original stems, version 1, no revision record."""
    target = tmp_path / "previous"
    shutil.copytree(BATCH, target)
    data = json.loads((target / "questions.json").read_text(encoding="utf-8"))
    for row in data["questions"]:
        prior = row.pop("revises", None)
        if prior:
            row["stem"] = prior["stem"]
        row["version"] = 1
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
            .where(Question.question_text.in_(REVISED_STEMS))
        )
        assert ledger == 0
        assert keyed == 0
        assert new_stems == 0
        assert syl.content_key is None
        assert syl.explanation == "SHORT SEED"


@pytest.mark.asyncio
@pytest.mark.parametrize("key", ADOPTED_REWORDED)
async def test_unexpected_original_stem_refuses_adoption(client, key):
    seeded = await _fresh_syllogism()
    prior = ROWS[key]["revises"]["stem"]
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(select(Question).where(Question.question_text == prior))
        ).scalar_one()
        row_id = row.id
        row.question_text = prior + " Choose one."
        await db.commit()
        refused = await apply_batch(db, BATCH, allow_remote=False)
    assert refused["refused"] is True
    assert any(item.startswith(key) and "found 0" in item for item in refused["rejected"])
    await _assert_nothing_applied(seeded["id"])
    async with AsyncSessionLocal() as db:
        row = await db.get(Question, row_id)
        assert row.question_text == prior + " Choose one."
        row.question_text = prior
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
    assert all(v1[key]["row"] == "adopted" for key in ADOPTED_REWORDED)
    assert all(v1[key]["row"] == "created" for key in REWORDED if key not in ADOPTED_REWORDED)

    async with AsyncSessionLocal() as db:
        upgraded = await apply_batch(db, BATCH, allow_remote=False)
    assert upgraded["refused"] is False, upgraded
    assert upgraded["counts"]["question"] == {
        "create": 0,
        "update": len(VERSIONED),
        "unchanged": 70 - len(VERSIONED),
        "rejected": 0,
    }
    v2 = {row["key"]: row for row in upgraded["identity"]}
    for key in VERSIONED:
        assert v2[key]["row"] == ("revised" if key in REWORDED else "updated"), key
        assert v2[key]["stem_changed"] is (key in REWORDED), key
        assert v2[key]["question_id"] == v1[key]["question_id"], key
        assert v2[key]["option_ids"] == v1[key]["option_ids"], key
        assert v2[key]["option_ids_changed"] is False and v2[key]["option_text_changed"] is False
    assert [row["key"] for row in upgraded["identity"] if row["stem_changed"]] == REWORDED

    async with AsyncSessionLocal() as db:
        replay = await apply_batch(db, previous, allow_remote=False)
    assert replay["refused"] is True
    assert sorted(replay["rejected"]) == sorted(
        f"{key} changed without a version bump" for key in VERSIONED
    )
    async with AsyncSessionLocal() as db:
        for key in VERSIONED:
            saved = (
                await db.execute(select(Question).where(Question.content_key == key))
            ).scalar_one()
            assert saved.question_text == ROWS[key]["stem"]
            assert saved.explanation == ROWS[key]["explanation"]
        ledger = (
            (
                await db.execute(
                    select(ContentBatchItem).where(ContentBatchItem.item_key.in_(VERSIONED))
                )
            )
            .scalars()
            .all()
        )
        assert len(ledger) == len(VERSIONED)
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
        adopted_before = {}
        for row in QUESTIONS:
            if row["adoption"] != "required":
                continue
            stem = (row.get("revises") or {}).get("stem") or row["stem"]
            current = (
                await db.execute(
                    select(Question)
                    .options(selectinload(Question.options))
                    .where(Question.question_text == stem)
                )
            ).scalar_one()
            adopted_before[row["key"]] = (
                str(current.id),
                [str(opt.id) for opt in sorted(current.options, key=lambda item: item.sort_order)],
                (current.marks, current.negative_marks),
            )
        assert len(adopted_before) == 50
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
    assert sum(row["row"] == "adopted" for row in result["identity"]) == 50 - len(ADOPTED_REWORDED)
    assert [row["key"] for row in result["identity"] if row["row"] == "revised"] == ADOPTED_REWORDED
    assert all(
        row["option_ids_changed"] is False and row["option_text_changed"] is False
        for row in result["identity"]
    )
    for key, (question_id, option_ids, _marks) in adopted_before.items():
        assert (identity[key]["question_id"], identity[key]["option_ids"]) == (
            question_id,
            option_ids,
        )

    async with AsyncSessionLocal() as db:
        for key, (question_id, option_ids, marks) in adopted_before.items():
            kept = (
                await db.execute(select(Question).where(Question.content_key == key))
            ).scalar_one()
            assert str(kept.id) == question_id
            assert (kept.marks, kept.negative_marks) == marks
            assert kept.question_text == ROWS[key]["stem"]
            assert kept.explanation == ROWS[key]["explanation"]

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
    assert sorted(opt["id"] for opt in old_view.json()["question"]["options"]) == sorted(
        seeded["option_ids"]
    )
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
                .where(Question.question_text.in_(list(REVISED_SEED_STEMS)))
            )
            == 0
        )
        after_seed = await apply_batch(db, BATCH, allow_remote=False)
    assert after_seed["refused"] is False, after_seed
    assert after_seed["counts"]["question"]["unchanged"] == 70
