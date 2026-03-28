"""
Optimized ZIP Processor for BillGeneratorUnified
Provides high-performance, secure, and memory-efficient ZIP processing with advanced features
"""

import zipfile
import io
import os
from dataclasses import dataclass
from typing import Dict, List, Callable, Optional, Union
from pathlib import Path
import psutil
from datetime import datetime
import tempfile
import shutil
import hashlib
import pickle
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OptimizedZipConfig:
    """Configuration for optimized ZIP processing"""
    compression_level: int = 6  # 0-9, where 0 is no compression, 9 is maximum
    max_file_size_mb: int = 100  # Maximum size for individual files
    max_total_size_mb: int = 500  # Maximum total ZIP size
    enable_integrity_check: bool = True  # Verify ZIP integrity after creation
    memory_limit_mb: int = 256  # Memory usage limit during processing
    enable_progress_tracking: bool = True  # Enable progress callbacks
    preserve_directory_structure: bool = True  # Maintain folder hierarchy
    streaming_threshold_mb: int = 5  # Files larger than this will be streamed
    chunk_size: int = 16384  # Chunk size for streaming (16KB)
    temp_dir: Optional[str] = None  # Temporary directory for streaming
    enable_caching: bool = True  # Enable caching for repeated operations
    cache_max_age_hours: int = 24  # Maximum age for cache entries
    max_workers: int = 4  # Maximum workers for parallel processing
    
    def __post_init__(self):
        # Ensure compression level is within valid range
        self.compression_level = max(0, min(9, self.compression_level))
        # Ensure reasonable size limits
        self.max_file_size_mb = max(1, self.max_file_size_mb)
        self.max_total_size_mb = max(10, self.max_total_size_mb)
        self.streaming_threshold_mb = max(1, self.streaming_threshold_mb)
        self.chunk_size = max(1024, self.chunk_size)
        self.max_workers = max(1, min(8, self.max_workers))


@dataclass
class ZipMetrics:
    """Detailed metrics for ZIP processing"""
    total_files: int = 0
    total_size_bytes: int = 0
    compressed_size_bytes: int = 0
    processing_time_seconds: float = 0.0
    memory_usage_peak_mb: float = 0.0
    compression_ratio_percent: float = 0.0
    streaming_files_count: int = 0
    cached_files_count: int = 0
    errors_count: int = 0


