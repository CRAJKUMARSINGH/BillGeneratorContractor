"""
Enterprise-Grade Error Diagnostics System
3-Level Intelligent Validation: Structural → Semantic → Anomaly Detection

Author: Senior Data Validation Engineer
Standards: Precise error pinpointing, Actionable suggestions, Pattern detection
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
import re

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

class ErrorSeverity(Enum):
    """Error severity levels."""
    FATAL = "fatal"  # Cannot proceed
    ERROR = "error"  # Data issue, can continue
    WARNING = "warning"  # Potential issue
    INFO = "info"  # Informational


class ErrorCode(Enum):
    """Standardized error codes."""
    # Level 1: Structural
    SCHEMA_MISSING_COLUMN = "E1001"
    SCHEMA_INVALID_TYPE = "E1002"
    SCHEMA_NULL_VALUE = "E1003"
    SCHEMA_OUT_OF_RANGE = "E1004"
    
    # Level 2: Semantic
    BUSINESS_TOTAL_MISMATCH = "E2001"
    BUSINESS_DUPLICATE_ID = "E2002"
    BUSINESS_INVALID_DATE = "E2003"
    BUSINESS_NEGATIVE_VALUE = "E2004"
    BUSINESS_RATE_MISMATCH = "E2005"
    
    # Level 3: Anomaly
    ANOMALY_OUTLIER = "E3001"
    ANOMALY_PATTERN_BREAK = "E3002"
    ANOMALY_SUSPICIOUS_VALUE = "E3003"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ValidationError:
    """Detailed validation error with pinpointing."""
    error_code: ErrorCode
    severity: ErrorSeverity
    message: str
    row_number: Optional[int] = None
    column_name: Optional[str] = None
    actual_value: Optional[Any] = None
    expected_value: Optional[Any] = None
    suggestion: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'error_code': self.error_code.value,
            'severity': self.severity.value,
            'message': self.message,
            'row_number': self.row_number,
            'column_name': self.column_name,
            'actual_value': str(self.actual_value) if self.actual_value is not None else None,
            'expected_value': str(self.expected_value) if self.expected_value is not None else None,
            'suggestion': self.suggestion,
            'context': self.context
        }
    
    def __str__(self) -> str:
        """Human-readable error message."""
        parts = [f"[{self.error_code.value}] {self.message}"]
        
        if self.row_number is not None:
            parts.append(f"Row: {self.row_number}")
        
        if self.column_name:
            parts.append(f"Column: {self.column_name}")
        
        if self.actual_value is not None:
            parts.append(f"Actual: {self.actual_value}")
        
        if self.expected_value is not None:
            parts.append(f"Expected: {self.expected_value}")
        
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        
        return " | ".join(parts)


@dataclass
class ValidationResult:
    """Result of validation operation."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    info: List[ValidationError] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error: ValidationError):
        """Add error based on severity."""
        if error.severity == ErrorSeverity.FATAL or error.severity == ErrorSeverity.ERROR:
            self.errors.append(error)
            self.is_valid = False
        elif error.severity == ErrorSeverity.WARNING:
            self.warnings.append(error)
        else:
            self.info.append(error)
    
    def get_all_issues(self) -> List[ValidationError]:
        """Get all issues (errors + warnings + info)."""
        return self.errors + self.warnings + self.info
    
    def get_fatal_errors(self) -> List[ValidationError]:
        """Get only fatal errors."""
        return [e for e in self.errors if e.severity == ErrorSeverity.FATAL]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'is_valid': self.is_valid,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'info_count': len(self.info),
            'errors': [e.to_dict() for e in self.errors],
            'warnings': [w.to_dict() for w in self.warnings],
            'info': [i.to_dict() for i in self.info],
            'metadata': self.metadata
        }


# ============================================================================
# LEVEL 1: STRUCTURAL VALIDATION
# ============================================================================

