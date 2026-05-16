from typing import List, Dict, Any

def calculate_row_confidence(raw_row: Dict[str, Any]) -> float:
    """
    Calculate a confidence score for a parsed row.
    Missing fields, jargon mismatch, or anomalous values reduce the score.
    """
    score = 100.0
    
    desc = str(raw_row.get('description', ''))
    qty = raw_row.get('quantity', 0)
    rate = raw_row.get('rate', 0)
    unit = str(raw_row.get('unit', '')).lower()
    
    # 1. Missing crucial fields
    if not desc or len(desc) < 3:
        score -= 30.0
    if not isinstance(qty, (int, float)) or qty <= 0:
        score -= 15.0
    if not isinstance(rate, (int, float)) or rate <= 0:
        score -= 15.0
        
    # 2. Jargon/Unit Validation (PWD Specific)
    valid_units = {'cum', 'sqm', 'rm', 'mtr', 'kg', 'nos', 'each', 'ls', 'sqft', 'cft', 'mt'}
    if unit and unit not in valid_units:
        score -= 10.0
        
    # 3. OCR Noise Detection (junk characters in description)
    noise_chars = ['|', '_', '@', '#', '$', '%', '^', '*', '~']
    noise_count = sum(1 for char in desc if char in noise_chars)
    if noise_count > 2:
        score -= 10.0
    
    # 4. Math Consistency (quantity * rate == amount)
    expected_amount = qty * rate
    actual_amount = raw_row.get('amount', 0)
    if expected_amount > 0 and abs(expected_amount - actual_amount) > 1.0: # Allow 1.0 rounding diff
        score -= 10.0
        
    return max(0.0, score / 100.0)

def aggregate_document_confidence(row_confidences: List[float]) -> float:
    """
    Compute an overall confidence score for the entire document based on its rows.
    """
    if not row_confidences:
        return 1.0
    return sum(row_confidences) / len(row_confidences)
