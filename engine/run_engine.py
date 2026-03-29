#!/usr/bin/env python3
"""
Bill Generator Engine — Standalone Runner
Usage:  python run_engine.py <input.xlsx> [--template-version v1|v2] [--no-pdf]

Pipeline:
  Excel → EnterpriseExcelProcessor → process_bill() → BillDocument
        → EnterpriseHTMLRenderer (Jinja2 templates)
        → PDFGenerator (WeasyPrint fallback chain)

Phase 3 — Engine Extraction.
DO NOT add UI, server, or async logic here.
"""
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# ── Path setup ────────────────────────────────────────────────────────────────
ENGINE_DIR = Path(__file__).parent
sys.path.insert(0, str(ENGINE_DIR))

from calculation.excel_processor_enterprise import EnterpriseExcelProcessor
from calculation.bill_processor import process_bill
from rendering.html_renderer_enterprise import (
    EnterpriseHTMLRenderer, RenderConfig, DocumentType
)
from rendering.pdf_generator import PDFGenerator
from model.document import BillDocument

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


# ── Constants ─────────────────────────────────────────────────────────────────
SHEET_WORK_ORDER   = "Work Order"
SHEET_BILL_QTY     = "Bill Quantity"
SHEET_EXTRA_ITEMS  = "Extra Items"

DOCUMENT_TYPES = [
    DocumentType.FIRST_PAGE,
    DocumentType.DEVIATION_STATEMENT,
    DocumentType.EXTRA_ITEMS,
    DocumentType.NOTE_SHEET,
    DocumentType.CERTIFICATE_II,
    DocumentType.CERTIFICATE_III,
    DocumentType.LAST_PAGE,
]


# ── Excel loading ─────────────────────────────────────────────────────────────
def load_excel_sheets(input_path: Path) -> dict:
    """Load Work Order, Bill Quantity, Extra Items sheets via EnterpriseExcelProcessor."""
    processor = EnterpriseExcelProcessor(sanitize_strings=True, validate_schemas=False)
    result = processor.process_file(
        input_path,
        sheet_names=[SHEET_WORK_ORDER, SHEET_BILL_QTY, SHEET_EXTRA_ITEMS]
    )
    if not result.success:
        logger.error(f"Excel processing failed: {result.errors}")
        raise RuntimeError(f"Excel load failed: {result.errors}")
    if result.warnings:
        for w in result.warnings:
            logger.warning(w)
    return result.data  # dict[sheet_name → DataFrame]


# ── Extract metadata from header rows ────────────────────────────────────────
_HEADER_KEY_MAP = {
    "agreement no": "agreement_no",
    "agreement no.": "agreement_no",
    "name of work": "name_of_work",
    "name of contractor or supplier": "name_of_firm",
    "name of contractor": "name_of_firm",
    "contractor": "name_of_firm",
    "work order amount rs.": "work_order_amount",
    "amount of work order": "work_order_amount",
    "date of written order to commence work": "date_commencement",
    "st. date of completion": "date_completion",
    "date of actual completion of work": "actual_completion",
}

def _extract_header_meta(header_rows: list) -> dict:
    """
    Scan the header rows (list of lists) produced by process_bill()
    and extract key metadata fields for the note_sheet template.
    Each row is a list of cell values; key is usually in one cell,
    value in the next non-empty cell on the same row.
    """
    meta = {k: "" for k in set(_HEADER_KEY_MAP.values())}
    meta["work_order_amount"] = 0.0

    for row in header_rows:
        # flatten row to non-empty strings
        cells = [str(c).strip() for c in row if str(c).strip() and str(c).strip() != "nan"]
        for i, cell in enumerate(cells):
            norm = cell.lower().rstrip(":;- ")
            field = _HEADER_KEY_MAP.get(norm)
            if field and i + 1 < len(cells):
                val = cells[i + 1]
                if field == "work_order_amount":
                    try:
                        meta[field] = float(str(val).replace(",", "").strip())
                    except ValueError:
                        pass
                else:
                    if not meta[field]:  # first match wins
                        meta[field] = val
    return meta


