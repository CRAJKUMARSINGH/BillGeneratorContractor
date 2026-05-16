"""
Backend Pydantic models — request/response contracts.
Unified with engine/models.py for consistency across all input modes.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field as SQLField, Column as SQLColumn
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Column
from datetime import datetime, timezone

# Import core models to ensure consistency
from engine.models import BillItem, ExtraItem, UnifiedBillDocument as ParsedBillData, GenerateOptions, GenerateRequest, JobStatus, DocumentInfo

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
    created_at: datetime = SQLField(default_factory=lambda: datetime.now(timezone.utc))
    file_paths: dict = SQLField(default_factory=dict, sa_column=SQLColumn(JSON))
    data_hash: Optional[str] = SQLField(default=None)

# --- ADDITIONAL API MODELS ---
class TemplateRequest(BaseModel):
    prompt: str

class HealthResponse(BaseModel):
    status: str
    redis: str
    worker: str
    engine: str
    version: str = "1.0.0"

class PreviewRequest(BaseModel):
    document_type: str
    fileId: str
    titleData: dict
    billItems: list[BillItem]
    extraItems: list[ExtraItem]
    options: GenerateOptions = Field(default_factory=GenerateOptions)

class PreviewResponse(BaseModel):
    document_type: str
    html: str
