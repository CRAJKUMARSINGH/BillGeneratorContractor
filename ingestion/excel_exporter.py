"""
Reverse Excel Exporter
Creates a standard 4-sheet Excel `.xlsx` file from parsed bill data.
Required for the Human-in-the-Loop OCR correction process.
"""
import io
from datetime import datetime
import pandas as pd
from typing import Dict, Any

def generate_excel_from_data(parsed_data: Dict[str, Any]) -> io.BytesIO:
    """
    Takes ParsedBillData dictionary format and generates a standard 
    4-sheet Excel file representing the Work Order, Bill Quantity, and Extra Items.
    Returns a BytesIO object containing the xlsx file.
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # --- SHEET 1: TITLE (Metadata Summary) ---
        title_data = parsed_data.get("titleData", {})
        title_rows = [
            ["Platform", "Antigravity SaaS consolidated"],
            ["Export Date", datetime.now().strftime("%Y-%m-%d %H:%M")],
            ["Agreement No.", title_data.get("Agreement No.", "")],
            ["Total Amount", parsed_data.get("totalAmount", 0.0)]
        ]
        df_title = pd.DataFrame(title_rows, columns=["Key", "Value"])
        df_title.to_excel(writer, sheet_name='TITLE', index=False, header=False)

        # --- SHEET 2: WORK ORDER ---
        wo_rows = []
        wo_rows.append(["Agreement No.", title_data.get("Agreement No.", "")])
        wo_rows.append(["Name of Work", title_data.get("Name of Work", "")])
        wo_rows.append(["Name of Contractor", title_data.get("Name of Contractor", "")])
        wo_rows.append(["Work Order Amount Rs.", title_data.get("Work Order Amount Rs.", "")])
        wo_rows.append(["Date of written order to commence work", title_data.get("Date of written order to commence work", "")])
        wo_rows.append(["St. Date of Completion", title_data.get("St. Date of Completion", "")])
        wo_rows.append(["Date of actual completion of work", title_data.get("Date of actual completion of work", "")])
        
        df_wo = pd.DataFrame(wo_rows, columns=["Field", "Value"])
        df_wo.to_excel(writer, sheet_name='WORK ORDER', index=False, header=False)
        
        # --- SHEET 3: BILL QUANTITY ---
        bill_items = parsed_data.get("billItems", [])
        bq_columns = ["S.No.", "Description of Item", "Unit", "Quantity Since Prev", "Rate", "Amount"]
        bq_rows = []
        for i, item in enumerate(bill_items, 1):
            bq_rows.append([
                item.get("itemNo", str(i)),
                item.get("description", ""),
                item.get("unit", ""),
                item.get("quantity", 0.0),
                item.get("rate", 0.0),
                item.get("amount", 0.0)
            ])
            
        df_bq = pd.DataFrame(bq_rows, columns=bq_columns)
        df_bq.to_excel(writer, sheet_name='BILL QUANTITY', index=False)
        
        # --- SHEET 4: EXTRA ITEMS ---
        extra_items = parsed_data.get("extraItems", [])
        ei_columns = ["S.No.", "Ref. BSR No.", "Qty.", "unit", "Rate", "Amount"]
        ei_rows = []
        for i, item in enumerate(extra_items, 1):
            ei_rows.append([
                f"E-{i:02d}",
                item.get("description", ""),
                item.get("quantity", 0.0),
                item.get("unit", ""),
                item.get("rate", 0.0),
                item.get("amount", 0.0)
            ])
        df_ei = pd.DataFrame(ei_rows, columns=ei_columns)
        df_ei.to_excel(writer, sheet_name='EXTRA ITEMS', index=False)
        
    output.seek(0)
    return output
