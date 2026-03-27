"""Unified Document Model — single source of truth for all pipeline stages"""
from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator
import math


class DocumentState(str, Enum):
    UPLOADED = "uploaded"
    PARSED = "parsed"
    INPUT_EDITED = "input_edited"
    CALCULATED = "calculated"
    FINAL_EDITED = "final_edited"
    PRINT_READY = "print_ready"
    EXPORTED = "exported"


class BillItem(BaseModel):
    itemNo: str = ""
    description: str = ""
    unit: str = ""
    quantitySince: float = 0.0
    quantityUpto: float = 0.0
    quantity: float = 0.0
    rate: float = 0.0
    amount: float = 0.0

    @model_validator(mode="after")
    def compute_amount(self) -> "BillItem":
        """Auto-compute amount if missing but qty+rate present"""
        if self.amount == 0.0 and self.quantity > 0 and self.rate > 0:
            self.amount = round(self.quantity * self.rate, 2)
        return self

    @model_validator(mode="after")
    def sanitize_floats(self) -> "BillItem":
        for field in ("quantitySince", "quantityUpto", "quantity", "rate", "amount"):
            v = getattr(self, field)
            if math.isnan(v) or math.isinf(v):
                setattr(self, field, 0.0)
        return self


class ExtraItem(BaseModel):
    itemNo: str = ""
    bsr: str = ""
    description: str = ""
    quantity: float = 0.0
    unit: str = ""
    rate: float = 0.0
    amount: float = 0.0
    remark: str = ""

    @model_validator(mode="after")
    def compute_amount(self) -> "ExtraItem":
        if self.amount == 0.0 and self.quantity > 0 and self.rate > 0:
            self.amount = round(self.quantity * self.rate, 2)
        return self


class TitleData(BaseModel):
    model_config = {"extra": "allow"}


class GenerateOptions(BaseModel):
    generatePdf: bool = True
    generateHtml: bool = True
    generateWord: bool = False


class UnifiedDocument(BaseModel):
    """The single document model that flows through the entire pipeline"""
    fileId: str
    fileName: str
    state: DocumentState = DocumentState.UPLOADED
    titleData: dict[str, Any] = Field(default_factory=dict)
    billItems: list[BillItem] = Field(default_factory=list)
    extraItems: list[ExtraItem] = Field(default_factory=list)
    totalAmount: float = 0.0
    hasExtraItems: bool = False
    sheets: list[str] = Field(default_factory=list)
    options: GenerateOptions = Field(default_factory=GenerateOptions)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def recompute_totals(self) -> None:
        self.totalAmount = sum(i.amount for i in self.billItems)
        self.hasExtraItems = len(self.extraItems) > 0


class DocumentInfo(BaseModel):
    name: str
    format: str
    size: int = 0


class JobStatus(BaseModel):
    jobId: str
    status: str  # pending | processing | complete | error
    progress: float = 0
    message: str = ""
    documents: list[DocumentInfo] = Field(default_factory=list)
    error: Optional[str] = None
