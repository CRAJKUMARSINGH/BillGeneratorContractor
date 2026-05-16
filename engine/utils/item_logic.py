import re
from typing import List, Tuple, Union, Any

def canonicalize_item_code(code: Any) -> str:
    """
    Standardizes PWD item codes (e.g. 1.2.3c, 1-2-3c, 1.2.3 C) into a canonical key.
    """
    if code is None or str(code).lower() in ['nan', 'none', '']:
        return ""
    
    # Stringify and lower
    s = str(code).strip().lower()
    
    # Replace common separators with dots
    s = re.sub(r'[\s\-]+', '.', s)
    
    # Remove redundant dots
    s = re.sub(r'\.+', '.', s)
    
    # Strip leading/trailing dots
    s = s.strip('.')
    
    return s

def split_code_for_sorting(code: str) -> List[Union[int, str]]:
    """
    Splits a code like '1.2.10c' into [1, 2, 10, 'c'] for natural sorting.
    """
    parts = code.split('.')
    result = []
    for p in parts:
        # Match numeric part and trailing letter
        match = re.match(r'(\d+)([a-z]*)', p)
        if match:
            num, letter = match.groups()
            result.append(int(num))
            if letter:
                result.append(letter)
        else:
            result.append(p)
    return result

def sort_bill_items(items: List[Any]) -> List[Any]:
    """
    Sorts a list of BillItems (or dicts) hierarchically based on itemNo.
    """
    def get_key(item):
        code = item.itemNo if hasattr(item, 'itemNo') else item.get('itemNo', '')
        # Handle cases where itemNo might be empty or a description header
        if not code:
            return [float('inf')] # Put empty codes at the bottom
        return split_code_for_sorting(canonicalize_item_code(code))

    return sorted(items, key=get_key)
