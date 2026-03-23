"""
Work Order File Organizer
Organizes uploaded work order files into dated subfolders
"""
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict


@dataclass
class WorkOrderInfo:
    """Information about a work order"""
    work_order_id: str
    folder_path: str
    created_at: str
    file_count: int
    files: List[str]


class WorkOrderOrganizer:
    """Organizes work order files into structured folders"""
    
    def __init__(self, base_path: str = "INPUT/work_order_samples"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def create_work_order_folder(self, work_order_id: str, date: Optional[str] = None) -> Path:
        """
        Create a subfolder for a work order
        
        Args:
            work_order_id: Identifier for the work order (e.g., "work_01")
            date: Date string in DDMMYYYY format (defaults to today)
        
        Returns:
            Path to the created folder
        """
        if date is None:
            date = datetime.now().strftime("%d%m%Y")
        
        folder_name = f"{work_order_id}_{date}"
        folder_path = self.base_path / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        
        return folder_path
    
    def get_next_work_order_id(self) -> str:
        """
        Generate next available work order ID
        
        Returns:
            Next work order ID (e.g., "work_01", "work_02")
        """
        existing_folders = [f for f in self.base_path.iterdir() if f.is_dir() and f.name.startswith("work_")]
        
        if not existing_folders:
            return "work_01"
        
        # Extract numbers from folder names
        numbers = []
        for folder in existing_folders:
            parts = folder.name.split("_")
            if len(parts) >= 2:
                try:
                    num = int(parts[1])
                    numbers.append(num)
                except ValueError:
                    continue
        
        if not numbers:
            return "work_01"
        
        next_num = max(numbers) + 1
        return f"work_{next_num:02d}"
    
    def save_uploaded_file(self, file_data: bytes, filename: str, folder: Path, category: str) -> Path:
        """
        Save uploaded file with category prefix
        
        Args:
            file_data: File content as bytes
            filename: Original filename
            folder: Destination folder path
            category: Category prefix (work_order, bill_quantities, extra_items)
        
        Returns:
            Path to saved file
        """
        # Add category prefix to filename
        prefixed_filename = f"{category}_{filename}"
        file_path = folder / prefixed_filename
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        return file_path
    
    def save_metadata(self, folder: Path, metadata: Dict) -> None:
        """
        Save metadata JSON file in work order folder
        
        Args:
            folder: Work order folder path
            metadata: Metadata dictionary
        """
        metadata_path = folder / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def list_work_orders(self) -> List[WorkOrderInfo]:
        """
        List all existing work orders with metadata
        
        Returns:
            List of WorkOrderInfo objects
        """
        work_orders = []
        
        for folder in self.base_path.iterdir():
            if folder.is_dir() and folder.name.startswith("work_"):
                files = [f.name for f in folder.iterdir() if f.is_file() and f.suffix != '.json']
                
                # Try to load metadata
                metadata_path = folder / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        created_at = metadata.get('created_at', 'Unknown')
                else:
                    created_at = datetime.fromtimestamp(folder.stat().st_ctime).isoformat()
                
                work_order_info = WorkOrderInfo(
                    work_order_id=folder.name.split('_')[1] if '_' in folder.name else folder.name,
                    folder_path=str(folder),
                    created_at=created_at,
                    file_count=len(files),
                    files=files
                )
                work_orders.append(work_order_info)
        
        return sorted(work_orders, key=lambda x: x.created_at, reverse=True)
    
    def organize_files(self, 
                      source_files: List[str], 
                      work_order_id: str, 
                      date: Optional[str] = None) -> Path:
        """
        Move files to organized work order folder
        
        Args:
            source_files: List of file paths to organize
            work_order_id: Identifier for the work order
            date: Date string in DDMMYYYY format
        
        Returns:
            Path to the destination folder
        """
        dest_folder = self.create_work_order_folder(work_order_id, date)
        
        for file_path in source_files:
            src = Path(file_path)
            if src.exists():
                dest = dest_folder / src.name
                shutil.move(str(src), str(dest))
        
        return dest_folder
    
    def organize_uploaded_files(self, 
                                work_order_id: str, 
                                file_pattern: str = "*.jpeg",
                                date: Optional[str] = None) -> Path:
        """
        Organize all files matching pattern in base folder
        
        Args:
            work_order_id: Identifier for the work order
            file_pattern: Glob pattern for files to organize
            date: Date string in DDMMYYYY format
        
        Returns:
            Path to the destination folder
        """
        files = list(self.base_path.glob(file_pattern))
        file_paths = [str(f) for f in files]
        
        return self.organize_files(file_paths, work_order_id, date)


def organize_work_order_cli():
    """CLI interface for organizing work orders"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m core.utils.work_order_organizer <work_order_id> [date_DDMMYYYY]")
        sys.exit(1)
    
    work_order_id = sys.argv[1]
    date = sys.argv[2] if len(sys.argv) > 2 else None
    
    organizer = WorkOrderOrganizer()
    dest_folder = organizer.organize_uploaded_files(work_order_id, date=date)
    
    print(f"Files organized into: {dest_folder}")


if __name__ == "__main__":
    organize_work_order_cli()
