"""
Unit Tests for Enterprise Excel Processor
Comprehensive test coverage for production-grade Excel processing.
"""

import io
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from core.processors.excel_processor_enterprise import (
    ExcelProcessor,
    ExcelValidator,
    FileType,
    ProcessingError,
    ProcessingResult,
    SheetSchema,
    ValidationError,
    ValidationResult,
)


class TestExcelValidator(unittest.TestCase):
    """Test cases for ExcelValidator class."""
    
    def test_validate_file_path_nonexistent(self):
        """Test validation of non-existent file."""
        result = ExcelValidator.validate_file_path("nonexistent.xlsx")
        self.assertFalse(result.is_valid)
        self.assertIn("File not found", result.errors[0])
    
    def test_validate_file_path_unsupported_extension(self):
        """Test validation of unsupported file type."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                result = ExcelValidator.validate_file_path("test.csv")
                self.assertFalse(result.is_valid)
                self.assertIn("Unsupported file type", result.errors[0])
    
    def test_sanitize_string_formula_injection(self):
        """Test sanitization of formula injection attempts."""
        # Test various formula patterns
        test_cases = [
            ("=1+1", "'=1+1"),
            ("@SUM(A1:A10)", "'@SUM(A1:A10)"),
            ("+1+1", "'+1+1"),
            ("-1-1", "'-1-1"),
            ("|cmd", "'|cmd"),
            ("normal text", "normal text"),
        ]
        
        for input_val, expected in test_cases:
            result = ExcelValidator.sanitize_string(input_val)
            self.assertEqual(result, expected)
    
    def test_sanitize_string_nan_value(self):
        """Test sanitization of NaN values."""
        result = ExcelValidator.sanitize_string(pd.NA)
        self.assertEqual(result, "")
    
    def test_validate_sheet_schema_empty_dataframe(self):
        """Test schema validation with empty DataFrame."""
        df = pd.DataFrame()
        schema = SheetSchema(
            name="TestSheet",
            required_columns=["Col1", "Col2"],
            allow_empty=False
        )
        
        result = ExcelValidator.validate_sheet_schema(df, schema)
        self.assertFalse(result.is_valid)
        self.assertIn("empty", result.errors[0].lower())
    
    def test_validate_sheet_schema_missing_columns(self):
        """Test schema validation with missing required columns."""
        df = pd.DataFrame({
            'Col1': [1, 2, 3],
            'Col3': [4, 5, 6]
        })
        schema = SheetSchema(
            name="TestSheet",
            required_columns=["Col1", "Col2"],
            min_rows=1
        )
        
        result = ExcelValidator.validate_sheet_schema(df, schema)
        self.assertFalse(result.is_valid)
        self.assertIn("missing required columns", result.errors[0].lower())
    
    def test_validate_sheet_schema_row_count(self):
        """Test schema validation with row count constraints."""
        df = pd.DataFrame({
            'Col1': [1, 2],
            'Col2': [3, 4]
        })
        schema = SheetSchema(
            name="TestSheet",
            required_columns=["Col1", "Col2"],
            min_rows=5
        )
        
        result = ExcelValidator.validate_sheet_schema(df, schema)
        self.assertFalse(result.is_valid)
        self.assertIn("minimum required", result.errors[0].lower())
    
    def test_validate_sheet_schema_success(self):
        """Test successful schema validation."""
        df = pd.DataFrame({
            'Col1': [1, 2, 3],
            'Col2': [4, 5, 6]
        })
        schema = SheetSchema(
            name="TestSheet",
            required_columns=["Col1", "Col2"],
            min_rows=1
        )
        
        result = ExcelValidator.validate_sheet_schema(df, schema)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)


class TestExcelProcessor(unittest.TestCase):
    """Test cases for ExcelProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = ExcelProcessor(
            sanitize_strings=True,
            validate_schemas=True
        )
    
    def test_initialization(self):
        """Test processor initialization."""
        self.assertIsNotNone(self.processor.validator)
        self.assertTrue(self.processor.sanitize_strings)
        self.assertTrue(self.processor.validate_schemas)
    
    def test_clean_dataframe_empty_rows(self):
        """Test cleaning of empty rows."""
        df = pd.DataFrame({
            'Col1': [1, None, 3],
            'Col2': [4, None, 6]
        })
        
        df_clean = self.processor._clean_dataframe(df, "TestSheet")
        
        # Should remove row with all NaN values
        self.assertEqual(len(df_clean), 2)
    
    def test_clean_dataframe_empty_columns(self):
        """Test cleaning of empty columns."""
        df = pd.DataFrame({
            'Col1': [1, 2, 3],
            'Col2': [None, None, None],
            'Col3': [4, 5, 6]
        })
        
        df_clean = self.processor._clean_dataframe(df, "TestSheet")
        
        # Should remove column with all NaN values
        self.assertEqual(len(df_clean.columns), 2)
        self.assertNotIn('Col2', df_clean.columns)
    
    def test_clean_dataframe_sanitize_strings(self):
        """Test string sanitization during cleaning."""
        df = pd.DataFrame({
            'Col1': ['=1+1', 'normal', '@SUM(A1)']
        })
        
        df_clean = self.processor._clean_dataframe(df, "TestSheet")
        
        # Should sanitize formula strings
        self.assertTrue(df_clean['Col1'].iloc[0].startswith("'"))
        self.assertEqual(df_clean['Col1'].iloc[1], 'normal')
    
    def test_to_json_conversion(self):
        """Test conversion of DataFrames to JSON."""
        data = {
            'Sheet1': pd.DataFrame({
                'Col1': [1, 2, 3],
                'Col2': ['a', 'b', 'c']
            })
        }
        
        json_data = self.processor.to_json(data)
        
        self.assertIn('Sheet1', json_data)
        self.assertEqual(len(json_data['Sheet1']), 3)
        self.assertIsInstance(json_data['Sheet1'], list)
    
    @patch('pandas.read_excel')
    def test_load_sheet_success(self, mock_read_excel):
        """Test successful sheet loading."""
        mock_df = pd.DataFrame({'Col1': [1, 2, 3]})
        mock_read_excel.return_value = mock_df
        
        df = self.processor._load_sheet('test.xlsx', 'Sheet1', 'xlsx')
        
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 3)
        mock_read_excel.assert_called_once()
    
    @patch('pandas.read_excel')
    def test_load_sheet_failure(self, mock_read_excel):
        """Test sheet loading failure."""
        mock_read_excel.side_effect = Exception("Read error")
        
        df = self.processor._load_sheet('test.xlsx', 'Sheet1', 'xlsx')
        
        self.assertIsNone(df)


