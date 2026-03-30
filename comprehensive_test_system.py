#!/usr/bin/env python3
"""
Comprehensive Test System for Bill Generator
Tests all available Excel files through the complete pipeline
Validates PDF outputs, extra items handling, and all 6 templates
"""
import os
import sys
import json
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Add project root to path
ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engine"))

# Set environment for testing
os.environ.setdefault("ALLOW_INSECURE_SECRET", "1")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Test directories
TEST_DIRS = [
    ROOT / "RESOURCES_ARCHIVE" / "TEST_INPUT_FILES",
    ROOT / "tests" / "SYNTHETIC_INPUTS",
    ROOT / "REF_APPS_ARCHIVE" / "BillGeneratorUnified" / "TEST_INPUT_FILES",
]

# Output directories
OUTPUT_BASE = ROOT / "TEST_OUTPUTS"
REPORT_DIR = ROOT / "TEST_REPORTS"

# Expected templates for each document type
EXPECTED_TEMPLATES = {
    "NO_EXTRA": [
        "first_page.html",
        "deviation_statement.html", 
        "note_sheet.html",
        "certificate_ii.html",
        "certificate_iii.html",
        "last_page.html"
    ],
    "WITH_EXTRA": [
        "first_page.html",
        "deviation_statement.html",
        "extra_items.html",
        "note_sheet.html", 
        "certificate_ii.html",
        "certificate_iii.html",
        "last_page.html"
    ]
}

class TestResult:
    """Container for test results"""
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_name = file_path.name
        self.has_extra_items = self._classify_file()
        self.output_dir = OUTPUT_BASE / file_path.stem
        
        # Test results
        self.parse_success = False
        self.calculation_success = False
        self.html_generation_success = False
        self.pdf_generation_success = False
        
        # Counts
        self.html_count = 0
        self.pdf_count = 0
        self.expected_html_count = len(EXPECTED_TEMPLATES["WITH_EXTRA" if self.has_extra_items else "NO_EXTRA"])
        
        # Data validation
        self.grand_total = 0.0
        self.payable_amount = 0.0
        self.extra_items_count = 0
        self.extra_items_in_first_page = False
        self.extra_items_in_deviation = False
        self.extra_items_in_note_sheet = False
        
        # File sizes
        self.pdf_sizes = {}
        self.html_sizes = {}
        
        # Errors and warnings
        self.errors = []
        self.warnings = []
        
    def _classify_file(self) -> bool:
        """Classify if file has extra items based on filename"""
        name = self.file_name.lower()
        extra_indicators = ["extra", "vid", "wextra", "with", "9th", "amli"]
        no_extra_indicators = ["noextra", "n-extra"]
        
        # Check for explicit no-extra indicators first
        if any(indicator in name for indicator in no_extra_indicators):
            return False
            
        # Check for extra indicators
        return any(indicator in name for indicator in extra_indicators)
    
    def is_success(self) -> bool:
        """Check if test passed all criteria"""
        return (
            self.parse_success and
            self.calculation_success and
            self.html_generation_success and
            self.pdf_generation_success and
            self.html_count >= self.expected_html_count and
            self.pdf_count >= self.expected_html_count and
            len(self.errors) == 0
        )