# ── Build BillDocument from process_bill() output ────────────────────────────
def build_document(sheets: dict, premium_percent: float, premium_type: str,
                   previous_bill_amount: float) -> BillDocument:
    """
    Call the deterministic process_bill() engine and map output to BillDocument.
    process_bill() signature is preserved exactly — no modification.
    """
    import pandas as pd

    ws_wo    = sheets.get(SHEET_WORK_ORDER)
    ws_bq    = sheets.get(SHEET_BILL_QTY)
    ws_extra = sheets.get(SHEET_EXTRA_ITEMS)

    if ws_wo is None or ws_bq is None:
        raise RuntimeError(
            f"Required sheets missing. Found: {list(sheets.keys())}"
        )

    if ws_extra is None:
        ws_extra = pd.DataFrame()

    first_page, last_page, deviation, extra_items, note_sheet = process_bill(
        ws_wo, ws_bq, ws_extra,
        premium_percent=premium_percent,
        premium_type=premium_type,
        previous_bill_amount=previous_bill_amount
    )

    header_rows = first_page.get("header", [])
    meta = _extract_header_meta(header_rows)
    extra_item_amount = float(first_page["totals"].get("extra_items_sum", 0) or 0)

    doc = BillDocument(
        header=header_rows,
        items=first_page.get("items", []),
        totals=first_page.get("totals", {}),
        deviation_items=deviation.get("items", []),
        deviation_summary=deviation.get("summary", {}),
        extra_items=extra_items.get("items", []),
        agreement_no=meta["agreement_no"],
        name_of_work=meta["name_of_work"],
        name_of_firm=meta["name_of_firm"],
        date_commencement=meta["date_commencement"],
        date_completion=meta["date_completion"],
        actual_completion=meta["actual_completion"],
        work_order_amount=meta["work_order_amount"],
        extra_item_amount=extra_item_amount,
    )
    return doc


# ── Render HTML documents ─────────────────────────────────────────────────────
def render_html(doc: BillDocument, output_dir: Path,
                template_version: str = "v1") -> list[Path]:
    """Render all document types to HTML files."""
    template_dir = ENGINE_DIR / "templates" / template_version
    if not template_dir.exists():
        raise RuntimeError(f"Template directory not found: {template_dir}")

    config = RenderConfig(
        template_dir=template_dir,
        output_dir=output_dir,
        enable_security_checks=True,
        pdf_ready=True,
    )
    renderer = EnterpriseHTMLRenderer(config)
    template_data = doc.to_template_dict()

    rendered_paths = []
    has_extra = bool(doc.extra_items)

    for doc_type in DOCUMENT_TYPES:
        # Skip extra_items and deviation if no extra items
        if doc_type == DocumentType.EXTRA_ITEMS and not has_extra:
            logger.info("Skipping extra_items — no extra items in this bill")
            continue

        filename = f"{doc_type.value}.html"
        result = renderer.render(doc_type, {"data": template_data}, filename)

        if result.success:
            rendered_paths.append(result.output_path)
            logger.info(f"✅ Rendered {doc_type.value} → {filename}")
        else:
            logger.warning(f"⚠️  Skipped {doc_type.value}: {result.errors}")

    return rendered_paths


