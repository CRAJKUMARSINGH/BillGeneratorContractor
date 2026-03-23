"""
Error Handling and Recovery System for BillGenerator Unified
Provides comprehensive error handling, logging, and recovery mechanisms
"""
import logging
import traceback
import sys
import time
import functools
from typing import Dict, List, Optional, Callable, Any, Type, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import threading
from datetime import datetime

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories"""
    FILE_IO = "file_io"
    MEMORY = "memory"
    NETWORK = "network"
    PROCESSING = "processing"
    VALIDATION = "validation"
    EXTERNAL_SERVICE = "external_service"
    USER_INPUT = "user_input"
    SYSTEM = "system"

@dataclass
class ErrorInfo:
    """Detailed error information"""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    exception_type: str
    traceback_str: str
    context: Dict[str, Any] = field(default_factory=dict)
    user_message: str = ""
    recovery_suggestions: List[str] = field(default_factory=list)
    retry_count: int = 0
    resolved: bool = False

class ErrorHandler:
    """Advanced error handling and recovery system"""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or "error_handler.log"
        self.error_history: List[ErrorInfo] = []
        self.error_callbacks: Dict[ErrorCategory, List[Callable]] = {}
        self.recovery_strategies: Dict[Type[Exception], Callable] = {}
        self._lock = threading.Lock()
        
        # Setup logging
        self._setup_logging()
        
        # Register default recovery strategies
        self._register_default_recovery_strategies()
    
    def _setup_logging(self):
        """Setup comprehensive logging"""
        # Create logger
        self.logger = logging.getLogger('BillGeneratorErrorHandler')
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _register_default_recovery_strategies(self):
        """Register default error recovery strategies"""
        self.recovery_strategies.update({
            MemoryError: self._handle_memory_error,
            FileNotFoundError: self._handle_file_not_found,
            PermissionError: self._handle_permission_error,
            TimeoutError: self._handle_timeout_error,
            ConnectionError: self._handle_connection_error,
            ValueError: self._handle_value_error,
            KeyError: self._handle_key_error,
        })
    
    def handle_error(
        self, 
        exception: Exception, 
        context: Optional[Dict[str, Any]] = None,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        user_message: Optional[str] = None
    ) -> ErrorInfo:
        """Handle an error with comprehensive logging and recovery"""
        
        # Generate error ID
        error_id = f"ERR_{int(time.time())}_{id(exception)}"
        
        # Determine error details
        exception_type = type(exception).__name__
        traceback_str = traceback.format_exc()
        
        # Auto-detect category and severity if not provided
        if category is None:
            category = self._categorize_error(exception)
        
        if severity is None:
            severity = self._determine_severity(exception, category)
        
        # Generate user-friendly message
        if user_message is None:
            user_message = self._generate_user_message(exception, category)
        
        # Create error info
        error_info = ErrorInfo(
            error_id=error_id,
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=str(exception),
            exception_type=exception_type,
            traceback_str=traceback_str,
            context=context or {},
            user_message=user_message,
            recovery_suggestions=self._get_recovery_suggestions(exception, category)
        )
        
        # Log error
        self._log_error(error_info)
        
        # Store in history
        with self._lock:
            self.error_history.append(error_info)
        
        # Call category-specific callbacks
        self._call_error_callbacks(error_info)
        
        # Attempt recovery
        self._attempt_recovery(error_info)
        
        return error_info
    
    def _categorize_error(self, exception: Exception) -> ErrorCategory:
        """Automatically categorize an error"""
        exception_type = type(exception)
        
        category_map = {
            MemoryError: ErrorCategory.MEMORY,
            FileNotFoundError: ErrorCategory.FILE_IO,
            PermissionError: ErrorCategory.FILE_IO,
            TimeoutError: ErrorCategory.NETWORK,
            ConnectionError: ErrorCategory.NETWORK,
            ValueError: ErrorCategory.USER_INPUT,
            KeyError: ErrorCategory.PROCESSING,
            AttributeError: ErrorCategory.PROCESSING,
            ImportError: ErrorCategory.SYSTEM,
            OSError: ErrorCategory.SYSTEM,
        }
        
        return category_map.get(exception_type, ErrorCategory.SYSTEM)
    
    def _determine_severity(self, exception: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity"""
        # Critical errors
        if isinstance(exception, (MemoryError, SystemError)):
            return ErrorSeverity.CRITICAL
        
        # High severity
        if category in [ErrorCategory.SYSTEM, ErrorCategory.MEMORY]:
            return ErrorSeverity.HIGH
        
        # Medium severity
        if category in [ErrorCategory.FILE_IO, ErrorCategory.PROCESSING, ErrorCategory.EXTERNAL_SERVICE]:
            return ErrorSeverity.MEDIUM
        
        # Low severity
        return ErrorSeverity.LOW
    
    def _generate_user_message(self, exception: Exception, category: ErrorCategory) -> str:
        """Generate user-friendly error message"""
        messages = {
            ErrorCategory.FILE_IO: "There was an issue accessing a file. Please check if the file exists and you have permission to access it.",
            ErrorCategory.MEMORY: "The system is running low on memory. Please try again with smaller files or close other applications.",
            ErrorCategory.NETWORK: "There was a network connectivity issue. Please check your internet connection and try again.",
            ErrorCategory.PROCESSING: "There was an issue processing your data. Please check the file format and try again.",
            ErrorCategory.VALIDATION: "The input data is not valid. Please check your data and try again.",
            ErrorCategory.EXTERNAL_SERVICE: "An external service is currently unavailable. Please try again later.",
            ErrorCategory.USER_INPUT: "The input provided is not valid. Please check your input and try again.",
            ErrorCategory.SYSTEM: "A system error occurred. Please try again or contact support if the issue persists.",
        }
        
        base_message = messages.get(category, "An unexpected error occurred. Please try again.")
        
        # Add specific exception info for common cases
        if isinstance(exception, FileNotFoundError):
            return f"File not found: {exception}"
        elif isinstance(exception, PermissionError):
            return f"Permission denied: {exception}"
        elif isinstance(exception, MemoryError):
            return "Not enough memory to complete this operation. Please try with smaller files."
        
        return base_message
    
    def _get_recovery_suggestions(self, exception: Exception, category: ErrorCategory) -> List[str]:
        """Get recovery suggestions for an error"""
        suggestions = {
            ErrorCategory.FILE_IO: [
                "Check if the file exists and is accessible",
                "Verify you have read/write permissions",
                "Ensure the file is not being used by another program",
                "Try using a different file location"
            ],
            ErrorCategory.MEMORY: [
                "Close other applications to free up memory",
                "Try processing smaller files",
                "Restart the application",
                "Increase system RAM if possible"
            ],
            ErrorCategory.NETWORK: [
                "Check your internet connection",
                "Try again in a few moments",
                "Check if firewall is blocking the connection",
                "Try using a different network"
            ],
            ErrorCategory.PROCESSING: [
                "Verify the file format is supported",
                "Check if the file is corrupted",
                "Try with a different file",
                "Ensure all required data is present"
            ],
            ErrorCategory.VALIDATION: [
                "Check all required fields are filled",
                "Verify data format is correct",
                "Remove any special characters if applicable",
                "Refer to the documentation for proper format"
            ]
        }
        
        return suggestions.get(category, ["Try again", "Contact support if issue persists"])
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level"""
        log_message = f"""
