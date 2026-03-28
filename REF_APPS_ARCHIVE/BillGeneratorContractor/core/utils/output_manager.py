"""
Output Manager - Centralized output folder management
Handles timestamped files in file-wise subfolders within OUTPUT folder
"""
from pathlib import Path
from datetime import datetime
import shutil
import zipfile
import io
from typing import Dict, List, Tuple, Optional

class OutputManager:
    """Manages output files in file-wise subfolders with date/time stamps"""
    
    def __init__(self, base_output_dir: str = "OUTPUT", source_filename: Optional[str] = None):
        """
        Initialize output manager
        
        Args:
            base_output_dir: Base output directory name (default: OUTPUT)
            source_filename: Source Excel filename (without extension) for subfolder creation
        """
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
        self.source_filename = source_filename
        self.current_subfolder = None
        
        # Create subfolder if source filename provided
        if source_filename:
            self._create_subfolder(source_filename)
    
    def _create_subfolder(self, source_filename: str) -> Path:
        """
        Create timestamped subfolder for source file
        
        Args:
            source_filename: Source filename (without extension)
            
        Returns:
            Path to created subfolder
        """
        # Clean filename (remove extension if present)
        clean_name = Path(source_filename).stem
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create subfolder name: filename_YYYYMMDD_HHMMSS
        subfolder_name = f"{clean_name}_{timestamp}"
        subfolder_path = self.base_output_dir / subfolder_name
        subfolder_path.mkdir(exist_ok=True)
        
        self.current_subfolder = subfolder_path
        return subfolder_path
    
    def set_source_file(self, source_filename: str) -> Path:
        """
        Set source filename and create corresponding subfolder
        
        Args:
            source_filename: Source filename (without extension)
            
        Returns:
            Path to created subfolder
        """
        self.source_filename = source_filename
        return self._create_subfolder(source_filename)
    
    def get_output_folder(self) -> Path:
        """
        Get current output folder (subfolder if set, otherwise base folder)
        
        Returns:
            Path to output folder
        """
        return self.current_subfolder if self.current_subfolder else self.base_output_dir
    
    def create_timestamped_filename(self, base_name: str, extension: str) -> str:
        """
        Create timestamped filename
        
        Args:
            base_name: Base name without extension
            extension: File extension (with or without dot)
            
        Returns:
            Timestamped filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = extension if extension.startswith('.') else f'.{extension}'
        return f"{base_name}_{timestamp}{ext}"
    
    def save_file(self, content: bytes, base_name: str, extension: str) -> Path:
        """
        Save file with timestamp in appropriate folder
        
        Args:
            content: File content (bytes)
            base_name: Base name without extension
            extension: File extension
            
        Returns:
            Path to saved file
        """
        # Get output folder (subfolder if set, otherwise base)
        output_folder = self.get_output_folder()
        
        # Create simple filename without timestamp (timestamp is in folder name)
        ext = extension if extension.startswith('.') else f'.{extension}'
        filename = f"{base_name}{ext}"
        filepath = output_folder / filename
        
        with open(filepath, 'wb') as f:
            f.write(content)
        
        return filepath
    
    def save_text_file(self, content: str, base_name: str, extension: str) -> Path:
        """
        Save text file in appropriate folder
        
        Args:
            content: File content (string)
            base_name: Base name without extension
            extension: File extension
            
        Returns:
            Path to saved file
        """
        # Get output folder (subfolder if set, otherwise base)
        output_folder = self.get_output_folder()
        
        # Create simple filename without timestamp (timestamp is in folder name)
        ext = extension if extension.startswith('.') else f'.{extension}'
        filename = f"{base_name}{ext}"
        filepath = output_folder / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def create_zip(self, zip_name: Optional[str] = None) -> Tuple[bytes, str]:
        """
        Create ZIP file of current subfolder contents
        
        Args:
            zip_name: Optional custom ZIP filename (without extension)
            
        Returns:
            Tuple of (zip_bytes, zip_filename)
        """
        output_folder = self.get_output_folder()
        
        # Generate ZIP filename
        if zip_name is None:
            if self.current_subfolder:
                zip_name = self.current_subfolder.name
            else:
                zip_name = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        zip_filename = f"{zip_name}.zip"
        
        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add all files from output folder
            for file_path in output_folder.glob('*'):
                if file_path.is_file():
                    zip_file.write(file_path, file_path.name)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue(), zip_filename
    
    def save_zip(self, zip_name: Optional[str] = None) -> Path:
        """
        Create and save ZIP file of current subfolder contents
        
        Args:
            zip_name: Optional custom ZIP filename (without extension)
            
        Returns:
            Path to saved ZIP file
        """
        zip_bytes, zip_filename = self.create_zip(zip_name)
        
        # Save ZIP to base OUTPUT folder
        zip_path = self.base_output_dir / zip_filename
        with open(zip_path, 'wb') as f:
            f.write(zip_bytes)
        
        return zip_path
    
    def get_all_files(self) -> List[Path]:
        """Get all files in OUTPUT folder"""
        return list(self.base_output_dir.glob('*'))
    
    def clean_old_files(self, keep_latest: int = 10) -> Tuple[int, int]:
        """
        Clean old files, keeping only the latest N files
        
        Args:
            keep_latest: Number of latest files to keep
            
        Returns:
            Tuple of (files_deleted, space_freed_bytes)
        """
        files = sorted(
            self.base_output_dir.glob('*'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        files_to_delete = files[keep_latest:]
        space_freed = 0
        files_deleted = 0
        
        for file in files_to_delete:
            if file.is_file():
                space_freed += file.stat().st_size
                file.unlink()
                files_deleted += 1
        
        return files_deleted, space_freed
    
    def get_folder_size(self) -> int:
        """Get total size of OUTPUT folder in bytes"""
        total_size = 0
        for file in self.base_output_dir.glob('*'):
            if file.is_file():
                total_size += file.stat().st_size
        return total_size
    
    def format_size(self, size_bytes: int) -> str:
        """Format size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def clean_all(self) -> Tuple[int, int]:
        """
        Clean all files in OUTPUT folder
        
        Returns:
            Tuple of (files_deleted, space_freed_bytes)
        """
        files = list(self.base_output_dir.glob('*'))
        space_freed = 0
        files_deleted = 0
        
        for file in files:
            if file.is_file():
                space_freed += file.stat().st_size
                file.unlink()
                files_deleted += 1
        
        return files_deleted, space_freed


# Global instance
_output_manager = None

def get_output_manager() -> OutputManager:
    """Get global output manager instance"""
    global _output_manager
    if _output_manager is None:
        _output_manager = OutputManager()
    return _output_manager
