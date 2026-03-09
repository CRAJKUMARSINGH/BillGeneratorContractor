# Image-by-Image Data Entry Guide

## 📂 Your Files

**Excel File:** `OUTPUT/work_order_from_images.xlsx` ✅ OPENED
**Images Folder:** `INPUT/work_order_samples/work_01_27022026/` ✅ OPENED

**Structure:** Matches TEST_INPUT_FILES exactly ✅

---

## 📸 What to Extract from Each Image

### Image 1: WhatsApp Image 2026-02-25 at 1.13.49 PM.jpeg

**Look for (Title Sheet - Column B):**
- [ ] **Work Name** - Project/work description
- [ ] **Contractor Name** - Name of contractor
- [ ] **Agreement Number** - Agreement reference
- [ ] **Work Order Number** - WO number and date
- [ ] **Work Order Amount** - Total sanctioned amount
- [ ] **Department/Division** - PWD division details
- [ ] **Dates** - Commencement, start, completion dates

**Look for (Work Order Sheet):**
- [ ] **First few items** - Item numbers, descriptions, units

---

### Image 2: WhatsApp Image 2026-02-25 at 1.14.08 PM.jpeg

**Look for (Work Order Sheet):**
- [ ] **Continuation of items** - More item descriptions
- [ ] **Quantities** - Quantity values for items
- [ ] **Units** - sqm, cum, kg, nos, rmt, etc.

---

### Image 3: WhatsApp Image 2026-02-25 at 1.14.51 PM.jpeg

**Look for (Work Order Sheet):**
- [ ] **Middle section items** - More work items
- [ ] **Rates** - Rate per unit for each item
- [ ] **BSR Codes** - BSR reference codes (if visible)

---

### Image 4: WhatsApp Image 2026-02-25 at 1.15.04 PM.jpeg

**Look for (Work Order Sheet):**
- [ ] **More items** - Additional work items
- [ ] **Amounts** - Calculated amounts (Qty × Rate)
- [ ] **Sub-items** - Any sub-categories

---

### Image 5: WhatsApp Image 2026-02-25 at 1.15.19 PM.jpeg

**Look for:**
- [ ] **Final items** - Last few work items
- [ ] **Total Amount** - Grand total
- [ ] **Signatures** - For reference
- [ ] **Additional notes** - Any special conditions

---

## 📋 Excel Sheet Structure

### Sheet 1: Title (Column A = Labels, Column B = Your Data)

```
Row 1:  Header (already filled)
Row 2:  Bill Number → [Enter from image]
Row 3:  Running or Final → [Keep "Final" or change]
Row 4:  Voucher No. → [Enter if available]
Row 5:  Contractor Name → [Enter from image]
Row 6:  Work Name → [Enter from image]
Row 7:  Bill Serial No. → [e.g., "First & Final Bill"]
Row 8:  Last Bill → [Keep "Not Applicable" for first bill]
Row 9:  Work Order Reference → [Enter WO number and date]
Row 10: Agreement No. → [Enter from image]
Row 11: Work Order Amount → [Enter total amount]
Row 12: Commencement Date → [Format: 2025-01-09]
Row 13: Start Date → [Format: 2025-01-18]
Row 14: Completion Date → [Format: 2025-04-17]
Row 15: Actual Completion → [Format: 2025-06-28]
Row 16: Measurement Date → [Format: 2025-03-03]
Row 17: Tender Premium % → [e.g., 11.22]
Row 18: Above/Below → [Keep "Above" or change to "Below"]
Row 19: Last Bill Amount → [Keep 0 for first bill]
```

---

### Sheet 2: Work Order (7 Columns)

| Column | Header | What to Enter | Example |
|--------|--------|---------------|---------|
| A | Item | Item number | 1.0, 2.0, 3.0 |
| B | Description | Full item description | "Excavation in ordinary soil" |
| C | Unit | Unit of measurement | sqm, cum, kg, nos, rmt |
| D | Quantity | Quantity from work order | 100.00 |
| E | Rate | Rate per unit | 50.00 |
| F | Amount | Quantity × Rate | 5000.00 |
| G | BSR | BSR code (if available) | 1.5.1 |

**Important:**
- Main items: Use numbers like 1.0, 2.0, 3.0
- Sub-items: Leave Column A empty, indent description
- Add rows as needed (right-click → Insert)
- Delete sample rows you don't need

---

### Sheet 3: Bill Quantity (Same as Work Order)

**Steps:**
1. Copy all items from Work Order sheet
2. Update Column D (Quantity) with actual work done
3. Keep rates same
4. Recalculate Column F (Amount)

---

### Sheet 4: Extra Items (8 Columns)

Only fill if you have extra items NOT in original work order:

