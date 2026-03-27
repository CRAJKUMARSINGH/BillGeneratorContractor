"""
Procedural Batch Input Generator
Creates 24 diverse ParsedBillData JSON payloads mimicking OCR output
to rigorously test the AI anomaly detectors and batch throughput capabilities.
"""
import sys, os, json, random
from pathlib import Path

root_dir = Path(__file__).parent.absolute()
batch_dir = root_dir / "BATCH_SYSTEM" / "PENDING_INPUTS"
batch_dir.mkdir(parents=True, exist_ok=True)

# Base template matching the ParsedBillData / UnifiedDocumentModel structure
def create_mock_payload(index: int, with_extra: bool, force_dirty: bool) -> dict:
    scenario = "CLEAN" if not force_dirty else "DIRTY"
    extra_str = "With_ExtraItems" if with_extra else "No_ExtraItems"
    
    file_id = f"BATCH_{index:02d}_{scenario}_{extra_str}"
    
    amount_multiplier = 1.0 if not force_dirty else random.choice([0.1, 5.0])
    qty_multiplier = 1.0 if not force_dirty else random.choice([0.0, 10.0])
    
    payload = {
        "fileId": file_id,
        "fileName": f"{file_id}.json",
        "titleData": {
            "Agreement No.": f"AGR-BATCH-{index}",
            "Name of Work": f"Construction of Batch Asset {index} (Scenario: {scenario})",
            "Name of Contractor": "Antigravity Automated Contractor Ltd.",
            "Work Order Amount Rs.": f"{500000 + (index * 15000)}",
            "Date of written order to commence work": "10/01/2026",
            "St. Date of Completion": "10/08/2026",
            "Date of actual completion of work": ""
        },
        "billItems": [
            {
                "itemNo": "1",
                "description": f"Earthwork excavation in {scenario} conditions",
                "unit": "cum",
                "quantitySince": 0,
                "quantityUpto": 100 * qty_multiplier,
                "quantity": 100 * qty_multiplier,
                "rate": 150.0,
                "amount": 15000 * amount_multiplier
            },
            {
                "itemNo": "2",
                "description": "Providing and laying PCC 1:4:8",
                "unit": "cum",
                "quantitySince": 0,
                "quantityUpto": 25 * qty_multiplier,
                "quantity": 25 * qty_multiplier,
                "rate": 4500.0,
                "amount": 112500 * amount_multiplier
            }
        ],
        "extraItems": [],
        "hasExtraItems": with_extra,
        "sheets": ["OCR Output"]
    }
    
    # Calculate Total
    total = sum(i["amount"] for i in payload["billItems"])
    
    if with_extra:
        payload["extraItems"] = [
            {
                "itemNo": "E-01",
                "bsr": "10.0.1",
                "description": "Extra item scanned from field notes",
                "quantity": 5.0 * qty_multiplier,
                "unit": "sqm",
                "rate": 1200.0,
                "amount": 6000.0 * amount_multiplier,
                "remark": "Approved"
            }
        ]
        total += sum(i["amount"] for i in payload["extraItems"])
        
    payload["totalAmount"] = total
    
    return payload

def main():
    print("Generating 24 Batch Input Files (12 w/o Extra Items, 12 w/ Extra Items)")
    
    count = 0
    # Generate 12 WITHOUT extra items
    for i in range(1, 13):
        # make 10% dirty to test quarantine
        force_dirty = (i % 6 == 0) 
        payload = create_mock_payload(i, with_extra=False, force_dirty=force_dirty)
        
        file_path = batch_dir / f"{payload['fileName']}"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        count += 1
        
    # Generate 12 WITH extra items
    for i in range(13, 25):
        # make 10% dirty to test quarantine
        force_dirty = (i % 6 == 0) 
        payload = create_mock_payload(i, with_extra=True, force_dirty=force_dirty)
        
        file_path = batch_dir / f"{payload['fileName']}"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        count += 1

    print(f"✅ Successfully wrote {count} files to {batch_dir}")

if __name__ == "__main__":
    main()
