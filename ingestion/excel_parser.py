import pandas as pd
from typing import Dict, Any, List
import uuid

def parse_excel_to_raw(file_path: str) -> Dict[str, Any]:
    """
    Parse an Excel file and extract raw rows and metadata.
    """
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        raise ValueError(f"Failed to read Excel file: {str(e)}")
        
    raw_rows = []
    
    # Simple heuristic to find data rows
    for index, row in df.iterrows():
        # Clean dict to remove NaN
        clean_row = {
            col: val if pd.notna(val) else None 
            for col, val in row.to_dict().items()
        }
        # Only add rows that likely have meaningful data
        if any(clean_row.values()):
            raw_rows.append(clean_row)
            
    return {
        "metadata": {"filename": file_path, "total_rows_parsed": len(raw_rows)},
        "raw_rows": raw_rows
    }
