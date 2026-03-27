"""
Enhanced batch processing for the Stream Bill Generator
This script provides improved batch processing capabilities.
"""
import os
import pandas as pd
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Import our modular components
from core.computations.bill_processor import process_bill
from exports.renderers import generate_pdf, create_word_doc, merge_pdfs, create_zip_archive
from exports.advanced_formats import export_bill_data
from scripts.monitoring import log_performance, log_event

def process_single_file(file_path: str, 
                       output_dir: str,
                       premium_percent: float = 5.0,
                       premium_type: str = "above") -> Dict[str, Any]:
    """
    Process a single Excel file
    
    Args:
        file_path (str): Path to the Excel file
        output_dir (str): Directory for output files
        premium_percent (float): Tender premium percentage
        premium_type (str): Premium type ("above" or "below")
        
    Returns:
        Dict[str, Any]: Processing results
    """
    start_time = time.time()
    result = {
        "file": file_path,
        "status": "failed",
        "error": None,
        "output_files": [],
        "processing_time": 0
    }
    
    try:
        # Read Excel file
        xl_file = pd.ExcelFile(file_path)
        sheet_names = xl_file.sheet_names
        
        # Check required sheets
        required_sheets = ["Work Order", "Bill Quantity", "Extra Items"]
        missing_sheets = [sheet for sheet in required_sheets if sheet not in sheet_names]
        
        if missing_sheets:
            raise ValueError(f"Missing required sheets: {', '.join(missing_sheets)}")
        
        # Read sheets
        ws_wo = pd.read_excel(xl_file, "Work Order", header=None)
        ws_bq = pd.read_excel(xl_file, "Bill Quantity", header=None)
        ws_extra = pd.read_excel(xl_file, "Extra Items", header=None)
        
        # Process bill
        first_page_data, last_page_data, deviation_data, extra_items_data, note_sheet_data = process_bill(
            ws_wo, ws_bq, ws_extra, premium_percent, premium_type
        )
        
        # Create output directory for this file
        file_name = Path(file_path).stem
        file_output_dir = os.path.join(output_dir, file_name)
        os.makedirs(file_output_dir, exist_ok=True)
        
        # Generate PDFs
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        
        pdf_files = []
        
        # Generate First Page
        first_page_pdf = generate_pdf(
            "First Page", 
            first_page_data, 
            "landscape", 
            template_dir, 
            file_output_dir
        )
        pdf_files.append(first_page_pdf)
        
        # Generate Last Page
        last_page_pdf = generate_pdf(
            "Last Page", 
            last_page_data, 
            "portrait", 
            template_dir, 
            file_output_dir
        )
        pdf_files.append(last_page_pdf)
        
        # Generate Deviation Statement
        deviation_pdf = generate_pdf(
            "Deviation Statement", 
            deviation_data, 
            "landscape", 
            template_dir, 
            file_output_dir
        )
        pdf_files.append(deviation_pdf)
        
        # Generate Extra Items
        extra_items_pdf = generate_pdf(
            "Extra Items", 
            extra_items_data, 
            "landscape", 
            template_dir, 
            file_output_dir
        )
        pdf_files.append(extra_items_pdf)
        
        # Generate Note Sheet
        note_sheet_pdf = generate_pdf(
            "Note Sheet", 
            note_sheet_data, 
            "portrait", 
            template_dir, 
            file_output_dir
        )
        pdf_files.append(note_sheet_pdf)
        
        # Create Word documents
        word_files = []
        
        first_page_doc = os.path.join(file_output_dir, "first_page.docx")
        create_word_doc("First Page", first_page_data, first_page_doc)
        word_files.append(first_page_doc)
        
        last_page_doc = os.path.join(file_output_dir, "last_page.docx")
        create_word_doc("Last Page", last_page_data, last_page_doc)
        word_files.append(last_page_doc)
        
        deviation_doc = os.path.join(file_output_dir, "deviation_statement.docx")
        create_word_doc("Deviation Statement", deviation_data, deviation_doc)
        word_files.append(deviation_doc)
        
        extra_items_doc = os.path.join(file_output_dir, "extra_items.docx")
        create_word_doc("Extra Items", extra_items_data, extra_items_doc)
        word_files.append(extra_items_doc)
        
        note_sheet_doc = os.path.join(file_output_dir, "note_sheet.docx")
        create_word_doc("Note Sheet", note_sheet_data, note_sheet_doc)
        word_files.append(note_sheet_doc)
        
        # Generate advanced formats
        advanced_files = export_bill_data(
            first_page_data, last_page_data, deviation_data, 
            extra_items_data, note_sheet_data, file_output_dir
        )
        
        # Merge all PDFs
        merged_pdf = os.path.join(file_output_dir, "complete_bill.pdf")
        merge_pdfs(pdf_files, merged_pdf)
        
        # Create ZIP archive
        all_files = pdf_files + word_files + advanced_files + [merged_pdf]
        zip_path = os.path.join(file_output_dir, f"{file_name}_documents.zip")
        create_zip_archive(all_files, zip_path)
        
        result["status"] = "success"
        result["output_files"] = all_files + [zip_path]
        
        # Log performance
        processing_time = time.time() - start_time
        result["processing_time"] = processing_time
        log_performance("batch_file_processing", processing_time, {
            "file": file_path,
            "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
        })
        
        log_event("batch_file_processed", {
            "file": file_path,
            "status": "success",
            "processing_time": processing_time
        })
        
    except Exception as e:
        result["error"] = str(e)
        result["processing_time"] = time.time() - start_time
        log_event("batch_file_processed", {
            "file": file_path,
            "status": "failed",
            "error": str(e),
            "processing_time": result["processing_time"]
        })
        
    return result