class ComprehensiveTestSystem:
    """Main test system class"""
    
    def __init__(self):
        self.test_files = []
        self.results = []
        self.start_time = datetime.now()
        
        # Create output directories
        OUTPUT_BASE.mkdir(exist_ok=True)
        REPORT_DIR.mkdir(exist_ok=True)
        
    def discover_test_files(self) -> List[Path]:
        """Discover all Excel test files"""
        files = []
        seen_names = set()
        
        for test_dir in TEST_DIRS:
            if not test_dir.exists():
                logger.warning(f"Test directory not found: {test_dir}")
                continue
                
            for excel_file in sorted(test_dir.glob("*.xlsx")):
                # Skip temporary files
                if excel_file.name.startswith("~$"):
                    continue
                    
                # Avoid duplicates
                if excel_file.name not in seen_names:
                    files.append(excel_file)
                    seen_names.add(excel_file.name)
                    
        logger.info(f"Discovered {len(files)} unique test files")
        return files
    
    def test_single_file(self, file_path: Path) -> TestResult:
        """Test a single Excel file through the complete pipeline"""
        result = TestResult(file_path)
        
        try:
            logger.info(f"Testing: {file_path.name}")
            
            # Step 1: Parse Excel file
            result.parse_success = self._test_parsing(file_path, result)
            if not result.parse_success:
                return result
                
            # Step 2: Test calculation engine
            result.calculation_success = self._test_calculation(file_path, result)
            if not result.calculation_success:
                return result
                
            # Step 3: Test HTML generation
            result.html_generation_success = self._test_html_generation(file_path, result)
            
            # Step 4: Test PDF generation
            result.pdf_generation_success = self._test_pdf_generation(result)
            
            # Step 5: Validate extra items handling
            self._validate_extra_items_handling(result)
            
        except Exception as e:
            result.errors.append(f"Unexpected error: {str(e)}")
            logger.error(f"Error testing {file_path.name}: {e}")
            
        return result
    
    def _test_parsing(self, file_path: Path, result: TestResult) -> bool:
        """Test Excel parsing using the ingestion pipeline"""
        try:
            from ingestion.excel_parser import parse_excel_to_raw
            
            # Use the existing ingestion pipeline
            raw_data = parse_excel_to_raw(str(file_path))
            
            if not raw_data:
                result.errors.append("No data extracted from Excel file")
                return False
                
            return True
            
        except Exception as e:
            result.errors.append(f"Parsing failed: {str(e)}")
            return False
    
    def _test_calculation(self, file_path: Path, result: TestResult) -> bool:
        """Test bill calculation"""
        try:
            from ingestion.excel_parser import parse_excel_to_raw
            from ingestion.normalizer import normalize_to_unified_model
            from engine.calculation.bill_processor import process_unified_bill
            
            # Parse and normalize
            raw_data = parse_excel_to_raw(str(file_path))
            unified_doc = normalize_to_unified_model(raw_data, source_type="excel")
            
            # Calculate
            calculated_data = process_unified_bill(unified_doc)
            
            # Extract key metrics
            result.grand_total = calculated_data.get("totals", {}).get("grand_total", 0)
            result.payable_amount = calculated_data.get("totals", {}).get("payable", 0)
            result.extra_items_count = len(calculated_data.get("extra_items", {}).get("items", []))
            
            return True
            
        except Exception as e:
            result.errors.append(f"Calculation failed: {str(e)}")
            return False
    
    def _test_html_generation(self, file_path: Path, result: TestResult) -> bool:
        """Test HTML generation for all templates"""
        try:
            from ingestion.excel_parser import parse_excel_to_raw
            from ingestion.normalizer import normalize_to_unified_model
            from engine.calculation.bill_processor import process_unified_bill
            from engine.rendering.html_renderer_enterprise import (
                EnterpriseHTMLRenderer, RenderConfig, DocumentType
            )
            
            # Parse, normalize, and calculate
            raw_data = parse_excel_to_raw(str(file_path))
            unified_doc = normalize_to_unified_model(raw_data, source_type="excel")
            calculated_data = process_unified_bill(unified_doc)
            
            # Setup renderer
            config = RenderConfig(
                template_dir=ROOT / "engine" / "templates" / "v2",
                output_dir=result.output_dir
            )
            renderer = EnterpriseHTMLRenderer(config)
            
            # Generate all templates
            expected_templates = EXPECTED_TEMPLATES["WITH_EXTRA" if result.has_extra_items else "NO_EXTRA"]
            
            for template_name in expected_templates:
                doc_type = DocumentType(template_name.replace(".html", ""))
                render_result = renderer.render(
                    doc_type,
                    {"data": calculated_data},
                    template_name
                )
                
                if render_result.success:
                    result.html_count += 1
                    if render_result.output_path:
                        result.html_sizes[template_name] = render_result.output_path.stat().st_size
                        
                    # Check extra items in specific templates
                    if result.has_extra_items and render_result.html_content:
                        if "first_page" in template_name and "extra" in render_result.html_content.lower():
                            result.extra_items_in_first_page = True
                        if "deviation" in template_name and "extra" in render_result.html_content.lower():
                            result.extra_items_in_deviation = True
                        if "note_sheet" in template_name and "extra" in render_result.html_content.lower():
                            result.extra_items_in_note_sheet = True
                else:
                    result.errors.extend(render_result.errors)
            
            return result.html_count > 0
            
        except Exception as e:
            result.errors.append(f"HTML generation failed: {str(e)}")
            return False
    
    def _test_pdf_generation(self, result: TestResult) -> bool:
        """Test PDF generation from HTML files"""
        try:
            from engine.rendering.pdf_generator import PDFGenerator
            
            pdf_gen = PDFGenerator()
            
            # Generate PDFs from HTML files
            for html_file in result.output_dir.glob("*.html"):
                pdf_path = result.output_dir / (html_file.stem + ".pdf")
                
                success = pdf_gen.generate_pdf(
                    html_file.read_text(encoding="utf-8"),
                    str(pdf_path)
                )
                
                if success and pdf_path.exists() and pdf_path.stat().st_size > 0:
                    result.pdf_count += 1
                    result.pdf_sizes[pdf_path.name] = pdf_path.stat().st_size
                else:
                    result.errors.append(f"PDF generation failed for {html_file.name}")
            
            return result.pdf_count > 0
            
        except Exception as e:
            result.errors.append(f"PDF generation failed: {str(e)}")
            return False
    
    def _validate_extra_items_handling(self, result: TestResult):
        """Validate that extra items are properly handled"""
        if not result.has_extra_items:
            return
            
        # Check that extra items appear in the right places
        if result.extra_items_count == 0:
            result.warnings.append("File classified as having extra items but none found")
            
        if not result.extra_items_in_first_page:
            result.warnings.append("Extra items not found in first page")
            
        if not result.extra_items_in_note_sheet:
            result.warnings.append("Extra items not found in note sheet")
    
    def run_all_tests(self) -> List[TestResult]:
        """Run tests on all discovered files"""
        self.test_files = self.discover_test_files()
        self.results = []
        
        logger.info(f"Starting comprehensive test run on {len(self.test_files)} files")
        
        for i, file_path in enumerate(self.test_files, 1):
            logger.info(f"Progress: {i}/{len(self.test_files)} - {file_path.name}")
            result = self.test_single_file(file_path)
            self.results.append(result)
            
            # Print immediate result
            status = "✅ PASS" if result.is_success() else "❌ FAIL"
            extra_flag = "[EXTRA]" if result.has_extra_items else "[NO-EXTRA]"
            print(f"  {status} {extra_flag} {file_path.name}")
            
            if result.errors:
                for error in result.errors[:3]:  # Show first 3 errors
                    print(f"    ERROR: {error}")
        
        return self.results
    
    def generate_report(self):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Summary statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.is_success())
        failed_tests = total_tests - passed_tests
        
        with_extra = sum(1 for r in self.results if r.has_extra_items)
        without_extra = total_tests - with_extra
        
        # Generate detailed report
        report_path = REPORT_DIR / f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Comprehensive Test Report\n\n")
            f.write(f"**Generated:** {end_time.strftime('%Y-%m-%d %H:%M:%S')}  \n")
            f.write(f"**Duration:** {duration.total_seconds():.1f} seconds  \n")
            f.write(f"**Total Files:** {total_tests}  \n")
            f.write(f"**Passed:** {passed_tests}  \n")
            f.write(f"**Failed:** {failed_tests}  \n")
            f.write(f"**Success Rate:** {(passed_tests/total_tests*100):.1f}%  \n\n")
            
            f.write("## Summary by Type\n\n")
            f.write(f"- **With Extra Items:** {with_extra} files\n")
            f.write(f"- **Without Extra Items:** {without_extra} files\n\n")
            
            f.write("## Detailed Results\n\n")
            f.write("| File | Type | Status | HTML | PDF | Total | Payable | Errors |\n")
            f.write("|------|------|--------|------|-----|-------|---------|--------|\n")
            
            for result in self.results:
                status = "✅ PASS" if result.is_success() else "❌ FAIL"
                file_type = "WITH_EXTRA" if result.has_extra_items else "NO_EXTRA"
                error_count = len(result.errors)
                
                f.write(f"| {result.file_name} | {file_type} | {status} | "
                       f"{result.html_count}/{result.expected_html_count} | "
                       f"{result.pdf_count}/{result.expected_html_count} | "
                       f"{result.grand_total:,.0f} | {result.payable_amount:,.0f} | "
                       f"{error_count} |\n")
            
            # Failed tests details
            failed_results = [r for r in self.results if not r.is_success()]
            if failed_results:
                f.write("\n## Failed Tests Details\n\n")
                for result in failed_results:
                    f.write(f"### {result.file_name}\n\n")
                    f.write(f"**Type:** {('WITH_EXTRA' if result.has_extra_items else 'NO_EXTRA')}  \n")
                    f.write(f"**HTML Generated:** {result.html_count}/{result.expected_html_count}  \n")
                    f.write(f"**PDF Generated:** {result.pdf_count}/{result.expected_html_count}  \n")
                    
                    if result.errors:
                        f.write("**Errors:**\n")
                        for error in result.errors:
                            f.write(f"- {error}\n")
                    
                    if result.warnings:
                        f.write("**Warnings:**\n")
                        for warning in result.warnings:
                            f.write(f"- {warning}\n")
                    f.write("\n")
            
            # PDF Size Analysis
            f.write("## PDF Size Analysis\n\n")
            f.write("| File | Template | Size (KB) | Status |\n")
            f.write("|------|----------|-----------|--------|\n")
            
            for result in self.results:
                for pdf_name, size in result.pdf_sizes.items():
                    size_kb = size / 1024
                    status = "✅ OK" if size_kb > 1 else "⚠️ Small"
                    f.write(f"| {result.file_name} | {pdf_name} | {size_kb:.1f} | {status} |\n")
        
        logger.info(f"Report generated: {report_path}")
        return report_path

def main():
    """Main entry point"""
    print("🧪 Starting Comprehensive Test System")
    print("=" * 60)
    
    test_system = ComprehensiveTestSystem()
    results = test_system.run_all_tests()
    report_path = test_system.generate_report()
    
    # Summary
    total = len(results)
    passed = sum(1 for r in results if r.is_success())
    failed = total - passed
    
    print("\n" + "=" * 60)
    print(f"🎯 TEST SUMMARY")
    print(f"   Total: {total}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Success Rate: {(passed/total*100):.1f}%")
    print(f"📄 Report: {report_path}")
    print("=" * 60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())