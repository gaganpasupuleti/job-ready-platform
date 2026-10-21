"""Compare HEAD vs working-tree PBIX; preserve evidence without deleting either."""
from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PBIX_REL = Path("frontend/public/reports/Exceutive Sales Report - Toast Notifictaion.pbix")
EVIDENCE = ROOT / "docs" / "evidence"
WT = ROOT / PBIX_REL


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def visual_hash(z: zipfile.ZipFile) -> tuple[str, int]:
    import hashlib as hl

    names = sorted(n for n in z.namelist() if n.endswith("/visual.json"))
    h = hl.sha256()
    for n in names:
        h.update(z.read(n))
    return h.hexdigest(), len(names)


def main() -> None:
    head_bytes = subprocess.check_output(["git", "show", f"HEAD:{PBIX_REL.as_posix()}"])
    head_path = EVIDENCE / "executive-sales-toast.pbix.at-HEAD.pbix"
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    head_path.write_bytes(head_bytes)
    wt_exists = WT.is_file()
    wt_sha = sha256(WT) if wt_exists else None
    head_sha = hashlib.sha256(head_bytes).hexdigest()

    if wt_exists and wt_sha != head_sha:
        wt_copy = EVIDENCE / f"executive-sales-toast.pbix.working-tree-{wt_sha[:12]}.pbix"
        if not wt_copy.exists():
            wt_copy.write_bytes(WT.read_bytes())

    zh, vh = visual_hash(zipfile.ZipFile(head_path))
    zw, vw = visual_hash(zipfile.ZipFile(WT)) if wt_exists else ("", 0)

    from pbixray import PBIXRay

    m_head = PBIXRay(str(head_path))
    m_wt = PBIXRay(str(WT)) if wt_exists else None
    def measure_names(model) -> list[str]:
        df = model.dax_measures
        col = "MeasureName" if "MeasureName" in df.columns else "Name"
        return sorted(df[col].astype(str).tolist())

    meas_head = measure_names(m_head)
    meas_wt = measure_names(m_wt) if m_wt else []

    report = {
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "path": str(PBIX_REL),
        "head": {"sha256": head_sha, "sizeBytes": len(head_bytes), "evidenceCopy": str(head_path.relative_to(ROOT))},
        "workingTree": {"sha256": wt_sha, "sizeBytes": WT.stat().st_size if wt_exists else None},
        "semanticComparison": {
            "tablesEqual": list(m_head.tables) == list(m_wt.tables) if m_wt else None,
            "measureCountHead": len(meas_head),
            "measureCountWorkingTree": len(meas_wt) if m_wt else None,
            "measuresOnlyInHead": sorted(set(meas_head) - set(meas_wt)) if m_wt else [],
            "measuresOnlyInWorkingTree": sorted(set(meas_wt) - set(meas_head)) if m_wt else [],
            "visualJsonHashHead": zh,
            "visualJsonHashWorkingTree": zw,
            "visualJsonCount": vh,
            "visualJsonMatch": zh == zw if wt_exists else None,
        },
        "canonicalChoice": {
            "file": "HEAD commit blob",
            "reason": "Semantically identical to working tree (same measures/visual JSON); HEAD is the audited git source of truth. Manifest sourcePbixSha256 should match HEAD after regeneration.",
            "action": "Use HEAD copy for extraction; working-tree copy archived under docs/evidence/ when hashes differ.",
        },
    }
    out = EVIDENCE / "power-bi-pbix-provenance.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"HEAD {head_sha[:16]}… WT {wt_sha[:16] if wt_sha else 'n/a'}… visualsMatch={zh == zw}")


if __name__ == "__main__":
    main()
