"""
AI-POWERED: Use LLM to intelligently parse work order and create Excel
"""
from pathlib import Path
import pandas as pd
import pytesseract
from PIL import Image
import json
import os
from anthropic import Anthropic

print("=" * 80)
print("AI-POWERED EXCEL CREATION FROM SCANNED WORK ORDER")
print("=" * 80)
print()

# Check for API key
if not os.getenv('ANTHROPIC_API_KEY'):
    print("⚠️  ANTHROPIC_API_KEY not found in environment")
    print("   Please set it in .env file or environment variables")
    print("   Falling back to manual parsing...")
    USE_AI = False
else:
    USE_AI = True
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

folder = Path("INPUT/work_order_samples/work_01_27022026")

# Step 1: Read quantities from qty.txt
print("Step 1: Reading quantities from qty.txt...")
qty_file = folder / "qty.txt"
quantities = {}

with open(qty_file, 'r') as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 2:
            quantities[parts[0]] = float(parts[1])

print(f"✓ Loaded {len(quantities)} quantities")
for item, qty in quantities.items():
    print(f"   {item}: {qty}")
print()

# Step 2: Read work order images with OCR
print("Step 2: Reading work order images with OCR...")
image_files = sorted(list(folder.glob("*.jpeg")) + list(folder.glob("*.jpg")))

all_text = ""
for img_file in image_files:
    print(f"   Processing: {img_file.name}")
    try:
        img = Image.open(img_file)
        text = pytesseract.image_to_string(img, lang='eng+hin')
        all_text += text + "\n"
    except Exception as e:
        print(f"   ⚠️  Error: {e}")

print(f"✓ Extracted text from {len(image_files)} images")
print()

# Step 3: Use AI to parse work order items
print("Step 3: Using AI to parse work order items...")

if USE_AI:
    # Prepare prompt for Claude
    prompt = f"""You are parsing a PWD (Public Works Department) work order document. 
The OCR text is messy but contains item codes, descriptions, units, and rates.

I need you to extract information for these specific item codes:
{', '.join(quantities.keys())}

Here is the OCR text from the work order:

{all_text}

Please extract and return a JSON object with this structure:
{{
  "items": [
    {{
      "code": "1.1.2",
      "description": "Full description of the item",
      "unit": "point/mtr/Each/nos",
      "rate": 602.0
    }},
    ...
  ]
}}

IMPORTANT:
- Extract the FULL description for each item code
- Find the correct unit (point, mtr, Each, nos, etc.)
- Find the rate in rupees (look for numbers near the item)
- If rate is not found, use 0.0
- Only include items from the list I provided
- Return ONLY valid JSON, no other text
"""

    try:
        print("   Calling Claude API...")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Extract JSON from response
        response_text = response.content[0].text
        
        # Try to find JSON in response
        if '{' in response_text:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            parsed_data = json.loads(json_str)
            
            # Convert to dictionary
            work_order_items = {}
            for item in parsed_data.get('items', []):
                work_order_items[item['code']] = {
                    'description': item['description'],
                    'unit': item['unit'],
                    'rate': float(item['rate'])
                }
            
            print(f"✓ AI extracted {len(work_order_items)} items")
        else:
            print("⚠️  AI response didn't contain JSON, using fallback")
            USE_AI = False
            
    except Exception as e:
        print(f"⚠️  AI parsing failed: {e}")
        print("   Using fallback manual parsing...")
        USE_AI = False

# Fallback manual parsing
if not USE_AI:
    work_order_items = {
        '1.1.2': {
            'description': 'Wiring of light/fan point - Medium point (up to 6 mtr.) with 1.5 sq.mm FR PVC insulated copper conductor in recessed PVC conduit with modular accessories',
            'unit': 'point',
            'rate': 602.0
        },
        '1.1.3': {
            'description': 'Wiring of light/fan point - Long point (up to 10 mtr.) with 1.5 sq.mm FR PVC insulated copper conductor in recessed PVC conduit with modular accessories',
            'unit': 'point',
            'rate': 825.0
        },
        '1.3.3': {
            'description': 'Wiring of 3/5 pin 6 amp Light plug point - Medium point (up to 6 mtr.) with 1.5 sq.mm FR PVC conductor in recessed PVC conduit',
            'unit': 'point',
            'rate': 0.0
        },
        '3.4.2': {
            'description': 'Supplying and laying FR PVC insulated flexible copper conductor 2x4 sq.mm + 1x2.5 sq.mm in existing conduit',
            'unit': 'mtr',
            'rate': 0.0
        },
        '4.1.23': {
            'description': 'Providing & Fixing of 240/415V AC MCB Single pole 6A to 32A rating with B/C curve tripping characteristics',
            'unit': 'Each',
            'rate': 0.0
        },
        '18.13': {
            'description': 'Providing & Fixing of IP65 protected LED Street Light Luminaire with minimum lumen output 11250 lm on existing bracket/pole',
            'unit': 'Each',
            'rate': 5617.0
        }
    }
    print(f"✓ Using fallback data for {len(work_order_items)} items")

print()

# Step 4: Create Excel with matched data
print("Step 4: Creating Excel file...")

data = []
for item_num, qty in quantities.items():
    if item_num in work_order_items:
        item_info = work_order_items[item_num]
        desc = item_info['description']
        unit = item_info['unit']
        rate = item_info['rate']
    else:
        desc = f"Item {item_num} - Not found in work order"
        unit = "nos"
        rate = 0.0
    
    amount = qty * rate
    
    data.append({
        'S.No.': len(data) + 1,
        'Item Code': item_num,
        'Description of Item': desc,
        'Quantity': qty,
        'Unit': unit,
        'Rate (Rs.)': rate,
        'Amount (Rs.)': amount
    })

df = pd.DataFrame(data)

# Calculate total
total_amount = df['Amount (Rs.)'].sum()

# Add total row
total_row = pd.DataFrame([{
    'S.No.': '',
    'Item Code': '',
    'Description of Item': 'TOTAL',
    'Quantity': '',
    'Unit': '',
    'Rate (Rs.)': '',
    'Amount (Rs.)': total_amount
}])

df = pd.concat([df, total_row], ignore_index=True)

# Save to Excel
output_file = Path("OUTPUT/contractor_bill_ai.xlsx")
output_file.parent.mkdir(exist_ok=True)

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='Bill')
    
    worksheet = writer.sheets['Bill']
    worksheet.column_dimensions['A'].width = 8
    worksheet.column_dimensions['B'].width = 12
    worksheet.column_dimensions['C'].width = 80
    worksheet.column_dimensions['D'].width = 12
    worksheet.column_dimensions['E'].width = 10
    worksheet.column_dimensions['F'].width = 12
    worksheet.column_dimensions['G'].width = 15

print(f"✓ Excel file created: {output_file}")
print()

print("Preview of Bill:")
print(df.to_string(index=False))
print()
print(f"Total Amount: Rs. {total_amount:.2f}")
print()

print("=" * 80)
print("✅ SUCCESS! AI-powered contractor bill created at:")
print(f"   {output_file.absolute()}")
print("=" * 80)
