"""
Enterprise Structured JSON Logger
Production-ready logging with JSON output for log aggregation systems.

Author: Senior DevOps Engineer
Standards: JSON structured logging, Log levels, Context tracking
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from enum import Enum


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """
    Structured JSON logger for production environments.
    Outputs logs in JSON format for easy parsing by log aggregation systems.
    """
    
    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        output_file: Optional[Path] = None,
        include_context: bool = True
    ):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (usually module name)
            level: Minimum log level
            output_file: Optional file path for log output
            include_context: Include contextual information (timestamp, level, etc.)
        """
        self.name = name
        self.level = level
        self.output_file = output_file
        self.include_context = include_context
        
        # Create Python logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(console_handler)
        
        # Add file handler if specified
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(output_file)
            file_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(file_handler)
    
    def _get_formatter(self) -> logging.Formatter:
        """Get JSON formatter."""
        return logging.Formatter('%(message)s')
    
    def _format_log(
        self,
        level: str,
        event: str,
        message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Format log entry as JSON.
        
        Args:
            level: Log level
            event: Event name/type
            message: Optional message
            **kwargs: Additional context fields
        
        Returns:
            JSON formatted log string
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "logger": self.name,
            "event": event
        }
        
        if message:
            log_entry["message"] = message
        
        # Add additional context
        if kwargs:
            log_entry.update(kwargs)
        
        return json.dumps(log_entry)
    
    def debug(self, event: str, message: Optional[str] = None, **kwargs):
        """Log debug message."""
        log_msg = self._format_log("DEBUG", event, message, **kwargs)
        self.logger.debug(log_msg)
    
    def info(self, event: str, message: Optional[str] = None, **kwargs):
        """Log info message."""
        log_msg = self._format_log("INFO", event, message, **kwargs)
        self.logger.info(log_msg)
    
    def warning(self, event: str, message: Optional[str] = None, **kwargs):
        """Log warning message."""
        log_msg = self._format_log("WARNING", event, message, **kwargs)
        self.logger.warning(log_msg)
    
    def error(self, event: str, message: Optional[str] = None, **kwargs):
        """Log error message."""
        log_msg = self._format_log("ERROR", event, message, **kwargs)
        self.logger.error(log_msg)
    
    def critical(self, event: str, message: Optional[str] = None, **kwargs):
        """Log critical message."""
        log_msg = self._format_log("CRITICAL", event, message, **kwargs)
        self.logger.critical(log_msg)
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        **kwargs
    ):
        """
        Log performance metrics.
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            **kwargs: Additional metrics
        """
        self.info(
            event="performance_metric",
            operation=operation,
            duration_ms=round(duration_ms, 2),
            success=success,
            **kwargs
        )
    
    def log_validation_error(
        self,
        error_code: str,
        row_number: Optional[int] = None,
        column_name: Optional[str] = None,
        actual_value: Any = None,
        expected_value: Any = None,
        suggestion: Optional[str] = None
    ):
        """
        Log validation error with structured fields.
        
        Args:
            error_code: Error code
            row_number: Row number where error occurred
            column_name: Column name
            actual_value: Actual value found
            expected_value: Expected value
            suggestion: Suggestion for fixing
        """
        self.error(
            event="validation_error",
            error_code=error_code,
            row_number=row_number,
            column_name=column_name,
            actual_value=str(actual_value) if actual_value is not None else None,
            expected_value=str(expected_value) if expected_value is not None else None,
            suggestion=suggestion
        )
    
    def log_batch_progress(
        self,
        job_id: str,
        total_records: int,
        processed_records: int,
        successful_records: int,
        failed_records: int,
        progress_percent: float
    ):
        """
        Log batch processing progress.
        
        Args:
            job_id: Batch job ID
            total_records: Total records to process
            processed_records: Records processed so far
            successful_records: Successful records
            failed_records: Failed records
            progress_percent: Progress percentage
        """
        self.info(
            event="batch_progress",
            job_id=job_id,
            total_records=total_records,
            processed_records=processed_records,
            successful_records=successful_records,
            failed_records=failed_records,
            progress_percent=round(progress_percent, 2)
        )


# Global logger instance
_global_logger: Optional[StructuredLogger] = None


def get_structured_logger(
    name: str = "enterprise_system",
    level: LogLevel = LogLevel.INFO,
    output_file: Optional[Path] = None
) -> StructuredLogger:
    """
    Get or create structured logger instance.
    
    Args:
        name: Logger name
        level: Log level
        output_file: Optional output file
    
    Returns:
        StructuredLogger instance
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = StructuredLogger(
            name=name,
            level=level,
            output_file=output_file
        )
    
    return _global_logger


# Example usage
if __name__ == "__main__":
    # Create logger
    logger = get_structured_logger(
        name="test_logger",
        level=LogLevel.DEBUG,
        output_file=Path("logs/test.log")
    )
    
    # Log various events
    logger.info("application_started", message="Application initialized successfully")
    
    logger.log_performance(
        operation="excel_processing",
        duration_ms=1234.56,
        success=True,
        rows_processed=1000
    )
    
    logger.log_validation_error(
        error_code="E2001",
        row_number=14,
        column_name="amount",
        actual_value=10000,
        expected_value=9500,
        suggestion="Verify line item values"
    )
    
    logger.log_batch_progress(
        job_id="batch_001",
        total_records=100,
        processed_records=50,
        successful_records=48,
        failed_records=2,
        progress_percent=50.0
    )
    
    logger.error(
        "processing_failed",
        message="Failed to process record",
        record_id="REC-123",
        error_type="ValueError"
    )
