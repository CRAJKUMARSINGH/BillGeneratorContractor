from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class BillItem(BaseModel):
    itemNo: str = Field("", description="Standard PWD item code or serial number")
    description: str = Field("", description="Item description text")
    unit: str = Field("", description="Unit of measurement (e.g., cum, sqm, m)")
    quantity: float = Field(0.0, description="Quantity for this bill")
    rate: float = Field(0.0, description="Applied rate (may be part-rate)")
    amount: float = Field(0.0, description="Total amount (qty * rate)")
    
    # Mode 2 & 3 specifics
    wo_quantity: Optional[float] = Field(None, description="Original Work Order quantity (Mode 2)")
    wo_rate: Optional[float] = Field(None, description="Original Work Order rate (Mode 2)")
    confidence: float = Field(1.0, description="Confidence score for OCR/Parsing (0.0 to 1.0)")
    aiNote: Optional[str] = Field(None, description="AI-generated note or suggestion")
    source_ref: Optional[str] = Field(None, description="Source reference for audit (e.g. 'Page 2')")

class ExtraItem(BaseModel):
    itemNo: str = ""
    bsr: str = ""
    description: str = ""
    quantity: float = 0.0
    unit: str = ""
    rate: float = 0.0
    amount: float = 0.0
    remark: str = ""

class UnifiedBillDocument(BaseModel):
    fileId: str
    fileName: str
    mode: str = Field("mode1", description="Inut mode: mode1 (Full Excel), mode2 (Hybrid), mode3 (OCR)")
    titleData: Dict[str, Any] = Field(default_factory=dict)
    billItems: List[BillItem] = Field(default_factory=list)
    extraItems: List[ExtraItem] = Field(default_factory=list)
    totalAmount: float = 0.0
    hasExtraItems: bool = False
    sheets: List[str] = Field(default_factory=list)
    
    # Performance & Quality metrics
    confidenceOverall: float = 1.0
    anomaly_warnings: List[str] = Field(default_factory=list)
    
    # Metadata
    source_type: str = "excel" # excel, ocr, manual
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    processed_at: Optional[str] = None

class IngestionResult(BaseModel):
    success: bool
    document: Optional[UnifiedBillDocument] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class GenerateOptions(BaseModel):
    generatePdf: bool = True
    generateHtml: bool = True
    templateVersion: str = "v1"
    premiumPercent: float = 0.0
    premiumType: str = "above"
    previousBillAmount: float = 0.0

class GenerateRequest(BaseModel):
    fileId: str
    titleData: dict
    billItems: list[BillItem]
    extraItems: list[ExtraItem]
    options: GenerateOptions = Field(default_factory=GenerateOptions)

class DocumentInfo(BaseModel):
    name: str
    format: str
    size: int = 0
    url: Optional[str] = None

class JobStatus(BaseModel):
    jobId: str
    status: str          # pending | processing | complete | error
    progress: float = 0
    message: str = ""
    documents: list[DocumentInfo] = []
    error: Optional[str] = None
