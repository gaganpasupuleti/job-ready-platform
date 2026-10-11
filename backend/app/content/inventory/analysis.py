"""Reference checks, duplicate detection, counting views, and topic coverage."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from itertools import combinations
from typing import Any

from app.content.hashing import token_set
from app.content.inventory.extract import (
    CRT_AREAS,
    DSA_FOUNDATIONS,
    dsa_topics,
    taxonomy_topics,
)
from app.content.inventory.sources import CallExpr, function_values, module_values

PENDING = "Production verification pending."
SEED_COLLECTIONS = (
    "phase11-aptitude",
    "phase11-technical",
    "build6-ai",
    "build7-cloud",
    "build7-devops",
    "build7-cybersecurity",
    "runner-samples",
    "runner-templates",
)
PHASE11 = ("phase11-aptitude", "phase11-technical")
VIEWS: dict[str, tuple[str, ...]] = {
    "master": ("master",),
    "master+pr-17": ("master", "pr-17"),
    "master+pr-18": ("master", "pr-18"),
    "master+quality-gate": ("master", "quality-gate"),
}
UNUSABLE_FLAGS = frozenset(
    {"placeholder-options", "topic-not-in-taxonomy", "runner-topic-already-filled"}
)
SEMANTIC_THRESHOLD = 0.6
SEMANTIC_MIN_TOKENS = 6
TOPIC_TARGET = 30
CURRICULUM_TARGET = 1260


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def batch_digests(snapshot: dict[str, Any]) -> dict[tuple[str, str, str, str], str]:
    """Content digest per (label, batch, kind, key); material digests include the body."""
    digests: dict[tuple[str, str, str, str], str] = {}
    kinds = {
        "questions": "mcq",
        "materials": "learning_material",
        "packs": "practice_pack",
        "entries": "syllabus_entry",
    }
    for label, batches in snapshot["batches"].items():
        for batch_id, batch in batches.items():
            for collection, kind in kinds.items():
                for row in batch.get(collection, []):
                    payload = dict(row)
                    if kind == "learning_material" and row.get("body_file"):
                        payload["_body_sha256"] = batch["files"].get(row["body_file"])
                    digests[(label, batch_id, kind, str(row.get("key")))] = digest(payload)
    return digests


def stems(snapshot: dict[str, Any]) -> dict[str, str]:
    """Stem text per item id, for similarity only. Never written to the report."""
    texts: dict[str, str] = {}
    from_seed = {
        "phase11-aptitude": ("phase11_aptitude_mcq.py", "APTITUDE_MCQS", 4),
        "phase11-technical": ("phase11_technical_mcq.py", "TECHNICAL_MCQS", 4),
        "build6-ai": ("build6_mcq.py", "AI_MCQS", 3),
        "build7-cloud": ("build7_mcq.py", "CLOUD_MCQS", 3),
        "build7-devops": ("build7_mcq.py", "DEVOPS_MCQS", 3),
        "build7-cybersecurity": ("build7_mcq.py", "CYBER_MCQS", 3),
    }
    for collection, (filename, name, position) in from_seed.items():
        for index, row in enumerate(snapshot["seed"][filename].get(name, [])):
            fields = row.args if isinstance(row, CallExpr) else row
            texts[f"master/{collection}/#{index + 1:03d}"] = str(fields[position])
    runner = snapshot["sources"]["runner.py"]
    for index, row in enumerate(module_values(runner).get("SAMPLE_QUESTIONS", [])):
        texts[f"master/runner-samples/#{index + 1:03d}"] = str(row.get("text", ""))
    for index, row in enumerate(function_values(runner, "_expand_questions").get("templates", [])):
        texts[f"master/runner-templates/#{index + 1:03d}"] = str(row[3])
    for label, batches in snapshot["batches"].items():
        for batch_id, batch in batches.items():
            for row in batch.get("questions", []):
                texts[f"{label}/{batch_id}/{row.get('key')}"] = str(row.get("stem", ""))
    return texts


def annotate(snapshot: dict[str, Any], items: list[dict[str, Any]]) -> None:
    """Add reference, seedability, and adoption flags in place. Pure over the snapshot."""
    known = taxonomy_topics(snapshot)
    problem_topics = Counter(i["topic"] for i in items if i["kind"] == "coding_problem")
    phase11_by_fp: dict[str, str] = {}
    for item in items:
        if item["collection"] in PHASE11 and item["stem_fingerprint"]:
            phase11_by_fp.setdefault(item["stem_fingerprint"], item["item_id"])

    runner_filled: set[tuple[str, str, str]] = set()
    for item in items:
        if item["source_label"] == "master" and item["collection"] in SEED_COLLECTIONS:
            topic_key = (item["domain"], item["category"], item["topic"])
            if topic_key not in known:
                item["flags"].append("topic-not-in-taxonomy")
            elif item["collection"].startswith("runner-"):
                if topic_key in runner_filled:
                    item["flags"].append("runner-topic-already-filled")
                runner_filled.add(topic_key)

    batch_keys: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for item in items:
        if item["source_file"].startswith("backend/content/batches/"):
            batch_keys[(item["source_label"], item["collection"])][item["kind"]].add(
                item["content_key"]
            )

    for item in items:
        label, batch_id = item["source_label"], item["collection"]
        if item["kind"] == "mcq" and item["adoption_mode"] == "batch-adopt":
            source = phase11_by_fp.get(item["stem_fingerprint"] or "") or phase11_by_fp.get(
                item.get("revises_fingerprint") or ""
            )
            if source:
                item["adopts"] = source
            else:
                item["flags"].append("adoption-source-not-found")
        if item["kind"] == "mcq" and item["related_lesson"]:
            materials = set()
            for (other_label, _batch), keys in batch_keys.items():
                if other_label in ("master", label):
                    materials |= keys["learning_material"]
            if item["related_lesson"] not in materials:
                item["flags"].append("related-lesson-unresolved")
        if item["kind"] in ("practice_pack", "syllabus_entry"):
            keys = batch_keys[(label, batch_id)]
            for ref in item["references"]:
                kind, _, key = ref.partition(":")
                pool = keys["mcq"] if kind == "question" else keys["learning_material"]
                if key not in pool:
                    item["flags"].append(f"unresolved-{kind}-reference:{key}")
            if item["kind"] == "syllabus_entry" and item["publication_declaration"] == (
                "status=published"
            ):
                if not any(ref.startswith("material:") for ref in item["references"]):
                    item["flags"].append("published-without-material")
        if item["kind"] == "learning_material":
            files = snapshot["batches"][label][batch_id]["files"]
            for ref in item["references"]:
                if ref.startswith("file:") and ref[5:] not in files:
                    item["flags"].append("material-body-missing")
        if item["kind"] == "learning_path":
            if not item["topic"]:
                item["flags"].append("path-has-no-topic")
            elif problem_topics[item["topic"]] == 0:
                item["flags"].append("path-topic-has-no-coding-problems")

    interview_slugs = {i["content_key"] for i in items if i["collection"] == "build8-QUESTIONS"}
    for item in items:
        if item["kind"] == "interview_pack":
            for ref in item["references"]:
                if ref.partition(":")[2] not in interview_slugs:
                    item["flags"].append(f"unresolved-interview-reference:{ref.partition(':')[2]}")
    for item in items:
        item["flags"] = sorted(set(item["flags"]))


def manifest_checks(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    findings = []
    for label, batches in sorted(snapshot["batches"].items()):
        for batch_id, batch in sorted(batches.items()):
            manifest = batch.get("manifest") or {}
            for entry in manifest.get("items", []):
                actual = batch["files"].get(entry.get("path"))
                status = (
                    "match"
                    if actual == entry.get("sha256")
                    else ("missing" if actual is None else "mismatch")
                )
                findings.append(
                    {
                        "source_label": label,
                        "batch": batch_id,
                        "path": entry.get("path"),
                        "checkout_eol": batch.get("checkout_eol") or "unspecified",
                        "status": status,
                    }
                )
    return findings


def view_items(items: list[dict[str, Any]], view: str) -> list[dict[str, Any]]:
    labels = VIEWS[view]
    return [item for item in items if item["source_label"] in labels]


def _distinct(items: list[dict[str, Any]]) -> int:
    return len({i["stem_fingerprint"] for i in items if i["stem_fingerprint"]})


def methodology_counts(items: list[dict[str, Any]], view: str) -> dict[str, Any]:
    scoped = view_items(items, view)
    mcqs = [i for i in scoped if i["kind"] == "mcq"]
    batch_mcqs = [i for i in mcqs if i["adoption_mode"] and i["adoption_mode"].startswith("batch")]
    seed_mcqs = [i for i in mcqs if i["collection"] in SEED_COLLECTIONS]
    syllabus_questions: set[str] = set()
    for entry in (i for i in scoped if i["kind"] == "syllabus_entry"):
        for ref in entry["references"]:
            if ref.startswith("question:"):
                syllabus_questions.add(f"{entry['source_label']}/{entry['collection']}/{ref[9:]}")
    published_entries = [
        i
        for i in scoped
        if i["kind"] == "syllabus_entry" and i["publication_declaration"] == "status=published"
    ]
    coding = [i for i in scoped if i["kind"] == "coding_problem"]
    return {
        "1_definitions_in_source": {
            "mcq_rows": len(mcqs),
            "seed_mcq_rows": len(seed_mcqs),
            "batch_mcq_rows": len(batch_mcqs),
        },
        "2_unique_authored_keys": {
            "distinct_mcq_stem_fingerprints": _distinct(mcqs),
            "distinct_batch_question_keys": len({i["content_key"] for i in batch_mcqs}),
        },
        "3_adoption_references": sum(1 for i in mcqs if i["adoption_mode"] == "batch-adopt"),
        "4_new_batch_questions": sum(
            1 for i in mcqs if i["adoption_mode"] in ("batch-create", "batch-new")
        ),
        "5_published_source_declarations": {
            "published_syllabus_entries": len(published_entries),
            "batch_materials_published_on_apply": sum(
                1 for i in scoped if i["kind"] == "learning_material"
            ),
            "batch_packs_published_on_apply": sum(
                1 for i in scoped if i["kind"] == "practice_pack"
            ),
        },
        "6_actual_published_database_rows": PENDING,
        "7_unscored_syllabus_reading_checks": len(syllabus_questions),
        "8_dsa_coding_definitions": len(coding),
        "9_executable_coding_problems": {
            "definitions_with_tests_and_starter_code": sum(
                1 for i in coding if i["test_case_count"] and i["option_count"]
            ),
            "runtime_execution": PENDING,
        },
    }


def sprint_accounting(items: list[dict[str, Any]], label: str) -> dict[str, Any]:
    rows = [
        i
        for i in items
        if i["source_label"] == label
        and i["kind"] == "mcq"
        and i["collection"] == "2026-10-10-crt-dsa-sprint-001"
    ]
    adopted = [i for i in rows if i["adoption_mode"] == "batch-adopt"]
    return {
        "rows": len(rows),
        "adopt": len(adopted),
        "create": sum(1 for i in rows if i["adoption_mode"] == "batch-create"),
        "adopt_linked_to_phase11": sum(1 for i in adopted if i["adopts"]),
        "adopt_stem_unchanged": sum(
            1 for i in adopted if i["adopts"] and not i["revises_fingerprint"]
        ),
        "versions": dict(sorted(Counter(str(i["version"]) for i in rows).items())),
        "with_revises": sum(1 for i in rows if i["revises_fingerprint"]),
    }


def version_comparison(
    items: list[dict[str, Any]],
    digests: dict[tuple[str, str, str, str], str],
    base: str,
    head: str,
) -> dict[str, Any]:
    """Compare batch rows shared by key between two refs (or master and another ref)."""

    def rows(label: str) -> dict[tuple[str, str], dict[str, Any]]:
        return {
            (i["kind"], i["content_key"]): i
            for i in items
            if i["source_label"] == label and i["source_file"].startswith("backend/content/")
        }

    left, right = rows(base), rows(head)
    result: dict[str, list[str]] = defaultdict(list)
    for key in sorted(set(left) & set(right)):
        a, b = left[key], right[key]
        same = digests[(base, a["collection"], *key)] == digests[(head, b["collection"], *key)]
        name = f"{key[0]}:{key[1]}"
        if same:
            result["unchanged"].append(name)
        elif b["version"] > a["version"]:
            result["changed_with_version_bump"].append(name)
        else:
            result["changed_without_version_bump"].append(name)
    result["only_in_head"] = [f"{k}:{v}" for k, v in sorted(set(right) - set(left))]
    return {k: sorted(v) for k, v in sorted(result.items())}


def duplicate_keys(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[tuple[str, str, str, str], list[str]] = defaultdict(list)
    for item in items:
        if item["content_key"]:
            seen[
                (item["source_label"], item["collection"], item["kind"], item["content_key"])
            ].append(item["item_id"])
    return [
        {"scope": f"{k[0]}/{k[1]}", "kind": k[2], "key": k[3], "count": len(v)}
        for k, v in sorted(seen.items())
        if len(v) > 1
    ]


def cross_batch_keys(items: list[dict[str, Any]], view: str) -> list[dict[str, Any]]:
    owners: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in view_items(items, view):
        if item["source_file"].startswith("backend/content/batches/") and item["content_key"]:
            owners[(item["kind"], item["content_key"])].append(item)
    findings = []
    for (kind, key), owned in sorted(owners.items()):
        batches = sorted({(i["source_label"], i["collection"]) for i in owned})
        if len(batches) > 1:
            findings.append(
                {
                    "kind": kind,
                    "key": key,
                    "occurrences": [
                        f"{i['source_label']}/{i['collection']} v{i['version']} "
                        f"({i['publication_declaration'].split(';')[0]})"
                        for i in sorted(owned, key=lambda x: (x["source_label"], x["collection"]))
                    ],
                }
            )
    return findings


def exact_duplicates(items: list[dict[str, Any]], view: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in view_items(items, view):
        if item["kind"] == "mcq" and item["stem_fingerprint"]:
            groups[item["stem_fingerprint"]].append(item)
    findings = []
    for fp, members in sorted(groups.items()):
        if len(members) < 2:
            continue
        ids = sorted(i["item_id"] for i in members)
        targets = {i["adopts"] for i in members if i["adopts"]}
        expected = bool(targets) and all(
            i["item_id"] in targets or i["adopts"] in ids for i in members
        )
        findings.append(
            {
                "stem_fingerprint": fp,
                "items": ids,
                "classification": "expected-adoption-overlap" if expected else "exact-duplicate",
                "topics": sorted({str(i["topic"] or i["skill"]) for i in members}),
            }
        )
    return findings


def semantic_candidates(
    items: list[dict[str, Any]], texts: dict[str, str], view: str
) -> list[dict[str, Any]]:
    mcqs = [
        (i, token_set(texts[i["item_id"]]))
        for i in view_items(items, view)
        if i["kind"] == "mcq" and i["item_id"] in texts
    ]
    mcqs = [(i, tokens) for i, tokens in mcqs if len(tokens) >= SEMANTIC_MIN_TOKENS]
    found = []
    for (a, ta), (b, tb) in combinations(mcqs, 2):
        if a["stem_fingerprint"] == b["stem_fingerprint"]:
            continue
        if a["adopts"] == b["item_id"] or b["adopts"] == a["item_id"]:
            continue
        score = len(ta & tb) / len(ta | tb)
        if score >= SEMANTIC_THRESHOLD:
            first, second = sorted((a["item_id"], b["item_id"]))
            found.append({"items": [first, second], "jaccard": round(score, 3)})
    return sorted(found, key=lambda f: (-f["jaccard"], f["items"]))


def coverage(items: list[dict[str, Any]], snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Per-topic coverage for the six CRT and DSA areas, using the widest candidate view."""
    master = view_items(items, "master")
    candidate = [i for i in items if i["source_label"] == "quality-gate"]
    rows: list[dict[str, Any]] = []
    topic_rows: list[tuple[str, str, str, str]] = []
    for area, topics in CRT_AREAS.items():
        topic_rows += [(area, "placement", "aptitude", t) for t in topics]
    for topic in dsa_topics(snapshot):
        area = "DSA Foundations" if topic in DSA_FOUNDATIONS else "DSA Intermediate and Advanced"
        topic_rows.append((area, "technical", "dsa", topic))
    exact = exact_duplicates(items, "master+quality-gate")
    for area, domain, category, topic in topic_rows:

        def match(i: dict[str, Any]) -> bool:
            return (i["domain"], i["category"], i["topic"]) == (domain, category, topic)

        seed = [i for i in master if i["kind"] == "mcq" and match(i)]
        usable = [i for i in seed if not set(i["flags"]) & UNUSABLE_FLAGS]
        phase11 = [i for i in seed if i["collection"] in PHASE11]
        runner = [i for i in seed if i["collection"].startswith("runner-")]
        sprint = [i for i in candidate if i["kind"] == "mcq" and match(i)]
        lessons = sorted({i["related_lesson"] for i in sprint if i["related_lesson"]})
        paths = sorted(
            i["content_key"] for i in master if i["kind"] == "learning_path" and i["topic"] == topic
        )
        coding = sum(1 for i in master if i["kind"] == "coding_problem" and i["topic"] == topic)
        dupes = sum(
            1
            for d in exact
            if topic in d["topics"] and d["classification"] != ("expected-adoption-overlap")
        )
        distinct = len({i["stem_fingerprint"] for i in usable + sprint if i["stem_fingerprint"]})
        missing = []
        if not usable:
            missing.append("no usable seed questions")
        if not sprint:
            missing.append("no Sprint 1 questions")
        if not lessons and not paths:
            missing.append("no linked learning material")
        if category == "dsa" and not coding:
            missing.append("no coding problems")
        if distinct < TOPIC_TARGET:
            missing.append(f"{TOPIC_TARGET - distinct} below even-split target of {TOPIC_TARGET}")
        rows.append(
            {
                "area": area,
                "topic": topic,
                "basis": "taxonomy topic",
                "source_questions": len(seed),
                "phase11_questions": len(phase11),
                "runner_rows": len(runner),
                "unusable_seed_rows": len(seed) - len(usable),
                "reviewed_questions": sum(1 for i in sprint if i["adoption_mode"] == "batch-adopt"),
                "new_candidates": sum(1 for i in sprint if i["adoption_mode"] == "batch-create"),
                "distinct_usable_stems": distinct,
                "learning_materials": lessons,
                "learning_paths": paths,
                "coding_problems": coding,
                "exact_duplicate_groups": dupes,
                "missing_coverage": missing,
                "publication_status": _publication(phase11, runner, sprint),
                "student_ready": "not determined",
                "evidence_limitations": "source definitions only; " + PENDING,
            }
        )
    return rows