class StructuralValidator:
    """Validates Excel schema and structure."""
    
    @staticmethod
    def validate_required_columns(
        df: pd.DataFrame,
        required_columns: List[str],
        sheet_name: str = "Sheet"
    ) -> List[ValidationError]:
        """
        Validate presence of required columns.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            sheet_name: Name of sheet for error context
            
        Returns:
            List of validation errors
        """
        errors = []
        missing_columns = set(required_columns) - set(df.columns)
        
        for col in missing_columns:
            errors.append(ValidationError(
                error_code=ErrorCode.SCHEMA_MISSING_COLUMN,
                severity=ErrorSeverity.FATAL,
                message=f"Required column missing in {sheet_name}",
                column_name=col,
                suggestion=f"Add column '{col}' to the Excel sheet",
                context={'sheet': sheet_name, 'available_columns': list(df.columns)}
            ))
        
        return errors
    
    @staticmethod
    def validate_column_types(
        df: pd.DataFrame,
        column_types: Dict[str, type],
        sheet_name: str = "Sheet"
    ) -> List[ValidationError]:
        """
        Validate column data types.
        
        Args:
            df: DataFrame to validate
            column_types: Expected column types
            sheet_name: Sheet name for context
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for col, expected_type in column_types.items():
            if col not in df.columns:
                continue
            
            actual_type = df[col].dtype
            
            # Type checking logic
            is_valid = False
            if expected_type == int:
                is_valid = pd.api.types.is_integer_dtype(actual_type)
            elif expected_type == float:
                is_valid = pd.api.types.is_numeric_dtype(actual_type)
            elif expected_type == str:
                is_valid = pd.api.types.is_string_dtype(actual_type) or pd.api.types.is_object_dtype(actual_type)
            elif expected_type == datetime or expected_type == date:
                is_valid = pd.api.types.is_datetime64_any_dtype(actual_type)
            
            if not is_valid:
                errors.append(ValidationError(
                    error_code=ErrorCode.SCHEMA_INVALID_TYPE,
                    severity=ErrorSeverity.ERROR,
                    message=f"Invalid data type in column '{col}'",
                    column_name=col,
                    actual_value=str(actual_type),
                    expected_value=expected_type.__name__,
                    suggestion=f"Convert column '{col}' to {expected_type.__name__}",
                    context={'sheet': sheet_name}
                ))
        
        return errors
    
    @staticmethod
    def validate_null_values(
        df: pd.DataFrame,
        non_null_columns: List[str],
        sheet_name: str = "Sheet"
    ) -> List[ValidationError]:
        """
        Validate null values in required columns.
        
        Args:
            df: DataFrame to validate
            non_null_columns: Columns that cannot have null values
            sheet_name: Sheet name for context
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for col in non_null_columns:
            if col not in df.columns:
                continue
            
            null_rows = df[df[col].isna()].index.tolist()
            
            for row_idx in null_rows:
                errors.append(ValidationError(
                    error_code=ErrorCode.SCHEMA_NULL_VALUE,
                    severity=ErrorSeverity.ERROR,
                    message=f"Null value in required column",
                    row_number=row_idx + 2,  # +2 for Excel (1-indexed + header)
                    column_name=col,
                    actual_value=None,
                    expected_value="Non-null value",
                    suggestion=f"Provide a value for '{col}' in row {row_idx + 2}",
                    context={'sheet': sheet_name}
                ))
        
        return errors
    
    @staticmethod
    def validate_value_ranges(
        df: pd.DataFrame,
        range_constraints: Dict[str, tuple],
        sheet_name: str = "Sheet"
    ) -> List[ValidationError]:
        """
        Validate numeric values are within allowed ranges.
        
        Args:
            df: DataFrame to validate
            range_constraints: Dict of {column: (min, max)}
            sheet_name: Sheet name for context
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for col, (min_val, max_val) in range_constraints.items():
            if col not in df.columns:
                continue
            
            # Find out-of-range values
            out_of_range = df[
                (df[col].notna()) &
                ((df[col] < min_val) | (df[col] > max_val))
            ]
            
            for idx, row in out_of_range.iterrows():
                errors.append(ValidationError(
                    error_code=ErrorCode.SCHEMA_OUT_OF_RANGE,
                    severity=ErrorSeverity.ERROR,
                    message=f"Value out of allowed range",
                    row_number=idx + 2,
                    column_name=col,
                    actual_value=row[col],
                    expected_value=f"Between {min_val} and {max_val}",
                    suggestion=f"Ensure '{col}' is between {min_val} and {max_val}",
                    context={'sheet': sheet_name}
                ))
        
        return errors


# ============================================================================
# LEVEL 2: SEMANTIC VALIDATION (Business Logic)
# ============================================================================

class SemanticValidator:
    """Validates business logic and semantic rules."""
    
    @staticmethod
    def validate_total_matches_sum(
        df: pd.DataFrame,
        line_item_col: str,
        total_col: str,
        tolerance: float = 0.01,
        sheet_name: str = "Sheet"
    ) -> List[ValidationError]:
        """
        Validate that total matches sum of line items.
        
        Args:
            df: DataFrame to validate
            line_item_col: Column with line item values
            total_col: Column with total value
            tolerance: Acceptable difference
            sheet_name: Sheet name for context
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if line_item_col not in df.columns or total_col not in df.columns:
            return errors
        
        for idx, row in df.iterrows():
            if pd.isna(row[total_col]):
                continue
            
            calculated_total = df[line_item_col].sum()
            actual_total = row[total_col]
            
            if abs(calculated_total - actual_total) > tolerance:
                errors.append(ValidationError(
                    error_code=ErrorCode.BUSINESS_TOTAL_MISMATCH,
                    severity=ErrorSeverity.ERROR,
                    message="Total does not match sum of line items",
                    row_number=idx + 2,
                    column_name=total_col,
                    actual_value=actual_total,
                    expected_value=calculated_total,
                    suggestion=f"Verify line item values or update total to {calculated_total:.2f}",
                    context={'sheet': sheet_name, 'difference': abs(calculated_total - actual_total)}
                ))
        
        return errors
    
    @staticmethod
    def validate_no_duplicates(
        df: pd.DataFrame,
        unique_columns: List[str],
        sheet_name: str = "Sheet"
    ) -> List[ValidationError]:
        """
        Validate no duplicate values in unique columns.
        
        Args:
            df: DataFrame to validate
            unique_columns: Columns that must have unique values
            sheet_name: Sheet name for context
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for col in unique_columns:
            if col not in df.columns:
                continue
            
            # Find duplicates
            duplicates = df[df.duplicated(subset=[col], keep=False)]
            
            if not duplicates.empty:
                duplicate_values = duplicates[col].unique()
                
                for dup_val in duplicate_values:
                    dup_rows = df[df[col] == dup_val].index.tolist()
                    
                    errors.append(ValidationError(
                        error_code=ErrorCode.BUSINESS_DUPLICATE_ID,
                        severity=ErrorSeverity.ERROR,
                        message=f"Duplicate value found in unique column",
                        column_name=col,
                        actual_value=dup_val,
                        suggestion=f"Remove or update duplicate entries in rows {[r+2 for r in dup_rows]}",
                        context={'sheet': sheet_name, 'duplicate_rows': [r+2 for r in dup_rows]}
                    ))
        
        return errors
    
    @staticmethod
    def validate_date_logic(
        df: pd.DataFrame,
        start_date_col: str,
        end_date_col: str,
        sheet_name: str = "Sheet"
    ) -> List[ValidationError]:
        """
        Validate date logic (end date after start date).
        
        Args:
            df: DataFrame to validate
            start_date_col: Start date column
            end_date_col: End date column
            sheet_name: Sheet name for context
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if start_date_col not in df.columns or end_date_col not in df.columns:
            return errors
        
        for idx, row in df.iterrows():
            start_date = row[start_date_col]
            end_date = row[end_date_col]
            
            if pd.isna(start_date) or pd.isna(end_date):
                continue
            
            try:
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                
                if end_dt < start_dt:
                    errors.append(ValidationError(
                        error_code=ErrorCode.BUSINESS_INVALID_DATE,
                        severity=ErrorSeverity.ERROR,
                        message="End date is before start date",
                        row_number=idx + 2,
                        column_name=end_date_col,
                        actual_value=end_date,
                        expected_value=f"Date after {start_date}",
                        suggestion="Ensure end date is after start date",
                        context={'sheet': sheet_name, 'start_date': str(start_date)}
                    ))
            except Exception:
                pass  # Invalid date format handled by structural validation
        
        return errors
    
    @staticmethod
    def validate_positive_values(
        df: pd.DataFrame,
        positive_columns: List[str],
        sheet_name: str = "Sheet"
    ) -> List[ValidationError]:
        """
        Validate that specified columns have only positive values.
        
        Args:
            df: DataFrame to validate
            positive_columns: Columns that must be positive
            sheet_name: Sheet name for context
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for col in positive_columns:
            if col not in df.columns:
                continue
            
            negative_rows = df[(df[col].notna()) & (df[col] < 0)]
            
            for idx, row in negative_rows.iterrows():
                errors.append(ValidationError(
                    error_code=ErrorCode.BUSINESS_NEGATIVE_VALUE,
                    severity=ErrorSeverity.ERROR,
                    message=f"Negative value in column that must be positive",
                    row_number=idx + 2,
                    column_name=col,
                    actual_value=row[col],
                    expected_value="Positive value",
                    suggestion=f"Ensure '{col}' is a positive number",
                    context={'sheet': sheet_name}
                ))
        
        return errors


# ============================================================================
# LEVEL 3: ANOMALY DETECTION
# ============================================================================

class AnomalyDetector:
    """Detects patterns and anomalies in data."""
    
    @staticmethod
    def detect_outliers(
        df: pd.DataFrame,
        numeric_columns: List[str],
        threshold_multiplier: float = 10.0,
        sheet_name: str = "Sheet"
    ) -> List[ValidationError]:
        """
        Detect outliers using statistical methods.
        
        Args:
            df: DataFrame to analyze
            numeric_columns: Columns to check for outliers
            threshold_multiplier: Multiplier for mean to detect outliers
            sheet_name: Sheet name for context
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        for col in numeric_columns:
            if col not in df.columns:
                continue
            
            # Calculate statistics
            values = df[col].dropna()
            if len(values) < 3:
                continue
            
            mean_val = values.mean()
            std_val = values.std()
            
            if mean_val == 0:
                continue
            
            # Detect outliers
            outliers = df[
                (df[col].notna()) &
                (df[col] > mean_val * threshold_multiplier)
            ]
            
            for idx, row in outliers.iterrows():
                warnings.append(ValidationError(
                    error_code=ErrorCode.ANOMALY_OUTLIER,
                    severity=ErrorSeverity.WARNING,
                    message=f"Potential outlier detected",
                    row_number=idx + 2,
                    column_name=col,
                    actual_value=row[col],
                    expected_value=f"Typical range: {mean_val:.2f} ± {std_val:.2f}",
                    suggestion="Verify this value is correct",
                    context={
                        'sheet': sheet_name,
                        'mean': mean_val,
                        'std': std_val,
                        'z_score': (row[col] - mean_val) / std_val if std_val > 0 else 0
                    }
                ))
        
        return warnings
    
    @staticmethod
    def detect_repeated_values(
        df: pd.DataFrame,
        columns: List[str],
        min_repetitions: int = 5,
        sheet_name: str = "Sheet"
    ) -> List[ValidationError]:
        """
        Detect suspiciously repeated values.
        
        Args:
            df: DataFrame to analyze
            columns: Columns to check
            min_repetitions: Minimum repetitions to flag
            sheet_name: Sheet name for context
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        for col in columns:
            if col not in df.columns:
                continue
            
            value_counts = df[col].value_counts()
            repeated = value_counts[value_counts >= min_repetitions]
            
            for value, count in repeated.items():
                if pd.isna(value):
                    continue
                
                warnings.append(ValidationError(
                    error_code=ErrorCode.ANOMALY_PATTERN_BREAK,
                    severity=ErrorSeverity.WARNING,
                    message=f"Value repeated {count} times",
                    column_name=col,
                    actual_value=value,
                    suggestion="Verify if this repetition is intentional",
                    context={'sheet': sheet_name, 'repetition_count': count}
                ))
        
        return warnings


# ============================================================================
# COMPREHENSIVE VALIDATOR
# ============================================================================

class ComprehensiveValidator:
    """Combines all validation levels."""
    
    def __init__(self):
        """Initialize comprehensive validator."""
        self.structural = StructuralValidator()
        self.semantic = SemanticValidator()
        self.anomaly = AnomalyDetector()
    
    def validate_dataframe(
        self,
        df: pd.DataFrame,
        validation_rules: Dict[str, Any],
        sheet_name: str = "Sheet"
    ) -> ValidationResult:
        """
        Run comprehensive validation on DataFrame.
        
        Args:
            df: DataFrame to validate
            validation_rules: Validation configuration
            sheet_name: Sheet name for context
            
        Returns:
            ValidationResult with all issues
        """
        result = ValidationResult(is_valid=True)
        
        # Level 1: Structural validation
        if 'required_columns' in validation_rules:
            errors = self.structural.validate_required_columns(
                df, validation_rules['required_columns'], sheet_name
            )
            for error in errors:
                result.add_error(error)
        
        if 'column_types' in validation_rules:
            errors = self.structural.validate_column_types(
                df, validation_rules['column_types'], sheet_name
            )
            for error in errors:
                result.add_error(error)
        
        if 'non_null_columns' in validation_rules:
            errors = self.structural.validate_null_values(
                df, validation_rules['non_null_columns'], sheet_name
            )
            for error in errors:
                result.add_error(error)
        
        # Level 2: Semantic validation
        if 'unique_columns' in validation_rules:
            errors = self.semantic.validate_no_duplicates(
                df, validation_rules['unique_columns'], sheet_name
            )
            for error in errors:
                result.add_error(error)
        
        if 'positive_columns' in validation_rules:
            errors = self.semantic.validate_positive_values(
                df, validation_rules['positive_columns'], sheet_name
            )
            for error in errors:
                result.add_error(error)
        
        # Level 3: Anomaly detection
        if 'detect_outliers' in validation_rules:
            warnings = self.anomaly.detect_outliers(
                df, validation_rules['detect_outliers'], sheet_name=sheet_name
            )
            for warning in warnings:
                result.add_error(warning)
        
        return result