class TestSheetSchema(unittest.TestCase):
    """Test cases for SheetSchema dataclass."""
    
    def test_schema_creation(self):
        """Test schema creation with default values."""
        schema = SheetSchema(
            name="TestSheet",
            required_columns=["Col1", "Col2"]
        )
        
        self.assertEqual(schema.name, "TestSheet")
        self.assertEqual(len(schema.required_columns), 2)
        self.assertEqual(len(schema.optional_columns), 0)
        self.assertFalse(schema.allow_empty)
        self.assertEqual(schema.min_rows, 0)
        self.assertIsNone(schema.max_rows)
    
    def test_schema_with_all_parameters(self):
        """Test schema creation with all parameters."""
        schema = SheetSchema(
            name="TestSheet",
            required_columns=["Col1"],
            optional_columns=["Col2"],
            column_types={"Col1": int},
            allow_empty=True,
            min_rows=5,
            max_rows=100
        )
        
        self.assertTrue(schema.allow_empty)
        self.assertEqual(schema.min_rows, 5)
        self.assertEqual(schema.max_rows, 100)


class TestValidationResult(unittest.TestCase):
    """Test cases for ValidationResult dataclass."""
    
    def test_validation_result_success(self):
        """Test successful validation result."""
        result = ValidationResult(is_valid=True)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)
    
    def test_validation_result_with_errors(self):
        """Test validation result with errors."""
        result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"]
        )
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 2)
        self.assertEqual(len(result.warnings), 1)


class TestProcessingResult(unittest.TestCase):
    """Test cases for ProcessingResult dataclass."""
    
    def test_processing_result_success(self):
        """Test successful processing result."""
        data = {'Sheet1': pd.DataFrame({'Col1': [1, 2, 3]})}
        result = ProcessingResult(success=True, data=data)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertEqual(len(result.errors), 0)
    
    def test_processing_result_failure(self):
        """Test failed processing result."""
        result = ProcessingResult(
            success=False,
            errors=["Processing failed"]
        )
        
        self.assertFalse(result.success)
        self.assertIsNone(result.data)
        self.assertEqual(len(result.errors), 1)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_large_dataframe_handling(self):
        """Test handling of large DataFrames."""
        # Create large DataFrame
        large_df = pd.DataFrame({
            f'Col{i}': range(10000) for i in range(10)
        })
        
        processor = ExcelProcessor(chunk_size=1000)
        df_clean = processor._clean_dataframe(large_df, "LargeSheet")
        
        self.assertEqual(len(df_clean), 10000)
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters."""
        df = pd.DataFrame({
            'Col1': ['Hello', '你好', 'مرحبا', '🎉']
        })
        
        processor = ExcelProcessor()
        df_clean = processor._clean_dataframe(df, "UnicodeSheet")
        
        self.assertEqual(len(df_clean), 4)
    
    def test_mixed_data_types(self):
        """Test handling of mixed data types."""
        df = pd.DataFrame({
            'Col1': [1, '2', 3.0, None, '=5'],
            'Col2': ['a', 'b', 'c', 'd', 'e']  # Add second column to prevent row removal
        })
        
        processor = ExcelProcessor(sanitize_strings=True)
        df_clean = processor._clean_dataframe(df, "MixedSheet")
        
        # Should handle mixed types without errors
        self.assertEqual(len(df_clean), 5)


# Pytest fixtures
@pytest.fixture
def sample_dataframe():
    """Fixture providing sample DataFrame."""
    return pd.DataFrame({
        'Item No.': ['1', '2', '3'],
        'Description': ['Item 1', 'Item 2', 'Item 3'],
        'Quantity': [10, 20, 30],
        'Rate': [100.0, 200.0, 300.0]
    })


@pytest.fixture
def sample_schema():
    """Fixture providing sample schema."""
    return SheetSchema(
        name="TestSheet",
        required_columns=['Item No.', 'Description', 'Quantity', 'Rate'],
        min_rows=1
    )


# Pytest test functions
def test_validator_with_sample_data(sample_dataframe, sample_schema):
    """Test validator with sample data."""
    result = ExcelValidator.validate_sheet_schema(sample_dataframe, sample_schema)
    assert result.is_valid
    assert len(result.errors) == 0


def test_processor_initialization():
    """Test processor can be initialized with different configurations."""
    configs = [
        {'sanitize_strings': True, 'validate_schemas': True},
        {'sanitize_strings': False, 'validate_schemas': False},
        {'chunk_size': 5000},
    ]
    
    for config in configs:
        processor = ExcelProcessor(**config)
        assert processor is not None


if __name__ == '__main__':
    # Run unit tests
    unittest.main(verbosity=2)
