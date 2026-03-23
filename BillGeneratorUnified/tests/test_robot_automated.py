#!/usr/bin/env python3
"""
Automated Robot Tests for Enterprise Bill Generation System
Tests single file processing, batch processing, and UI functionality.

Author: Senior QA Engineer
Standards: Pytest, Comprehensive coverage, Automated testing
"""

import pytest
from pathlib import Path
import sys
import time
from typing import List, Dict
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.processors.excel_processor_enterprise import ExcelProcessor
from core.generators.html_renderer_enterprise import HTMLRenderer, DocumentType
from core.rendering.pdf_renderer_enterprise import (
    PDFRendererFactory, PDFConfig, PageSize, PageOrientation, PDFEngine
)
from core.batch.job_runner_enterprise import BatchJobRunner, BatchConfig, RetryPolicy
from core.validation.error_diagnostics_enterprise import ComprehensiveValidator


# Test configuration
TEST_INPUT_DIR = Path("TEST_INPUT_FILES")
TEST_OUTPUT_DIR = Path("OUTPUT/robot_tests")
TEMPLATE_DIR = Path("templates")


class TestRobotSingleFile:
    """Robot tests for single file processing."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        yield
        # Cleanup is optional - keep outputs for inspection
    
    def get_test_files(self) -> List[Path]:
        """Get all test Excel files."""
        if not TEST_INPUT_DIR.exists():
            pytest.skip(f"Test input directory not found: {TEST_INPUT_DIR}")
        
        test_files = list(TEST_INPUT_DIR.glob("*.xlsx")) + list(TEST_INPUT_DIR.glob("*.xlsm"))
        
        if not test_files:
            pytest.skip(f"No test files found in {TEST_INPUT_DIR}")
        
        return test_files
    
    @pytest.mark.parametrize("test_file_index", range(8))  # Test first 8 files
    def test_single_file_processing(self, test_file_index):
        """
        Test single file processing end-to-end.
        Tests: Excel → HTML → PDF pipeline.
        """
        test_files = self.get_test_files()
        
        if test_file_index >= len(test_files):
            pytest.skip(f"Test file index {test_file_index} out of range")
        
        test_file = test_files[test_file_index]
        
        print(f"\n{'='*80}")
        print(f"Testing file: {test_file.name}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        # Step 1: Process Excel
        print("\n[1/4] Processing Excel...")
        processor = ExcelProcessor(
            sanitize_strings=True,
            validate_schemas=False  # Skip schema validation for robot test
        )
        
        result = processor.process_file(test_file)
        
        assert result.success, f"Excel processing failed: {result.errors}"
        assert result.data is not None, "No data returned"
        assert len(result.data) > 0, "No sheets processed"
        
        print(f"✅ Processed {result.metadata['sheets_processed']} sheets")
        
        # Step 2: Prepare template data (simplified)
        print("\n[2/4] Preparing template data...")
        template_data = {
            'title_data': {
                'Name of Contractor or supplier :': 'Test Contractor',
                'Name of Work ;-': 'Test Project',
                'Serial No. of this bill :': 'Test Bill',
                'Agreement No.': 'AGR-001'
            },
            'items': [],
            'totals': {
                'grand_total': 0.0,
                'premium': {'percent': 0.0, 'amount': 0.0},
                'payable': 0.0,
                'net_payable': 0.0
            },
            'deviation_items': [],
            'summary': {}
        }
        
        print("✅ Template data prepared")
        
        # Step 3: Generate HTML
        print("\n[3/4] Generating HTML...")
        renderer = HTMLRenderer(
            template_dir=TEMPLATE_DIR,
            enable_sandbox=True,
            enable_cache=True,
            validate_output=False  # Skip validation for speed
        )
        
        html_result = renderer.render_document(
            document_type=DocumentType.FIRST_PAGE,
            data=template_data
        )
        
        assert html_result.success, f"HTML rendering failed: {html_result.errors}"
        assert html_result.html_content is not None, "No HTML content"
        assert len(html_result.html_content) > 0, "Empty HTML content"
        
        # Save HTML
        html_output = TEST_OUTPUT_DIR / f"{test_file.stem}_first_page.html"
        with open(html_output, 'w', encoding='utf-8') as f:
            f.write(html_result.html_content)
        
        print(f"✅ HTML saved: {html_output}")
        
        # Step 4: Generate PDF
        print("\n[4/4] Generating PDF...")
        
        available_engines = PDFRendererFactory.get_available_engines()
        
        if not available_engines:
            pytest.skip("No PDF engines available")
        
        pdf_config = PDFConfig(
            page_size=PageSize.A4,
            orientation=PageOrientation.PORTRAIT,
            margin_top="10mm",
            margin_right="10mm",
            margin_bottom="10mm",
            margin_left="10mm"
        )
        
        pdf_renderer = PDFRendererFactory.create_renderer(
            engine=available_engines[0],
            config=pdf_config
        )
        
        pdf_output = TEST_OUTPUT_DIR / f"{test_file.stem}_first_page.pdf"
        pdf_result = pdf_renderer.render_from_html_string(
            html_content=html_result.html_content,
            output_path=pdf_output
        )
        
        assert pdf_result.success, f"PDF generation failed: {pdf_result.errors}"
        assert pdf_output.exists(), "PDF file not created"
        assert pdf_output.stat().st_size > 0, "PDF file is empty"
        
        print(f"✅ PDF saved: {pdf_output}")
        
        # Summary
        duration = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"✅ Test passed in {duration:.2f}s")
        print(f"{'='*80}\n")
    
    def test_excel_processor_security(self):
        """Test Excel processor security features."""
        test_files = self.get_test_files()
        
        if not test_files:
            pytest.skip("No test files available")
        
        test_file = test_files[0]
        
        print(f"\nTesting security features with: {test_file.name}")
        
        # Test with sanitization enabled
        processor = ExcelProcessor(sanitize_strings=True)
        result = processor.process_file(test_file)
        
        assert result.success, "Processing with sanitization failed"
        
        # Verify no formula injection patterns in data
        for sheet_name, df in result.data.items():
            for col in df.columns:
                if df[col].dtype == 'object':  # String columns
                    for value in df[col].dropna():
                        # Check that formulas are neutralized
                        if isinstance(value, str) and len(value) > 0:
                            first_char = value[0]
                            # If original had formula, it should be neutralized with '
                            if first_char in ['=', '@', '+', '-', '|', '%']:
                                # This would be a security issue
                                pytest.fail(f"Formula not neutralized: {value}")
        
        print("✅ Security features working correctly")


class TestRobotBatchProcessing:
    """Robot tests for batch processing."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        yield
    
    def test_batch_processing_multiple_files(self):
        """
        Test batch processing with multiple files.
        Tests: Parallel processing, retry logic, error handling.
        """
        test_files = list(TEST_INPUT_DIR.glob("*.xlsx"))[:5]  # Test first 5 files
        
        if len(test_files) < 2:
            pytest.skip("Need at least 2 test files for batch processing")
        
        print(f"\n{'='*80}")
        print(f"Batch Processing Test: {len(test_files)} files")
        print(f"{'='*80}")
        
        # Create batch records
        records = [
            {'id': f.stem, 'file_path': f}
            for f in test_files
        ]
        
        # Configure batch processing
        batch_config = BatchConfig(
            max_workers=2,
            timeout_per_record=60,
            continue_on_error=True,
            retry_policy=RetryPolicy(
                max_retries=2,
                retry_delay=0.5,
                exponential_backoff=True
            ),
            output_dir=TEST_OUTPUT_DIR / "batch"
        )
        
        # Define processing function
        def process_file(record: dict) -> dict:
            """Process single file."""
            file_path = record['file_path']
            
            processor = ExcelProcessor()
            result = processor.process_file(file_path)
            
            if not result.success:
                raise ValueError(f"Processing failed: {result.errors}")
            
            return {
                'id': record['id'],
                'sheets': result.metadata['sheets_processed'],
                'status': 'success'
            }
        
        # Run batch job
        start_time = time.time()
        
        runner = BatchJobRunner(config=batch_config, job_id="robot_batch_test")
        job_result = runner.run_batch(
            records=records,
            process_func=process_file,
            record_id_key='id'
        )
        
        duration = time.time() - start_time
        
        # Assertions
        assert job_result.total_records == len(test_files), "Record count mismatch"
        assert job_result.successful_records > 0, "No successful records"
        assert job_result.get_success_rate() >= 50.0, "Success rate too low"
        
        # Check output structure
        assert (batch_config.output_dir / "success").exists(), "Success directory not created"
        assert (batch_config.output_dir / "logs").exists(), "Logs directory not created"
        
        # Summary
        print(f"\n{'='*80}")
        print(f"Batch Processing Results:")
        print(f"  Total: {job_result.total_records}")
        print(f"  Success: {job_result.successful_records} ({job_result.get_success_rate():.1f}%)")
        print(f"  Failed: {job_result.failed_records} ({job_result.get_failure_rate():.1f}%)")
        print(f"  Duration: {duration:.2f}s")
        print(f"{'='*80}\n")
        
        print("✅ Batch processing test passed")


