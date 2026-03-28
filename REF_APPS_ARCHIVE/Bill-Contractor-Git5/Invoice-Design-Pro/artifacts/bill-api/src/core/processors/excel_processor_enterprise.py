"""
Enterprise-Grade Excel Processor
Production-ready data processing with robust validation, security, and performance optimization.

Author: Senior Python Data-Processing Engineer
Standards: PEP-8, Type Hints, Modular Architecture
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class FileType(Enum):
    """Supported Excel file types."""
    XLSX = "xlsx"
    XLSM = "xlsm"
    XLS = "xls"


# Security: Formula injection patterns
FORMULA_INJECTION_PATTERNS = [
    r'^=', r'^@', r'^\+', r'^-', r'^\|', r'^%'
]

# Performance: Default chunk size for large files
DEFAULT_CHUNK_SIZE = 10000

# Validation: File size limits (in bytes)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB



# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class ExcelProcessingError(Exception):
    """Base exception for Excel processing errors."""
    pass


class ValidationError(ExcelProcessingError):
    """Raised when validation fails."""
    pass


class ProcessingError(ExcelProcessingError):
    """Raised when processing fails."""
    pass


class SecurityError(ExcelProcessingError):
    """Raised when security checks fail."""
    pass


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SheetSchema:
    """Schema definition for Excel sheet validation."""
    name: str
    required_columns: List[str]
    optional_columns: List[str] = field(default_factory=list)
    column_types: Dict[str, type] = field(default_factory=dict)
    allow_empty: bool = False
    min_rows: int = 0
    max_rows: Optional[int] = None


@dataclass
class ValidationResult:
    """Result of validation operation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)


@dataclass
class ProcessingResult:
    """Result of processing operation."""
    success: bool
    data: Optional[Dict[str, pd.DataFrame]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)



# ============================================================================
# VALIDATOR CLASS
# ============================================================================

class ExcelValidator:
    """Validates Excel files and data before processing."""
    
    @staticmethod
    def validate_file_path(file_path: Union[str, Path]) -> ValidationResult:
        """
        Validate file path and basic file properties.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True)
        path = Path(file_path)
        
        # Check file exists
        if not path.exists():
            result.add_error(f"File not found: {file_path}")
            return result
        
        # Check is file (not directory)
        if not path.is_file():
            result.add_error(f"Path is not a file: {file_path}")
            return result
        
        # Check file extension
        extension = path.suffix.lower().lstrip('.')
        try:
            FileType(extension)
        except ValueError:
            result.add_error(
                f"Unsupported file type: {extension}. "
                f"Supported: {', '.join([ft.value for ft in FileType])}"
            )
            return result
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            result.add_error(
                f"File too large: {file_size / (1024*1024):.2f} MB. "
                f"Maximum: {MAX_FILE_SIZE / (1024*1024):.2f} MB"
            )
            return result
        
        if file_size == 0:
            result.add_error("File is empty")
            return result
        
        logger.info(f"File validation passed: {file_path}")
        return result
    
    @staticmethod
    def sanitize_string(value: Any) -> str:
        """
        Sanitize string to prevent formula injection.
        
        Args:
            value: Value to sanitize
            
        Returns:
            Sanitized string
        """
        if pd.isna(value):
            return ""
        
        str_value = str(value)
        
        # Check for formula injection patterns
        import re
        for pattern in FORMULA_INJECTION_PATTERNS:
            if re.match(pattern, str_value):
                # Neutralize by prepending single quote
                return f"'{str_value}"
        
        return str_value
    
    @staticmethod
    def validate_sheet_schema(
        df: pd.DataFrame,
        schema: SheetSchema
    ) -> ValidationResult:
        """
        Validate DataFrame against schema.
        
        Args:
            df: DataFrame to validate
            schema: Schema definition
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True)
        
        # Check empty DataFrame
        if df.empty and not schema.allow_empty:
            result.add_error(f"Sheet '{schema.name}' is empty")
            return result
        
        # Check required columns
        missing_cols = set(schema.required_columns) - set(df.columns)
        if missing_cols:
            result.add_error(
                f"Sheet '{schema.name}' missing required columns: "
                f"{', '.join(missing_cols)}"
            )
        
        # Check row count
        row_count = len(df)
        if row_count < schema.min_rows:
            result.add_error(
                f"Sheet '{schema.name}' has {row_count} rows, "
                f"minimum required: {schema.min_rows}"
            )
        
        if schema.max_rows and row_count > schema.max_rows:
            result.add_warning(
                f"Sheet '{schema.name}' has {row_count} rows, "
                f"maximum expected: {schema.max_rows}"
            )
        
        # Check column types (if specified)
        for col, expected_type in schema.column_types.items():
            if col in df.columns:
                actual_type = df[col].dtype
                # Type checking logic here (simplified)
                if expected_type == int and not pd.api.types.is_integer_dtype(actual_type):
                    result.add_warning(
                        f"Column '{col}' expected type {expected_type.__name__}, "
                        f"got {actual_type}"
                    )
        
        if result.is_valid:
            logger.info(f"Schema validation passed for sheet: {schema.name}")
        
        return result
    
    @staticmethod
    def detect_sheets(file_path: Union[str, Path]) -> List[str]:
        """
        Detect available sheets in Excel file.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            List of sheet names
        """
        try:
            excel_file = pd.ExcelFile(file_path)
            sheets = excel_file.sheet_names
            logger.info(f"Detected {len(sheets)} sheets: {', '.join(sheets)}")
            return sheets
        except Exception as e:
            logger.error(f"Failed to detect sheets: {e}")
            raise ValidationError(f"Cannot read Excel file: {e}")



