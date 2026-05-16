import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import io
import logging

logger = logging.getLogger(__name__)

def find_header_row(df: pd.DataFrame) -> Optional[int]:
    """
    Scans a DataFrame to find the row index that most likely contains headers.
    """
    keywords = {"description", "rate", "quantity", "qty", "item", "unit", "amount", "bsr"}
    for idx, row in df.iterrows():
        row_values = [str(v).lower() for v in row.values if pd.notna(v)]
        matches = sum(1 for v in row_values if any(kw in v for kw in keywords))
        if matches >= 3: # Heuristic: 3 keywords define a header
            return idx
    return None

def map_columns(header_row: pd.Series) -> Dict[str, str]:
    """
    Maps column indices/names to canonical names based on header text.
    """
    mapping = {}
    keywords_map = {
        "item_no": ["bsr", "item no", "code", "item code", "ref. bsr"],
        "serial_no": ["item", "s.no", "sl.no", "serial"],
        "description": ["description", "particulars"],
        "quantity": ["quantity", "qty", "quantity_upto_date"],
        "rate": ["rate"],
        "amount": ["amount"],
        "unit": ["unit"]
    }
    
    for idx, val in header_row.items():
        if pd.isna(val): continue
        s = str(val).lower()
        for canonical, kws in keywords_map.items():
            if any(kw in s for kw in kws):
                # Prioritize item_no for 'BSR' or 'Item No'
                if canonical == "item_no":
                    mapping[idx] = "item_no"
                elif idx not in mapping: # Don't overwrite if already mapped to something better
                    mapping[idx] = canonical
    return mapping

def parse_excel_to_raw(file_path_or_bytes: Any) -> Dict[str, Any]:
    """
    Robustly parses PWD Excel files, even haphazard ones.
    """
    try:
        # We process all sheets if it's an ExcelFile, or just the first one if we can't find specific ones
        if isinstance(file_path_or_bytes, (str, bytes, io.BytesIO)):
            excel_file = pd.ExcelFile(file_path_or_bytes)
        else:
            excel_file = file_path_or_bytes

        all_raw_rows = []
        metadata = {"filename": str(file_path_or_bytes) if isinstance(file_path_or_bytes, str) else "bytes"}
        
        # Priority sheets
        target_sheets = [s for s in excel_file.sheet_names if any(kw in s.lower() for kw in ["bill", "quantity", "work order"])]
        if not target_sheets:
            target_sheets = excel_file.sheet_names[:2] # Fallback to first two sheets

        for sheet_name in target_sheets:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
            header_idx = find_header_row(df)
            
            if header_idx is not None:
                header_row = df.iloc[header_idx]
                col_mapping = map_columns(header_row)
                
                # Data starts after header
                data_df = df.iloc[header_idx + 1:]
                
                for _, row in data_df.iterrows():
                    raw_row = {}
                    has_data = False
                    for col_idx, canonical_name in col_mapping.items():
                        val = row[col_idx]
                        if pd.notna(val):
                            raw_row[canonical_name] = val
                            if canonical_name in ["description", "quantity", "amount"] and val:
                                has_data = True
                    
                    if has_data:
                        # Carry over sheet name for context
                        raw_row["source_sheet"] = sheet_name
                        all_raw_rows.append(raw_row)
            else:
                logger.warning(f"Could not find header in sheet '{sheet_name}'")

        metadata["total_rows_parsed"] = len(all_raw_rows)
        metadata["sheets"] = excel_file.sheet_names
        
        return {
            "metadata": metadata,
            "raw_rows": all_raw_rows
        }
    except Exception as e:
        logger.error(f"Failed to parse Excel: {e}")
        raise ValueError(f"Failed to parse Excel: {str(e)}")
