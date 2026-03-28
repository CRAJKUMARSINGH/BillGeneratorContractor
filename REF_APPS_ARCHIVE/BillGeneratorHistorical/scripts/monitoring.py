"""
Monitoring and telemetry utilities for the Stream Bill Generator
This module provides basic monitoring and usage tracking capabilities.
"""
import json
import time
import hashlib
import os
from typing import Dict, Any, Optional
from datetime import datetime

class UsageMonitor:
    """Monitors application usage and performance metrics"""
    
    def __init__(self, log_file: str = "logs/usage_log.json"):
        """
        Initialize the UsageMonitor
        
        Args:
            log_file (str): Path to the usage log file
        """
        self.log_file = log_file
        self._ensure_log_directory()
    
    def _ensure_log_directory(self) -> None:
        """Ensure the log directory exists"""
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def log_event(self, event: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a usage event
        
        Args:
            event (str): Event name
            context (Dict[str, Any]): Additional context data
        """
        if context is None:
            context = {}
        
        log_entry = {
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            # Silently fail to avoid disrupting main functionality
            pass
    
    def log_performance(self, operation: str, duration: float, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a performance metric
        
        Args:
            operation (str): Operation name
            duration (float): Duration in seconds
            details (Dict[str, Any]): Additional details
        """
        if details is None:
            details = {}
        
        context = {
            "operation": operation,
            "duration": duration,
            "details": details
        }
        
        self.log_event("performance", context)
    
    def log_error(self, error: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an error
        
        Args:
            error (str): Error message
            context (Dict[str, Any]): Additional context
        """
        if context is None:
            context = {}
        
        context["error"] = error
        self.log_event("error", context)

def add_verification_stamp(file_path: str) -> str:
    """
    Add a verification stamp (SHA-256 checksum) to a generated file
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: SHA-256 checksum
    """
    if not os.path.exists(file_path):
        return ""
    
    try:
        # Calculate SHA-256 checksum
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(4096):
                sha256_hash.update(chunk)
        
        checksum = sha256_hash.hexdigest()
        
        # Save checksum to .hash file
        hash_file = file_path + ".hash"
        with open(hash_file, "w") as f:
            f.write(checksum)
        
        return checksum
    except Exception as e:
        print(f"Error creating verification stamp: {e}")
        return ""

def get_system_info() -> Dict[str, Any]:
    """Get basic system information"""
    import platform
    try:
        import psutil  # This might not be available, so we'll handle it gracefully
        psutil_available = True
    except ImportError:
        psutil_available = False
    
    info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "platform_release": platform.release(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }
    
    # Try to get memory info
    if psutil_available:
        try:
            import psutil
            memory = psutil.virtual_memory()
            info["total_memory_gb"] = round(memory.total / (1024**3), 2)
            info["available_memory_gb"] = round(memory.available / (1024**3), 2)
        except:
            info["total_memory_gb"] = "unknown"
            info["available_memory_gb"] = "unknown"
    else:
        info["total_memory_gb"] = "unknown"
        info["available_memory_gb"] = "unknown"
    
    return info

def benchmark_function(func, *args, **kwargs) -> tuple:
    """
    Benchmark a function execution time
    
    Args:
        func: Function to benchmark
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        tuple: (result, execution_time)
    """
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        raise e

# Global monitor instance
_monitor = UsageMonitor()

def get_monitor() -> UsageMonitor:
    """Get the global monitor instance"""
    return _monitor

def log_event(event: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log a usage event"""
    get_monitor().log_event(event, context)

def log_performance(operation: str, duration: float, details: Optional[Dict[str, Any]] = None) -> None:
    """Log a performance metric"""
    get_monitor().log_performance(operation, duration, details)

def log_error(error: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log an error"""
    get_monitor().log_error(error, context)

if __name__ == "__main__":
    # Example usage
    monitor = get_monitor()
    
    # Log a simple event
    monitor.log_event("app_start", {"version": "1.0.0"})
    
    # Log performance
    monitor.log_performance("pdf_generation", 2.5, {"file_size": "1.2MB"})
    
    # Log an error
    monitor.log_error("template_not_found", {"template": "first_page.html"})
    
    print("Monitoring examples completed")