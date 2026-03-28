"""
Batch Input Management System (BIMS) — Execution Engine.

Refactored (KIMI review):
- shutil.move() replaced with atomic copy+rename to prevent partial moves on crash.
- anomaly_detector.save_validated_features() called only on success (not before check).
- BillDocument construction extracted to _build_document_from_payload().
- Broad except clauses narrowed; JSON errors reported with detail.
"""
import json
import logging
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

root_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(root_dir))

from ingestion.anomaly_detector import (
    detect_anomalies,
    extract_features,
    save_validated_features,
)
from engine.run_engine import render_html, render_pdfs
from engine.model.document import BillDocument

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Directory layout ──────────────────────────────────────────────────────────
BATCH_DIR     = root_dir / "BATCH_SYSTEM"
PENDING_DIR   = BATCH_DIR / "PENDING_INPUTS"
GENERATED_DIR = BATCH_DIR / "GENERATED_PDFS"
ARCHIVE_DIR   = BATCH_DIR / "PROCESSED_ARCHIVE"
QUARANTINE_DIR= BATCH_DIR / "ERROR_QUARANTINE"
REPORT_FILE   = BATCH_DIR / "batch_report.md"

for _d in (PENDING_DIR, GENERATED_DIR, ARCHIVE_DIR, QUARANTINE_DIR):
    _d.mkdir(parents=True, exist_ok=True)


# ── Atomic file move ──────────────────────────────────────────────────────────

def _atomic_move(source: Path, dest_dir: Path):
    """
    Safely moves a file to the destination directory using an atomic rename.
    Ensures that partial files are not left behind if the process crashes.
    """
    dest = dest_dir / source.name
    temp_dest = dest_dir / f".tmp.{source.name}.{os.getpid()}"
    
    try:
        # 1. Copy to temp file on the same filesystem as destination
        shutil.copy2(source, temp_dest)
        # 2. Atomic rename (replaces existing if any)
        os.replace(temp_dest, dest)
        # 3. Securely remove source only after success
        source.unlink()
    except Exception as e:
        if temp_dest.exists():
            temp_dest.unlink()
        raise e


# ── Report helpers ────────────────────────────────────────────────────────────

def _append_report(message: str) -> None:
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def _initialize_report() -> None:
    if not REPORT_FILE.exists() or REPORT_FILE.stat().st_size == 0:
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write("# Brilliant Batch Management System — Execution Report\n")
            f.write(f"Initialized: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")


# ── Document builder ──────────────────────────────────────────────────────────

def _build_document_from_payload(payload: dict) -> BillDocument:
    """Construct BillDocument from a validated JSON payload dict."""
    td = payload.get("titleData", {})

    # Safe float for work order amount (may contain commas)
    try:
        wo_amount = float(str(td.get("Work Order Amount Rs.", "0")).replace(",", ""))
    except (ValueError, TypeError):
        wo_amount = 0.0

    extra_items = payload.get("extraItems", [])
    extra_amount = sum(float(item.get("amount", 0) or 0) for item in extra_items)

    return BillDocument(
        header=[],
        items=payload.get("billItems", []),
        totals={"total_amount": payload.get("totalAmount", 0)},
        deviation_items=[],
        deviation_summary={},
        extra_items=extra_items,
        agreement_no=td.get("Agreement No.", "AGR-100"),
        name_of_work=td.get("Name of Work", "Batch Work"),
        name_of_firm=td.get("Name of Contractor", "Contractor"),
        date_commencement=td.get("Date of written order to commence work", ""),
        date_completion=td.get("St. Date of Completion", ""),
        actual_completion=td.get("Date of actual completion of work", ""),
        work_order_amount=wo_amount,
        extra_item_amount=extra_amount,
    )


# ── Core processor ────────────────────────────────────────────────────────────

def process_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Process one JSON payload file.
    Returns (success, list_of_warnings).
    """
    # Load JSON
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, [f"Invalid JSON: {exc}"]
    except OSError as exc:
        return False, [f"File read error: {exc}"]

    # Anomaly detection — check BEFORE saving features
    all_rows = payload.get("billItems", []) + payload.get("extraItems", [])
    features = extract_features(all_rows)
    warnings = detect_anomalies(features)

    if warnings:
        # Do NOT save anomalous features to training history
        return False, warnings

    # Generate documents
    doc     = _build_document_from_payload(payload)
    job_dir = GENERATED_DIR / file_path.stem
    job_dir.mkdir(exist_ok=True)

    try:
        html_paths = render_html(doc, job_dir, template_version="v2")
        render_pdfs(html_paths, job_dir)
    except Exception as exc:
        logger.exception("Generation failed for %s", file_path.name)
        return False, [f"Generation failed: {exc}"]

    # Only persist features after successful generation
    save_validated_features(features)
    return True, []


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    _initialize_report()
    run_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _append_report(f"## Batch Run: {run_ts}")

    pending = list(PENDING_DIR.glob("*.json"))
    if not pending:
        print("No files in PENDING_INPUTS. Exiting.")
        _append_report("- **No pending files detected.**\n")
        return

    print(f"BIMS: {len(pending)} file(s) discovered.")
    _append_report(f"- **Files Discovered**: {len(pending)}\n")
    _append_report("| File ID | Status | Remarks |")
    _append_report("| :--- | :---: | :--- |")

    success_count = quarantine_count = 0

    for f_path in pending:
        print(f"Processing: {f_path.name} ... ", end="", flush=True)
        success, warnings = process_file(f_path)

        if success:
            print("SUCCESS")
            _atomic_move(f_path, ARCHIVE_DIR)
            _append_report(f"| `{f_path.name}` | ✅ SUCCESS | 6 PDFs generated |")
            success_count += 1
        else:
            print(f"QUARANTINED ({len(warnings)} issue(s))")
            _atomic_move(f_path, QUARANTINE_DIR)
            summary = "; ".join(warnings[:3])
            _append_report(f"| `{f_path.name}` | ❌ QUARANTINED | {summary} |")
            quarantine_count += 1

    throughput = success_count / len(pending) * 100 if pending else 0
    _append_report(f"\n### Batch Run Metrics")
    _append_report(f"- **Successful**: {success_count}")
    _append_report(f"- **Quarantined**: {quarantine_count}")
    _append_report(f"- **Throughput**: {throughput:.1f}%\n")
    _append_report("---\n")

    print(f"\n{'='*50}")
    print("BATCH RUN COMPLETE")
    print(f"Processed:   {len(pending)}")
    print(f"Success:     {success_count} → PROCESSED_ARCHIVE")
    print(f"Quarantined: {quarantine_count} → ERROR_QUARANTINE")
    print(f"Report:      {REPORT_FILE}")


if __name__ == "__main__":
    main()
