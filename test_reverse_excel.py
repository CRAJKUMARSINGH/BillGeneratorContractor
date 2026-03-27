"""
Test the Reverse Excel Generator (Option B)
"""
import sys
from pathlib import Path

root = Path(__file__).parent.absolute()
sys.path.insert(0, str(root))

from ingestion.excel_exporter import generate_excel_from_data

# Mock OCR Data simulating a dirty scan that was normalized
mock_data = {
    "titleData": {
        "Agreement No.": "AGR-123",
        "Name of Work": "Repair of Dirty Road Scan",
        "Name of Contractor": "OCR Fixer Ltd.",
        "Work Order Amount Rs.": "500000",
        "Date of written order to commence work": "01/01/2026",
        "St. Date of Completion": "01/06/2026",
        "Date of actual completion of work": ""
    },
    "billItems": [
        {
            "itemNo": "1",
            "description": "Earthwork excavation with dirty OCR numbers",
            "unit": "cum",
            "quantity": 105.5,
            "rate": 150.0,
            "amount": 15825.0
        },
        {
            "itemNo": "2",
            "description": "PCC 1:4:8",
            "unit": "cum",
            "quantity": 25.0,
            "rate": 4500.0,
            "amount": 112500.0
        }
    ],
    "extraItems": [
        {
            "description": "Extra item scanned improperly",
            "quantity": 5.0,
            "unit": "sqm",
            "rate": 1200.0,
            "amount": 6000.0
        }
    ]
}

print("Running Reverse Excel Generator...")
excel_io = generate_excel_from_data(mock_data)

out_path = root / "ANTIGRAVITY IMAGE TEXT SAMPLES" / "Reverse_Excel_Test.xlsx"
out_path.write_bytes(excel_io.getvalue())

print(f"Success! Generated Excel file saved to: {out_path}")
