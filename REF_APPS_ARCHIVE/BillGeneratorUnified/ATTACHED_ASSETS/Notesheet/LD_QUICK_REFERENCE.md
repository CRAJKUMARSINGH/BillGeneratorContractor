# Liquidated Damages - Quick Reference Card

## PWD Quarterly Method | त्रैमासिक विधि

---

## Formula | सूत्र

### Case 1: Incomplete Work | अपूर्ण कार्य
```
LD = Penalty Rate × (Required Progress - Actual Progress)
LD = दंड दर × (आवश्यक प्रगति - वास्तविक प्रगति)
```

### Case 2: Complete but Delayed | पूर्ण लेकिन विलंबित
```
LD = 10% × (Q4 Daily Rate × Delay Days)
LD = 10% × (Q4 दैनिक दर × देरी के दिन)
```

---

## Quarterly Distribution | त्रैमासिक वितरण

| Quarter<br>तिमाही | Work %<br>कार्य % | Penalty Rate<br>दंड दर | Period<br>अवधि |
|---------|--------|--------------|--------|
| Q1 | 12.5% | 2.5% | 0-25% |
| Q2 | 25.0% | 5.0% | 25-50% |
| Q3 | 25.0% | 7.5% | 50-75% |
| Q4 | 37.5% | 10.0% | 75-100% |

---

## Quick Examples | त्वरित उदाहरण

### Example 1 | उदाहरण 1
- Work Order: ₹10,00,000
- Complete: 100% | पूर्ण: 100%
- Delay: 5 days | देरी: 5 दिन
- **LD: ₹4,167**

### Example 2 | उदाहरण 2
- Work Order: ₹10,00,000
- Complete: 70% | पूर्ण: 70%
- Delay: 30 days | देरी: 30 दिन
- **LD: ₹30,000**

### Example 3 | उदाहरण 3
- Work Order: ₹10,00,000
- Complete: 100% | पूर्ण: 100%
- Delay: 0 days | देरी: 0 दिन
- **LD: ₹0**

---

## VBA Function | VBA फ़ंक्शन

```vba
=CalculateLiquidatedDamages(
    WorkOrderAmount,
    ActualProgress,
    StartDate,
    ScheduledCompletion,
    ActualCompletion
)
```

---

## Note Sheet Text | नोट शीट पाठ

```
Agreement clause 2 के अनुसार liquidated damages की गणना 
रुपया [amount] है। वसूली योग्य LD हेतु विनिर्णय का 
स्पष्ट अंकन अपेक्षित है।
```

---

## Files | फ़ाइलें

### Python
- `core/generators/base_generator.py`

### VBA
- `LD_CALCULATION_VBA_CODE.vba`

### Excel
- `HINDI_BILL_NOTE_SHEET_2026.xlsm`

### Documentation
- `VBA_UPDATE_INSTRUCTIONS.md` (English)
- `VBA_UPDATE_INSTRUCTIONS_HINDI.md` (हिंदी)
- `LD_IMPLEMENTATION_COMPLETE.md` (Full Details)

---

## Key Points | मुख्य बिंदु

✅ No delay = No LD | कोई देरी नहीं = कोई LD नहीं

✅ 100% complete + delayed = Q4 method | 100% पूर्ण + विलंबित = Q4 विधि

✅ Incomplete + delayed = Quarterly method | अपूर्ण + विलंबित = त्रैमासिक विधि

✅ Progressive penalties by quarter | तिमाही के अनुसार प्रगतिशील दंड

---

## Reference | संदर्भ

**Source**: SAMPLE_ld_COMPUTATION.pdf  
**Web Tool**: pwd-tools-priyanka.netlify.app  
**Initiative**: Mrs. Premlata Jain, AAO, PWD Udaipur

---

**Version**: 1.0 | **Date**: Feb 25, 2026
