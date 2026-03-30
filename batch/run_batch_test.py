#!/usr/bin/env python3
"""
Comprehensive Batch Test Runner

This script runs a complete batch test of all 24 synthetic input files.
It processes both individually and in batch mode, then generates detailed reports.

Usage:
    python batch\run_batch_test.py
"""
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

# Setup paths - add parent directory to path for imports
root_dir = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(root_dir))
os.environ.setdefault('ALLOW_INSECURE_SECRET', '1')

from batch.input_manager import BrilliantBatchInputManager
from batch.processor import BrilliantBatchProcessor


async def run_individual_tests():
    """Test each input file individually."""
    print("\n" + "=" * 70)
    print("INDIVIDUAL FILE TESTING")
    print("=" * 70)
    
    mgr = BrilliantBatchInputManager()
    pending_files = mgr.get_pending_files()
    
    if not pending_files:
        print("No pending files found. Please run registration first.")
        return
    
    processor = BrilliantBatchProcessor(mgr)
    
    print(f"\nTesting {len(pending_files)} files individually...\n")
    
    results = []
    for i, file_meta in enumerate(pending_files, 1):
        extra_marker = " [WITH EXTRA]" if file_meta.has_extra_items else ""
        print(f"[{i}/{len(pending_files)}] Testing: {file_meta.filename}{extra_marker}")
        
        try:
            success = await processor._process_single_file(
                file_meta,
                template_version="v2",
                generate_pdf=True
            )
            
            if success:
                print(f"  [PASS]")
                results.append(("PASS", file_meta.filename, None))
            else:
                print(f"  [FAIL]")
                results.append(("FAIL", file_meta.filename, "Processing failed"))
                
        except Exception as e:
            print(f"  [ERROR] {e}")
            results.append(("FAIL", file_meta.filename, str(e)))
    
    # Summary
    passed = sum(1 for r in results if r[0] == "PASS")
    failed = len(results) - passed
    
    print(f"\n{'=' * 70}")
    print(f"INDIVIDUAL TEST SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    
    if failed > 0:
        print(f"\nFailed tests:")
        for status, filename, error in results:
            if status == "FAIL":
                print(f"  - {filename}: {error}")
    
    return results


async def run_batch_processing():
    """Process all pending files in batch mode."""
    print("\n" + "=" * 70)
    print("BATCH PROCESSING MODE")
    print("=" * 70)
    
    mgr = BrilliantBatchInputManager()
    processor = BrilliantBatchProcessor(mgr)
    
    # Reset any processed/failed files back to pending for batch run
    for filename, meta in mgr.metadata.get("files", {}).items():
        if meta.get("status") in ["failed", "completed"]:
            # This correctly moves the file back to the pending directory
            mgr.update_file_status(filename, "pending", error_message=None)
    
    print("\nStarting batch processing with max 4 concurrent jobs...")
    
    start_time = datetime.now()
    
    batch_results = await processor.process_batch(
        max_concurrent=4,
        template_version="v2",
        generate_pdf=True
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n{'=' * 70}")
    print(f"BATCH PROCESSING RESULTS")
    print(f"{'=' * 70}")
    print(f"Total Files: {batch_results['total']}")
    print(f"Completed: {batch_results['completed']}")
    print(f"Failed: {batch_results['failed']}")
    print(f"Duration: {duration:.2f} seconds")
    
    # Generate final report
    report_path = root_dir / "backend" / "outputs" / f"batch_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    final_report = processor.generate_batch_report(report_path)
    
    print(f"\n[REPORT] Final report saved to: {report_path}")
    print("\n" + "=" * 70)
    
    return batch_results


def main():
    print("\n" + "=" * 70)
    print("COMPREHENSIVE BATCH TEST SUITE")
    print("Brilliant Batch Input Management System")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run individual tests
    individual_results = asyncio.run(run_individual_tests())
    
    # Run batch processing
    batch_results = asyncio.run(run_batch_processing())
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL COMPREHENSIVE SUMMARY")
    print("=" * 70)
    
    mgr = BrilliantBatchInputManager()
    stats = mgr.metadata.get("stats", {})
    
    print(f"Total Registered Files: {stats.get('total', 0)}")
    print(f"Successfully Completed: {stats.get('completed', 0)}")
    print(f"Failed: {stats.get('failed', 0)}")
    
    # Show output location
    output_dir = root_dir / "backend" / "outputs"
    print(f"\n[INFO] Generated outputs located in: {output_dir}")
    
    # List generated PDFs
    pdf_files = list(output_dir.glob("*/*.pdf"))
    print(f"\n[INFO] Generated {len(pdf_files)} PDF files")
    
    print("\n" + "=" * 70)
    print("[SUCCESS] BATCH TESTING COMPLETE")
    print("=" * 70)
    
    return {
        "individual": individual_results,
        "batch": batch_results,
        "stats": stats
    }


if __name__ == "__main__":
    results = main()
