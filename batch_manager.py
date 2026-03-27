"""
Batch Input Management System (BIMS) - The Execution Engine
Automatically processes the PENDING_INPUTS folder, identifies AI Anomalies,
moves bad files to ERROR_QUARANTINE, generates 6 PDFs for valid files
saving them to GENERATED_PDFS, and archives the inputs into PROCESSED_ARCHIVE.

Maintains a comprehensive running batch_report.md
"""
import sys, os, json, shutil
from pathlib import Path
from datetime import datetime

root_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(root_dir))

from ingestion.anomaly_detector import extract_features, detect_anomalies
from engine.run_engine import render_html, render_pdfs
from engine.model.document import BillDocument

BATCH_DIR = root_dir / "BATCH_SYSTEM"
PENDING_DIR = BATCH_DIR / "PENDING_INPUTS"
GENERATED_DIR = BATCH_DIR / "GENERATED_PDFS"
ARCHIVE_DIR = BATCH_DIR / "PROCESSED_ARCHIVE"
QUARANTINE_DIR = BATCH_DIR / "ERROR_QUARANTINE"
REPORT_FILE = BATCH_DIR / "batch_report.md"

for d in [PENDING_DIR, GENERATED_DIR, ARCHIVE_DIR, QUARANTINE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def append_to_report(message: str):
    """Appends a markdown message to the running batch report."""
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def initialize_report():
    if not REPORT_FILE.exists() or REPORT_FILE.stat().st_size == 0:
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write("# Brilliant Batch Management System - Execution Report\n")
            f.write(f"Initialized System: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

def process_file(file_path: Path):
    """Process a single JSON input payload."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        return False, ["Invalid JSON payload format"]
        
    # Run AI Anomaly Detection
    all_rows = payload.get("billItems", []) + payload.get("extraItems", [])
    features = extract_features(all_rows)
    warnings = detect_anomalies(features)
    
    if warnings:
        return False, warnings
        
    # Generate the 6 PDF Templates
    # Convert payload into BillDocument
    title_data = payload.get("titleData", {})
    
    # Simple extraction for document required fields
    doc = BillDocument(
        header=[], 
        items=payload.get("billItems", []),
        totals={"total_amount": payload.get("totalAmount", 0)},
        deviation_items=[],
        deviation_summary={},
        extra_items=payload.get("extraItems", []),
        agreement_no=title_data.get("Agreement No.", "AGR-100"),
        name_of_work=title_data.get("Name of Work", "Batch Work"),
        name_of_firm=title_data.get("Name of Contractor", "Contractor"),
        date_commencement=title_data.get("Date of written order to commence work", ""),
        date_completion=title_data.get("St. Date of Completion", ""),
        actual_completion=title_data.get("Date of actual completion of work", ""),
        work_order_amount=float(str(title_data.get("Work Order Amount Rs.", "0")).replace(",","")),
        extra_item_amount=sum(i.get("amount",0) for i in payload.get("extraItems", []))
    )
    
    job_dir = GENERATED_DIR / file_path.stem
    job_dir.mkdir(exist_ok=True)
    
    html_paths = render_html(doc, job_dir, template_version="v2")
    render_pdfs(html_paths, job_dir)
    
    return True, []

def main():
    initialize_report()
    run_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    append_to_report(f"## Batch Run: {run_timestamp}")
    
    pending_files = list(PENDING_DIR.glob("*.json"))
    if not pending_files:
        print("No files in PENDING_INPUTS. Exiting.")
        append_to_report("- **No pending files detected.**\n")
        return
        
    print(f"BIMS Discovered {len(pending_files)} files in PENDING_INPUTS.")
    append_to_report(f"- **Files Discovered**: {len(pending_files)}\n")
    append_to_report("| File ID | Status | Remarks |")
    append_to_report("| :--- | :---: | :--- |")
    
    success_count = 0
    quarantine_count = 0
    
    for f_path in pending_files:
        print(f"Processing: {f_path.name} ... ", end="")
        success, warnings = process_file(f_path)
        
        if success:
            print("SUCCESS")
            # Move to Archive
            shutil.move(str(f_path), str(ARCHIVE_DIR / f_path.name))
            append_to_report(f"| `{f_path.name}` | ✅ SUCCESS | 6 PDFs generated and archived |")
            success_count += 1
        else:
            print(f"QUARANTINED ({len(warnings)} anomalies)")
            # Move to Quarantine
            shutil.move(str(f_path), str(QUARANTINE_DIR / f_path.name))
            warning_str = "<br>".join(warnings)
            append_to_report(f"| `{f_path.name}` | ❌ QUARANTINED | {warning_str} |")
            quarantine_count += 1
            
    # Finalize run report
    append_to_report(f"\n### Batch Run Core Metrics")
    append_to_report(f"- **Successful Archives**: {success_count}")
    append_to_report(f"- **AI Quarantined Files**: {quarantine_count}")
    append_to_report(f"- **Throughput Ratio**: {(success_count/len(pending_files)*100):.1f}%\n")
    append_to_report("---\n")
    
    print("\n" + "="*50)
    print("BATCH RUN COMPLETE")
    print(f"Processed: {len(pending_files)}")
    print(f"Success: {success_count} -> Saved to PROCESSED_ARCHIVE")
    print(f"Quarantined: {quarantine_count} -> Saved to ERROR_QUARANTINE")
    print(f"Report updated at {REPORT_FILE}")

if __name__ == "__main__":
    main()
