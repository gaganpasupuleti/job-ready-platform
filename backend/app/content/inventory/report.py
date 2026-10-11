"""Render the inventory evidence files. Output is byte-stable: sorted, no timestamps, LF."""

from __future__ import annotations

import csv
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.content.inventory import analysis
from app.content.inventory.extract import ITEM_FIELDS, build_items, count_only, load_snapshot
from app.content.inventory.sources import PINNED_REFS

COMMAND = "python -m app.content.inventory --out ../docs/audits/2026-10-11-content-inventory"
CHECK_COMMAND = f"{COMMAND} --check"
PENDING = analysis.PENDING
HISTORICAL = {
    "source": "docs/PRODUCTION_CONTENT_ACTIVATION.md",
    "measured_on": "2026-09-05",
    "status": "historical measurement; not re-verified by this audit",
    "active_mcqs": 642,
    "active_mcqs_by_domain": {
        "placement": 119,
        "technical": 121,
        "ai": 117,
        "cloud": 107,
        "devops": 98,
        "cybersecurity": 80,
    },
    "phase11_rows_inserted": 219,
    "phase11_rows_skipped_as_duplicate": 1,
}
GENERATED_FILES = (
    "CONTENT_INVENTORY.md",
    "TOPIC_COVERAGE.md",
    "DUPLICATES_AND_GAPS.md",
    "EVIDENCE_AND_LIMITATIONS.md",
    "SOURCE_COUNTS.json",
    "SOURCE_COUNTS.csv",
    "CONTENT_ITEMS.json",
    "CONTENT_ITEMS.csv",
)


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _csv(header: list[str], rows: list[list[Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ";".join(str(v) for v in value)
    return str(value)


def _table(header: list[str], rows: list[list[Any]]) -> str:
    def fmt(value: Any) -> str:
        return _cell(value).replace("|", "\\|").replace("\n", " ") or "-"

    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def build(repo: Path) -> dict[str, Any]:
    snapshot = load_snapshot(repo)
    items = build_items(snapshot)
    analysis.annotate(snapshot, items)
    digests = analysis.batch_digests(snapshot)
    texts = analysis.stems(snapshot)
    return {
        "snapshot": snapshot,
        "items": items,
        "counts": {view: analysis.methodology_counts(items, view) for view in analysis.VIEWS},
        "sprint": {
            label: analysis.sprint_accounting(items, label) for label in ("pr-18", "quality-gate")
        },
        "versions": {
            "pr-18 -> quality-gate": analysis.version_comparison(
                items, digests, "pr-18", "quality-gate"
            ),
            "master -> pr-17": analysis.version_comparison(items, digests, "master", "pr-17"),
            "master -> quality-gate": analysis.version_comparison(
                items, digests, "master", "quality-gate"
            ),
        },
        "manifests": analysis.manifest_checks(snapshot),
        "duplicate_keys": analysis.duplicate_keys(items),
        "cross_batch": {view: analysis.cross_batch_keys(items, view) for view in analysis.VIEWS},
        "exact": {view: analysis.exact_duplicates(items, view) for view in analysis.VIEWS},
        "semantic": analysis.semantic_candidates(items, texts, "master+quality-gate"),
        "coverage": analysis.coverage(items, snapshot),
        "area_level": analysis.area_level(items),
        "concepts": analysis.concept_rows(items, snapshot),
        "count_only": count_only(snapshot),
    }


def _by_source(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for item in items:
        groups.setdefault((item["source_label"], item["collection"], item["kind"]), []).append(item)
    rows = []
    for (label, collection, kind), members in sorted(groups.items()):
        rows.append(
            {
                "source_label": label,
                "collection": collection,
                "kind": kind,
                "source_file": members[0]["source_file"],
                "rows": len(members),
                "distinct_stem_fingerprints": len(
                    {m["stem_fingerprint"] for m in members if m["stem_fingerprint"]}
                ),
                "versions": dict(
                    sorted(Counter(str(m["version"]) for m in members if m["version"]).items())
                ),
                "flagged_rows": sum(1 for m in members if m["flags"]),
            }
        )
    return rows


def _by_category(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(
        (i["source_label"], i["domain"] or "-", i["category"] or "-", i["curriculum_area"] or "-")
        for i in items
        if i["kind"] == "mcq"
    )
    return [
        {
            "source_label": k[0],
            "domain": k[1],
            "category": k[2],
            "curriculum_area": k[3],
            "mcq_rows": v,
        }
        for k, v in sorted(counts.items())
    ]


def source_counts(data: dict[str, Any]) -> dict[str, Any]:
    exact = {
        view: dict(sorted(Counter(f["classification"] for f in found).items()))
        for view, found in data["exact"].items()
    }
    manifests = Counter(
        f"{m['source_label']}/{m['batch']}: {m['status']} (eol {m['checkout_eol']})"
        for m in data["manifests"]
    )
    return {
        "generation_command": COMMAND,
        "inputs": [
            {
                "label": r.label,
                "branch": r.branch,
                "sha": r.sha,
                "status": r.status,
                "paths": list(r.paths),
            }
            for r in PINNED_REFS
        ],
        "curriculum_target": {
            "mcqs": analysis.CURRICULUM_TARGET,
            "status": "target, not an existing completion count",
        },
        "methodology_counts": data["counts"],
        "sprint1_accounting": data["sprint"],
        "version_comparisons": {
            name: {k: len(v) for k, v in result.items()}
            for name, result in data["versions"].items()
        },
        "by_source": _by_source(data["items"]),
        "by_category": _by_category(data["items"]),
        "count_only_sources": data["count_only"],
        "exact_duplicate_groups": exact,
        "semantic_duplicate_candidates": len(data["semantic"]),
        "duplicate_keys_within_scope": len(data["duplicate_keys"]),
        "manifest_checks": dict(sorted(manifests.items())),
        "flags": dict(
            sorted(Counter(f.split(":")[0] for i in data["items"] for f in i["flags"]).items())
        ),
        "historical_measurements": [HISTORICAL],
        "production_status": PENDING,
    }


def _flatten(prefix: str, value: Any, out: list[list[Any]]) -> None:
    if isinstance(value, dict):
        for key in sorted(value):
            _flatten(f"{prefix}.{key}" if prefix else str(key), value[key], out)
    else:
        out.append([prefix, _cell(value)])


def source_counts_csv(counts: dict[str, Any]) -> str:
    rows: list[list[Any]] = []
    _flatten("methodology_counts", counts["methodology_counts"], rows)
    _flatten("sprint1_accounting", counts["sprint1_accounting"], rows)
    _flatten("version_comparisons", counts["version_comparisons"], rows)
    _flatten("count_only_sources", counts["count_only_sources"], rows)
    _flatten("exact_duplicate_groups", counts["exact_duplicate_groups"], rows)
    _flatten("manifest_checks", counts["manifest_checks"], rows)
    _flatten("flags", counts["flags"], rows)
    rows.append(["semantic_duplicate_candidates", counts["semantic_duplicate_candidates"]])
    rows.append(["production_status", PENDING])
    for row in counts["by_source"]:
        rows.append(
            [f"by_source.{row['source_label']}.{row['collection']}.{row['kind']}", row["rows"]]
        )
    for row in counts["by_category"]:
        key = ".".join(
            [row["source_label"], row["domain"], row["category"], row["curriculum_area"]]
        )
        rows.append([f"by_category.{key}", row["mcq_rows"]])
    return _csv(["metric", "value"], rows)


def items_json(items: list[dict[str, Any]]) -> str:
    return _json([{field: item[field] for field in ITEM_FIELDS} for item in items])


def items_csv(items: list[dict[str, Any]]) -> str:
    return _csv(list(ITEM_FIELDS), [[_cell(item[f]) for f in ITEM_FIELDS] for item in items])


def _header(title: str) -> str:
    refs = "\n".join(f"- `{r.label}`: `{r.sha}` ({r.branch}; {r.status})" for r in PINNED_REFS)
    return (
        f"# {title}\n\n"
        "Generated by the read-only content inventory. Do not edit by hand; regenerate from\n"
        f"`backend/` with `{COMMAND}`.\n\n"
        f"Pinned inputs:\n\n{refs}\n\n"
        f"Actual database and production state: {PENDING}\n\n"
    )


def content_inventory_md(data: dict[str, Any], counts: dict[str, Any]) -> str:
    out = [_header("Content inventory")]
    out.append(
        "## Counting methodology\n\n"
        "Each view is a set of pinned sources read together. Views overlap, so never add one\n"
        "view's counts to another's. The Sprint 1 batch exists in two candidate versions\n"
        "(`pr-18` and `quality-gate`); count it once, from one of them.\n\n"
        f"The {analysis.CURRICULUM_TARGET:,}-MCQ curriculum is a target, not an existing "
        "completion count.\n\n"
    )
    metrics = [
        ("1. Definitions in source (MCQ rows)", lambda c: c["1_definitions_in_source"]["mcq_rows"]),
        ("   of which seed rows", lambda c: c["1_definitions_in_source"]["seed_mcq_rows"]),
        ("   of which batch rows", lambda c: c["1_definitions_in_source"]["batch_mcq_rows"]),
        (
            "2. Distinct MCQ stem fingerprints",
            lambda c: c["2_unique_authored_keys"]["distinct_mcq_stem_fingerprints"],
        ),
        (
            "2. Distinct batch question keys",
            lambda c: c["2_unique_authored_keys"]["distinct_batch_question_keys"],
        ),
        ("3. Adoption references", lambda c: c["3_adoption_references"]),
        ("4. New batch questions", lambda c: c["4_new_batch_questions"]),
        (
            "5. Published syllabus entries",
            lambda c: c["5_published_source_declarations"]["published_syllabus_entries"],
        ),
        (
            "5. Batch materials published on apply",
            lambda c: c["5_published_source_declarations"]["batch_materials_published_on_apply"],
        ),
        (
            "5. Batch packs published on apply",
            lambda c: c["5_published_source_declarations"]["batch_packs_published_on_apply"],
        ),
        ("6. Actual published database rows", lambda c: c["6_actual_published_database_rows"]),
        ("7. Unscored syllabus reading checks", lambda c: c["7_unscored_syllabus_reading_checks"]),
        ("8. DSA coding definitions", lambda c: c["8_dsa_coding_definitions"]),
        (
            "9. Coding problems with tests and starter code",
            lambda c: c["9_executable_coding_problems"]["definitions_with_tests_and_starter_code"],
        ),
        (
            "9. Coding runtime execution",
            lambda c: c["9_executable_coding_problems"]["runtime_execution"],
        ),
    ]
    views = list(analysis.VIEWS)
    out.append(
        _table(
            ["Count", *views],
            [[name, *[fn(data["counts"][v]) for v in views]] for name, fn in metrics],
        )
    )
    out.append(
        "\nCount 7 lists question keys referenced by syllabus entries. The syllabus practice\n"
        "endpoint returns correctness without storing a score. The same rows are also imported\n"
        "as active questions under the `studio-saturday-001` topic, so they are not exclusive\n"
        "to reading checks.\n\n"
    )
    out.append("## Sprint 1 adoption and version accounting\n\n")
    sprint_rows = [
        [
            label,
            *[
                data["sprint"][label][k]
                for k in (
                    "rows",
                    "adopt",
                    "create",
                    "adopt_linked_to_phase11",
                    "adopt_stem_unchanged",
                    "with_revises",
                )
            ],
            _cell([f"v{k}={v}" for k, v in data["sprint"][label]["versions"].items()]),
        ]
        for label in ("pr-18", "quality-gate")
    ]
    out.append(
        _table(
            [
                "Source",
                "Rows",
                "Adopt",
                "Create",
                "Adopt linked to Phase 11",
                "Adopt with unchanged stem",
                "Rows with revises",
                "Versions",
            ],
            sprint_rows,
        )
    )
    out.append(
        "\nAn adoption is linked when its stem, or the stem recorded in `revises`, has the same\n"
        "fingerprint as a Phase 11 row. Adoptions reuse Phase 11 stems; they are not new\n"
        "questions and are excluded from count 4.\n\n"
    )
    out.append("## Version comparisons\n\n")
    vrows = [
        [
            name,
            *[
                len(result.get(k, []))
                for k in (
                    "unchanged",
                    "changed_with_version_bump",
                    "changed_without_version_bump",
                    "only_in_head",
                )
            ],
        ]
        for name, result in data["versions"].items()
    ]
    out.append(
        _table(
            [
                "Comparison",
                "Unchanged",
                "Changed with version bump",
                "Changed without version bump",
                "Only in head",
            ],
            vrows,
        )
    )
    for name, result in data["versions"].items():
        changed = result.get("changed_with_version_bump", [])
        if changed:
            out.append(f"\n{name}, changed with a version bump: {', '.join(changed)}.\n")
    out.append("\n## Totals by source\n\n")
    out.append(
        _table(
            [
                "Source",
                "Collection",
                "Kind",
                "File",
                "Rows",
                "Distinct stems",
                "Versions",
                "Flagged rows",
            ],
            [
                [
                    r["source_label"],
                    r["collection"],
                    r["kind"],
                    f"`{r['source_file']}`",
                    r["rows"],
                    r["distinct_stem_fingerprints"],
                    _cell([f"v{k}={v}" for k, v in r["versions"].items()]),
                    r["flagged_rows"],
                ]
                for r in counts["by_source"]
            ],
        )
    )
    out.append("\n## MCQ rows by domain, category, and curriculum area\n\n")
    out.append(
        _table(
            ["Source", "Domain", "Category", "Curriculum area", "MCQ rows"],
            [
                [r["source_label"], r["domain"], r["category"], r["curriculum_area"], r["mcq_rows"]]
                for r in counts["by_category"]
            ],
        )
    )
    out.append("\n## Count-only sources\n\n")
    out.append(_table(["Kind", "Definitions"], [[k, v] for k, v in data["count_only"].items()]))
    out.append("\nThese are listed for completeness. They are outside the CRT and DSA MCQ scope.\n")
    return "".join(out)


def topic_coverage_md(data: dict[str, Any]) -> str:
    out = [_header("Topic coverage")]
    out.append(
        "The canonical Astra 42-topic list is not in the repository. This matrix uses the\n"
        "repository's own topics: 25 placement aptitude topics and 15 DSA topics, 40 in all.\n"
        "DSA concepts that have only learning paths or syllabus entries are listed after the\n"
        "matrix. Mapping a topic to one of the six areas is an audit convention that needs\n"
        "human confirmation.\n\n"
        "Column notes:\n\n"
        "- Source questions are master seed rows. Phase 11 rows need `phase11_activate`.\n"
        "- Unusable seed rows have placeholder options, a topic no seed creates, or a topic\n"
        "  an earlier runner row already fills. They are excluded from distinct usable stems.\n"
        "- Reviewed questions are Sprint 1 adoptions of Phase 11 stems at the quality gate.\n"
        "- New candidates are Sprint 1 creates at the quality gate.\n"
        "- Both Sprint 1 groups had agent review only. No human approval is recorded and both\n"
        "  are unmerged.\n"
        "- Distinct usable stems count each stem fingerprint once across usable seed rows and\n"
        "  Sprint 1 rows, so an adoption is not counted twice.\n"
        f"- The gap column assumes an even split of {analysis.CURRICULUM_TARGET:,} across 42 "
        f"topics ({analysis.TOPIC_TARGET} per topic).\n"
        "  That split is an illustration, not an Astra rule.\n"
        "- Student-ready is never claimed from source content alone.\n\n"
    )
    header = [
        "Area",
        "Topic",
        "Source questions",
        "Phase 11",
        "Runner rows",
        "Unusable seed rows",
        "Reviewed",
        "New candidates",
        "Distinct usable stems",
        "Materials",
        "Paths",
        "Coding problems",
        "Exact duplicate groups",
        "Missing coverage",
        "Publication status",
        "Student-ready",
    ]
    rows = [
        [
            r["area"],
            r["topic"],
            r["source_questions"],
            r["phase11_questions"],
            r["runner_rows"],
            r["unusable_seed_rows"],
            r["reviewed_questions"],
            r["new_candidates"],
            r["distinct_usable_stems"],
            r["learning_materials"],
            r["learning_paths"],
            r["coding_problems"],
            r["exact_duplicate_groups"],
            r["missing_coverage"],
            r["publication_status"],
            r["student_ready"],
        ]
        for r in data["coverage"]
    ]
    out.append(_table(header, rows))
    out.append("\n## Area totals\n\n")
    areas: dict[str, Counter[str]] = {}
    for r in data["coverage"]:
        tally = areas.setdefault(r["area"], Counter())
        tally["topics"] += 1
        tally["source"] += r["source_questions"]
        tally["unusable"] += r["unusable_seed_rows"]
        tally["reviewed"] += r["reviewed_questions"]
        tally["new"] += r["new_candidates"]
        tally["distinct"] += r["distinct_usable_stems"]
        tally["coding"] += r["coding_problems"]
        tally["empty"] += 1 if r["distinct_usable_stems"] == 0 else 0
    out.append(
        _table(
            [
                "Area",
                "Topics",
                "Source questions",
                "Unusable seed rows",
                "Reviewed",
                "New candidates",
                "Distinct usable stems",
                "Coding problems",
                "Topics with no usable questions",
            ],
            [
                [
                    a,
                    t["topics"],
                    t["source"],
                    t["unusable"],
                    t["reviewed"],
                    t["new"],
                    t["distinct"],
                    t["coding"],
                    t["empty"],
                ]
                for a, t in areas.items()
            ],
        )
    )
    out.append("\n## Batch questions tagged by area only\n\n")
    out.append(
        "These rows carry a skill such as `quantitative` but no topic, so they are counted at\n"
        "area level and not in the matrix.\n\n"
    )
    out.append(
        _table(
            ["Source", "Batch", "Area", "Questions"],
            [
                [r["source_label"], r["batch"], r["area"], r["questions"]]
                for r in data["area_level"]
            ],
        )
    )
    out.append("\n## DSA concepts without a question topic\n\n")
    out.append(
        _table(["Concept", "Evidence"], [[r["concept"], r["evidence"]] for r in data["concepts"]])
    )
    return "".join(out)


def duplicates_md(data: dict[str, Any]) -> str:
    out = [_header("Duplicates and gaps")]
    out.append(
        "Nothing here is merged, deleted, or rewritten automatically. Each finding needs a\n"
        "human decision.\n\n## Duplicate keys within one source scope\n\n"
    )
    out.append(
        _table(
            ["Scope", "Kind", "Key", "Count"],
            [[d["scope"], d["kind"], d["key"], d["count"]] for d in data["duplicate_keys"]],
        )
        if data["duplicate_keys"]
        else "None found.\n"
    )
    out.append("\n## Keys reused across batches\n\n")
    seen: set[tuple[str, str]] = set()
    rows = []
    for view, findings in data["cross_batch"].items():
        for f in findings:
            if (f["kind"], f["key"]) not in seen:
                seen.add((f["kind"], f["key"]))
                rows.append([view, f["kind"], f["key"], f["occurrences"]])
    out.append(
        _table(["First seen in view", "Kind", "Key", "Occurrences"], rows)
        if rows
        else "None found.\n"
    )
    out.append("\n## Exact duplicate stems\n\n")
    for view, findings in data["exact"].items():
        kinds = Counter(f["classification"] for f in findings)
        out.append(
            f"- `{view}`: {kinds.get('exact-duplicate', 0)} unexpected groups, "
            f"{kinds.get('expected-adoption-overlap', 0)} expected adoption overlaps.\n"
        )
    unexpected = [
        f for f in data["exact"]["master+quality-gate"] if f["classification"] == "exact-duplicate"
    ]
    if unexpected:
        out.append("\n")
        out.append(
            _table(
                ["Fingerprint", "Items", "Topics"],
                [[f["stem_fingerprint"][:12], f["items"], f["topics"]] for f in unexpected],
            )
        )
    out.append(
        "\nSeeders skip a stem that already exists, so each unexpected group above inserts at\n"
        "most once. The first master group explains the one Phase 11 row recorded as skipped\n"
        "on 2026-09-05; that link is an inference from source text, not a database check.\n"
    )
    out.append(
        f"\n## Possible semantic duplicates (manual review)\n\n"
        f"Token Jaccard similarity of at least {analysis.SEMANTIC_THRESHOLD} between stems with "
        f"at least {analysis.SEMANTIC_MIN_TOKENS} tokens, in the `master+quality-gate` view.\n"
        "Exact duplicates and adoption pairs are excluded. A high score can still be two\n"
        "different questions.\n\n"
    )
    out.append(
        _table(
            ["Jaccard", "Item A", "Item B"],
            [[s["jaccard"], s["items"][0], s["items"][1]] for s in data["semantic"]],
        )
        if data["semantic"]
        else "None found.\n"
    )
    out.append("\n## Reference and seedability flags\n\n")
    flagged = [
        [i["item_id"], i["flags"]]
        for i in data["items"]
        if any(not f.startswith("placeholder-") for f in i["flags"])
    ]
    out.append(_table(["Item", "Flags"], flagged) if flagged else "None found.\n")
    out.append(
        "\nFlag meanings:\n\n"
        "- `topic-not-in-taxonomy`: no seed creates this topic, so `python -m app.seed` skips\n"
        "  the row.\n"
        "- `runner-topic-already-filled`: an earlier runner row fills the same empty topic, so\n"
        "  this row is skipped.\n"
        "- `path-has-no-topic` and `path-topic-has-no-coding-problems`: the path is created\n"
        "  with a browse link instead of linked problems.\n"
        "- `related-lesson-unresolved`, `unresolved-*-reference`, `published-without-material`,\n"
        "  and `adoption-source-not-found`: broken references.\n"
        "\n17 runner template rows also use placeholder options and a placeholder explanation\n"
        '("Sample development question for engine testing."). They are counted as\n'
        "definitions but are not curriculum content.\n"
    )
    out.append("\n## Coverage gaps\n\n")
    gaps = [
        [r["area"], r["topic"], r["missing_coverage"]]
        for r in data["coverage"]
        if any(not m.endswith(f"target of {analysis.TOPIC_TARGET}") for m in r["missing_coverage"])
    ]
    out.append(_table(["Area", "Topic", "Missing"], gaps))
    return "".join(out)


def evidence_md(data: dict[str, Any]) -> str:
    out = [_header("Evidence and limitations")]
    out.append(
        "## How the evidence was produced\n\n"
        "The inventory reads only the pinned commits above through `git show` and\n"
        "`git ls-tree`. It never reads the working tree, never imports or runs seed modules\n"
        "(it parses their syntax), and never opens a database connection. If a pinned commit\n"
        "or file is missing, it stops with `SourceUnavailable` instead of substituting another\n"
        "branch.\n\n"
        f"Regenerate from `backend/`:\n\n```\n{COMMAND}\n```\n\n"
        f"Check committed files without rewriting them:\n\n```\n{CHECK_COMMAND}\n```\n\n"
        "Item IDs such as `master/phase11-aptitude/#067` are source locators, not database IDs.\n"
        "Stem fingerprints use `app.content.hashing.content_hash`, the same normalized hash the\n"
        "Phase 11 activation uses for duplicate detection.\n\n"
        "## Manifest integrity\n\n"
        "Batch manifests hash files as a checkout writes them. Where `git check-attr` reports\n"
        "`eol=crlf` for a batch at its pinned commit, the inventory hashes CRLF bytes;\n"
        "otherwise it hashes the stored bytes.\n\n"
    )
    manifests = Counter(
        (m["source_label"], m["batch"], m["checkout_eol"], m["status"]) for m in data["manifests"]
    )
    out.append(
        _table(
            ["Source", "Batch", "Checkout eol", "Status", "Files"],
            [[*k, v] for k, v in sorted(manifests.items())],
        )
    )
    out.append(
        "\nPR #17 and PR #18 each append a different line to `.gitattributes`. Merging the\n"
        "second one will likely need a manual conflict resolution in that file.\n\n"
        "## Historical measurements\n\n"
        "These numbers come from earlier documents. They are kept with their source and date\n"
        "and were not re-verified.\n\n"
    )
    h = HISTORICAL
    out.append(
        _table(
            ["Source", "Measured on", "Measurement", "Value"],
            [
                [h["source"], h["measured_on"], "active MCQs", h["active_mcqs"]],
                [
                    h["source"],
                    h["measured_on"],
                    "active MCQs by domain",
                    [f"{k}={v}" for k, v in h["active_mcqs_by_domain"].items()],
                ],
                [
                    h["source"],
                    h["measured_on"],
                    "Phase 11 rows inserted",
                    h["phase11_rows_inserted"],
                ],
                [
                    h["source"],
                    h["measured_on"],
                    "Phase 11 rows skipped as duplicate",
                    h["phase11_rows_skipped_as_duplicate"],
                ],
            ],
        )
    )
    out.append(
        "\n## Limitations\n\n"
        f"- Actual published database rows: {PENDING}\n"
        f"- Coding problem execution: {PENDING} Judge0 activation is out of scope.\n"
        "- The canonical Astra 42-topic list is not in the repository. The coverage matrix\n"
        "  uses repository topics (40) and needs human confirmation.\n"
        '- "Reviewed" means the agent quality gate on Sprint 1. No human content approval is\n'
        "  recorded for PR #18 or for the 17 version 2 revisions.\n"
        "- Batch questions from the 2026-09-14 and 2026-09-19 batches carry skills, not topics.\n"
        "  The importer files every batch question under one `studio-saturday-001` topic, so\n"
        "  database topic counts will not match this matrix.\n"
        "- Learning path availability declared in source can change at seed time:\n"
        "  `build51_seed` marks existing DSA paths as available. See `README.md` for the local\n"
        "  seed check.\n"
        "- Semantic duplicate detection is lexical. It cannot find paraphrases with different\n"
        "  words, and it flags some distinct questions.\n"
        "- Generated interview files under `backend/content/generated/` are listed as drafts.\n"
        "  No importer reference was verified.\n"
    )
    return "".join(out)


def render(repo: Path) -> dict[str, str]:
    data = build(repo)
    counts = source_counts(data)
    return {
        "CONTENT_INVENTORY.md": content_inventory_md(data, counts),
        "TOPIC_COVERAGE.md": topic_coverage_md(data),
        "DUPLICATES_AND_GAPS.md": duplicates_md(data),
        "EVIDENCE_AND_LIMITATIONS.md": evidence_md(data),
        "SOURCE_COUNTS.json": _json(counts),
        "SOURCE_COUNTS.csv": source_counts_csv(counts),
        "CONTENT_ITEMS.json": items_json(data["items"]),
        "CONTENT_ITEMS.csv": items_csv(data["items"]),
    }


def write(files: dict[str, str], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (out_dir / name).write_bytes(content.encode("utf-8"))


def check(files: dict[str, str], out_dir: Path) -> list[str]:
    stale = []
    for name, content in files.items():
        path = out_dir / name
        current = path.read_bytes().decode("utf-8").replace("\r\n", "\n") if path.exists() else None
        if current != content:
            stale.append(name)
    return stale