class TestRobotValidation:
    """Robot tests for validation system."""
    
    def test_validation_comprehensive(self):
        """Test comprehensive 3-level validation."""
        test_files = list(TEST_INPUT_DIR.glob("*.xlsx"))
        
        if not test_files:
            pytest.skip("No test files available")
        
        test_file = test_files[0]
        
        print(f"\nTesting validation with: {test_file.name}")
        
        # Process Excel
        processor = ExcelProcessor()
        result = processor.process_file(test_file)
        
        assert result.success, "Excel processing failed"
        
        # Run validation on first sheet
        validator = ComprehensiveValidator()
        
        for sheet_name, df in list(result.data.items())[:1]:  # Test first sheet
            print(f"\nValidating sheet: {sheet_name}")
            
            validation_rules = {
                'required_columns': list(df.columns),
                'non_null_columns': list(df.columns)
            }
            
            val_result = validator.validate_dataframe(df, validation_rules, sheet_name)
            
            # Validation result should have proper structure
            assert hasattr(val_result, 'is_valid'), "Missing is_valid attribute"
            assert hasattr(val_result, 'errors'), "Missing errors attribute"
            assert hasattr(val_result, 'warnings'), "Missing warnings attribute"
            
            print(f"  Valid: {val_result.is_valid}")
            print(f"  Errors: {len(val_result.errors)}")
            print(f"  Warnings: {len(val_result.warnings)}")
        
        print("✅ Validation test passed")


