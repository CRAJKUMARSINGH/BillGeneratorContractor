# Quick Start: Complete Bill Generation

## 3 Simple Steps

### Step 1: Prepare Input
```
INPUT_WORK_ORDER_IMAGES_TEXT/
├── *.jpg (your work order images)
└── qty.txt (quantities)
```

### Step 2: Run Script
```bash
python generate_complete_bill_docs.py
```

### Step 3: Get Output
```
OUTPUT/
├── BILL_INPUT_COMPLETE.xlsx
├── FIRST_PAGE.pdf
├── DEVIATION.pdf
├── MATERIAL_CERT.pdf
├── LABOUR_CERT.pdf
├── MEASUREMENT_CERT.pdf
└── ABSTRACT.pdf
```

## That's It! 🎉

The system automatically:
- ✅ Extracts data from images (AI-powered)
- ✅ Creates Excel with all data
- ✅ Generates all bill PDFs

## Need Help?

Run the test first:
```bash
python test_complete_bill_generation.py
```

Check the log:
```
OUTPUT/complete_bill_generation_log.txt
```

Read the full guide:
```
COMPLETE_BILL_GENERATION_GUIDE.md
```

---

**From images to complete bill documentation in under 60 seconds!** ⚡
