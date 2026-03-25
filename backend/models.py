"""
Backend Pydantic models — request/response contracts.
Derived from Git5 bill-api models, aligned to engine/model/document.py.
"""
from pydantic import BaseModel, Field
from typing import Optional


class BillItem(BaseModel):
    itemNo: str = ""
    description: str = ""
    unit: str = ""
    quantitySince: float = 0
    quantityUpto: float = 0
    quantity: float = 0
    rate: float = 0
    amount: float = 0


class ExtraItem(BaseModel):
    itemNo: str = ""
    bsr: str = ""
    description: str = ""
    quantity: float = 0
    unit: str = ""
    rate: float = 0
    amount: float = 0
    remark: str = ""


class ParsedBillData(BaseModel):
    fileId: str
    fileName: str
    titleData: dict
    billItems: list[BillItem]
    extraItems: list[ExtraItem]
    totalAmount: float
    hasExtraItems: bool
    sheets: list[str]


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


class JobStatus(BaseModel):
    jobId: str
    status: str          # pending | processing | complete | error
    progress: float = 0
    message: str = ""
    documents: list[DocumentInfo] = []
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    engine: str
    version: str = "1.0.0"
