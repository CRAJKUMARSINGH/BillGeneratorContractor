"""
Enterprise-Grade Batch Job Runner
Orchestrates processing of thousands of records with retry logic and reporting.

Author: Senior Batch Processing Engineer
Standards: Fault tolerance, Progress tracking, Comprehensive reporting
"""

import logging
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import traceback


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class JobStatus(Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class RecordStatus(Enum):
    """Individual record status."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


# Batch processing defaults
DEFAULT_MAX_WORKERS = 4
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0  # seconds
DEFAULT_TIMEOUT = 300  # seconds per record


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class RetryPolicy:
    """Retry policy configuration."""
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay: float = DEFAULT_RETRY_DELAY
    exponential_backoff: bool = True
    retry_on_errors: List[str] = field(default_factory=lambda: ["*"])  # Retry on all errors


@dataclass
class BatchConfig:
    """Batch processing configuration."""
    max_workers: int = DEFAULT_MAX_WORKERS
    timeout_per_record: int = DEFAULT_TIMEOUT
    continue_on_error: bool = True
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    save_intermediate: bool = True
    output_dir: Path = field(default_factory=lambda: Path("OUTPUT/batch"))


@dataclass
class RecordResult:
    """Result of processing a single record."""
    record_id: str
    status: RecordStatus
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    retry_count: int = 0
    processing_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        return data


@dataclass
class JobResult:
    """Result of batch job execution."""
    job_id: str
    status: JobStatus
    total_records: int
    successful_records: int
    failed_records: int
    skipped_records: int
    start_time: str
    end_time: Optional[str] = None
    total_duration: float = 0.0
    record_results: List[RecordResult] = field(default_factory=list)
    errors_summary: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        data['record_results'] = [r.to_dict() for r in self.record_results]
        return data
    
    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_records == 0:
            return 0.0
        return (self.successful_records / self.total_records) * 100
    
    def get_failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_records == 0:
            return 0.0
        return (self.failed_records / self.total_records) * 100


# ============================================================================
# BATCH JOB RUNNER
# ============================================================================

class BatchJobRunner:
    """
    Enterprise-grade batch job runner with retry logic and reporting.
    """
    
    def __init__(
        self,
        config: Optional[BatchConfig] = None,
        job_id: Optional[str] = None
    ):
        """
        Initialize batch job runner.
        
        Args:
            config: Batch configuration
            job_id: Optional job identifier
        """
        self.config = config or BatchConfig()
        self.job_id = job_id or self._generate_job_id()
        
        # Create output directories
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self.success_dir = self.config.output_dir / "success"
        self.failed_dir = self.config.output_dir / "failed"
        self.logs_dir = self.config.output_dir / "logs"
        
        for dir_path in [self.success_dir, self.failed_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            f"BatchJobRunner initialized: "
            f"job_id={self.job_id}, workers={self.config.max_workers}"
        )
    
    def _generate_job_id(self) -> str:
        """Generate unique job ID."""
        return f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def run_batch(
        self,
        records: List[Dict[str, Any]],
        process_func: Callable[[Dict[str, Any]], Dict[str, Any]],
        record_id_key: str = "id"
    ) -> JobResult:
        """
        Run batch processing job.
        
        Args:
            records: List of records to process
            process_func: Function to process each record
            record_id_key: Key to extract record ID
            
        Returns:
            JobResult with comprehensive results
        """
        start_time = datetime.now()
        
        # Initialize job result
        job_result = JobResult(
            job_id=self.job_id,
            status=JobStatus.RUNNING,
            total_records=len(records),
            successful_records=0,
            failed_records=0,
            skipped_records=0,
            start_time=start_time.isoformat()
        )
        
        logger.info(f"Starting batch job: {self.job_id} ({len(records)} records)")
        
        # Process records
        if self.config.max_workers > 1:
            # Parallel processing
            job_result.record_results = self._process_parallel(
                records, process_func, record_id_key
            )
        else:
            # Sequential processing
            job_result.record_results = self._process_sequential(
                records, process_func, record_id_key
            )
        
        # Calculate statistics
        for record_result in job_result.record_results:
            if record_result.status == RecordStatus.SUCCESS:
                job_result.successful_records += 1
            elif record_result.status == RecordStatus.FAILED:
                job_result.failed_records += 1
                # Track error types
                error_type = record_result.error_message or "Unknown"
                job_result.errors_summary[error_type] = \
                    job_result.errors_summary.get(error_type, 0) + 1
            elif record_result.status == RecordStatus.SKIPPED:
                job_result.skipped_records += 1
        
        # Finalize job
        end_time = datetime.now()
        job_result.end_time = end_time.isoformat()
        job_result.total_duration = (end_time - start_time).total_seconds()
        
        # Determine final status
        if job_result.failed_records == 0:
            job_result.status = JobStatus.SUCCESS
        elif job_result.successful_records == 0:
            job_result.status = JobStatus.FAILED
        else:
            job_result.status = JobStatus.PARTIAL
        
        # Save results
        self._save_job_report(job_result)
        
        logger.info(
            f"Batch job completed: {self.job_id} | "
            f"Success: {job_result.successful_records}/{job_result.total_records} | "
            f"Failed: {job_result.failed_records} | "
            f"Duration: {job_result.total_duration:.2f}s"
        )
        
        return job_result
    
    def _process_sequential(
        self,
        records: List[Dict[str, Any]],
        process_func: Callable,
        record_id_key: str
    ) -> List[RecordResult]:
        """Process records sequentially."""
        results = []
        
        for idx, record in enumerate(records, 1):
            record_id = str(record.get(record_id_key, f"record_{idx}"))
            logger.info(f"Processing {idx}/{len(records)}: {record_id}")
            
            result = self._process_single_record(
                record_id, record, process_func
            )
            results.append(result)
            
            # Save intermediate results if enabled
            if self.config.save_intermediate:
                self._save_record_result(result)
        
        return results
    
    def _process_parallel(
        self,
        records: List[Dict[str, Any]],
        process_func: Callable,
        record_id_key: str
    ) -> List[RecordResult]:
        """Process records in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all tasks
            future_to_record = {}
            for idx, record in enumerate(records, 1):
                record_id = str(record.get(record_id_key, f"record_{idx}"))
                future = executor.submit(
                    self._process_single_record,
                    record_id,
                    record,
                    process_func
                )
                future_to_record[future] = (idx, record_id)
            
            # Collect results as they complete
            for future in as_completed(future_to_record):
                idx, record_id = future_to_record[future]
                try:
                    result = future.result(timeout=self.config.timeout_per_record)
                    results.append(result)
                    logger.info(f"Completed {idx}/{len(records)}: {record_id}")
                    
                    # Save intermediate results
                    if self.config.save_intermediate:
                        self._save_record_result(result)
                        
                except Exception as e:
                    logger.error(f"Future failed for {record_id}: {e}")
                    # Create failed result
                    result = RecordResult(
                        record_id=record_id,
                        status=RecordStatus.FAILED,
                        input_data={},
                        error_message=f"Future execution failed: {e}"
                    )
                    results.append(result)
        
        # Sort results by original order
        return results
    
    def _process_single_record(
        self,
        record_id: str,
        record: Dict[str, Any],
        process_func: Callable
    ) -> RecordResult:
        """
        Process a single record with retry logic.
        
        Args:
            record_id: Record identifier
            record: Record data
            process_func: Processing function
            
        Returns:
            RecordResult
        """
        retry_count = 0
        last_error = None
        
        while retry_count <= self.config.retry_policy.max_retries:
            start_time = time.time()
            
            try:
                # Process record
                output_data = process_func(record)
                
                # Success
                processing_time = time.time() - start_time
                return RecordResult(
                    record_id=record_id,
                    status=RecordStatus.SUCCESS,
                    input_data=record,
                    output_data=output_data,
                    retry_count=retry_count,
                    processing_time=processing_time
                )
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                if retry_count <= self.config.retry_policy.max_retries:
                    # Calculate retry delay
                    if self.config.retry_policy.exponential_backoff:
                        delay = self.config.retry_policy.retry_delay * (2 ** (retry_count - 1))
                    else:
                        delay = self.config.retry_policy.retry_delay
                    
                    logger.warning(
                        f"Record {record_id} failed (attempt {retry_count}), "
                        f"retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    # Max retries exceeded
                    processing_time = time.time() - start_time
                    logger.error(f"Record {record_id} failed after {retry_count} attempts: {e}")
                    
                    return RecordResult(
                        record_id=record_id,
                        status=RecordStatus.FAILED,
                        input_data=record,
                        error_message=str(e),
                        error_traceback=traceback.format_exc(),
                        retry_count=retry_count - 1,
                        processing_time=processing_time
                    )
        
        # Should not reach here
        return RecordResult(
            record_id=record_id,
            status=RecordStatus.FAILED,
            input_data=record,
            error_message="Unknown error"
        )
    
    def _save_record_result(self, result: RecordResult):
        """Save individual record result."""
        try:
            if result.status == RecordStatus.SUCCESS:
                output_dir = self.success_dir
            else:
                output_dir = self.failed_dir
            
            output_file = output_dir / f"{result.record_id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save record result {result.record_id}: {e}")
    
    def _save_job_report(self, job_result: JobResult):
        """Save comprehensive job report."""
        try:
            # Save JSON report
            report_file = self.logs_dir / f"{self.job_id}_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(job_result.to_dict(), f, indent=2)
            
            # Save summary text report
            summary_file = self.logs_dir / f"{self.job_id}_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(self._generate_summary_report(job_result))
            
            logger.info(f"Job report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save job report: {e}")
    
    def _generate_summary_report(self, job_result: JobResult) -> str:
        """Generate human-readable summary report."""
        lines = [
            "=" * 80,
            f"BATCH JOB REPORT: {job_result.job_id}",
            "=" * 80,
            "",
            f"Status: {job_result.status.value.upper()}",
            f"Start Time: {job_result.start_time}",
            f"End Time: {job_result.end_time}",
            f"Duration: {job_result.total_duration:.2f} seconds",
            "",
            "STATISTICS:",
            f"  Total Records: {job_result.total_records}",
            f"  Successful: {job_result.successful_records} ({job_result.get_success_rate():.1f}%)",
            f"  Failed: {job_result.failed_records} ({job_result.get_failure_rate():.1f}%)",
            f"  Skipped: {job_result.skipped_records}",
            "",
        ]
        
        if job_result.errors_summary:
            lines.append("ERROR SUMMARY:")
            for error_type, count in sorted(
                job_result.errors_summary.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                lines.append(f"  {error_type}: {count} occurrences")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def run_batch_job(
    records: List[Dict[str, Any]],
    process_func: Callable,
    config: Optional[BatchConfig] = None,
    **kwargs
) -> JobResult:
    """
    Convenience function to run batch job.
    
    Args:
        records: List of records to process
        process_func: Processing function
        config: Batch configuration
        **kwargs: Additional arguments for BatchJobRunner
        
    Returns:
        JobResult
    """
    runner = BatchJobRunner(config=config, **kwargs)
    return runner.run_batch(records, process_func)
