from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class DocumentRow(BaseModel):
    item_id: Optional[str] = None
    description: str
    quantity: float = 0.0
    unit: str = ""
    rate: float = 0.0
    amount: float = 0.0
    confidence_score: float = 1.0

class UnifiedDocumentModel(BaseModel):
    document_id: str
    source_type: str = Field(description="e.g., 'excel', 'ocr', 'hybrid'")
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
    rows: List[DocumentRow] = Field(default_factory=list)
    total_amount: float = 0.0
    overall_confidence: float = 1.0
    anomaly_warnings: List[str] = Field(default_factory=list)