Error ID: {error_info.error_id}
Severity: {error_info.severity.value}
Category: {error_info.category.value}
Message: {error_info.message}
User Message: {error_info.user_message}
Context: {json.dumps(error_info.context, indent=2)}
Traceback: {error_info.traceback_str}
        """.strip()
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def _call_error_callbacks(self, error_info: ErrorInfo):
        """Call registered error callbacks"""
        callbacks = self.error_callbacks.get(error_info.category, [])
        for callback in callbacks:
            try:
                callback(error_info)
            except Exception as e:
                self.logger.error(f"Error in error callback: {e}")
    
    def _attempt_recovery(self, error_info: ErrorInfo):
        """Attempt to recover from the error"""
        exception_type = type(eval(error_info.exception_type))
        
        if exception_type in self.recovery_strategies:
            try:
                self.recovery_strategies[exception_type](error_info)
            except Exception as e:
                self.logger.error(f"Recovery strategy failed: {e}")
    
    def _handle_memory_error(self, error_info: ErrorInfo):
        """Handle memory errors"""
        import gc
        gc.collect()
        
        # Try to free up memory
        try:
            from core.utils.memory_manager import get_memory_manager
            memory_manager = get_memory_manager()
            memory_manager.force_cleanup()
        except:
            pass
    
    def _handle_file_not_found(self, error_info: ErrorInfo):
        """Handle file not found errors"""
        # Log missing file for debugging
        if 'file_path' in error_info.context:
            self.logger.warning(f"Missing file: {error_info.context['file_path']}")
    
    def _handle_permission_error(self, error_info: ErrorInfo):
        """Handle permission errors"""
        # Suggest alternative locations
        self.logger.info("Permission error - suggesting temp directory")
    
    def _handle_timeout_error(self, error_info: ErrorInfo):
        """Handle timeout errors"""
        # Increase timeout for next attempt
        if 'timeout' in error_info.context:
            new_timeout = error_info.context['timeout'] * 1.5
            error_info.context['suggested_timeout'] = new_timeout
    
    def _handle_connection_error(self, error_info: ErrorInfo):
        """Handle connection errors"""
        # Suggest retry with exponential backoff
        retry_delay = min(300, 2 ** error_info.retry_count)  # Max 5 minutes
        error_info.context['retry_delay'] = retry_delay
    
    def _handle_value_error(self, error_info: ErrorInfo):
        """Handle value errors"""
        # Provide more specific guidance
        if 'value' in error_info.context:
            self.logger.warning(f"Invalid value: {error_info.context['value']}")
    
    def _handle_key_error(self, error_info: ErrorInfo):
        """Handle key errors"""
        # Suggest available keys
        if 'available_keys' in error_info.context:
            available = error_info.context['available_keys']
            self.logger.info(f"Available keys: {available}")
    
    def register_error_callback(self, category: ErrorCategory, callback: Callable[[ErrorInfo], None]):
        """Register a callback for specific error category"""
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)
    
    def register_recovery_strategy(self, exception_type: Type[Exception], strategy: Callable[[ErrorInfo], None]):
        """Register a custom recovery strategy"""
        self.recovery_strategies[exception_type] = strategy
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        if not self.error_history:
            return {}
        
        # Count by category
        category_counts = {}
        severity_counts = {}
        
        for error in self.error_history:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
        
        # Recent errors (last hour)
        recent_time = datetime.now().timestamp() - 3600
        recent_errors = [e for e in self.error_history if e.timestamp.timestamp() > recent_time]
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors': len(recent_errors),
            'category_breakdown': category_counts,
            'severity_breakdown': severity_counts,
            'most_common_category': max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None,
            'error_rate': len(recent_errors) / 60  # Errors per minute
        }
    
    def export_error_report(self, file_path: str):
        """Export detailed error report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_error_stats(),
            'errors': [
                {
                    'error_id': e.error_id,
                    'timestamp': e.timestamp.isoformat(),
                    'severity': e.severity.value,
                    'category': e.category.value,
                    'message': e.message,
                    'user_message': e.user_message,
                    'exception_type': e.exception_type,
                    'context': e.context,
                    'recovery_suggestions': e.recovery_suggestions,
                    'retry_count': e.retry_count,
                    'resolved': e.resolved
                }
                for e in self.error_history[-100:]  # Last 100 errors
            ]
        }
        
        with open(file_path, 'w') as f:
            json.dump(report, f, indent=2)

