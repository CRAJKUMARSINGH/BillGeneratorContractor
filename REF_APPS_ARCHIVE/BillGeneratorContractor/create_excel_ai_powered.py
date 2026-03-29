#!/usr/bin/env python3
"""
WORLD-CLASS AUTOMATED SOLUTION
Create INPUT Excel from Work Order Images + QTY.txt
Uses Google Gemini Vision API for OCR (no Tesseract needed)
100% Automated - Zero Manual Entry

NOTE (Genspark security fix):
  API key is read from the GEMINI_API_KEY environment variable.
  NEVER hardcode API keys in source files.
"""
import json
import os
import re
import sys
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side

# Try to import google.generativeai
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not installed. Install with: pip install google-generativeai")


class WorkOrderExtractor:
    """Extract work order data from images using Gemini Vision API."""

    PROMPT = (
        "You are an expert at extracting structured data from Indian PWD "
        "(Public Works Department) work order documents.\n\n"
        "Analyze these work order images and return ONLY a valid JSON object "
        "with this exact structure:\n"
        '{\n'
        '  "title_info": {\n'
        '    "contractor_name": "Full contractor/supplier name",\n'
        '    "work_name": "Complete work description",\n'
        '    "work_order_number": "WO number",\n'
        '    "agreement_number": "Agreement number",\n'
        '    "work_order_amount": "Total amount in Rs.",\n'
        '    "tender_premium_percent": "Premium percentage",\n'
        '    "premium_type": "Above or Below"\n'
        '  },\n'
        '  "work_items": [\n'
        '    {\n'
        '      "item_no": "Item number (e.g., 1.0, 1.1.2)",\n'
        '      "description": "Complete item description in English",\n'
        '      "unit": "Unit of measurement (e.g., Each, P. point, Sqm, Cum)",\n'
        '      "quantity": "Quantity from work order (number only)",\n'
        '      "rate": "Rate per unit in Rs. (number only)",\n'
        '      "amount": "Total amount (number only)",\n'
        '      "bsr_code": "BSR code if available"\n'
        '    }\n'
        '  ]\n'
        '}\n\n'
        "CRITICAL REQUIREMENTS:\n"
        "1. Extract EVERY item — main items and sub-items\n"
        "2. Item numbers must match exactly (1.0, 1.1.2, 1.3.3, 3.4.2, 4.1.23, 18.13, etc.)\n"
        "3. Descriptions must be complete and accurate\n"
        "4. Units must be standard PWD units\n"
        "5. All numerical values must be accurate numbers (no commas)\n"
        "6. Include bsr_code if visible\n"
        "7. Return ONLY valid JSON — no markdown, no explanation"
    )

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Gemini API key (falls back to GEMINI_API_KEY env var)."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

        if not self.api_key:
            raise ValueError(
                "Gemini API key required.\n"
                "Set GEMINI_API_KEY in your .env file or shell.\n"
                "Get a free API key from: https://makersuite.google.com/app/apikey"
            )
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def extract_from_images(self, image_paths: List[Path]) -> Dict:
        """Extract complete work order data from images using Gemini Vision API."""
        print(f"\n{'='*80}\nAI-POWERED WORK ORDER EXTRACTION\n{'='*80}\n")

        # Encode images for Gemini
        parts = [self.PROMPT]
        for img_path in image_paths:
            print(f"  Loading image: {img_path.name}")
            with open(img_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            mime_type = "image/jpeg" if img_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
            parts.append({"mime_type": mime_type, "data": img_data})

        try:
            response = self.model.generate_content(parts)
            response_text = response.text.strip()

            # Locate and parse JSON block
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start == -1:
                raise ValueError("No JSON object found in Gemini response")

            parsed = json.loads(response_text[json_start:json_end])
            work_items = parsed.get("work_items", [])

            print(f"  ✓ Gemini extracted {len(work_items)} items")
            return parsed

        except Exception as exc:
            print(f"  ⚠️  AI extraction failed: {exc}\n  Using empty fallback.")
            return {"title_info": {}, "work_items": []}


# ── Standalone helpers ─────────────────────────────────────────────────────────

def _read_quantities(qty_file: Path) -> Dict[str, float]:
    """Read item quantities from qty.txt (format: <code> <qty> per line)."""
    quantities: Dict[str, float] = {}
    if not qty_file.exists():
        print(f"  ⚠️  {qty_file} not found — quantities will be 0")
        return quantities
    with open(qty_file, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                try:
                    quantities[parts[0]] = float(parts[1])
                except ValueError:
                    pass
    print(f"  ✓ Loaded {len(quantities)} quantities from {qty_file.name}")
    return quantities


def _save_excel(
    work_items: List[Dict],
    quantities: Dict[str, float],
    output_file: Path,
) -> None:
    """Build and save an Excel bill input file."""
    rows = []
    for item in work_items:
        code = str(item.get("bsr_code", item.get("item_no", "")))
        qty = quantities.get(code, float(item.get("quantity", 0) or 0))
        try:
            rate = float(str(item.get("rate", 0)).replace(",", "") or 0)
        except ValueError:
            rate = 0.0
        rows.append({
            "S.No.":                str(len(rows) + 1),
            "Item Code":            code,
            "Description of Item":  item.get("description", ""),
            "Quantity":             qty,
            "Unit":                 item.get("unit", ""),
            "Rate (Rs.)":           rate,
            "Amount (Rs.)":         round(qty * rate, 2),
        })

    df = pd.DataFrame(rows)
    total = df["Amount (Rs.)"].sum()

    # Append total row
    df = pd.concat([
        df,
        pd.DataFrame([{
            "S.No.": "", "Item Code": "",
            "Description of Item": "TOTAL",
            "Quantity": "", "Unit": "",
            "Rate (Rs.)": "", "Amount (Rs.)": total,
        }])
    ], ignore_index=True)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Bill")
        ws = writer.sheets["Bill"]
        ws.column_dimensions["A"].width = 8
        ws.column_dimensions["B"].width = 12
        ws.column_dimensions["C"].width = 80
        ws.column_dimensions["D"].width = 12
        ws.column_dimensions["E"].width = 10
        ws.column_dimensions["F"].width = 12
        ws.column_dimensions["G"].width = 15

    print(f"\n  ✓ Excel saved: {output_file}")
    print(f"  Total Amount: Rs. {total:,.2f}")


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    INPUT_FOLDER  = Path("INPUT_WORK_ORDER_IMAGES_TEXT")
    QTY_FILE      = INPUT_FOLDER / "qty.txt"
    OUTPUT_FILE   = Path("OUTPUT/contractor_bill_ai.xlsx")

    extractor = WorkOrderExtractor()   # reads GEMINI_API_KEY from env

    images = sorted(INPUT_FOLDER.glob("*.jpg")) + sorted(INPUT_FOLDER.glob("*.jpeg"))
    if not images:
        print(f"No images found in {INPUT_FOLDER}")
        return

    data = extractor.extract_from_images(images)
    quantities = _read_quantities(QTY_FILE)
    _save_excel(data.get("work_items", []), quantities, OUTPUT_FILE)

    print("\n" + "="*80)
    print("✅ SUCCESS! AI-powered contractor bill created at:")
    print(f"   {OUTPUT_FILE.absolute()}")
    print("="*80)


if __name__ == "__main__":
    main()
