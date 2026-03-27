from typing import Dict, Any
import uuid
import pandas as pd

from .models import UnifiedDocumentModel, DocumentRow
from .confidence_score import calculate_row_confidence, aggregate_document_confidence
from .anomaly_detector import extract_features, detect_anomalies

def normalize_to_unified_model(raw_data: Dict[str, Any], source_type: str = "excel") -> UnifiedDocumentModel:
    """
    Takes raw data (e.g. from excel_parser) and maps it into a UnifiedDocumentModel.
    """
    raw_rows = raw_data.get("raw_rows", [])
    metadata = raw_data.get("metadata", {})
    
    document_rows = []
    row_confidences = []
    total_amount = 0.0
    
    for row in raw_rows:
        # Flexible key matching for basic columns
        desc = row.get("description", row.get("Description", row.get("Item", "Unknown")))
        qty = row.get("quantity", row.get("Quantity", row.get("Qty", 0.0)))
        rate = row.get("rate", row.get("Rate", 0.0))
        amt = row.get("amount", row.get("Amount", 0.0))
        unit = row.get("unit", row.get("Unit", ""))
        
        # Calculate derived amount if not present or inconsistent
        if not amt and isinstance(qty, (int, float)) and isinstance(rate, (int, float)):
            amt = qty * rate
            
        row_conf = calculate_row_confidence({
            "description": desc,
            "quantity": qty,
            "rate": rate,
            "amount": amt
        })
        row_confidences.append(row_conf)
        
        doc_row = DocumentRow(
            item_id=str(uuid.uuid4()),
            description=str(desc),
            quantity=float(qty) if pd.notna(qty) and isinstance(qty, (int, float)) else 0.0,
            rate=float(rate) if pd.notna(rate) and isinstance(rate, (int, float)) else 0.0,
            amount=float(amt) if pd.notna(amt) and isinstance(amt, (int, float)) else 0.0,
            unit=str(unit),
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
        anomaly_warnings=anomalies
    )
