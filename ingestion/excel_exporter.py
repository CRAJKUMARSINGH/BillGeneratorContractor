"""
Reverse Excel Exporter
Creates a standard 4-sheet Excel `.xlsx` file from parsed bill data.
Required for the Human-in-the-Loop OCR correction process.
Matches the structure expected by the Mode 1 Strict Guardian.
"""
import io
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any

def generate_excel_from_data(parsed_data: Dict[str, Any]) -> io.BytesIO:
    """
    Generates a PWD-structured Excel file (21-row header padding)
    that can be re-uploaded as Mode 1.
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # --- TITLE SHEET ---
        title_data = parsed_data.get("titleData", {})
        title_rows = [
            ["Platform", "Antigravity SaaS consolidated"],
            ["Export Date", datetime.now().strftime("%Y-%m-%d %H:%M")],
            ["Agreement No.", title_data.get("Agreement No.", "")],
            ["Total Amount", parsed_data.get("totalAmount", 0.0)]
        ]
        df_title = pd.DataFrame(title_rows)
        df_title.to_excel(writer, sheet_name='Title', index=False, header=False)

        # --- WORK ORDER SHEET (Mode 1 format) ---
        wo_header = [[""] * 7] * 21
        # Fill some header info in the first 21 rows
        wo_header[0] = ["Name of Work:", title_data.get("Name of Work", ""), "", "", "", "", ""]
        wo_header[1] = ["Agreement No:", title_data.get("Agreement No.", ""), "", "", "", "", ""]
        wo_header[2] = ["Contractor:", title_data.get("Name of Firm", title_data.get("Name of Contractor", "")), "", "", "", "", ""]
        
        # Column Headers at Row 20
        wo_header[20] = ["Item No.", "Description of Item", "Unit", "Quantity", "Rate", "Amount", "Remark"]
        
        bill_items = parsed_data.get("billItems", [])
        wo_data_rows = []
        for item in bill_items:
            wo_data_rows.append([
                item.get("itemNo", ""),
                item.get("description", ""),
                item.get("unit", ""),
                item.get("quantity", 0.0),
                item.get("rate", 0.0),
                item.get("amount", 0.0),
                item.get("remark", "")
            ])
            
        df_wo = pd.DataFrame(wo_header + wo_data_rows)
        df_wo.to_excel(writer, sheet_name='Work Order', index=False, header=False)
        
        # --- BILL QUANTITY SHEET ---
        bq_header = [[""] * 7] * 21
        bq_header[20] = ["Item No.", "Description of Item", "Unit", "Quantity", "Rate", "Amount", "Remark"]
        
        bq_data_rows = []
        for item in bill_items:
            bq_data_rows.append([
                item.get("itemNo", ""),
                item.get("description", ""),
                item.get("unit", ""),
                item.get("quantity", 0.0),
                item.get("rate", 0.0),
                item.get("amount", 0.0),
                item.get("remark", "")
            ])
            
        df_bq = pd.DataFrame(bq_header + bq_data_rows)
        df_bq.to_excel(writer, sheet_name='Bill Quantity', index=False, header=False)
        
        # --- EXTRA ITEMS SHEET ---
        extra_items = parsed_data.get("extraItems", [])
        ei_header = [[""] * 8] * 21
        ei_header[20] = ["Item No.", "Description of Item", "Unit", "Quantity", "Rate", "Amount", "BSR Ref", "Remark"]
        
        ei_data_rows = []
        for item in extra_items:
            ei_data_rows.append([
                item.get("itemNo", ""),
                item.get("description", ""),
                item.get("unit", ""),
                item.get("quantity", 0.0),
                item.get("rate", 0.0),
                item.get("amount", 0.0),
                item.get("bsr", ""),
                item.get("remark", "")
            ])
        df_ei = pd.DataFrame(ei_header + ei_data_rows)
        df_ei.to_excel(writer, sheet_name='Extra Items', index=False, header=False)
        
    output.seek(0)
    return output
