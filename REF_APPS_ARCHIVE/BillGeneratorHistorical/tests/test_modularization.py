"""
Test suite for verifying the modularization of the Stream Bill Generator
"""
import sys
import os
import unittest

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

class TestModularization(unittest.TestCase):
    
    def test_core_module_import(self):
        """Test that the core computation module can be imported"""
        try:
            from core.computations.bill_processor import process_bill, safe_float, number_to_words
            self.assertIsNotNone(process_bill)
            self.assertIsNotNone(safe_float)
            self.assertIsNotNone(number_to_words)
        except ImportError as e:
            self.fail(f"Failed to import core modules: {e}")

    def test_exports_module_import(self):
        """Test that the exports module can be imported"""
        try:
            from exports.renderers import generate_pdf, create_word_doc, merge_pdfs, create_zip_archive
            self.assertIsNotNone(generate_pdf)
            self.assertIsNotNone(create_word_doc)
            self.assertIsNotNone(merge_pdfs)
            self.assertIsNotNone(create_zip_archive)
        except ImportError as e:
            self.fail(f"Failed to import exports modules: {e}")

    def test_app_module_import(self):
        """Test that the app module can be imported"""
        try:
            import app.main
            self.assertIsNotNone(app.main)
        except ImportError as e:
            self.fail(f"Failed to import app module: {e}")

    def test_safe_float_function(self):
        """Test the safe_float function from core module"""
        from core.computations.bill_processor import safe_float
        
        # Test normal float conversion
        self.assertEqual(safe_float("123.45"), 123.45)
        self.assertEqual(safe_float(123), 123.0)
        self.assertEqual(safe_float(123.45), 123.45)
        
        # Test edge cases
        self.assertEqual(safe_float(None), 0.0)
        self.assertEqual(safe_float(""), 0.0)
        self.assertEqual(safe_float("   "), 0.0)
        self.assertEqual(safe_float("abc"), 0.0)
        self.assertEqual(safe_float("12,345.67"), 12345.67)

    def test_number_to_words_function(self):
        """Test the number_to_words function from core module"""
        from core.computations.bill_processor import number_to_words
        
        # Test basic conversion
        result = number_to_words(123)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        
        # Test edge cases
        result = number_to_words(0)
        self.assertIsInstance(result, str)
        
        result = number_to_words(-123)
        self.assertIsInstance(result, str)

if __name__ == "__main__":
    unittest.main()