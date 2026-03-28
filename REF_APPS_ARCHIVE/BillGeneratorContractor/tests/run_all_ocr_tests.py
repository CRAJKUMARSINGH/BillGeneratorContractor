#!/usr/bin/env python3
"""
Master Test Runner for Smart Cascade OCR
Runs all OCR tests and generates comprehensive report
"""
import sys
import unittest
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test modules
from tests.test_smart_cascade_ocr import TestSmartCascadeOCR, TestQualityMetrics
from tests.test_ocr_integration import TestOCRIntegration, TestProviderFallback


def print_banner(text):
    """Print formatted banner"""
    print("\n" + "="*80)
    print(text.center(80))
    print("="*80 + "\n")


def main():
    """Run all OCR tests"""
    print_banner("SMART CASCADE OCR - COMPLETE TEST SUITE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    print("📦 Loading test suites...")
    suite.addTests(loader.loadTestsFromTestCase(TestSmartCascadeOCR))
    suite.addTests(loader.loadTestsFromTestCase(TestQualityMetrics))
    suite.addTests(loader.loadTestsFromTestCase(TestOCRIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestProviderFallback))
    print(f"   ✅ Loaded {suite.countTestCases()} tests\n")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate report
    print_banner("FINAL TEST REPORT")
    
    print(f"📊 Test Execution Summary:")
    print(f"   Total Tests: {result.testsRun}")
    print(f"   ✅ Passed: {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
    print(f"   ❌ Failed: {len(result.failures)}")
    print(f"   ⚠️  Errors: {len(result.errors)}")
    print(f"   ⏭️  Skipped: {len(result.skipped)}")
    
    if result.failures:
        print(f"\n❌ Failed Tests:")
        for test, traceback in result.failures:
            print(f"   - {test}")
    
    if result.errors:
        print(f"\n⚠️  Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}")
    
    # Success rate
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / 
                       result.testsRun * 100)
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