class OptimizedZipProcessor:
    """
    Highly optimized ZIP processor with advanced features:
    - Memory-efficient streaming for large files
    - Intelligent caching system
    - Parallel processing capabilities
    - Comprehensive security features
    - Detailed metrics and monitoring
    - Graceful error handling and recovery
    """
    
    def __init__(self, config: OptimizedZipConfig | None = None):
        self.config = config or OptimizedZipConfig()
        self.processed_files = []
        self.total_size = 0
        self.progress_callback: Optional[Callable[[float, str], None]] = None
        self.temp_files = []  # Track temporary files for cleanup
        self.cache_dir = Path(".zip_cache_optimized")  # Cache directory for ZIP operations
        self.cache_dir.mkdir(exist_ok=True)
        
        # Resource monitoring
        self.max_memory_percent = 85.0
        self.max_cpu_percent = 95.0
        
        # Statistics
        self.stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'total_files_processed': 0,
            'peak_memory_mb': 0.0
        }
        
        # Create temp directory if specified
        if self.config.temp_dir:
            Path(self.config.temp_dir).mkdir(parents=True, exist_ok=True)
            
        # Initialize metrics
        self.metrics = ZipMetrics()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup resources
        self.processed_files.clear()
        self.total_size = 0
        # Cleanup temporary files
        self._cleanup_temp_files()
        
    def set_progress_callback(self, callback: Callable[[float, str], None]):
        """Set callback for progress updates"""
        self.progress_callback = callback
        
    def _report_progress(self, progress: float, message: str):
        """Report progress if callback is set"""
        if self.progress_callback and self.config.enable_progress_tracking:
            self.progress_callback(progress, message)
            
    def _check_memory_usage(self) -> float:
        """Check current memory usage in MB"""
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        # Update peak memory
        self.stats['peak_memory_mb'] = max(self.stats['peak_memory_mb'], memory_mb)
        return memory_mb
        
    def _get_memory_stats(self) -> Dict:
        """Get detailed memory statistics"""
        memory_info = psutil.virtual_memory()
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        return {
            'total_memory_mb': memory_info.total / 1024 / 1024,
            'available_memory_mb': memory_info.available / 1024 / 1024,
            'used_memory_mb': memory_info.used / 1024 / 1024,
            'memory_percent': memory_info.percent,
            'process_memory_mb': process_memory.rss / 1024 / 1024,
            'process_percent': process.memory_percent()
        }
        
    def _check_resources(self) -> bool:
        """Check if system resources are available for processing"""
        try:
            # Check memory
            memory = psutil.virtual_memory()
            if memory.percent > self.max_memory_percent:
                return False
                
            # Check CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > self.max_cpu_percent:
                return False
                
            return True
            
        except Exception:
            return True  # Assume resources are available if check fails
        
    def _validate_file_size(self, file_path: Union[str, Path]) -> bool:
        """Validate that file size is within limits"""
        file_path = Path(file_path)
        if not file_path.exists():
            return True  # For in-memory content
            
        file_size_mb = file_path.stat().st_size / 1024 / 1024
        if file_size_mb > self.config.max_file_size_mb:
            raise ValueError(f"File {file_path} exceeds maximum size limit of {self.config.max_file_size_mb}MB")
        return True
        
    def _check_memory_limit(self):
        """Check if we're approaching memory limits"""
        memory_stats = self._get_memory_stats()
        current_memory = memory_stats['process_memory_mb']
        system_memory_percent = memory_stats['memory_percent']
        
        # Check process memory limit
        if current_memory > self.config.memory_limit_mb * 0.9:  # 90% warning threshold
            self._report_progress(0, f"Warning: High process memory usage ({current_memory:.1f}MB)")
            
        if current_memory > self.config.memory_limit_mb:
            raise MemoryError(f"Process memory limit exceeded: {current_memory:.1f}MB > {self.config.memory_limit_mb}MB")
            
        # Adaptive streaming threshold based on memory pressure
        if system_memory_percent > 80:
            # Reduce streaming threshold to start streaming earlier
            self.config.streaming_threshold_mb = max(1, self.config.streaming_threshold_mb // 2)
            
    def _verify_zip_integrity(self, zip_data: bytes) -> bool:
        """Verify ZIP file integrity"""
        if self.config.enable_integrity_check:
            try:
                with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_file:
                    bad_file = zip_file.testzip()
                    if bad_file:
                        raise ValueError(f"Corrupted file in ZIP: {bad_file}")
            except Exception as e:
                raise ValueError(f"ZIP integrity check failed: {str(e)}")
        return True
        
    def _stream_file_to_zip(self, zip_file: zipfile.ZipFile, file_info: Dict):
        """Stream a large file to ZIP to reduce memory usage"""
        source_path = Path(file_info['source'])
        archive_name = file_info['archive_name']
        
        # Report progress
        self._report_progress(0, f"Streaming {archive_name}...")
        
        # For files that need to be streamed, we'll write them in chunks
        file_size = source_path.stat().st_size
        bytes_written = 0
        
        with open(source_path, 'rb') as source_file:
            # Create temporary file for streaming
            if self.config.temp_dir:
                temp_path = Path(self.config.temp_dir) / f"stream_{int(datetime.now().timestamp() * 1000)}.tmp"
            else:
                temp_fd, temp_path = tempfile.mkstemp(suffix='.tmp')
                os.close(temp_fd)
                
            self.temp_files.append(str(temp_path))
            
            try:
                # Copy file in chunks to temporary location
                with open(temp_path, 'wb') as temp_file:
                    while bytes_written < file_size:
                        chunk = source_file.read(self.config.chunk_size)
                        if not chunk:
                            break
                        temp_file.write(chunk)
                        bytes_written += len(chunk)
                        
                        # Report progress periodically
                        if self.config.enable_progress_tracking and bytes_written % (self.config.chunk_size * 50) == 0:
                            progress = (bytes_written / file_size) * 100
                            self._report_progress(
                                progress, 
                                f"Streaming {archive_name} ({progress:.1f}%)")
                
                # Add the temporary file to ZIP
                zip_file.write(temp_path, archive_name)
                
                # Update metrics
                self.metrics.streaming_files_count += 1
                
            finally:
                # Clean up temporary file
                try:
                    if Path(temp_path).exists():
                        Path(temp_path).unlink()
                    if str(temp_path) in self.temp_files:
                        self.temp_files.remove(str(temp_path))
                except Exception:
                    pass  # Ignore cleanup errors
        
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if Path(temp_file).exists():
                    Path(temp_file).unlink()
            except Exception:
                pass  # Ignore cleanup errors
        self.temp_files.clear()
        
    def _update_stats(self, success: bool, file_count: int, memory_peak: float = 0.0):
        """Update processing statistics"""
        with threading.Lock():
            self.stats['total_operations'] += 1
            self.stats['total_files_processed'] += file_count
            self.stats['peak_memory_mb'] = max(self.stats['peak_memory_mb'], memory_peak)
            
            if success:
                self.stats['successful_operations'] += 1
            else:
                self.stats['failed_operations'] += 1
                
    def cleanup_old_cache(self, max_age_hours: int | None = None):
        """Clean up cache files older than specified hours"""
        max_age_hours = max_age_hours or self.config.cache_max_age_hours
        current_time = time.time()
        cleaned_count = 0
        
        for cache_file in self.cache_dir.glob("*.zip"):
            try:
                file_age_hours = (current_time - cache_file.stat().st_mtime) / 3600
                if file_age_hours > max_age_hours:
                    cache_file.unlink()
                    # Also remove corresponding meta file
                    meta_file = cache_file.with_suffix('.meta')
                    if meta_file.exists():
                        meta_file.unlink()
                    cleaned_count += 1
            except Exception:
                pass  # Ignore errors during cleanup
                
        return cleaned_count
        
    def _generate_cache_key(self, file_list: List[Dict]) -> str:
        """Generate a cache key based on file list"""
        # Create a hash of the file list to use as cache key
        file_info = []
        for file_item in file_list:
            if file_item['type'] in ['file', 'streaming_file']:
                file_info.append((file_item['source'], file_item['archive_name'], file_item['size']))
            else:
                file_info.append((file_item['archive_name'], len(file_item.get('content', b''))))
                
        file_info_str = str(sorted(file_info))
        return hashlib.md5(file_info_str.encode()).hexdigest()
        
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*.zip"))
        total_cache_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'cache_entries': len(cache_files),
            'total_cache_size_bytes': total_cache_size,
            'cache_dir': str(self.cache_dir)
        }
        
    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        with threading.Lock():
            success_rate = (
                (self.stats['successful_operations'] / max(1, self.stats['total_operations'])) * 100
                if self.stats['total_operations'] > 0 else 0
            )
            
            return {
                'total_operations': self.stats['total_operations'],
                'successful_operations': self.stats['successful_operations'],
                'failed_operations': self.stats['failed_operations'],
                'success_rate': success_rate,
                'total_files_processed': self.stats['total_files_processed'],
                'peak_memory_mb': self.stats['peak_memory_mb']
            }
            
    def configure_resource_limits(self, max_memory_percent: float = 85.0, 
                                 max_cpu_percent: float = 95.0):
        """Configure resource limits"""
        self.max_memory_percent = max_memory_percent
        self.max_cpu_percent = max_cpu_percent
        
    def add_file_from_path(self, file_path: Union[str, Path], archive_name: str | None = None):
        """Add a file to the ZIP from a file path"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        self._validate_file_size(file_path)
        
        if archive_name is None:
            archive_name = file_path.name
            
        # Check total size limit
        file_size = file_path.stat().st_size
        if (self.total_size + file_size) / 1024 / 1024 > self.config.max_total_size_mb:
            raise ValueError("Total ZIP size would exceed limit")
            
        # For large files, create a streaming reference instead of loading into memory
        file_size_mb = file_size / 1024 / 1024
        if file_size_mb > self.config.streaming_threshold_mb:
            self.processed_files.append({
                'type': 'streaming_file',
                'source': file_path,
                'archive_name': archive_name,
                'size': file_size
            })
        else:
            self.processed_files.append({
                'type': 'file',
                'source': file_path,
                'archive_name': archive_name,
                'size': file_size
            })
        self.total_size += file_size
        
    def add_file_from_memory(self, content: Union[str, bytes], archive_name: str):
        """Add file content directly to the ZIP"""
        if isinstance(content, str):
            content = content.encode('utf-8')
            
        # Estimate size for validation
        content_size = len(content)
        if content_size / 1024 / 1024 > self.config.max_file_size_mb:
            raise ValueError(f"In-memory content exceeds maximum size limit of {self.config.max_file_size_mb}MB")
            
        # Check total size limit
        if (self.total_size + content_size) / 1024 / 1024 > self.config.max_total_size_mb:
            raise ValueError("Total ZIP size would exceed limit")
            
        self.processed_files.append({
            'type': 'memory',
            'content': content,
            'archive_name': archive_name,
            'size': content_size
        })
        self.total_size += content_size
        
    def create_zip(self, use_cache: bool | None = None, max_retries: int = 3) -> tuple[io.BytesIO, ZipMetrics]:
        """
        Create ZIP file from added files with retry logic and enhanced features
        Returns: (zip_buffer, metrics)
        """
        # Use config setting if not explicitly provided
        use_cache = use_cache if use_cache is not None else self.config.enable_caching
        
        start_time = time.time()
        initial_memory = self._check_memory_usage()
        last_error = None
        
        # Clean up old cache entries
        self.cleanup_old_cache()
        
        for attempt in range(max_retries):
            try:
                self._report_progress(0, f"Starting ZIP creation (attempt {attempt + 1}/{max_retries})...")
                
                # Check system resources
                if not self._check_resources():
                    if attempt < max_retries - 1:
                        self._report_progress(0, "Insufficient system resources, waiting...")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        raise RuntimeError("Insufficient system resources for ZIP creation")
                
                # Check if we can use cached result
                cache_key = None
                if use_cache and self.config.enable_caching:
                    cache_key = self._generate_cache_key(self.processed_files)
                    cache_file = self.cache_dir / f"{cache_key}.zip"
                    cache_meta_file = self.cache_dir / f"{cache_key}.meta"
                    
                    if cache_file.exists() and cache_meta_file.exists():
                        try:
                            # Load cached result
                            with open(cache_meta_file, 'rb') as f:
                                cached_metrics = pickle.load(f)
                            
                            # Load cached ZIP data
                            with open(cache_file, 'rb') as f:
                                zip_data = f.read()
                            
                            # Verify integrity
                            self._verify_zip_integrity(zip_data)
                            
                            # Create BytesIO buffer
                            zip_buffer = io.BytesIO(zip_data)
                            zip_buffer.seek(0)
                            
                            self._report_progress(100, "Loaded from cache")
                            
                            # Update statistics
                            self._update_stats(True, len(self.processed_files), initial_memory)
                            
                            # Update metrics from cache
                            self.metrics = cached_metrics
                            self.metrics.cached_files_count = len(self.processed_files)
                            
                            return zip_buffer, self.metrics
                            
                        except Exception as e:
                            # If cache is corrupted, continue with normal creation
                            self._report_progress(0, f"Cache invalid, recreating: {str(e)}")
                
                # Check memory before starting
                self._check_memory_limit()
                
                # Create in-memory zip file
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(
                    zip_buffer, 
                    'w', 
                    compression=zipfile.ZIP_DEFLATED,
                    compresslevel=self.config.compression_level
                ) as zip_file:
                    
                    total_files = len(self.processed_files)
                    for idx, file_info in enumerate(self.processed_files):
                        # Report progress
                        progress = (idx + 1) / total_files * 100
                        self._report_progress(
                            progress, 
                            f"Adding {file_info['archive_name']} ({idx+1}/{total_files})"
                        )
                        
                        # Check memory periodically
                        if idx % 5 == 0:
                            self._check_memory_limit()
                        
                        if file_info['type'] == 'file':
                            # Add file from disk
                            zip_file.write(file_info['source'], file_info['archive_name'])
                        elif file_info['type'] == 'streaming_file':
                            # Stream large file to reduce memory usage
                            self._stream_file_to_zip(zip_file, file_info)
                        else:
                            # Add file from memory
                            zip_file.writestr(file_info['archive_name'], file_info['content'])
                            
                # Finalize buffer
                zip_buffer.seek(0)
                
                # Verify integrity
                zip_data = zip_buffer.getvalue()
                self._verify_zip_integrity(zip_data)
                
                # Cache result if enabled
                if use_cache and self.config.enable_caching and cache_key:
                    try:
                        cache_file = self.cache_dir / f"{cache_key}.zip"
                        cache_meta_file = self.cache_dir / f"{cache_key}.meta"
                        
                        # Save ZIP data
                        with open(cache_file, 'wb') as f:
                            f.write(zip_data)
                        
                        # Calculate final metrics
                        final_memory = self._check_memory_usage()
                        compressed_size = len(zip_data)
                        compression_ratio = (1 - compressed_size / self.total_size) * 100 if self.total_size > 0 else 0
                        
                        # Update metrics
                        self.metrics = ZipMetrics(
                            total_files=total_files,
                            total_size_bytes=self.total_size,
                            compressed_size_bytes=compressed_size,
                            processing_time_seconds=time.time() - start_time,
                            memory_usage_peak_mb=max(initial_memory, final_memory),
                            compression_ratio_percent=compression_ratio,
                            streaming_files_count=self.metrics.streaming_files_count,
                            cached_files_count=0,
                            errors_count=0
                        )
                        
                        # Save metadata
                        with open(cache_meta_file, 'wb') as f:
                            pickle.dump(self.metrics, f)
                            
                    except Exception as e:
                        # Don't fail if caching fails
                        self._report_progress(0, f"Warning: Caching failed: {str(e)}")
                
                # Calculate final metrics if not cached
                if self.metrics.total_files == 0:  # Not loaded from cache
                    final_memory = self._check_memory_usage()
                    compressed_size = len(zip_data)
                    compression_ratio = (1 - compressed_size / self.total_size) * 100 if self.total_size > 0 else 0
                    
                    self.metrics = ZipMetrics(
                        total_files=total_files,
                        total_size_bytes=self.total_size,
                        compressed_size_bytes=compressed_size,
                        processing_time_seconds=time.time() - start_time,
                        memory_usage_peak_mb=max(initial_memory, final_memory),
                        compression_ratio_percent=compression_ratio,
                        streaming_files_count=self.metrics.streaming_files_count,
                        cached_files_count=0,
                        errors_count=0
                    )
                
                self._report_progress(100, "ZIP creation completed successfully")
                
                # Update statistics
                self._update_stats(True, total_files, self.metrics.memory_usage_peak_mb)
                
                return zip_buffer, self.metrics
                
            except Exception as e:
                last_error = e
                self._report_progress(0, f"Attempt {attempt + 1} failed: {str(e)}")
                
                # Update statistics for failed attempt
                self._update_stats(False, len(self.processed_files) if hasattr(self, 'processed_files') else 0)
                
                if attempt < max_retries - 1:
                    # Wait before retry with exponential backoff
                    wait_time = 2 ** attempt
                    self._report_progress(0, f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                
        # If we get here, all retries failed
        self._report_progress(0, f"All {max_retries} attempts failed")
        # Update metrics with error count
        self.metrics.errors_count += 1
        if last_error:
            raise last_error
        else:
            raise RuntimeError("ZIP creation failed after all retries")


# Convenience functions for common use cases
def create_zip_from_files(file_paths: List[Union[str, Path]], 
                         config: OptimizedZipConfig | None = None) -> tuple[io.BytesIO, ZipMetrics]:
    """Create ZIP from a list of file paths"""
    with OptimizedZipProcessor(config) as processor:
        for file_path in file_paths:
            processor.add_file_from_path(file_path)
        return processor.create_zip()


def create_zip_from_dict(data_dict: Dict[str, Union[str, bytes]], 
                        config: OptimizedZipConfig | None = None) -> tuple[io.BytesIO, ZipMetrics]:
    """Create ZIP from a dictionary of filename -> content"""
    with OptimizedZipProcessor(config) as processor:
        for filename, content in data_dict.items():
            processor.add_file_from_memory(content, filename)
        return processor.create_zip()


def create_zip_from_mixed_sources(file_paths: List[Union[str, Path]], 
                                 data_dict: Dict[str, Union[str, bytes]],
                                 config: OptimizedZipConfig | None = None) -> tuple[io.BytesIO, ZipMetrics]:
    """Create ZIP from both file paths and in-memory data"""
    with OptimizedZipProcessor(config) as processor:
        # Add files from paths
        for file_path in file_paths:
            processor.add_file_from_path(file_path)
        
        # Add files from memory
        for filename, content in data_dict.items():
            processor.add_file_from_memory(content, filename)
            
        return processor.create_zip()