| Column | Header | What to Enter |
|--------|--------|---------------|
| A | Item | E1, E2, E3, ... |
| B | Description | Extra item description |
| C | Unit | sqm, cum, etc. |
| D | Quantity | Quantity |
| E | Rate | Rate per unit |
| F | Amount | Quantity × Rate |
| G | Deviation % | Percentage deviation |
| H | BSR | BSR code |

---

## 🎯 Data Entry Workflow

### Step 1: Title Sheet (10 minutes)
1. Look at Image 1
2. Fill Column B (rows 2-19) with data from image
3. Use format YYYY-MM-DD for dates

### Step 2: Work Order Sheet (30-40 minutes)
1. Look at ALL images
2. For each item in work order:
   - Enter item number in Column A
   - Copy description exactly in Column B
   - Enter unit in Column C
   - Enter quantity in Column D
   - Enter rate in Column E
   - Calculate amount in Column F (or use formula =D2*E2)
   - Enter BSR code in Column G (if visible)
3. Add more rows as needed
4. Delete unused sample rows

### Step 3: Bill Quantity Sheet (5 minutes)
1. Copy all from Work Order sheet
2. Update quantities if different

### Step 4: Extra Items Sheet (5 minutes)
1. Only if you have extra items
2. Otherwise, leave as is or delete sample rows

### Step 5: Save & Process (2 minutes)
1. Save Excel file (Ctrl+S)
2. Run: `python process_first_bill.py OUTPUT\work_order_from_images.xlsx`

---

## 💡 Quick Tips

### Reading Images
- **Zoom in** if text is small
- **Adjust brightness** if image is dark
- **Use arrow keys** to navigate between images
- **Take notes** if something is unclear

### Entering Data
- **Copy exactly** - Don't abbreviate descriptions
- **Double-check numbers** - Verify all calculations
- **Use formulas** - In Column F: =D2*E2 (Quantity × Rate)
- **Save often** - Press Ctrl+S frequently
- **Keep backup** - Copy file before processing

### Common Patterns

**Item with sub-items:**
```
1.0  | Main item description        | sqm | 100 | 50 | 5000 | 1.5
     | Sub-item 1 (up to 3 mtr)     | sqm |  40 | 45 | 1800 | 1.5.1
     | Sub-item 2 (up to 6 mtr)     | sqm |  60 | 55 | 3300 | 1.5.2
```

**Simple item:**
```
2.0  | Providing and fixing switch  | nos |  10 | 50 |  500 | 7.1
```

---

## ✅ Verification Checklist

Before processing, verify:

### Title Sheet
- [ ] All required fields filled (rows 2, 5, 6, 9, 10, 11)
- [ ] Dates in correct format (YYYY-MM-DD)
- [ ] Numbers without commas or currency symbols
- [ ] Tender premium is a number (e.g., 11.22)

### Work Order Sheet
- [ ] All items from images entered
- [ ] Item numbers sequential (1.0, 2.0, 3.0, ...)
- [ ] Descriptions complete and accurate
- [ ] Units correct (sqm, cum, kg, nos, rmt, etc.)
- [ ] All quantities entered
- [ ] All rates entered
- [ ] All amounts calculated (Qty × Rate)
- [ ] No empty rows in middle of data

### Bill Quantity Sheet
- [ ] Copied from Work Order
- [ ] Quantities updated if needed

### Extra Items Sheet
- [ ] Filled only if extra items exist
- [ ] Item numbers start with E (E1, E2, E3)

---

## 🚀 After Filling Data

### Process the File
```bash
python process_first_bill.py OUTPUT\work_order_from_images.xlsx
```

### Expected Output
- Certificate II (HTML)
- Certificate III (HTML)
- Bill Scrutiny Sheet (HTML)
- First Page Summary (HTML)

### Convert to PDF
1. Open HTML file in browser
2. Press Ctrl+P (Print)
3. Select "Save as PDF"
4. Save to OUTPUT folder

---

## ❓ Troubleshooting

### Can't read text in image?
- Zoom in more
- Try different image viewer
- Adjust screen brightness
- Mark as "[Unclear]" and verify later

### Don't know which unit to use?
- Look at work order carefully
- Common: sqm (area), cum (volume), nos (count)
- Ask if unsure

### Calculation doesn't match?
- Verify Quantity × Rate = Amount
- Check for decimal points
- Use Excel formula: =D2*E2

### Too many items?
- Add more rows (right-click → Insert)
- Keep going, no limit
- Save frequently

---

## 📞 Need Help?

**Files to refer:**
- `FILLING_INSTRUCTIONS.txt` - Detailed instructions
- `COMPLETE_WORKFLOW_GUIDE.md` - Complete workflow
- `TEST_INPUT_FILES/FirstFINALnoExtra.xlsx` - Example file

**Compare your file with:**
```bash
# Open example file
start TEST_INPUT_FILES\FirstFINALnoExtra.xlsx
```

---

**Created:** March 9, 2026
**Status:** Ready for Data Entry
**Estimated Time:** 45-60 minutes
**Result:** Professional bill documents
