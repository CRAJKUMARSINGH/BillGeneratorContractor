"""
Backend Pydantic models — request/response contracts.
Derived from Git5 bill-api models, aligned to engine/model/document.py.
"""
from pydantic import BaseModel, Field
from typing import Optional
from sqlmodel import SQLModel, Field as SQLField
from datetime import datetime

# --- DATABASE MODELS ---
class User(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    username: str = SQLField(unique=True, index=True)
    hashed_password: str
    role: str = SQLField(default="operator")

class BillRecord(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    job_id: str = SQLField(unique=True, index=True)
    user_id: int = SQLField(foreign_key="user.id")
    status: str
    message: str
    total_amount: float = 0.0
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    file_paths: str = "" # serialized JSON string for simplicity

# --- API MODELS ---
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
    anomaly_warnings: list[str] = []


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

class TemplateRequest(BaseModel):
    prompt: str


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
    redis: str
    worker: str
    engine: str
    version: str = "1.0.0"
