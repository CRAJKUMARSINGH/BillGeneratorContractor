"""
Download Manager for BillGeneratorUnified
Organizes and manages download items with metadata and categorization
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class DownloadCategory(Enum):
    """Categories for download items"""
    HTML_DOCUMENTS = "HTML Documents"
    PDF_DOCUMENTS = "PDF Documents"
    DOC_DOCUMENTS = "DOC Documents"
    EXCEL_FILES = "Excel Files"
    TEMPLATES = "Templates"
    CONFIGURATION = "Configuration"
    GENERAL = "General"


class FileType(Enum):
    """File types for download items"""
    HTML = "text/html"
    PDF = "application/pdf"
    DOC = "application/msword"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    XLSM = "application/vnd.ms-excel.sheet.macroEnabled.12"  # NEW: Macro-enabled Excel
    JSON = "application/json"
    TXT = "text/plain"
    ZIP = "application/zip"


@dataclass
class DownloadItem:
    """Represents a downloadable item"""
    name: str
    content: bytes
    file_type: FileType
    description: str = ""
    category: DownloadCategory = DownloadCategory.GENERAL
    size_bytes: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if self.size_bytes == 0 and self.content:
            self.size_bytes = len(self.content)


class EnhancedDownloadManager:
    """Manages download items with organization and statistics"""
    
    def __init__(self):
        self.download_items: List[DownloadItem] = []
        self.created_at = datetime.now()
        
    def add_item(self, name: str, content: bytes, file_type: FileType, 
                 description: str = "", category: DownloadCategory = DownloadCategory.GENERAL):
        """Add a download item"""
        item = DownloadItem(
            name=name,
            content=content,
            file_type=file_type,
            description=description,
            category=category
        )
        self.download_items.append(item)
        
    def add_html_document(self, name: str, content: str, description: str = ""):
        """Add an HTML document"""
        if isinstance(content, str):
            content_bytes = content.encode('utf-8')
        else:
            content_bytes = content
        self.add_item(name, content_bytes, FileType.HTML, description, DownloadCategory.HTML_DOCUMENTS)
        
    def add_pdf_document(self, name: str, content: bytes, description: str = ""):
        """Add a PDF document"""
        self.add_item(name, content, FileType.PDF, description, DownloadCategory.PDF_DOCUMENTS)
        
    def add_doc_document(self, name: str, content: bytes, description: str = ""):
        """Add a DOC document"""
        self.add_item(name, content, FileType.DOC, description, DownloadCategory.DOC_DOCUMENTS)
        
    def add_excel_file(self, name: str, content: bytes, description: str = ""):
        """Add an Excel file"""
        # Determine if it's a macro-enabled file based on extension
        if name.endswith('.xlsm'):
            self.add_item(name, content, FileType.XLSM, description, DownloadCategory.EXCEL_FILES)
        else:
            self.add_item(name, content, FileType.XLSX, description, DownloadCategory.EXCEL_FILES)
        
    def get_items_by_category(self) -> Dict[DownloadCategory, List[DownloadItem]]:
        """Organize items by category"""
        categorized = {}
        for item in self.download_items:
            if item.category not in categorized:
                categorized[item.category] = []
            categorized[item.category].append(item)
        return categorized
        
    def get_items_by_type(self) -> Dict[FileType, List[DownloadItem]]:
        """Organize items by file type"""
        typed = {}
        for item in self.download_items:
            if item.file_type not in typed:
                typed[item.file_type] = []
            typed[item.file_type].append(item)
        return typed
        
    def get_statistics(self) -> Dict:
        """Get download statistics"""
        total_size = sum(item.size_bytes for item in self.download_items)
        category_counts = {}
        type_counts = {}
        
        for item in self.download_items:
            # Count by category
            category = item.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Count by type
            file_type = item.file_type.value
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
            
        return {
            'total_items': len(self.download_items),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'categories': category_counts,
            'file_types': type_counts,
            'created_at': self.created_at.isoformat()
        }
        
    def get_items_by_filter(self, category: Optional[DownloadCategory] = None, 
                           file_type: Optional[FileType] = None) -> List[DownloadItem]:
        """Get items filtered by category and/or file type"""
        filtered_items = self.download_items
        
        if category:
            filtered_items = [item for item in filtered_items if item.category == category]
            
        if file_type:
            filtered_items = [item for item in filtered_items if item.file_type == file_type]
            
        return filtered_items
        
    def clear_items(self):
        """Clear all download items"""
        self.download_items.clear()
        
    def get_all_items(self) -> List[DownloadItem]:
        """Get all download items"""
        return self.download_items[:]