def _publication(
    phase11: list[dict[str, Any]], runner: list[dict[str, Any]], sprint: list[dict[str, Any]]
) -> str:
    parts = []
    if phase11:
        parts.append("Phase 11 rows need phase11_activate")
    if runner:
        parts.append("runner rows seeded as samples")
    if sprint:
        parts.append("Sprint 1 rows unmerged (PR #18, quality gate awaiting human approval)")
    return "; ".join(parts) or "no question source"


def area_level(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Batch questions tagged only by skill or unit, which cannot be placed on a topic."""
    rows = []
    for item in items:
        if item["kind"] != "mcq" or item["topic"] or not item["curriculum_area"]:
            continue
        rows.append(item)
    counts = Counter((i["source_label"], i["collection"], i["curriculum_area"]) for i in rows)
    return [
        {"source_label": k[0], "batch": k[1], "area": k[2], "questions": v}
        for k, v in sorted(counts.items())
    ]


def concept_rows(items: list[dict[str, Any]], snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """DSA concepts that have paths or syllabus entries but no question topic."""
    known = set(dsa_topics(snapshot))
    concepts: dict[str, set[str]] = defaultdict(set)
    for item in items:
        if item["source_label"] != "master":
            continue
        if item["kind"] == "learning_path" and item["topic"] and item["topic"] not in known:
            concepts[item["topic"]].add(f"path {item['content_key']}")
        if item["kind"] == "learning_path" and not item["topic"]:
            concepts[item["content_key"]].add(f"path {item['content_key']} (no topic)")
        if item["kind"] == "syllabus_entry" and item["category"] == "dsa":
            unit = item["skill"]
            if unit and unit not in known:
                concepts[unit].add(
                    f"syllabus {item['content_key']} ({item['publication_declaration']})"
                )
    return [{"concept": k, "evidence": sorted(v)} for k, v in sorted(concepts.items())]