# Global error handler
_global_error_handler: Optional[ErrorHandler] = None

def get_error_handler() -> ErrorHandler:
    """Get or create global error handler"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler

def handle_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    reraise: bool = False
) -> ErrorInfo:
    """Handle an exception using the global error handler"""
    error_handler = get_error_handler()
    error_info = error_handler.handle_error(exception, context)
    
    if reraise:
        raise exception
    
    return error_info

def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    context: Optional[Dict[str, Any]] = None,
    reraise: bool = False,
    **kwargs
) -> Any:
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_info = handle_exception(e, context, reraise=reraise)
        return default_return

def error_boundary(
    default_return: Any = None,
    context: Optional[Dict[str, Any]] = None,
    reraise: bool = False
):
    """Decorator for adding error boundary to functions"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return safe_execute(func, *args, default_return=default_return, 
                            context=context, reraise=reraise, **kwargs)
        return wrapper
    return decorator

class RetryManager:
    """Manage retry logic with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def execute_with_retry(
        self, 
        func: Callable, 
        *args, 
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    break
                
                # Calculate delay with exponential backoff
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                
                # Log retry attempt
                error_handler = get_error_handler()
                error_info = error_handler.handle_error(
                    e, 
                    context={**(context or {}), 'attempt': attempt + 1, 'max_retries': self.max_retries + 1}
                )
                error_info.retry_count = attempt + 1
                
                # Wait before retry
                time.sleep(delay)
        
        # All retries failed
        raise last_exception