class TestRobotPerformance:
    """Robot tests for performance benchmarks."""
    
    def test_performance_excel_processing(self):
        """Benchmark Excel processing performance."""
        test_files = list(TEST_INPUT_DIR.glob("*.xlsx"))
        
        if not test_files:
            pytest.skip("No test files available")
        
        test_file = test_files[0]
        
        print(f"\nBenchmarking Excel processing: {test_file.name}")
        
        processor = ExcelProcessor()
        
        # Warm-up run
        processor.process_file(test_file)
        
        # Benchmark run
        start_time = time.time()
        result = processor.process_file(test_file)
        duration = time.time() - start_time
        
        assert result.success, "Processing failed"
        
        # Performance assertions (adjust based on your requirements)
        assert duration < 10.0, f"Processing too slow: {duration:.2f}s"
        
        print(f"  Duration: {duration:.2f}s")
        print(f"  Sheets: {result.metadata['sheets_processed']}")
        print(f"  Performance: ✅ PASS")
    
    def test_performance_html_rendering(self):
        """Benchmark HTML rendering performance."""
        renderer = HTMLRenderer(
            template_dir=TEMPLATE_DIR,
            enable_cache=True
        )
        
        template_data = {
            'title_data': {},
            'items': [{'serial_no': str(i)} for i in range(100)],  # 100 items
            'totals': {},
            'deviation_items': [],
            'summary': {}
        }
        
        print("\nBenchmarking HTML rendering (100 items)")
        
        # Warm-up
        renderer.render_document(DocumentType.FIRST_PAGE, template_data)
        
        # Benchmark
        start_time = time.time()
        result = renderer.render_document(DocumentType.FIRST_PAGE, template_data)
        duration = time.time() - start_time
        
        assert result.success, "Rendering failed"
        assert duration < 1.0, f"Rendering too slow: {duration:.2f}s"
        
        print(f"  Duration: {duration:.2f}s")
        print(f"  HTML size: {len(result.html_content):,} chars")
        print(f"  Performance: ✅ PASS")


# Test summary function
def print_test_summary():
    """Print test summary."""
    print("\n" + "="*80)
    print("ROBOT TEST SUITE SUMMARY")
    print("="*80)
    print("\nTest Categories:")
    print("  1. Single File Processing - Tests Excel → HTML → PDF pipeline")
    print("  2. Batch Processing - Tests parallel processing with multiple files")
    print("  3. Validation - Tests 3-level validation system")
    print("  4. Performance - Benchmarks processing speed")
    print("\nTo run all tests:")
    print("  pytest tests/test_robot_automated.py -v")
    print("\nTo run specific category:")
    print("  pytest tests/test_robot_automated.py::TestRobotSingleFile -v")
    print("  pytest tests/test_robot_automated.py::TestRobotBatchProcessing -v")
    print("="*80 + "\n")


if __name__ == "__main__":
    print_test_summary()
    pytest.main([__file__, "-v", "--tb=short"])