# ── Generate PDFs ─────────────────────────────────────────────────────────────
def render_pdfs(html_paths: list[Path], output_dir: Path) -> list[Path]:
    """Convert HTML files to PDF using best available engine."""
    pdf_gen = PDFGenerator(orientation="portrait")
    pdf_paths = []

    for html_path in html_paths:
        pdf_path = output_dir / (html_path.stem + ".pdf")
        html_content = html_path.read_text(encoding="utf-8")
        try:
            engine_used = pdf_gen.generate_with_fallback(html_content, str(pdf_path))
            logger.info(f"✅ PDF [{engine_used}] → {pdf_path.name}")
            pdf_paths.append(pdf_path)
        except Exception as e:
            logger.warning(f"⚠️  PDF failed for {html_path.name}: {e}")

    return pdf_paths


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Bill Generator Engine — Excel → HTML/PDF"
    )
    parser.add_argument("input", help="Path to input Excel file (.xlsx/.xlsm/.xls)")
    parser.add_argument(
        "--template-version", default="v1", choices=["v1", "v2"],
        help="Template version to use (default: v1)"
    )
    parser.add_argument(
        "--premium-percent", type=float, default=0.0,
        help="Tender premium percentage (default: 0.0)"
    )
    parser.add_argument(
        "--premium-type", default="above", choices=["above", "below"],
        help="Premium type: above or below (default: above)"
    )
    parser.add_argument(
        "--previous-bill", type=float, default=0.0,
        help="Amount paid in previous bill (default: 0.0)"
    )
    parser.add_argument(
        "--no-pdf", action="store_true",
        help="Skip PDF generation, output HTML only"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Output directory (default: ./engine_output/<timestamp>)"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir) if args.output_dir else \
        ENGINE_DIR.parent / "engine_output" / f"{input_path.stem}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Input:    {input_path}")
    logger.info(f"Output:   {output_dir}")
    logger.info(f"Template: {args.template_version}")

    # ── Step 1: Load Excel ────────────────────────────────────────────────────
    logger.info("Step 1/4 — Loading Excel sheets...")
    try:
        sheets = load_excel_sheets(input_path)
        logger.info(f"  Loaded sheets: {list(sheets.keys())}")
    except Exception as e:
        logger.error(f"FAILED Step 1: {e}")
        sys.exit(1)

    # ── Step 2: Calculate ─────────────────────────────────────────────────────
    logger.info("Step 2/4 — Running calculation engine...")
    try:
        doc = build_document(
            sheets,
            premium_percent=args.premium_percent,
            premium_type=args.premium_type,
            previous_bill_amount=args.previous_bill,
        )
        logger.info(f"  Items: {len(doc.items)}, Extra: {len(doc.extra_items)}")
        logger.info(f"  Grand total: {doc.totals.get('grand_total', 'N/A')}")
        logger.info(f"  Payable:     {doc.totals.get('payable', 'N/A')}")
    except Exception as e:
        logger.error(f"FAILED Step 2: {e}")
        sys.exit(1)

    # ── Step 3: Render HTML ───────────────────────────────────────────────────
    logger.info("Step 3/4 — Rendering HTML templates...")
    try:
        html_paths = render_html(doc, output_dir, args.template_version)
        logger.info(f"  HTML files: {len(html_paths)}")
    except Exception as e:
        logger.error(f"FAILED Step 3: {e}")
        sys.exit(1)

    # ── Step 4: Generate PDFs ─────────────────────────────────────────────────
    pdf_paths = []
    if not args.no_pdf:
        logger.info("Step 4/4 — Generating PDFs...")
        pdf_paths = render_pdfs(html_paths, output_dir)
        logger.info(f"  PDF files: {len(pdf_paths)}")
    else:
        logger.info("Step 4/4 — PDF skipped (--no-pdf)")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("ENGINE RUN COMPLETE")
    print("="*60)
    print(f"Input:        {input_path.name}")
    print(f"Output dir:   {output_dir}")
    print(f"HTML files:   {len(html_paths)}")
    print(f"PDF files:    {len(pdf_paths)}")
    print(f"Grand total:  {doc.totals.get('grand_total', 'N/A')}")
    print(f"Net payable:  {doc.totals.get('net_payable', doc.totals.get('payable', 'N/A'))}")
    print("="*60)

    if html_paths:
        print("\nGenerated files:")
        for p in sorted(html_paths + pdf_paths):
            print(f"  {p.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
