from typing import Dict, Any
import uuid
import pandas as pd

import sys
from pathlib import Path
root = Path(__file__).parent.parent
if str(root) not in sys.path:
    sys.path.append(str(root))

from engine.models import UnifiedBillDocument as UnifiedDocumentModel, BillItem as DocumentRow, ExtraItem
from .confidence_score import calculate_row_confidence, aggregate_document_confidence
from .anomaly_detector import extract_features, detect_anomalies
from engine.utils.item_logic import canonicalize_item_code, sort_bill_items

def normalize_to_unified_model(raw_data: Dict[str, Any], source_type: str = "excel") -> UnifiedDocumentModel:
    """
    Takes raw data (e.g. from excel_parser) and maps it into a UnifiedDocumentModel.
    """
    raw_rows = raw_data.get("raw_rows", [])
    extra_rows = raw_data.get("extra_rows", [])
    metadata = raw_data.get("metadata", {})
    
    document_rows = []
    document_rows_map: Dict[str, DocumentRow] = {}
    row_confidences = []

    for row in raw_rows:
        desc = row.get("description", row.get("Description", row.get("Item", "Unknown")))
        qty = row.get("quantity", row.get("quantity_upto_date", row.get("Quantity", row.get("Qty", 0.0))))
        rate = row.get("rate", row.get("Rate", 0.0))
        amt = row.get("amount", row.get("Amount", 0.0))
        unit = row.get("unit", row.get("Unit", ""))
        raw_item_code = row.get("item_no", row.get("ItemNo", row.get("Item No.", None)))
        
        canonical_code = canonicalize_item_code(raw_item_code)
        
        if not amt and isinstance(qty, (int, float)) and isinstance(rate, (int, float)):
            amt = qty * rate

        row_conf = calculate_row_confidence({
            "description": desc,
            "quantity": qty,
            "rate": rate,
            "amount": amt
        })
        row_confidences.append(row_conf)

        val_qty = float(qty) if pd.notna(qty) and isinstance(qty, (int, float)) else 0.0
        val_rate = float(rate) if pd.notna(rate) and isinstance(rate, (int, float)) else 0.0
        val_amt = float(amt) if pd.notna(amt) and isinstance(amt, (int, float)) else 0.0

        if canonical_code and canonical_code in document_rows_map:
            existing = document_rows_map[canonical_code]
            existing.quantity += val_qty
            existing.amount += val_amt
            if abs(existing.rate - val_rate) > 0.01 and val_rate > 0:
                existing.aiNote = f"Rate Conflict: Found {existing.rate} and {val_rate}"
        else:
            doc_row = DocumentRow(
                itemNo=canonical_code,
                description=str(desc),
                quantity=val_qty,
                rate=val_rate,
                amount=val_amt,
                unit=str(unit),
                confidence=row_conf
            )
            if canonical_code:
                document_rows_map[canonical_code] = doc_row
            else:
                document_rows.append(doc_row)

    document_rows.extend(document_rows_map.values())
    
    # Hierarchical Pruning & Synthesis
    active_codes = {item.itemNo for item in document_rows if item.quantity > 0}
    required_codes = set(active_codes)
    for code in active_codes:
        if not code: continue
        parts = code.split('.')
        for i in range(1, len(parts)):
            required_codes.add(".".join(parts[:i]))
            
    final_rows_map = {}
    for item in document_rows:
        if not item.itemNo:
            final_rows_map[str(uuid.uuid4())] = item
        elif item.itemNo in required_codes:
            final_rows_map[item.itemNo] = item
            
    for code in required_codes:
        if code not in final_rows_map:
            final_rows_map[code] = DocumentRow(
                itemNo=code,
                description=f"Header: {code}",
                quantity=0.0,
                rate=0.0,
                amount=0.0,
                unit="",
                confidence=0.5,
                aiNote="Synthesized Parent Header"
            )

    sorted_items = sort_bill_items(list(final_rows_map.values()))
    
    # Process Extra Items
    extra_items = []
    for er in extra_rows:
        extra_items.append(ExtraItem(
            itemNo=er.get("item_no", ""),
            description=er.get("description", ""),
            quantity=er.get("quantity", 0.0),
            unit=er.get("unit", ""),
            rate=er.get("rate", 0.0),
            amount=er.get("amount", 0.0),
            remark=er.get("section", "Extra Item")
        ))
    
    total_amount = sum(item.amount for item in sorted_items) + sum(item.amount for item in extra_items)
    overall_conf = aggregate_document_confidence(row_confidences)
    
    features = extract_features(raw_rows)
    anomalies = detect_anomalies(features)
    
    return UnifiedDocumentModel(
        fileId=metadata.get("file_id", str(uuid.uuid4())),
        fileName=metadata.get("filename", "unknown"),
        mode=source_type if source_type.startswith("mode") else f"mode_{source_type}",
        source_type=source_type,
        titleData=metadata,
        billItems=sorted_items,
        extraItems=extra_items,
        totalAmount=total_amount,
        hasExtraItems=len(extra_items) > 0,
        confidenceOverall=overall_conf,
        anomaly_warnings=anomalies,
        sheets=metadata.get("sheets", []),
        metadata={
            "original_count": len(raw_rows),
            "final_count": len(sorted_items),
            "pruned_count": len(raw_rows) - len(sorted_items),
            "extra_count": len(extra_items)
        }
    )
