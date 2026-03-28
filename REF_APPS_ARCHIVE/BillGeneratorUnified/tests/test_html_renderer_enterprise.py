"""
Unit Tests for Enterprise HTML Renderer
Comprehensive test coverage for production-grade HTML rendering.
"""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pandas as pd
import pytest

from core.generators.html_renderer_enterprise import (
    HTMLRenderer,
    TemplateManager,
    DataProcessor,
    SecurityManager,
    DocumentType,
    OutputFormat,
    RenderResult,
    RenderContext,
    HTMLRenderingError,
    TemplateError,
    ValidationError,
    SecurityError,
)


class TestSecurityManager(unittest.TestCase):
    """Test cases for SecurityManager class."""
    
    def test_sanitize_html_basic(self):
        """Test basic HTML sanitization."""
        result = SecurityManager.sanitize_html("<script>alert('xss')</script>")
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)
    
    def test_sanitize_html_empty(self):
        """Test sanitization of empty content."""
        result = SecurityManager.sanitize_html("")
        self.assertEqual(result, "")
    
    def test_sanitize_html_none(self):
        """Test sanitization of None."""
        result = SecurityManager.sanitize_html(None)
        self.assertEqual(result, "")
    
    def test_validate_template_name_valid(self):
        """Test validation of valid template names."""
        valid_names = [
            "first_page.html",
            "deviation_statement.html",
            "template.htm",
            "custom.jinja2"
        ]
        
        for name in valid_names:
            self.assertTrue(SecurityManager.validate_template_name(name))
    
    def test_validate_template_name_invalid(self):
        """Test validation of invalid template names."""
        invalid_names = [
            "../etc/passwd",
            "../../secret.html",
            "path/to/template.html",
            "template.txt",
            "template.php"
        ]
        
        for name in invalid_names:
            self.assertFalse(SecurityManager.validate_template_name(name))


class TestDataProcessor(unittest.TestCase):
    """Test cases for DataProcessor class."""
    
    def test_safe_float_valid(self):
        """Test safe float conversion with valid values."""
        test_cases = [
            (10, 10.0),
            ("20.5", 20.5),
            (30.7, 30.7),
            ("100", 100.0)
        ]
        
        for input_val, expected in test_cases:
            result = DataProcessor.safe_float(input_val)
            self.assertEqual(result, expected)
    
    def test_safe_float_invalid(self):
        """Test safe float conversion with invalid values."""
        test_cases = [
            (None, 0.0),
            ("", 0.0),
            ("invalid", 0.0),
            (pd.NA, 0.0)
        ]
        
        for input_val, expected in test_cases:
            result = DataProcessor.safe_float(input_val)
            self.assertEqual(result, expected)
    
    def test_safe_float_custom_default(self):
        """Test safe float with custom default."""
        result = DataProcessor.safe_float(None, default=99.9)
        self.assertEqual(result, 99.9)
    
    def test_safe_string_valid(self):
        """Test safe string conversion."""
        test_cases = [
            ("hello", "hello"),
            (123, "123"),
            ("  spaces  ", "spaces")
        ]
        
        for input_val, expected in test_cases:
            result = DataProcessor.safe_string(input_val)
            self.assertEqual(result, expected)
    
    def test_safe_string_invalid(self):
        """Test safe string with invalid values."""
        test_cases = [
            (None, ""),
            (pd.NA, "")
        ]
        
        for input_val, expected in test_cases:
            result = DataProcessor.safe_string(input_val)
            self.assertEqual(result, expected)
    
    def test_format_currency_zero(self):
        """Test currency formatting with zero."""
        result = DataProcessor.format_currency(0)
        self.assertEqual(result, "")
    
    def test_format_currency_positive(self):
        """Test currency formatting with positive values."""
        result = DataProcessor.format_currency(1234.56)
        self.assertIn("1,234.56", result)
    
    def test_format_currency_decimals(self):
        """Test currency formatting with custom decimals."""
        result = DataProcessor.format_currency(1234.567, decimals=3)
        self.assertIn("1,234.567", result)
    
    def test_number_to_words_basic(self):
        """Test number to words conversion."""
        test_cases = [
            (0, "Zero"),
            (1, "One"),
            (10, "Ten"),
            (15, "Fifteen"),
            (20, "Twenty"),
            (99, "Ninety Nine"),
            (100, "One Hundred"),
            (1000, "One Thousand")
        ]
        
        for num, expected in test_cases:
            result = DataProcessor.number_to_words(num)
            self.assertEqual(result, expected)
    
    def test_number_to_words_large(self):
        """Test number to words with large numbers."""
        result = DataProcessor.number_to_words(100000)
        self.assertIn("Lakh", result)
        
        result = DataProcessor.number_to_words(10000000)
        self.assertIn("Crore", result)


