from typing import Dict, Any
import uuid
import pandas as pd

from .models import UnifiedDocumentModel, DocumentRow
from .confidence_score import calculate_row_confidence, aggregate_document_confidence
from .anomaly_detector import extract_features, detect_anomalies

def normalize_to_unified_model(raw_data: Dict[str, Any], source_type: str = "excel") -> UnifiedDocumentModel:
    """
    Takes raw data (from excel_parser or ocr_extractor) and maps it into a UnifiedDocumentModel.
    Supports both traditional flat rows and the new 4-sheet PWD format.
    """
    raw_rows = raw_data.get("raw_rows", [])
    metadata = raw_data.get("metadata", {})
    warnings = raw_data.get("warnings", [])
    
    document_rows = []
    row_confidences = []
    total_amount = 0.0
    
    for row in raw_rows:
        # 1. Map canonical fields with fallback logic for OCR/Flat Excel
        desc = row.get("description", row.get("Description", row.get("Item", "Unknown")))
        unit = row.get("unit", row.get("Unit", ""))
        rate = row.get("rate", row.get("Rate", 0.0))
        amt  = row.get("amount", row.get("Amount", 0.0))
        sno  = row.get("serial_no", row.get("serial", ""))
        rem  = row.get("remarks", "")
        
        # 2. PWD Specific fields
        qty_since = row.get("qty_since_last_bill", 0.0)
        qty_to_date = row.get("qty_to_date", row.get("quantity", 0.0))
        
        # 3. Calculate derived amount if missing
        if not amt and isinstance(qty_to_date, (int, float)) and isinstance(rate, (int, float)):
            amt = qty_to_date * rate
            
        row_conf = calculate_row_confidence({
            "description": desc,
            "quantity": qty_to_date,
            "rate": rate,
            "amount": amt
        })
        row_confidences.append(row_conf)
        
        doc_row = DocumentRow(
            item_id=str(uuid.uuid4()),
            serial_no=str(sno),
            description=str(desc),
            unit=str(unit),
            qty_since_last_bill=float(qty_since),
            qty_to_date=float(qty_to_date),
            rate=float(rate),
            amount=float(amt),
            remarks=str(rem),
            confidence_score=row_conf
        )
        document_rows.append(doc_row)
        total_amount += doc_row.amount
        
    overall_conf = aggregate_document_confidence(row_confidences)
    
    # Run anomaly detection on extracted document features
    features = extract_features(raw_rows)
    anomalies = detect_anomalies(features)
    
    return UnifiedDocumentModel(
        document_id=str(uuid.uuid4()),
        source_type=source_type,
        raw_metadata=metadata,
        rows=document_rows,
        total_amount=total_amount,
        overall_confidence=overall_conf,
        anomaly_warnings=anomalies,
        warnings=warnings
    )
