from typing import List, Dict, Any

def calculate_row_confidence(raw_row: Dict[str, Any]) -> float:
    """
    Calculate a confidence score for a parsed row.
    Missing fields or anomalous values reduce the score.
    """
    score = 100.0
    
    # Check for missing crucial fields
    if not raw_row.get('description'):
        score -= 30.0
    if not isinstance(raw_row.get('quantity'), (int, float)) or raw_row.get('quantity', 0) <= 0:
        score -= 20.0
    if not isinstance(raw_row.get('rate'), (int, float)) or raw_row.get('rate', 0) <= 0:
        score -= 20.0
        
    # Check math consistency (quantity * rate == amount)
    qty = raw_row.get('quantity', 0)
    rate = raw_row.get('rate', 0)
    expected_amount = qty * rate
    actual_amount = raw_row.get('amount', 0)
    
    if expected_amount > 0 and abs(expected_amount - actual_amount) > 0.01:
        score -= 15.0
        
    return max(0.0, score / 100.0)

def aggregate_document_confidence(row_confidences: List[float]) -> float:
    """
    Compute an overall confidence score for the entire document based on its rows.
    """
    if not row_confidences:
        return 1.0
    return sum(row_confidences) / len(row_confidences)
