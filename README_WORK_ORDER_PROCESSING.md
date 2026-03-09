# Work Order Processing - Quick Start

## 🎯 Your Work Order Images

**Location:** `E:\Rajkumar\BillGeneratorContractor\INPUT\work_order_samples\work_01_27022026`

**Files:** 5 JPEG images of work order documents

---

## ✅ What's Ready

1. ✅ **Excel Template Created** - `OUTPUT/work_order_template.xlsx`
2. ✅ **Instructions File** - `OUTPUT/TEMPLATE_INSTRUCTIONS.txt`
3. ✅ **Processing Scripts** - All ready to use
4. ✅ **First Bill Example** - Successfully processed

---

## 🚀 Quick Start (3 Steps)

### Step 1: Open Template & Images

```bash
# Open Excel template
start OUTPUT\work_order_template.xlsx

# Open folder with work order images
start INPUT\work_order_samples\work_01_27022026\
```

### Step 2: Fill in Data

Arrange windows side-by-side:
- **Left:** Excel template
- **Right:** Image viewer with work order images

Read from images and type into Excel:
- **Title sheet:** Project details, contractor info
- **Work Order sheet:** All items with descriptions, units, quantities, rates
- **Bill Quantity sheet:** Copy from Work Order, update quantities
- **Extra Items sheet:** Any additional items (if applicable)

**Time needed:** 30-60 minutes

### Step 3: Process

```bash
python process_first_bill.py OUTPUT\work_order_template.xlsx
```

**Output:** 4 HTML documents in OUTPUT folder
- Certificate II
- Certificate III
- Bill Scrutiny Sheet
- First Page Summary

---

## 📋 What to Extract from Images

### From Title/Header (Image 1)
- [ ] Work Name
- [ ] Agreement Number
- [ ] Contractor Name
- [ ] Work Order Number
- [ ] Work Order Date
- [ ] Department/Division

### From Item List (All Images)
For each item:
- [ ] Item Number (1, 2, 3, ...)
- [ ] Description (complete text)
- [ ] Unit (sqm, cum, kg, nos, rmt, etc.)
- [ ] Quantity
- [ ] Rate
- [ ] Amount

---

## 💡 Tips

### Units to Use
- `sqm` - Square meter (area)
- `cum` - Cubic meter (volume)
- `kg` - Kilogram (weight)
- `nos` - Numbers (count)
- `rmt` - Running meter (length)
- `mt` - Metric ton
- `ltr` - Liter

### Number Format
- Use: `5000.00` (decimal point)
- Don't use: `5,000.00` or `₹5000` (no commas or symbols)

### Item Numbers
- Sequential: 1, 2, 3, 4, ...
- Extra items: E1, E2, E3, ...

---

## 🔄 Alternative: Automatic OCR

If you want automatic extraction instead of manual entry:

### Install Tesseract OCR
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Install with English + Hindi support
3. Add to PATH

### Run OCR
```bash
python simple_ocr_to_excel.py "INPUT\work_order_samples\work_01_27022026"
```

### Review & Process
```bash
# Check the extracted data
start OUTPUT\work_order_extracted.xlsx

# Process after verification
python process_first_bill.py OUTPUT\work_order_extracted.xlsx
```

---

## 📁 All Files Created for You

| File | Purpose |
|------|---------|
| `OUTPUT/work_order_template.xlsx` | Excel template for data entry |
| `OUTPUT/TEMPLATE_INSTRUCTIONS.txt` | Detailed instructions |
| `COMPLETE_WORKFLOW_GUIDE.md` | Complete workflow documentation |
| `VIEW_WORK_ORDER_IMAGES.md` | Guide for viewing images |
| `INSTALL_TESSERACT.md` | OCR installation guide |
| `process_first_bill.py` | Main processing script |
| `simple_ocr_to_excel.py` | OCR extraction script |
| `create_work_order_template.py` | Template creator |

---

## ❓ Need Help?

### Can't read text in images?
- Zoom in on the image
- Try different image viewer
- Adjust brightness/contrast

### Missing information?
- Leave blank in Excel
- Add note in Remarks column
- Can fill later from physical documents

### Calculation errors?
- Use Excel formula: `=C2*D2` (Quantity × Rate)
- Double-check all amounts

### Processing errors?
- Check all 4 sheets exist
- Verify column names match
- Ensure no empty required fields

---

## 📞 Support

**Prepared on Initiative of:**
Mrs. Premlata Jain, AAO
PWD Udaipur

**System:** BillGenerator Unified v2.0.0

---

## ✅ Summary

**Current Status:**
- ✅ Template ready for data entry
- ✅ Work order images available
- ✅ Processing scripts working
- ✅ Example bill successfully generated

**Next Action:**
1. Open template: `start OUTPUT\work_order_template.xlsx`
2. Open images: `start INPUT\work_order_samples\work_01_27022026\`
3. Fill in data (30-60 min)
4. Process: `python process_first_bill.py OUTPUT\work_order_template.xlsx`

**Result:** Professional bill documents ready for use!

---

**Created:** March 9, 2026
**Status:** Ready to Use