# ============================================================================
# PROCESSOR CLASS
# ============================================================================

class ExcelProcessor:
    """
    Enterprise-grade Excel processor with robust validation and security.
    """
    
    def __init__(
        self,
        sanitize_strings: bool = True,
        validate_schemas: bool = True,
        chunk_size: int = DEFAULT_CHUNK_SIZE
    ):
        """
        Initialize Excel processor.
        
        Args:
            sanitize_strings: Enable string sanitization for security
            validate_schemas: Enable schema validation
            chunk_size: Chunk size for processing large files
        """
        self.sanitize_strings = sanitize_strings
        self.validate_schemas = validate_schemas
        self.chunk_size = chunk_size
        self.validator = ExcelValidator()
        
        logger.info(
            f"ExcelProcessor initialized: "
            f"sanitize={sanitize_strings}, validate={validate_schemas}, "
            f"chunk_size={chunk_size}"
        )
    
    def process_file(
        self,
        file_path: Union[str, Path],
        schemas: Optional[Dict[str, SheetSchema]] = None,
        sheet_names: Optional[List[str]] = None
    ) -> ProcessingResult:
        """
        Process Excel file with validation and security checks.
        
        Args:
            file_path: Path to Excel file
            schemas: Optional schema definitions for validation
            sheet_names: Optional list of specific sheets to process
            
        Returns:
            ProcessingResult with processed data or errors
        """
        result = ProcessingResult(success=False)
        
        try:
            # Step 1: Validate file
            validation = self.validator.validate_file_path(file_path)
            if not validation.is_valid:
                result.errors = validation.errors
                return result
            
            # Step 2: Detect sheets
            available_sheets = self.validator.detect_sheets(file_path)
            sheets_to_process = sheet_names if sheet_names else available_sheets
            
            # Step 3: Determine file type and engine
            path = Path(file_path)
            extension = path.suffix.lower().lstrip('.')
            engine = 'openpyxl' if extension in ['xlsx', 'xlsm'] else 'xlrd'
            
            # Step 4: Process each sheet
            processed_data = {}
            
            for sheet_name in sheets_to_process:
                if sheet_name not in available_sheets:
                    result.warnings.append(f"Sheet not found: {sheet_name}")
                    continue
                
                try:
                    df = self._load_sheet(file_path, sheet_name, engine)
                    
                    if df is None:
                        result.warnings.append(f"Failed to load sheet: {sheet_name}")
                        continue
                    
                    # Validate schema if provided
                    if self.validate_schemas and schemas and sheet_name in schemas:
                        schema_validation = self.validator.validate_sheet_schema(
                            df, schemas[sheet_name]
                        )
                        if not schema_validation.is_valid:
                            result.errors.extend(schema_validation.errors)
                            continue
                        result.warnings.extend(schema_validation.warnings)
                    
                    # Clean and process DataFrame
                    df_clean = self._clean_dataframe(df, sheet_name)
                    processed_data[sheet_name] = df_clean
                    
                    logger.info(
                        f"Processed sheet '{sheet_name}': "
                        f"{len(df_clean)} rows, {len(df_clean.columns)} columns"
                    )
                    
                except Exception as e:
                    error_msg = f"Error processing sheet '{sheet_name}': {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)
            
            # Step 5: Finalize result
            if processed_data:
                result.success = True
                result.data = processed_data
                result.metadata = {
                    'file_path': str(file_path),
                    'sheets_processed': len(processed_data),
                    'total_sheets': len(available_sheets)
                }
                logger.info(f"Successfully processed {len(processed_data)} sheets")
            else:
                result.errors.append("No sheets were successfully processed")
            
        except Exception as e:
            error_msg = f"Fatal error processing file: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        
        return result
    
    def _load_sheet(
        self,
        file_path: Union[str, Path],
        sheet_name: str,
        engine: str
    ) -> Optional[pd.DataFrame]:
        """
        Load single sheet from Excel file.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet to load
            engine: Pandas engine to use
            
        Returns:
            DataFrame or None if loading fails
        """
        try:
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                engine=engine
            )
            return df
        except Exception as e:
            logger.error(f"Failed to load sheet '{sheet_name}': {e}")
            return None
    
    def _clean_dataframe(
        self,
        df: pd.DataFrame,
        sheet_name: str
    ) -> pd.DataFrame:
        """
        Clean DataFrame: remove empty rows/columns, sanitize strings.
        
        Args:
            df: DataFrame to clean
            sheet_name: Name of sheet (for logging)
            
        Returns:
            Cleaned DataFrame
        """
        df_clean = df.copy()
        
        # Remove completely empty rows
        df_clean = df_clean.dropna(how='all')
        
        # Remove completely empty columns
        df_clean = df_clean.dropna(axis=1, how='all')
        
        # Sanitize strings if enabled
        if self.sanitize_strings:
            for col in df_clean.columns:
                if df_clean[col].dtype == 'object':
                    df_clean[col] = df_clean[col].apply(self.validator.sanitize_string)
        
        logger.debug(
            f"Cleaned sheet '{sheet_name}': "
            f"{len(df)} -> {len(df_clean)} rows, "
            f"{len(df.columns)} -> {len(df_clean.columns)} columns"
        )
        
        return df_clean
    
    def to_json(
        self,
        data: Dict[str, pd.DataFrame],
        orient: str = 'records'
    ) -> Dict[str, Any]:
        """
        Convert processed data to JSON format.
        
        Args:
            data: Dictionary of DataFrames
            orient: Pandas to_json orient parameter
            
        Returns:
            Dictionary with JSON-serializable data
        """
        json_data = {}
        
        for sheet_name, df in data.items():
            try:
                json_data[sheet_name] = df.to_dict(orient=orient)
                logger.debug(f"Converted sheet '{sheet_name}' to JSON")
            except Exception as e:
                logger.error(f"Failed to convert sheet '{sheet_name}' to JSON: {e}")
        
        return json_data


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def process_excel_file(
    file_path: Union[str, Path],
    **kwargs
) -> ProcessingResult:
    """
    Convenience function to process Excel file with default settings.
    
    Args:
        file_path: Path to Excel file
        **kwargs: Additional arguments for ExcelProcessor
        
    Returns:
        ProcessingResult
    """
    processor = ExcelProcessor(**kwargs)
    return processor.process_file(file_path)


def validate_excel_file(file_path: Union[str, Path]) -> ValidationResult:
    """
    Convenience function to validate Excel file.
    
    Args:
        file_path: Path to Excel file
        
    Returns:
        ValidationResult
    """
    return ExcelValidator.validate_file_path(file_path)
