"""
Data Models
Core data structures for document processing
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path


@dataclass
class BoundingBox:
    """Spatial coordinates for extracted text"""
    x: int
    y: int
    width: int
    height: int
    page: int = 1


@dataclass
class Word:
    """Represents a single word extracted by OCR"""
    text: str
    confidence: float
    bounding_box: Optional[BoundingBox] = None


@dataclass
class Line:
    """Represents a line of handwritten text"""
    text: str
    confidence: float
    bounding_box: Optional[BoundingBox] = None


@dataclass
class OCRResult:
    """Raw OCR output"""
    text: str
    words: List[Word]
    confidence: float
    language: str


@dataclass
class HWRResult:
    """Raw handwriting recognition output"""
    text: str
    lines: List[Line]
    confidence: float


@dataclass
class WorkOrderItem:
    """Represents a single item from work order"""
    item_number: str
    description: str
    unit: str
    confidence_score: float
    page_number: int = 1
    bounding_box: Optional[BoundingBox] = None


@dataclass
class ItemQuantityPair:
    """Item number and quantity from bill quantities page"""
    item_number: str
    quantity: float
    confidence_score: float
    bounding_box: Optional[BoundingBox] = None


@dataclass
class ExtraItem:
    """Additional item not in work order"""
    description: str
    quantity: float
    rate: float
    unit: str
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    bounding_box: Optional[BoundingBox] = None


@dataclass
class DocumentMetadata:
    """Metadata for uploaded documents"""
    file_name: str
    upload_timestamp: datetime
    file_size: int
    file_type: str
    page_count: int = 1


@dataclass
class ExtractionMetadata:
    """Metadata about extraction process"""
    processing_timestamp: datetime
    ocr_engine_version: str
    hwr_engine_version: str
    average_confidence: float
    low_confidence_fields: List[str] = field(default_factory=list)
    manual_corrections: List[Dict] = field(default_factory=list)


@dataclass
class ProcessingError:
    """Error during processing"""
    error_type: str
    message: str
    timestamp: datetime
    component: str
    details: Optional[Dict] = None


@dataclass
class ProcessingWarning:
    """Warning during processing"""
    warning_type: str
    message: str
    timestamp: datetime
    component: str


@dataclass
class ProcessingStatus:
    """Status of document processing"""
    status: str  # "pending", "processing", "completed", "failed", "needs_review"
    progress: float  # 0.0 to 1.0
    errors: List[ProcessingError] = field(default_factory=list)
    warnings: List[ProcessingWarning] = field(default_factory=list)
    current_step: str = ""


@dataclass
class WorkOrderData:
    """Complete work order extraction result"""
    items: List[WorkOrderItem]
    metadata: DocumentMetadata
    processing_status: ProcessingStatus


@dataclass
class BillQuantitiesData:
    """Complete bill quantities extraction result"""
    quantities: Dict[str, ItemQuantityPair]  # item_number -> ItemQuantityPair
    metadata: DocumentMetadata
    processing_status: ProcessingStatus


@dataclass
class ExtraItemsData:
    """Complete extra items extraction result"""
    items: List[ExtraItem]
    metadata: DocumentMetadata
    processing_status: ProcessingStatus


@dataclass
class BillItem:
    """Final bill item for bill generator"""
    item_number: str
    description: str
    unit: str
    quantity: float
    rate: Optional[float] = None
    is_extra_item: bool = False
    confidence_score: float = 1.0


@dataclass
class BillGeneratorInput:
    """Complete input for bill generator system"""
    items: List[BillItem]
    work_order_metadata: DocumentMetadata
    extraction_metadata: ExtractionMetadata
    original_files: List[Path] = field(default_factory=list)


@dataclass
class ValidationError:
    """Represents a validation error"""
    field: str
    message: str
    severity: str = "error"  # "error", "warning"


@dataclass
class ValidationWarning:
    """Represents a validation warning"""
    field: str
    message: str


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)
    fields_requiring_review: List[str] = field(default_factory=list)


@dataclass
class ManualCorrection:
    """Record of manual correction"""
    field_name: str
    original_value: str
    corrected_value: str
    timestamp: datetime
    confidence_before: float
    user_id: Optional[str] = None


@dataclass
class WorkOrderSession:
    """Represents a work order processing session"""
    session_id: str
    work_order_id: str
    folder_path: Path
    created_at: datetime
    status: str
    work_order_data: Optional[WorkOrderData] = None
    bill_quantities_data: Optional[BillQuantitiesData] = None
    extra_items_data: Optional[ExtraItemsData] = None
    validation_result: Optional[ValidationResult] = None
    bill_generator_input: Optional[BillGeneratorInput] = None
