"""
Safe Data Type Conversions
Prevents crashes from invalid data in Excel files
"""

def safe_float(value, default=0.0):
    """
    Safely convert value to float, handling text and invalid values
    
    Args:
        value: Value to convert (can be string, number, None, etc.)
        default: Default value if conversion fails (default: 0.0)
    
    Returns:
        float: Converted value or default
    
    Examples:
        >>> safe_float(100)
        100.0
        >>> safe_float("100")
        100.0
        >>> safe_float("Above")
        0.0
        >>> safe_float("As per", default=1.0)
        1.0
        >>> safe_float(None)
        0.0
    """
    if value is None:
        return default
    
    # If already a number, return it
    if isinstance(value, (int, float)):
        return float(value)
    
    # Try to convert string to float
    try:
        return float(value)
    except (ValueError, TypeError):
        # Handle common text values in Excel
        text_value = str(value).strip().lower()
        
        # Log warning for debugging (optional)
        if text_value and text_value not in ['', 'nan', 'none', 'null']:
            # Could log here: print(f"Warning: Could not convert '{value}' to float, using {default}")
            pass
        
        return default


def safe_int(value, default=0):
    """
    Safely convert value to int, handling text and invalid values
    
    Args:
        value: Value to convert
        default: Default value if conversion fails (default: 0)
    
    Returns:
        int: Converted value or default
    """
    if value is None:
        return default
    
    if isinstance(value, int):
        return value
    
    try:
        return int(float(value))  # Convert via float first to handle "100.0"
    except (ValueError, TypeError):
        return default


def safe_str(value, default=''):
    """
    Safely convert value to string, handling None and invalid values
    
    Args:
        value: Value to convert
        default: Default value if conversion fails (default: '')
    
    Returns:
        str: Converted value or default
    """
    if value is None:
        return default
    
    try:
        text = str(value).strip()
        # Handle pandas NaN
        if text.lower() in ['nan', 'none', 'null']:
            return default
        return text
    except:
        return default


def clean_numeric_string(value):
    """
    Clean numeric string by removing currency symbols, commas, etc.
    
    Args:
        value: String value to clean
    
    Returns:
        str: Cleaned string ready for float conversion
    
    Examples:
        >>> clean_numeric_string("₹1,234.56")
        "1234.56"
        >>> clean_numeric_string("$1,000")
        "1000"
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove common currency symbols and formatting
    cleaned = value.strip()
    cleaned = cleaned.replace('₹', '')
    cleaned = cleaned.replace('$', '')
    cleaned = cleaned.replace('€', '')
    cleaned = cleaned.replace('£', '')
    cleaned = cleaned.replace(',', '')
    cleaned = cleaned.replace(' ', '')
    
    return cleaned


def safe_float_with_cleaning(value, default=0.0):
    """
    Safely convert value to float with automatic cleaning
    Handles currency symbols, commas, etc.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        float: Converted value or default
    
    Examples:
        >>> safe_float_with_cleaning("₹1,234.56")
        1234.56
        >>> safe_float_with_cleaning("Above")
        0.0
    """
    if value is None:
        return default
    
    if isinstance(value, (int, float)):
        return float(value)
    
    # Try direct conversion first
    try:
        return float(value)
    except (ValueError, TypeError):
        pass
    
    # Try with cleaning
    try:
        cleaned = clean_numeric_string(value)
        return float(cleaned)
    except (ValueError, TypeError):
        return default


# Convenience functions for common Excel data types
def safe_quantity(value):
    """Convert quantity value safely (default: 0.0)"""
    return safe_float(value, default=0.0)


def safe_rate(value):
    """Convert rate value safely (default: 0.0)"""
    return safe_float(value, default=0.0)


def safe_amount(value):
    """Convert amount value safely (default: 0.0)"""
    return safe_float_with_cleaning(value, default=0.0)


def safe_percentage(value):
    """Convert percentage value safely (default: 0.0)"""
    return safe_float(value, default=0.0)
