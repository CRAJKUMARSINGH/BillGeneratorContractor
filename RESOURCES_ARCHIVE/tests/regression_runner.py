import os
import sys
import shutil
import logging
from pathlib import Path
import time

# Add paths to sys.path
root_dir = Path("c:/Users/Rajkumar/New-Folder")
unif_dir = root_dir / "BillGeneratorUnified"
engine_dir = root_dir / "engine"

sys.path.append(str(unif_dir))
sys.path.append(str(root_dir))

from BillGeneratorUnified.core.processors.excel_processor import ExcelProcessor as UnifExcelProcessor
from BillGeneratorUnified.core.generators.document_generator import DocumentGenerator as UnifDocGenerator
from BillGeneratorUnified.core.generators.pdf_generator_fixed import FixedPDFGenerator

# NEW Engine Imports
import engine.run_engine as engine_runner

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("Regression")

def run_unif(excel_path: Path, output_base: Path):
    """Run the original Unified engine"""
    try:
        processor = UnifExcelProcessor()
        data = processor.process_excel(excel_path)
        doc_gen = UnifDocGenerator(data)
        docs = doc_gen.generate_all_documents()
        
        pdf_gen = FixedPDFGenerator(margin_mm=10)
        
        unif_out = output_base / "UNIF"
        unif_out.mkdir(parents=True, exist_ok=True)
        
        results = {}
        for name, html in docs.items():
            if not html: continue
            safe_name = name.lower().replace(" ", "_").replace("..", ".")
            pdf_path = unif_out / f"{safe_name}.pdf"
            html_path = unif_out / f"{safe_name}.html"
            
            html_path.write_text(html, encoding="utf-8")
            pdf_bytes = pdf_gen.auto_convert(html, doc_name=name)
            pdf_path.write_bytes(pdf_bytes)
            results[name] = {"pdf": pdf_path, "size": len(pdf_bytes)}
            
        return results
    except Exception as e:
        logger.error(f"UNIF failed for {excel_path.name}: {e}")
        return None

def run_consolidated(excel_path: Path, output_base: Path):
    """Run the new Consolidated engine"""
    try:
        cons_out = output_base / "CONS"
        cons_out.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Load Excel
        sheets = engine_runner.load_excel_sheets(excel_path)
        
        # Step 2: Calculate
        doc = engine_runner.build_document(
            sheets,
            premium_percent=0.0,
            premium_type="above",
            previous_bill_amount=0.0,
        )
        
        # Step 3: Render HTML
        html_paths = engine_runner.render_html(doc, cons_out, "v1")
        
        # Step 4: Render PDFs
        pdf_paths = engine_runner.render_pdfs(html_paths, cons_out)
        
        results = {}
        for p in pdf_paths:
            # Map back to template names for comparison
            # names: first_page, deviation_statement, extra_items, note_sheet, certificate_ii, certificate_iii
            results[p.stem] = {"pdf": p, "size": p.stat().st_size}
            
        return results
    except Exception as e:
        logger.error(f"CONS failed for {excel_path.name}: {e}")
        return None

def main():
    test_files_dir = unif_dir / "TEST_INPUT_FILES"
    regression_dir = root_dir / "REGRESSION_RESULTS"
    regression_dir.mkdir(exist_ok=True)
    
    excel_files = list(test_files_dir.glob("*.xlsx"))[:9] # Top 9
    
    print(f"Starting Regression on {len(excel_files)} files...")
    print(f"Templates: 6")
    
    report = []
    
    for excel_path in excel_files:
        print(f"\nProcessing: {excel_path.name}")
        case_dir = regression_dir / excel_path.stem
        case_dir.mkdir(exist_ok=True)
        
        unif_res = run_unif(excel_path, case_dir)
        cons_res = run_consolidated(excel_path, case_dir)
        
        if unif_res and cons_res:
            print(f"  OK: {excel_path.name}")
            
            # Mapping from UNIF to CONS names
            mapping = {
                "First Page Summary": "first_page",
                "Deviation Statement": "deviation_statement",
                "BILL SCRUTINY SHEET": "note_sheet",
                "Certificate II": "certificate_ii",
                "Certificate III": "certificate_iii",
                "Extra Items Statement": "extra_items"
            }
            
            for u_name, c_name in mapping.items():
                if u_name in unif_res and c_name in cons_res:
                    u_size = unif_res[u_name]['size']
                    c_size = cons_res[c_name]['size']
                    diff = abs(u_size - c_size)
                    p_diff = (diff / u_size * 100) if u_size > 0 else 0
                    print(f"    - {u_name} vs {c_name}: UNIF={u_size} CONS={c_size} Diff={diff}")
                    report.append(f"{excel_path.name},{u_name},{u_size},{c_size},{diff},{p_diff:.1f}")
                else:
                    logger.warning(f"Missing {u_name} or {c_name} in results")
        else:
            print(f"  FAILED: {excel_path.name}")
            report.append(f"{excel_path.name},FAILED,0,0,0,0")

    (regression_dir / "summary.csv").write_text("File,Template,UnifSize,ConsSize,Diff,PercentDiff\n" + "\n".join(report))
    print(f"\nRegression Complete. Summary saved to {regression_dir / 'summary.csv'}")

if __name__ == "__main__":
    main()
