"""Turn pinned source files into normalized inventory items.

`load_snapshot` is the only function that reads git. Everything else works on the
plain snapshot dictionary, so tests can feed malformed sources directly.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.content.hashing import content_hash
from app.content.inventory.sources import (
    MASTER,
    PINNED_REFS,
    SPRINT_BATCH,
    VISUAL_BATCH,
    CallExpr,
    GitReader,
    SourceRef,
    Symbol,
    checkout_bytes,
    function_values,
    module_values,
    sha256_hex,
)

SEED = "backend/app/seed"
BATCHES = "backend/content/batches"
GENERATED = "backend/content/generated"

ITEM_FIELDS = (
    "item_id",
    "kind",
    "source_label",
    "source_branch",
    "source_sha",
    "source_file",
    "collection",
    "content_key",
    "domain",
    "category",
    "topic",
    "skill",
    "curriculum_area",
    "difficulty",
    "question_type",
    "version",
    "version_declared",
    "stem_fingerprint",
    "option_count",
    "correct_count",
    "has_explanation",
    "related_lesson",
    "references",
    "test_case_count",
    "publication_declaration",
    "adoption_mode",
    "adopts",
    "revises_fingerprint",
    "flags",
)

CRT_AREAS: dict[str, tuple[str, ...]] = {
    "Quantitative Aptitude": (
        "percentages",
        "profit-and-loss",
        "time-and-work",
        "time-speed-distance",
        "ratio-and-proportion",
        "simple-interest",
        "compound-interest",
        "probability",
        "permutations-and-combinations",
    ),
    "Logical Reasoning": (
        "series",
        "coding-decoding",
        "blood-relations",
        "directions",
        "syllogisms",
        "seating-arrangement",
        "puzzles",
    ),
    "Verbal Ability": (
        "grammar",
        "vocabulary",
        "sentence-correction",
        "reading-comprehension",
        "para-jumbles",
    ),
    "Data Interpretation": ("tables", "charts", "graphs", "caselets"),
}
DSA_FOUNDATIONS = (
    "basics",
    "arrays",
    "strings",
    "hash-maps",
    "sorting",
    "two-pointers",
    "searching",
)
SKILL_AREAS = {
    "quantitative": "Quantitative Aptitude",
    "logical-reasoning": "Logical Reasoning",
    "reasoning": "Logical Reasoning",
    "verbal": "Verbal Ability",
    "data-interpretation": "Data Interpretation",
}
UNIT_AREAS = {
    "quantitative": "Quantitative Aptitude",
    "logical": "Logical Reasoning",
    "verbal": "Verbal Ability",
    "data-interpretation": "Data Interpretation",
}
CRT_TOPIC_AREA = {topic: area for area, topics in CRT_AREAS.items() for topic in topics}

PHASE11_DECLARATION = (
    "not inserted by python -m app.seed; python -m app.seed.phase11_activate inserts it "
    "active with is_sample=True"
)
APP_SEED_DECLARATION = "inserted active by python -m app.seed with is_sample=True"
RUNNER_DECLARATION = (
    "inserted active by python -m app.seed with is_sample=True, only into an existing topic "
    "that has no questions yet"
)
SEED_MCQ_SOURCES: tuple[tuple[str, str, str, str | None, str], ...] = (
    ("phase11-aptitude", "phase11_aptitude_mcq.py", "APTITUDE_MCQS", None, PHASE11_DECLARATION),
    ("phase11-technical", "phase11_technical_mcq.py", "TECHNICAL_MCQS", None, PHASE11_DECLARATION),
    ("build6-ai", "build6_mcq.py", "AI_MCQS", "ai", APP_SEED_DECLARATION),
    ("build7-cloud", "build7_mcq.py", "CLOUD_MCQS", "cloud", APP_SEED_DECLARATION),
    ("build7-devops", "build7_mcq.py", "DEVOPS_MCQS", "devops", APP_SEED_DECLARATION),
    ("build7-cybersecurity", "build7_mcq.py", "CYBER_MCQS", "cybersecurity", APP_SEED_DECLARATION),
)
COUNT_ONLY_SOURCES: tuple[tuple[str, str, str], ...] = (
    ("prompt_challenge", "build6_challenges.py", "PROMPT_CHALLENGES"),
    ("scenario", "build7_scenarios.py", "SCENARIOS"),
    ("sql_problem", "sql_problems_bank.py", "SQL_PROBLEM_BANK"),
    ("project_spec", "build51_catalog.py", "PROJECT_SPECS"),
)
RELATED_LESSON = re.compile(r"Related lesson\s*\n\s*([a-z0-9][a-z0-9-]*)")


def curriculum_area(domain: str | None, category: str | None, topic: str | None) -> str | None:
    if domain == "placement" and category == "aptitude" and topic in CRT_TOPIC_AREA:
        return CRT_TOPIC_AREA[topic]
    if domain == "technical" and category == "dsa" and topic:
        return "DSA Foundations" if topic in DSA_FOUNDATIONS else "DSA Intermediate and Advanced"
    return None


def fingerprint(text: Any) -> str | None:
    return content_hash(text) if isinstance(text, str) and text.strip() else None


def _blank(ref: SourceRef, kind: str, source_file: str, collection: str) -> dict[str, Any]:
    item: dict[str, Any] = {field: None for field in ITEM_FIELDS}
    item.update(
        kind=kind,
        source_label=ref.label,
        source_branch=ref.branch,
        source_sha=ref.sha,
        source_file=source_file,
        collection=collection,
        references=[],
        flags=[],
        version_declared=False,
    )
    return item


def _item_id(item: dict[str, Any], index: int) -> str:
    locator = item["content_key"] or f"#{index + 1:03d}"
    return f"{item['source_label']}/{item['collection']}/{locator}"


def _seed_mcq(
    ref: SourceRef,
    path: str,
    collection: str,
    index: int,
    fields: tuple[Any, ...],
    declaration: str,
    adoption_mode: str = "seed-definition",
) -> dict[str, Any]:
    domain, category, topic, difficulty, text, explanation, *options = fields
    item = _blank(ref, "mcq", path, collection)
    texts = [o for o in options if isinstance(o, str) and o.strip()]
    item.update(
        domain=domain,
        category=category,
        topic=topic,
        curriculum_area=curriculum_area(domain, category, topic),
        difficulty=difficulty,
        question_type="single",
        version=1,
        stem_fingerprint=fingerprint(text),
        option_count=len(texts),
        correct_count=1 if options and isinstance(options[0], str) and options[0].strip() else 0,
        has_explanation=bool(isinstance(explanation, str) and explanation.strip()),
        publication_declaration=declaration,
        adoption_mode=adoption_mode,
    )
    if len({t.strip().lower() for t in texts}) != len(texts):
        item["flags"].append("duplicate-option-text")
    item["item_id"] = _item_id(item, index)
    return item


def seed_mcq_items(ref: SourceRef, seed: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for source_id, filename, name, domain, declaration in SEED_MCQ_SOURCES:
        path = f"{SEED}/{filename}"
        rows = seed[filename].get(name, [])
        for index, row in enumerate(rows):
            fields = row.args if isinstance(row, CallExpr) else tuple(row)
            if domain is not None:
                fields = (domain, *fields)
            malformed = len(fields) != 10
            fields = (*fields[:10], *([None] * (10 - len(fields))))
            item = _seed_mcq(ref, path, source_id, index, fields, declaration)
            if malformed:
                item["flags"].append("malformed-row")
            items.append(item)
    return items


def runner_items(ref: SourceRef, runner_source: str) -> list[dict[str, Any]]:
    path = f"{SEED}/runner.py"
    module = module_values(runner_source)
    items: list[dict[str, Any]] = []
    for index, row in enumerate(module.get("SAMPLE_QUESTIONS", [])):
        options = row.get("options", [])
        item = _blank(ref, "mcq", path, "runner-samples")
        item.update(
            domain=row.get("domain"),
            category=row.get("category"),
            topic=row.get("topic"),
            curriculum_area=curriculum_area(
                row.get("domain"), row.get("category"), row.get("topic")
            ),
            difficulty=row.get("difficulty"),
            question_type="single",
            version=1,
            stem_fingerprint=fingerprint(row.get("text")),
            option_count=len(options),
            correct_count=sum(1 for option in options if option[1] is True),
            has_explanation=bool(row.get("explanation")),
            publication_declaration=RUNNER_DECLARATION,
            adoption_mode="seed-definition",
        )
        item["item_id"] = _item_id(item, index)
        items.append(item)

    local = function_values(runner_source, "_expand_questions")
    for index, row in enumerate(local.get("templates", [])):
        domain, category, topic, text = row
        item = _blank(ref, "mcq", path, "runner-templates")
        boolean = index % 2 == 1
        item.update(
            domain=domain,
            category=category,
            topic=topic,
            curriculum_area=curriculum_area(domain, category, topic),
            difficulty="easy" if index % 2 == 0 else "medium",
            question_type="single",
            version=1,
            stem_fingerprint=fingerprint(text),
            option_count=2 if boolean else 4,
            correct_count=1,
            has_explanation=True,
            publication_declaration=RUNNER_DECLARATION,
            adoption_mode="seed-definition",
            flags=["placeholder-options", "placeholder-explanation"],
        )
        item["item_id"] = _item_id(item, index)
        items.append(item)
    return items


def _resolve(value: Any, module: dict[str, Any]) -> Any:
    if isinstance(value, Symbol) and value.text in module:
        return module[value.text]
    return value


def coding_items(ref: SourceRef, bank_source: str) -> list[dict[str, Any]]:
    path = f"{SEED}/problems_bank.py"
    module = module_values(bank_source)
    items: list[dict[str, Any]] = []
    for index, row in enumerate(module.get("PROBLEM_BANK", [])):
        starter = _resolve(row.get("starter_code"), module)
        if isinstance(starter, CallExpr) and starter.func == "_starters":
            languages = 4
        elif isinstance(starter, dict):
            languages = len(starter)
        else:
            languages = 0
        tests = row.get("test_cases") or []
        item = _blank(ref, "coding_problem", path, "PROBLEM_BANK")
        item.update(
            content_key=row.get("slug"),
            domain="technical",
            category="dsa",
            topic=row.get("topic"),
            curriculum_area=curriculum_area("technical", "dsa", row.get("topic")),
            difficulty=row.get("difficulty"),
            question_type="coding",
            version=1,
            stem_fingerprint=fingerprint(row.get("description")),
            option_count=languages,
            has_explanation=False,
            test_case_count=len(tests) if isinstance(tests, list) else 0,
            publication_declaration="inserted active by python -m app.seed (coding_data)",
            adoption_mode="seed-definition",
        )
        if not tests:
            item["flags"].append("no-test-cases")
        if not languages:
            item["flags"].append("no-starter-code")
        item["item_id"] = _item_id(item, index)
        items.append(item)
    return items


def interview_items(ref: SourceRef, build8_source: str) -> list[dict[str, Any]]:
    path = f"{SEED}/build8_seed.py"
    module = module_values(build8_source)
    items: list[dict[str, Any]] = []
    for index, row in enumerate(module.get("QUESTIONS", [])):
        item = _blank(ref, "interview_question", path, "build8-QUESTIONS")
        item.update(
            content_key=row.get("slug"),
            difficulty=row.get("difficulty"),
            question_type=row.get("question_type"),
            stem_fingerprint=fingerprint(row.get("question_text")),
            has_explanation=bool(row.get("explanation") or row.get("expected_answer")),
            publication_declaration="inserted by python -m app.seed (build8)",
            adoption_mode="seed-definition",
        )
        item["item_id"] = _item_id(item, index)
        items.append(item)
    for index, row in enumerate(module.get("PACKS", [])):
        item = _blank(ref, "interview_pack", path, "build8-PACKS")
        item.update(
            content_key=row.get("slug"),
            references=[f"interview_question:{slug}" for slug in row.get("question_slugs", [])],
            publication_declaration="inserted by python -m app.seed (build8)",
            adoption_mode="seed-definition",
        )
        item["item_id"] = _item_id(item, index)
        items.append(item)
    return items


def generated_interview_items(ref: SourceRef, files: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(files):
        payload = files[path]
        collection = "generated-" + Path(path).stem
        for index, row in enumerate(payload.get("questions", [])):
            item = _blank(ref, "interview_question", path, collection)
            item.update(
                difficulty=row.get("difficulty"),
                question_type=row.get("question_type"),
                skill=payload.get("target_skill"),
                stem_fingerprint=fingerprint(row.get("question_text")),
                has_explanation=bool(row.get("explanation") or row.get("expected_answer")),
                publication_declaration="staged generated file; no importer reference verified",
                adoption_mode="generated-draft",
            )
            item["item_id"] = _item_id(item, index)
            items.append(item)
    return items


def path_items(ref: SourceRef, learn_source: str, catalog_source: str) -> list[dict[str, Any]]:
    path = f"{SEED}/learn_data.py"
    module = module_values(learn_source)
    items: list[dict[str, Any]] = []
    groups: list[tuple[str, list[Any], int | None]] = [
        ("BEGINNER_DSA_PATHS", module.get("BEGINNER_DSA_PATHS", []), None),
        ("DATA_STRUCTURE_PATHS", module.get("DATA_STRUCTURE_PATHS", []), 3),
        ("ALGORITHM_PATHS", module.get("ALGORITHM_PATHS", []), 3),
    ]
    for collection, rows, availability_index in groups:
        for index, row in enumerate(rows):
            slug, _title, topic = row[0], row[1], row[2]
            if availability_index is None:
                declared = "available"
            else:
                availability = row[availability_index]
                declared = (
                    availability.text.rsplit(".", 1)[-1].lower()
                    if isinstance(availability, Symbol)
                    else str(availability)
                )
            item = _blank(ref, "learning_path", path, collection)
            item.update(
                content_key=slug,
                domain="technical",
                category="dsa",
                topic=topic,
                curriculum_area=curriculum_area("technical", "dsa", topic) if topic else None,
                references=[f"topic:{topic}"] if topic else [],
                publication_declaration=f"declared {declared}",
                adoption_mode="seed-definition",
            )
            item["item_id"] = _item_id(item, index)
            items.append(item)
    catalog = module_values(catalog_source)
    for collection in ("NEW_DS_PATHS", "NEW_ALGO_PATHS"):
        for index, row in enumerate(catalog.get(collection, [])):
            item = _blank(ref, "learning_path", f"{SEED}/build51_catalog.py", collection)
            item.update(
                content_key=row[0],
                domain="technical",
                category="dsa",
                publication_declaration="declared available by build51 seed",
                adoption_mode="seed-definition",
            )
            item["item_id"] = _item_id(item, index)
            items.append(item)
    return items


def course_items(ref: SourceRef, learn_source: str) -> list[dict[str, Any]]:
    path = f"{SEED}/learn_data.py"
    items: list[dict[str, Any]] = []
    for module_row in module_values(learn_source).get("PYTHON_COURSE_MODULES", []):
        for index, lesson in enumerate(module_row.get("lessons", [])):
            item = _blank(ref, "course_lesson", path, f"python-course/{module_row.get('slug')}")
            item.update(
                content_key=lesson.get("slug"),
                question_type=lesson.get("lesson_type"),
                has_explanation=bool(lesson.get("statement")),
                publication_declaration="inserted by python -m app.seed (learn_data)",
                adoption_mode="seed-definition",
            )
            item["item_id"] = _item_id(item, index)
            items.append(item)
    return items


def _related_lesson(explanation: Any) -> str | None:
    if not isinstance(explanation, str):
        return None
    match = RELATED_LESSON.search(explanation)
    return match.group(1) if match else None


def _batch_mcq(
    ref: SourceRef, batch_id: str, row: dict[str, Any], index: int, declaration: str
) -> dict[str, Any]:
    path = f"{BATCHES}/{batch_id}/questions.json"
    options = row.get("options") or []
    item = _blank(ref, "mcq", path, batch_id)
    domain, category, topic = (
        row.get("domain_slug"),
        row.get("category_slug"),
        row.get("topic_slug"),
    )
    area = curriculum_area(domain, category, topic) or SKILL_AREAS.get(row.get("skill") or "")
    adoption = row.get("adoption")
    version = int(row.get("version") or 1)
    if adoption == "required":
        mode = "batch-adopt"
    elif adoption == "create":
        mode = "batch-create"
    else:
        mode = "batch-new"
    item.update(
        content_key=row.get("key"),
        domain=domain,
        category=category,
        topic=topic,
        skill=row.get("skill"),
        curriculum_area=area,
        difficulty=row.get("difficulty"),
        question_type=row.get("mode"),
        version=version,
        version_declared="version" in row,
        stem_fingerprint=fingerprint(row.get("stem")),
        option_count=len(options),
        correct_count=sum(1 for option in options if option.get("correct") is True),
        has_explanation=bool(row.get("explanation")),
        related_lesson=_related_lesson(row.get("explanation")),
        publication_declaration=declaration,
        adoption_mode=mode,
    )
    revises = row.get("revises")
    if isinstance(revises, dict):
        item["references"].append(f"revises:v{revises.get('version')}")
        item["revises_fingerprint"] = fingerprint(revises.get("stem"))
    if row.get("mode") == "single" and item["correct_count"] != 1:
        item["flags"].append("single-answer-correct-count")
    if row.get("mode") == "multi" and item["correct_count"] < 2:
        item["flags"].append("multi-answer-correct-count")
    texts = [str(option.get("text", "")).strip().lower() for option in options]
    if len(set(texts)) != len(texts):
        item["flags"].append("duplicate-option-text")
    item["item_id"] = _item_id(item, index)
    return item


def batch_items(ref: SourceRef, batch_id: str, batch: dict[str, Any]) -> list[dict[str, Any]]:
    manifest = batch.get("manifest") or {}
    declaration = manifest.get("authorization") or "no authorization field in manifest"
    if manifest.get("publish_mode"):
        declaration = f"{declaration}; publish_mode={manifest['publish_mode']}"
    items = [
        _batch_mcq(ref, batch_id, row, index, f"batch question; {declaration}")
        for index, row in enumerate(batch.get("questions", []))
    ]
    for index, row in enumerate(batch.get("materials", [])):
        item = _blank(ref, "learning_material", f"{BATCHES}/{batch_id}/materials.json", batch_id)
        item.update(
            content_key=row.get("key"),
            skill=",".join(row.get("skills") or []),
            question_type=row.get("kind"),
            version=int(row.get("version") or 1),
            version_declared="version" in row,
            references=[f"file:{row['body_file']}"] if row.get("body_file") else [],
            publication_declaration=f"importer publishes on apply; {declaration}",
            adoption_mode="batch-new",
        )
        item["item_id"] = _item_id(item, index)
        items.append(item)
    for index, row in enumerate(batch.get("packs", [])):
        item = _blank(ref, "practice_pack", f"{BATCHES}/{batch_id}/packs.json", batch_id)
        item.update(
            content_key=row.get("key"),
            question_type=row.get("kind"),
            version=int(row.get("version") or 1),
            version_declared="version" in row,
            references=[f"question:{key}" for key in row.get("question_keys", [])],
            publication_declaration=f"importer publishes on apply; {declaration}",
            adoption_mode="batch-new",
        )
        item["item_id"] = _item_id(item, index)
        items.append(item)
    for index, row in enumerate(batch.get("entries", [])):
        item = _blank(ref, "syllabus_entry", f"{BATCHES}/{batch_id}/syllabus.json", batch_id)
        refs = [f"question:{key}" for key in row.get("question_keys", [])]
        if row.get("material_key"):
            refs.insert(0, f"material:{row['material_key']}")
        item.update(
            content_key=row.get("key"),
            skill=row.get("unit"),
            category=row.get("track"),
            curriculum_area=UNIT_AREAS.get(row.get("unit") or "")
            if row.get("track") == "crt"
            else None,
            version=int(row.get("version") or 1),
            version_declared="version" in row,
            references=refs,
            publication_declaration=f"status={row.get('status')}",
            adoption_mode="batch-new",
        )
        item["item_id"] = _item_id(item, index)
        items.append(item)
    return items


def load_batch(reader: GitReader, batch_dir: str) -> dict[str, Any]:
    files = reader.list_files(batch_dir)
    eols = reader.checkout_eols(files)
    batch: dict[str, Any] = {
        "files": {},
        "manifest": None,
        "checkout_eol": eols.get(f"{batch_dir}/manifest.json", "unspecified"),
    }
    for path in files:
        name = path[len(batch_dir) + 1 :]
        data = reader.read_bytes(path)
        batch["files"][name] = sha256_hex(checkout_bytes(data, eols.get(path, "unspecified")))
        if name == "manifest.json":
            batch["manifest"] = json.loads(data)
        elif name in ("questions.json", "materials.json", "packs.json", "syllabus.json"):
            payload = json.loads(data)
            collection = {"syllabus.json": "entries"}.get(name, name.removesuffix(".json"))
            batch[collection] = payload.get(collection, [])
    return batch


def load_snapshot(repo: Path, refs: tuple[SourceRef, ...] = PINNED_REFS) -> dict[str, Any]:
    """Read every pinned input. Raises SourceUnavailable instead of substituting."""
    readers = {ref.label: GitReader(repo, ref) for ref in refs}
    master = readers[MASTER.label]
    seed_files = sorted(
        {filename for _, filename, _, _, _ in SEED_MCQ_SOURCES}
        | {filename for _, filename, _ in COUNT_ONLY_SOURCES}
    )
    snapshot: dict[str, Any] = {
        "refs": {ref.label: ref for ref in refs},
        "seed": {name: module_values(master.read_text(f"{SEED}/{name}")) for name in seed_files},
        "sources": {
            name: master.read_text(f"{SEED}/{name}")
            for name in (
                "runner.py",
                "problems_bank.py",
                "build8_seed.py",
                "learn_data.py",
                "build51_catalog.py",
                "taxonomy_data.py",
                "coding_data.py",
            )
        },
        "generated": {
            path: master.read_json(path)
            for path in master.list_files(GENERATED)
            if Path(path).name.startswith("interview_") and path.endswith(".json")
        },
        "batches": {},
    }
    batch_dirs = sorted({path.split("/")[3] for path in master.list_files(BATCHES)})
    snapshot["batches"][MASTER.label] = {
        batch_id: load_batch(master, f"{BATCHES}/{batch_id}") for batch_id in batch_dirs
    }
    for label, batch_dir in (("pr-17", VISUAL_BATCH), ("pr-18", SPRINT_BATCH)):
        if label in readers:
            snapshot["batches"][label] = {
                Path(batch_dir).name: load_batch(readers[label], batch_dir)
            }
    if "quality-gate" in readers:
        snapshot["batches"]["quality-gate"] = {
            Path(SPRINT_BATCH).name: load_batch(readers["quality-gate"], SPRINT_BATCH)
        }
    return snapshot


def taxonomy_topics(snapshot: dict[str, Any]) -> set[tuple[str, str, str]]:
    topics: set[tuple[str, str, str]] = set()
    for domain in module_values(snapshot["sources"]["taxonomy_data.py"]).get("TAXONOMY", []):
        for category in domain.get("categories", []):
            for topic in category.get("topics", []):
                topics.add((domain["slug"], category["slug"], topic["slug"]))
    for slug in dsa_topics(snapshot):
        topics.add(("technical", "dsa", slug))
    return topics


def dsa_topics(snapshot: dict[str, Any]) -> list[str]:
    extra = module_values(snapshot["sources"]["coding_data.py"]).get("EXTRA_TOPICS", [])
    return ["basics", "arrays", "strings", *[slug for slug, _name in extra]]


def build_items(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    refs: dict[str, SourceRef] = snapshot["refs"]
    master = refs[MASTER.label]
    sources = snapshot["sources"]
    builders: list[Callable[[], list[dict[str, Any]]]] = [
        lambda: seed_mcq_items(master, snapshot["seed"]),
        lambda: runner_items(master, sources["runner.py"]),
        lambda: coding_items(master, sources["problems_bank.py"]),
        lambda: interview_items(master, sources["build8_seed.py"]),
        lambda: generated_interview_items(master, snapshot["generated"]),
        lambda: path_items(master, sources["learn_data.py"], sources["build51_catalog.py"]),
        lambda: course_items(master, sources["learn_data.py"]),
    ]
    items = [item for build in builders for item in build()]
    for label, batches in snapshot["batches"].items():
        for batch_id, batch in sorted(batches.items()):
            items.extend(batch_items(refs[label], batch_id, batch))
    for item in items:
        for field, value in item.items():
            if isinstance(value, Symbol):
                item[field] = enum_member(value)
    return items


def enum_member(symbol: Symbol) -> str:
    """`Difficulty.EASY` becomes `easy`; other unevaluated names keep their source text."""
    owner, _, member = symbol.text.rpartition(".")
    return member.lower() if owner and member.isupper() else symbol.text


def count_only(snapshot: dict[str, Any]) -> dict[str, int]:
    counts = {
        kind: len(snapshot["seed"][filename].get(name, []))
        for kind, filename, name in COUNT_ONLY_SOURCES
    }
    return dict(sorted(counts.items()))
