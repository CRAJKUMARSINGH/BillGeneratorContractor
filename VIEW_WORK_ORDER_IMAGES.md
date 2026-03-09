# Work Order Images - Quick Reference

## Location
**Path:** `E:\Rajkumar\BillGeneratorContractor\INPUT\work_order_samples\work_01_27022026`

## Available Images (5 files)

### Image 1: WhatsApp Image 2026-02-25 at 1.13.49 PM.jpeg
- First page of work order
- Contains header information
- May have initial items

### Image 2: WhatsApp Image 2026-02-25 at 1.14.08 PM.jpeg
- Continuation of work order
- Contains more items

### Image 3: WhatsApp Image 2026-02-25 at 1.14.51 PM.jpeg
- Middle section of work order
- Contains item details

### Image 4: WhatsApp Image 2026-02-25 at 1.15.04 PM.jpeg
- More work order items
- May contain rates and quantities

### Image 5: WhatsApp Image 2026-02-25 at 1.15.19 PM.jpeg
- Final page of work order
- May contain totals and signatures

## How to View Images

### Option 1: Windows Photo Viewer
```bash
start INPUT\work_order_samples\work_01_27022026\
```
Then double-click each image to view

### Option 2: Open in Browser
1. Navigate to the folder in File Explorer
2. Right-click any image
3. Select "Open with" → "Microsoft Edge" or "Chrome"
4. Use arrow keys to navigate between images

### Option 3: Use PowerShell
```powershell
# View first image
Invoke-Item "INPUT\work_order_samples\work_01_27022026\WhatsApp Image 2026-02-25 at 1.13.49 PM.jpeg"
```

## Data Entry Workflow

### Step 1: Open Template
```bash
start OUTPUT\work_order_template.xlsx
```

### Step 2: Open Images
```bash
start INPUT\work_order_samples\work_01_27022026\
```

### Step 3: Side-by-Side View
1. Open Excel template on left half of screen
2. Open image viewer on right half of screen
3. Read from images and type into Excel

### Step 4: What to Extract

From the work order images, look for:

#### Title Information (Sheet 1)
- [ ] Work Name / Project Name
- [ ] Agreement Number
- [ ] Contractor Name
- [ ] Work Order Number
- [ ] Work Order Date
- [ ] Estimated Cost
- [ ] Agreement Amount
- [ ] Department/Division details

#### Work Items (Sheet 2)
For each item, extract:
- [ ] Item Number (1, 2, 3, etc.)
- [ ] Description (full text)
- [ ] Unit (sqm, cum, kg, nos, rmt, etc.)
- [ ] Quantity (from work order)
- [ ] Rate (per unit)
- [ ] Amount (Quantity × Rate)

#### Common Item Patterns
```
1. Excavation in ordinary soil                    cum    100.00    50.00    5000.00
2. Providing and laying cement concrete           cum     50.00   500.00   25000.00
3. Brick work in cement mortar                    sqm    200.00   150.00   30000.00
```

### Step 5: Verify Data
- [ ] All item numbers are sequential
- [ ] Descriptions are complete
- [ ] Units are correct
- [ ] Quantities match work order
- [ ] Rates match work order
- [ ] Amounts are calculated correctly (Qty × Rate)
- [ ] No missing items

### Step 6: Process
```bash
python process_first_bill.py OUTPUT\work_order_template.xlsx
```

## Tips for Accurate Data Entry

### 1. Item Numbers
- Keep sequential: 1, 2, 3, 4, ...
- Don't skip numbers
- Use E1, E2, E3 for extra items

### 2. Descriptions
- Copy exactly as written in work order
- Include all specifications
- Don't abbreviate unless in original
- Keep technical terms intact

### 3. Units
- Use standard abbreviations:
  - sqm (not sq.m or m²)
  - cum (not cu.m or m³)
  - rmt (not r.m or rm)
  - nos (not no. or pcs)

### 4. Numbers
- Use decimal point (.) not comma
- No currency symbols in Excel
- No thousand separators
- Example: 5000.00 (not 5,000.00 or ₹5000)

### 5. Calculations
- Amount = Quantity × Rate
- Double-check all calculations
- Use Excel formulas if needed: =C2*D2

## Troubleshooting

### Can't Read Text in Images
- Zoom in on the image
- Adjust brightness/contrast
- Try different image viewer
- If still unclear, mark as "Unclear - needs verification"

### Missing Information
- Leave blank if not visible in images
- Add note in Remarks column
- Can be filled later from physical documents

### Unclear Item Descriptions
- Type what you can read
- Add [?] for unclear parts
- Example: "Providing and [?] cement concrete"

## After Data Entry

Once you've filled the template:

1. **Save the file**
2. **Review all sheets**
3. **Run processing:**
   ```bash
   python process_first_bill.py OUTPUT\work_order_template.xlsx
   ```
4. **Check generated documents** in OUTPUT folder
5. **Verify accuracy** of generated bills

## Alternative: Install Tesseract for Automatic OCR

If you want automatic extraction:

1. **Install Tesseract OCR:**
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Install with English + Hindi language support

2. **Run OCR script:**
   ```bash
   python simple_ocr_to_excel.py "INPUT\work_order_samples\work_01_27022026"
   ```

3. **Review and correct** the auto-generated Excel file

## Need Help?

Refer to:
- `TEMPLATE_INSTRUCTIONS.txt` - Detailed instructions
- `WORK_ORDER_OCR_GUIDE.md` - Complete OCR guide
- `SESSION_SUMMARY.md` - What's been done so far
- `USER_MANUAL.md` - Full system manual

---

**Created:** March 9, 2026
**For:** Work Order Processing - work_01_27022026
**System:** BillGenerator Unified v2.0.0
