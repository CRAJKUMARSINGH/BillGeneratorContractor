import asyncio
import pandas as pd
import random
from pathlib import Path
import sys

root = Path(__file__).parent.parent
sys.path.append(str(root))

from ingestion.excel_parser import parse_excel_to_raw
from ingestion.normalizer import normalize_to_unified_model

async def simulate_robotic_billing(input_file: str):
    """
    Takes a Work Order Excel, robotically fills 5-10 items with random quantities,
    and runs it through the normalization pipeline.
    """
    print(f"--- ROBOTIC FILLER: {input_file} ---")
    
    # Use robust parser
    raw_data = parse_excel_to_raw(input_file)
    
    rows = raw_data.get("raw_rows", [])
    if not rows:
        print("No rows found to fill.")
        return

    # Randomly pick 5-10 items to fill
    num_to_fill = min(len(rows), random.randint(5, 10))
    indices = random.sample(range(len(rows)), num_to_fill)
    
    print(f"Filling {num_to_fill} random items...")
    for idx in indices:
        row = rows[idx]
        # Assumed quantity: between 10% and 100% of WO quantity (if exists) or random 1-100
        wo_qty = row.get("quantity", 100) # Fallback if no WO qty
        filled_qty = round(random.uniform(0.1, 1.0) * wo_qty, 2)
        row["quantity"] = filled_qty
        row["aiNote"] = f"Robotically filled with {filled_qty} units."

    # Normalize
    doc = normalize_to_unified_model(raw_data, source_type="mode_robotic")
    
    print(f"Unified Document Created: {doc.fileName}")
    print(f"Total Items: {len(doc.billItems)}")
    print(f"Filled Items: {num_to_fill}")
    print(f"Grand Total: {doc.totalAmount}")
    
    return doc

if __name__ == "__main__":
    sample = "INPUT/recent_projects/haphazard/SAMPLE BILL INPUT- NO EXTRA ITEMS.xlsx"
    if not Path(sample).exists():
        # Try finding any excel in recent_projects
        excels = list(Path("INPUT/recent_projects").glob("**/*.xlsx"))
        if excels:
            sample = str(excels[0])
        else:
            print("No sample excel found.")
            sys.exit(1)
            
    asyncio.run(simulate_robotic_billing(sample))
