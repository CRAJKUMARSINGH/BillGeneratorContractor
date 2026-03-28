from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class DocumentRow(BaseModel):
    item_id: Optional[str] = None
    serial_no: str = ""
    description: str
    unit: str = ""
    qty_since_last_bill: float = 0.0
    qty_to_date: float = 0.0
    rate: float = 0.0
    amount: float = 0.0
    remarks: str = ""
    confidence_score: float = 1.0

class UnifiedDocumentModel(BaseModel):
    document_id: str
    source_type: str = Field(description="e.g., 'excel', 'ocr', 'hybrid'")
    raw_metadata: Dict[str, Any] = Field(default_factory=dict, description="Original headers like Contractor Name, Agreement No")
    rows: List[DocumentRow] = Field(default_factory=list)
    total_amount: float = 0.0
    overall_confidence: float = 1.0
    anomaly_warnings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list, description="Parsing or validation warnings")