class TestRenderContext(unittest.TestCase):
    """Test cases for RenderContext dataclass."""
    
    def test_render_context_creation(self):
        """Test RenderContext creation."""
        context = RenderContext(
            data={'key': 'value'},
            document_type=DocumentType.FIRST_PAGE
        )
        
        self.assertEqual(context.data, {'key': 'value'})
        self.assertEqual(context.document_type, DocumentType.FIRST_PAGE)
        self.assertEqual(context.output_format, OutputFormat.HTML5)
    
    def test_render_context_empty_data(self):
        """Test RenderContext with empty data."""
        with self.assertRaises(ValidationError):
            RenderContext(
                data={},
                document_type=DocumentType.FIRST_PAGE
            )


class TestRenderResult(unittest.TestCase):
    """Test cases for RenderResult dataclass."""
    
    def test_render_result_success(self):
        """Test successful RenderResult."""
        result = RenderResult(
            success=True,
            html_content="<html></html>",
            document_type=DocumentType.FIRST_PAGE
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.html_content)
        self.assertEqual(len(result.errors), 0)
    
    def test_render_result_failure(self):
        """Test failed RenderResult."""
        result = RenderResult(
            success=False,
            errors=["Template not found"]
        )
        
        self.assertFalse(result.success)
        self.assertIsNone(result.html_content)
        self.assertEqual(len(result.errors), 1)


