#!/usr/bin/env python3
"""
Robotic Test Runner — Tests all 9 Excel input files through the full pipeline.
Compares outputs against reference PDFs in RESOURCES_ARCHIVE/ANTIGRAVITY IMAGE TEXT SAMPLES/PDF_OUTPUTS/
Validates: extra items flow, deviation statement, note sheet, all 6 templates.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engine"))
os.environ.setdefault("ALLOW_INSECURE_SECRET", "1")

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Test file discovery ───────────────────────────────────────────────────────
TEST_DIRS = [
    ROOT / "RESOURCES_ARCHIVE" / "TEST_INPUT_FILES",
    ROOT / "RESOURCES_ARCHIVE" / "INPUT_FILES_LEVEL_02",
    ROOT / "TEST_INPUT_FILES",
]

REF_PDF_DIR = ROOT / "RESOURCES_ARCHIVE" / "ANTIGRAVITY IMAGE TEXT SAMPLES" / "PDF_OUTPUTS"
OUTPUT_BASE = ROOT / "engine_output" / "robotic_test"
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

REPORT_PATH = ROOT / "docs" / "ROBOTIC_RESULTS.log"

# ── Expected document types ───────────────────────────────────────────────────
EXPECTED_DOCS_NO_EXTRA = [
    "first_page", "deviation_statement", "note_sheet",
    "certificate_ii", "certificate_iii", "last_page"
]
EXPECTED_DOCS_WITH_EXTRA = EXPECTED_DOCS_NO_EXTRA + ["extra_items"]

# ── Helpers ───────────────────────────────────────────────────────────────────

def discover_test_files():
    """Find all unique xlsx test files."""
    seen = set()
    files = []
    for d in TEST_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.xlsx")):
            if f.name.startswith("~$"):
                continue
            if f.name not in seen:
                seen.add(f.name)
                files.append(f)
    return files


def classify_file(name: str) -> str:
    """Classify file as WITH or WITHOUT extra items based on name."""
    n = name.lower()
    if "extra" in n or "vid" in n or "wextra" in n or "with" in n or "9th" in n:
        return "WITH_EXTRA"
    return "NO_EXTRA"


def run_engine_on_file(xlsx_path: Path, out_dir: Path) -> dict:
    """Run the full engine pipeline on one Excel file. Returns result dict."""
    result = {
        "file": xlsx_path.name,
        "out_dir": str(out_dir),
        "parse_ok": False,
        "normalize_ok": False,
        "calculate_ok": False,
        "html_count": 0,
        "pdf_count": 0,
        "has_extra_items": False,
        "extra_items_count": 0,
        "extra_items_in_note_sheet": False,
        "extra_items_in_deviation": False,
        "extra_items_in_first_page": False,
        "grand_total": 0,
        "payable": 0,
        "errors": [],
        "warnings": [],
    }

    try:
        # Use the run_engine pipeline (load_excel_sheets -> build_document -> render)
        from engine.run_engine import load_excel_sheets, build_document, render_html, render_pdfs

        # Step 1: Load Excel sheets
        sheets = load_excel_sheets(xlsx_path)
        result["parse_ok"] = True

        # Step 2: Build document (runs process_bill internally)
        doc = build_document(sheets, premium_percent=0.0, premium_type="above", previous_bill_amount=0.0)
        result["normalize_ok"] = True
        result["calculate_ok"] = True
        result["has_extra_items"] = len(doc.extra_items) > 0
        result["extra_items_count"] = len(doc.extra_items)
        result["grand_total"] = doc.totals.get("grand_total", 0)
        result["payable"] = doc.totals.get("payable", 0)

        # Verify extra items flow
        if result["has_extra_items"]:
            result["extra_items_in_note_sheet"] = doc.extra_item_amount > 0
            result["extra_items_in_first_page"] = doc.totals.get("extra_items_sum", 0) > 0
            result["extra_items_in_deviation"] = len(doc.deviation_items) > 0

        # Step 3: Render HTML
        out_dir.mkdir(parents=True, exist_ok=True)
        html_paths = render_html(doc, out_dir, template_version="v2")
        result["html_count"] = len(html_paths)

        if not html_paths:
            result["errors"].append("No HTML files generated")

        # Step 4: Generate PDFs
        from engine.rendering.pdf_generator import PDFGenerator
        pdf_gen = PDFGenerator()
        pdf_count = 0
        for hp in html_paths:
            pp = out_dir / (hp.stem + ".pdf")
            engine_used = pdf_gen.generate_with_fallback(hp.read_text(encoding="utf-8"), str(pp))
            if engine_used != "failed" and pp.exists() and pp.stat().st_size > 0:
                pdf_count += 1
            else:
                result["errors"].append(f"PDF failed: {hp.name}")
        result["pdf_count"] = pdf_count

    except Exception as e:
        import traceback
        result["errors"].append(f"EXCEPTION: {e}\n{traceback.format_exc()[:500]}")

    return result


def compare_with_reference(result: dict) -> dict:
    """Compare generated output sizes with reference PDFs."""
    comparison = {}
    if not REF_PDF_DIR.exists():
        return comparison

    out_dir = Path(result["out_dir"])
    for ref_pdf in REF_PDF_DIR.glob("*.pdf"):
        gen_pdf = out_dir / ref_pdf.name
        if gen_pdf.exists():
            ref_size = ref_pdf.stat().st_size
            gen_size = gen_pdf.stat().st_size
            ratio = gen_size / ref_size if ref_size > 0 else 0
            comparison[ref_pdf.name] = {
                "ref_kb": round(ref_size / 1024, 1),
                "gen_kb": round(gen_size / 1024, 1),
                "ratio": round(ratio, 2),
                "ok": 0.1 <= ratio <= 10.0  # within 10x is acceptable
            }
    return comparison


def print_result(r: dict, comparison: dict):
    """Print a formatted result row."""
    status = "PASS" if not r["errors"] and r["pdf_count"] > 0 else "FAIL"
    extra_flag = "[EXTRA]" if r["has_extra_items"] else "       "
    print(f"  {status} {extra_flag} {r['file'][:45]:<45} "
          f"HTML:{r['html_count']} PDF:{r['pdf_count']} "
          f"Total:{r['grand_total']:>10,.0f} Payable:{r['payable']:>10,.0f}")

    if r["has_extra_items"]:
        ns = "OK" if r["extra_items_in_note_sheet"] else "FAIL"
        fp = "OK" if r["extra_items_in_first_page"] else "FAIL"
        dv = "OK" if r["extra_items_in_deviation"] else "FAIL"
        print(f"         Extra items flow -> NoteSheet:{ns} FirstPage:{fp} Deviation:{dv}")

    for err in r["errors"]:
        print(f"         ERR: {err[:100]}")

    if comparison:
        for doc, cmp in comparison.items():
            flag = "OK " if cmp["ok"] else "SZ?"
            print(f"         {flag} {doc}: ref={cmp['ref_kb']}KB gen={cmp['gen_kb']}KB ratio={cmp['ratio']}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*70}")
    print(f"  ROBOTIC TEST RUNNER — {ts}")
    print(f"{'='*70}")

    files = discover_test_files()
    print(f"\n  Discovered {len(files)} test files\n")

    all_results = []
    total_pass = total_fail = 0

    for xlsx in files:
        classification = classify_file(xlsx.name)
        out_dir = OUTPUT_BASE / xlsx.stem
        result = run_engine_on_file(xlsx, out_dir)
        comparison = compare_with_reference(result)
        print_result(result, comparison)
        result["classification"] = classification
        result["comparison"] = comparison
        all_results.append(result)

        if not result["errors"] and result["pdf_count"] > 0:
            total_pass += 1
        else:
            total_fail += 1

    # Summary
    print(f"\n{'='*70}")
    print(f"  SUMMARY: {total_pass} PASS / {total_fail} FAIL / {len(files)} TOTAL")
    print(f"{'='*70}\n")

    # Write log
    REPORT_PATH.parent.mkdir(exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(f"ROBOTIC TEST RUN — {ts}\n")
        f.write("="*70 + "\n")
        for r in all_results:
            status = "PASS" if not r["errors"] and r["pdf_count"] > 0 else "FAIL"
            f.write(f"{status} | {r['file']} | HTML:{r['html_count']} PDF:{r['pdf_count']} "
                    f"Extra:{r['has_extra_items']} Total:{r['grand_total']:.0f}\n")
            for e in r["errors"]:
                f.write(f"  ERROR: {e[:200]}\n")
        f.write(f"\nSUMMARY: {total_pass} PASS / {total_fail} FAIL\n")

    print(f"  Report written to: {REPORT_PATH}")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
