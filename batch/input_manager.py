"""
Brilliant Batch Input Management System (BBIMS)

A robust, production-grade system for managing batch bill processing inputs.
Supports both individual and batch processing with comprehensive validation.

Features:
- Organized folder structure for input management
- Automatic validation of input files
- Support for files with/without extra items
- Atomic file operations to prevent corruption
- Comprehensive logging and reporting
- Integration with batch processing pipeline
"""
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import re

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class InputFileMetadata:
    """Metadata for each input file."""
    filename: str
    filepath: str
    has_extra_items: bool = False
    file_size_bytes: int = 0
    created_at: str = ""
    status: str = "pending"  # pending, processing, completed, failed, quarantined
    error_message: Optional[str] = None
    processed_at: Optional[str] = None
    output_path: Optional[str] = None


class BrilliantBatchInputManager:
    """
    Manages input files for batch bill processing.
    
    Directory Structure:
    INPUTS_MANAGEMENT/
    ├── pending/           # Files waiting to be processed
    ├── processing/        # Files currently being processed
    ├── completed/         # Successfully processed files
    ├── failed/            # Files that failed processing
    ├── quarantined/       # Files with validation errors
    └── metadata.json      # Central metadata registry
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent.parent / "INPUTS_MANAGEMENT"
        self.pending_dir = self.base_dir / "pending"
        self.processing_dir = self.base_dir / "processing"
        self.completed_dir = self.base_dir / "completed"
        self.failed_dir = self.base_dir / "failed"
        self.quarantined_dir = self.base_dir / "quarantined"
        self.metadata_file = self.base_dir / "metadata.json"
        
        # Create directory structure
        for directory in [self.pending_dir, self.processing_dir, 
                         self.completed_dir, self.failed_dir, self.quarantined_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Initialize metadata registry
        self.metadata = self._load_metadata()
        
        logger.info(f"Batch Input Manager initialized at {self.base_dir}")
    
    def _load_metadata(self) -> Dict:
        """Load metadata registry from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}. Starting fresh.")
        
        return {"files": {}, "stats": {"total": 0, "completed": 0, "failed": 0, "quarantined": 0}}
    
    def _save_metadata(self):
        """Save metadata registry to disk atomically."""
        temp_file = self.metadata_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, default=str)
            temp_file.replace(self.metadata_file)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            if temp_file.exists():
                temp_file.unlink()
    
    def register_input_file(self, source_path: Path, 
                           category: str = "pending") -> InputFileMetadata:
        """
        Register and copy an input file to the management system.
        
        Args:
            source_path: Path to the source Excel file
            category: Initial category (pending/processing)
            
        Returns:
            InputFileMetadata object
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Validate file extension
        valid_extensions = {'.xlsx', '.xls', '.xlsm'}
        if source_path.suffix.lower() not in valid_extensions:
            raise ValueError(f"Invalid file type: {source_path.suffix}. Must be {valid_extensions}")
        
        # Determine target directory
        target_dir = getattr(self, f"{category}_dir")
        target_path = target_dir / source_path.name
        
        # Check for duplicates
        if target_path.exists():
            logger.warning(f"File already exists in {category}: {source_path.name}")
            # Return existing metadata if available
            if source_path.name in self.metadata["files"]:
                return InputFileMetadata(**self.metadata["files"][source_path.name])
        
        # Copy file atomically
        self._atomic_copy(source_path, target_path)
        
        # Detect if file has extra items (based on filename pattern)
        has_extra = self._detect_extra_items(source_path.name)
        
        # Create metadata
        metadata = InputFileMetadata(
            filename=source_path.name,
            filepath=str(target_path),
            has_extra_items=has_extra,
            file_size_bytes=target_path.stat().st_size,
            created_at=datetime.now().isoformat(),
            status=category
        )
        
        # Update registry
        self.metadata["files"][source_path.name] = asdict(metadata)
        self.metadata["stats"]["total"] = len(self.metadata["files"])
        self._save_metadata()
        
        logger.info(f"Registered input file: {source_path.name} (has_extra={has_extra})")
        return metadata
    
    def _atomic_copy(self, source: Path, dest: Path):
        """Atomically copy a file using temp file + rename."""
        temp_dest = dest.with_suffix(dest.suffix + '.tmp')
        try:
            shutil.copy2(source, temp_dest)
            temp_dest.replace(dest)
            logger.debug(f"Atomic copy completed: {source} -> {dest}")
        except Exception as e:
            if temp_dest.exists():
                temp_dest.unlink()
            raise e
    
    def _detect_extra_items(self, filename: str) -> bool:
        """Detect if file likely has extra items based on filename patterns."""
        filename_lower = filename.lower()
        
        # Check for explicit "WithExtra" or "NoExtra" markers first
        if 'noextra' in filename_lower:
            return False
        if 'withextra' in filename_lower or 'wextra' in filename_lower:
            return True
        
        # Check for other extra-related patterns
        extra_patterns = [
            r'\bextra\b',  # Word boundary to avoid false positives
            r'deviation',
        ]
        
        for pattern in extra_patterns:
            if re.search(pattern, filename_lower):
                return True
        
        return False
    
    def get_pending_files(self) -> List[InputFileMetadata]:
        """Get all pending files ready for processing."""
        pending = []
        for filename, meta_dict in self.metadata["files"].items():
            if meta_dict.get("status") == "pending":
                pending.append(InputFileMetadata(**meta_dict))
        return pending
    
    def update_file_status(self, filename: str, new_status: str, 
                          error_message: Optional[str] = None,
                          output_path: Optional[str] = None):
        """
        Update the status of a file in the registry.
        
        Args:
            filename: Name of the file
            new_status: New status (processing/completed/failed/quarantined)
            error_message: Optional error message if failed
            output_path: Path to generated outputs if completed
        """
        if filename not in self.metadata["files"]:
            raise KeyError(f"File not found in registry: {filename}")
        
        meta = self.metadata["files"][filename]
        old_status = meta.get("status")
        
        # Move file to appropriate directory
        if old_status != new_status:
            self._move_file_to_category(filename, old_status, new_status)
        
        # Update metadata
        meta["status"] = new_status
        if error_message:
            meta["error_message"] = error_message
        if output_path:
            meta["output_path"] = output_path
        if new_status == "completed":
            meta["processed_at"] = datetime.now().isoformat()
            self.metadata["stats"]["completed"] += 1
        elif new_status in ["failed", "quarantined"]:
            self.metadata["stats"]["failed"] += 1
        
        self._save_metadata()
        logger.info(f"Updated {filename}: {old_status} -> {new_status}")
    
    def _move_file_to_category(self, filename: str, old_cat: str, new_cat: str):
        """Move file between category directories."""
        if not old_cat or old_cat == new_cat:
            return
            
        old_dir = getattr(self, f"{old_cat}_dir", None)
        new_dir = getattr(self, f"{new_cat}_dir", None)
        
        if not old_dir or not new_dir:
            return
        
        old_path = old_dir / filename
        new_path = new_dir / filename
        
        if old_path.exists():
            try:
                shutil.move(str(old_path), str(new_path))
                # Update filepath in metadata
                self.metadata["files"][filename]["filepath"] = str(new_path)
            except Exception as e:
                logger.error(f"Failed to move file {filename}: {e}")
    
    def quarantine_file(self, filename: str, reason: str):
        """Move a file to quarantine due to validation errors."""
        self.update_file_status(filename, "quarantined", error_message=reason)
        logger.warning(f"Quarantined file {filename}: {reason}")
    
    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """Generate a comprehensive batch processing report."""
        report = []
        report.append("# Brilliant Batch Input Management Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Statistics
        stats = self.metadata.get("stats", {})
        report.append("## Summary Statistics\n")
        report.append(f"- **Total Files:** {stats.get('total', 0)}")
        report.append(f"- **Completed:** {stats.get('completed', 0)}")
        report.append(f"- **Failed:** {stats.get('failed', 0)}")
        report.append(f"- **Pending:** {len(self.get_pending_files())}\n")
        
        # Files by category
        for category in ["pending", "processing", "completed", "failed", "quarantined"]:
            files = [f for f, m in self.metadata["files"].items() 
                    if m.get("status") == category]
            if files:
                report.append(f"\n## {category.upper()} FILES ({len(files)})\n")
                for filename in sorted(files):
                    meta = self.metadata["files"][filename]
                    extra_marker = " ⚠️ EXTRA" if meta.get("has_extra_items") else ""
                    report.append(f"- `{filename}`{extra_marker}")
                    if meta.get("error_message"):
                        report.append(f"  - Error: {meta['error_message']}")
        
        report_text = "\n".join(report)
        
        # Save to file if path provided
        if output_path:
            output_path.write_text(report_text, encoding='utf-8')
            logger.info(f"Report saved to {output_path}")
        
        return report_text
    
    def validate_all_inputs(self) -> Tuple[int, int]:
        """
        Validate all registered input files.
        
        Returns:
            Tuple of (valid_count, invalid_count)
        """
        valid = 0
        invalid = 0
        
        for filename, meta in self.metadata["files"].items():
            filepath = Path(meta.get("filepath", ""))
            
            if not filepath.exists():
                self.quarantine_file(filename, "File not found on disk")
                invalid += 1
                continue
            
            if filepath.stat().st_size == 0:
                self.quarantine_file(filename, "Empty file")
                invalid += 1
                continue
            
            # Additional validation can be added here
            valid += 1
        
        logger.info(f"Validation complete: {valid} valid, {invalid} invalid")
        return valid, invalid
    
    def cleanup_old_files(self, days_old: int = 30):
        """Clean up files older than specified days."""
        cutoff = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        for category in ["completed", "failed", "quarantined"]:
            dir_path = getattr(self, f"{category}_dir")
            for filepath in dir_path.glob("*"):
                if filepath.stat().st_ctime < cutoff:
                    try:
                        filepath.unlink()
                        logger.info(f"Cleaned up old file: {filepath.name}")
                    except Exception as e:
                        logger.error(f"Failed to cleanup {filepath.name}: {e}")


def create_sample_input_structure():
    """Create sample input files for testing the management system."""
    manager = BrilliantBatchInputManager()
    
    # Example usage
    print(f"Input Management System initialized at: {manager.base_dir}")
    print(f"Pending directory: {manager.pending_dir}")
    print(f"Completed directory: {manager.completed_dir}")
    
    return manager


if __name__ == "__main__":
    # Initialize and demonstrate the system
    mgr = create_sample_input_structure()
    report = mgr.generate_report()
    print("\n" + report)