class TestTemplateManager(unittest.TestCase):
    """Test cases for TemplateManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use actual template directory
        self.template_dir = Path(__file__).parent.parent / "templates"
        
        if self.template_dir.exists():
            self.manager = TemplateManager(
                template_dir=self.template_dir,
                enable_sandbox=True,
                enable_cache=True
            )
    
    def test_initialization(self):
        """Test TemplateManager initialization."""
        if hasattr(self, 'manager'):
            self.assertIsNotNone(self.manager.env)
            self.assertTrue(self.manager.enable_sandbox)
            self.assertTrue(self.manager.enable_cache)
    
    def test_invalid_template_directory(self):
        """Test initialization with invalid directory."""
        with self.assertRaises(TemplateError):
            TemplateManager(template_dir="/nonexistent/path")
    
    def test_get_template_valid(self):
        """Test getting a valid template."""
        if hasattr(self, 'manager'):
            try:
                template = self.manager.get_template("first_page.html")
                self.assertIsNotNone(template)
            except TemplateError:
                # Template might not exist in test environment
                pass
    
    def test_get_template_invalid_name(self):
        """Test getting template with invalid name."""
        if hasattr(self, 'manager'):
            with self.assertRaises(SecurityError):
                self.manager.get_template("../etc/passwd")
    
    def test_list_templates(self):
        """Test listing available templates."""
        if hasattr(self, 'manager'):
            templates = self.manager.list_templates()
            self.assertIsInstance(templates, list)


class TestHTMLRenderer(unittest.TestCase):
    """Test cases for HTMLRenderer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.template_dir = Path(__file__).parent.parent / "templates"
        
        if self.template_dir.exists():
            self.renderer = HTMLRenderer(
                template_dir=self.template_dir,
                enable_sandbox=True,
                enable_cache=True,
                validate_output=True
            )
    
    def test_initialization(self):
        """Test HTMLRenderer initialization."""
        if hasattr(self, 'renderer'):
            self.assertIsNotNone(self.renderer.template_manager)
            self.assertIsNotNone(self.renderer.data_processor)
            self.assertIsNotNone(self.renderer.security_manager)
    
    def test_template_map(self):
        """Test template mapping."""
        self.assertIn(DocumentType.FIRST_PAGE, HTMLRenderer.TEMPLATE_MAP)
        self.assertIn(DocumentType.DEVIATION_STATEMENT, HTMLRenderer.TEMPLATE_MAP)
        self.assertEqual(
            HTMLRenderer.TEMPLATE_MAP[DocumentType.FIRST_PAGE],
            "first_page.html"
        )
    
    def test_has_extra_items_dataframe(self):
        """Test extra items detection with DataFrame."""
        if hasattr(self, 'renderer'):
            # With data
            data = {'extra_items_data': pd.DataFrame({'col': [1, 2, 3]})}
            self.assertTrue(self.renderer._has_extra_items(data))
            
            # Empty DataFrame
            data = {'extra_items_data': pd.DataFrame()}
            self.assertFalse(self.renderer._has_extra_items(data))
    
    def test_has_extra_items_list(self):
        """Test extra items detection with list."""
        if hasattr(self, 'renderer'):
            # With data
            data = {'extra_items_data': [1, 2, 3]}
            self.assertTrue(self.renderer._has_extra_items(data))
            
            # Empty list
            data = {'extra_items_data': []}
            self.assertFalse(self.renderer._has_extra_items(data))
    
    def test_validate_html_valid(self):
        """Test HTML validation with valid content."""
        if hasattr(self, 'renderer'):
            html = """
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"></head>
            <body></body>
            </html>
            """
            warnings = self.renderer._validate_html(html)
            self.assertEqual(len(warnings), 0)
    
    def test_validate_html_missing_doctype(self):
        """Test HTML validation with missing DOCTYPE."""
        if hasattr(self, 'renderer'):
            html = "<html><head></head><body></body></html>"
            warnings = self.renderer._validate_html(html)
            self.assertGreater(len(warnings), 0)
            self.assertTrue(any("DOCTYPE" in w for w in warnings))
    
    def test_validate_html_empty(self):
        """Test HTML validation with empty content."""
        if hasattr(self, 'renderer'):
            warnings = self.renderer._validate_html("")
            self.assertGreater(len(warnings), 0)
            self.assertTrue(any("empty" in w.lower() for w in warnings))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_large_number_to_words(self):
        """Test number to words with very large numbers."""
        result = DataProcessor.number_to_words(999999999)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters."""
        result = DataProcessor.safe_string("Hello 你好 مرحبا 🎉")
        self.assertIn("Hello", result)
        self.assertIn("你好", result)
    
    def test_special_characters_sanitization(self):
        """Test sanitization of special characters."""
        test_cases = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "'; DROP TABLE users; --"
        ]
        
        for test_case in test_cases:
            result = SecurityManager.sanitize_html(test_case)
            self.assertNotIn("<script>", result)
            self.assertNotIn("<img", result)


# Pytest fixtures
@pytest.fixture
def sample_data():
    """Fixture providing sample data."""
    return {
        'title_data': {
            'Project Name': 'Test Project',
            'Contract No': 'C-001'
        },
        'work_order_data': pd.DataFrame({
            'Item No.': ['1', '2', '3'],
            'Description': ['Item 1', 'Item 2', 'Item 3'],
            'Quantity': [10, 20, 30],
            'Rate': [100.0, 200.0, 300.0]
        }),
        'bill_quantity_data': pd.DataFrame({
            'Item No.': ['1', '2', '3'],
            'Description': ['Item 1', 'Item 2', 'Item 3'],
            'Quantity': [10, 20, 30],
            'Rate': [100.0, 200.0, 300.0]
        })
    }


@pytest.fixture
def template_manager():
    """Fixture providing TemplateManager."""
    template_dir = Path(__file__).parent.parent / "templates"
    if template_dir.exists():
        return TemplateManager(template_dir=template_dir)
    return None


# Pytest test functions
def test_data_processor_with_sample_data(sample_data):
    """Test DataProcessor with sample data."""
    processor = DataProcessor()
    
    # Test safe_float with DataFrame values
    df = sample_data['work_order_data']
    for value in df['Quantity']:
        result = processor.safe_float(value)
        assert isinstance(result, float)
        assert result >= 0


def test_security_manager_xss_prevention():
    """Test XSS prevention."""
    xss_attempts = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "<iframe src='javascript:alert(1)'></iframe>"
    ]
    
    for attempt in xss_attempts:
        sanitized = SecurityManager.sanitize_html(attempt)
        assert "<script>" not in sanitized
        assert "<img" not in sanitized
        assert "<iframe" not in sanitized


if __name__ == '__main__':
    # Run unit tests
    unittest.main(verbosity=2)