def process_batch(input_dir: str, 
                 output_dir: str,
                 premium_percent: float = 5.0,
                 premium_type: str = "above",
                 max_workers: int = 4) -> List[Dict[str, Any]]:
    """
    Process multiple Excel files in batch
    
    Args:
        input_dir (str): Directory containing Excel files
        output_dir (str): Directory for output files
        premium_percent (float): Tender premium percentage
        premium_type (str): Premium type ("above" or "below")
        max_workers (int): Maximum number of concurrent workers
        
    Returns:
        List[Dict[str, Any]]: List of processing results
    """
    # Find Excel files
    excel_files = []
    for file_path in Path(input_dir).rglob("*.xlsx"):
        excel_files.append(str(file_path))
    for file_path in Path(input_dir).rglob("*.xls"):
        excel_files.append(str(file_path))
    
    if not excel_files:
        print("No Excel files found in the input directory")
        return []
    
    print(f"Found {len(excel_files)} Excel files to process")
    
    # Process files concurrently
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(
                process_single_file, 
                file_path, 
                output_dir, 
                premium_percent, 
                premium_type
            ): file_path for file_path in excel_files
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                results.append(result)
                if result["status"] == "success":
                    print(f"✓ Processed {file_path}")
                else:
                    print(f"✗ Failed to process {file_path}: {result['error']}")
            except Exception as e:
                result = {
                    "file": file_path,
                    "status": "failed",
                    "error": str(e),
                    "output_files": [],
                    "processing_time": 0
                }
                results.append(result)
                print(f"✗ Error processing {file_path}: {e}")
    
    return results

def generate_batch_report(results: List[Dict[str, Any]], report_path: str) -> None:
    """
    Generate a batch processing report
    
    Args:
        results (List[Dict[str, Any]]): Processing results
        report_path (str): Path where report should be saved
    """
    try:
        # Calculate statistics
        total_files = len(results)
        successful_files = sum(1 for r in results if r["status"] == "success")
        failed_files = total_files - successful_files
        total_processing_time = sum(r["processing_time"] for r in results)
        avg_processing_time = total_processing_time / total_files if total_files > 0 else 0
        
        # Create report
        report_data = {
            "summary": {
                "total_files": total_files,
                "successful_files": successful_files,
                "failed_files": failed_files,
                "success_rate": successful_files / total_files if total_files > 0 else 0,
                "total_processing_time": total_processing_time,
                "average_processing_time": avg_processing_time
            },
            "files": results
        }
        
        # Save as JSON
        import json
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"Batch report saved to {report_path}")
        
    except Exception as e:
        print(f"Error generating batch report: {e}")

if __name__ == "__main__":
    # Example usage
    print("Enhanced Batch Processor")
    print("Usage: Call process_batch('input_directory', 'output_directory')")