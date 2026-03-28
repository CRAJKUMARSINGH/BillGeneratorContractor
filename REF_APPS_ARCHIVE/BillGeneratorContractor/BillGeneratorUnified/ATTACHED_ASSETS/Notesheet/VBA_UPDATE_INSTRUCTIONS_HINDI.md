# हिंदी बिल नोट शीट के लिए VBA कोड अपडेट निर्देश

## अपडेट करने के लिए फ़ाइल
**HINDI_BILL_NOTE_SHEET_2026.xlsm**

---

## चरण-दर-चरण निर्देश

### चरण 1: Excel फ़ाइल खोलें
1. यहाँ जाएं: `C:\Users\Rajkumar\BillGeneratorUnified\ATTACHED_ASSETS\Notesheet`
2. खोलें: `HINDI_BILL_NOTE_SHEET_2026.xlsm`
3. यदि संकेत मिले तो मैक्रोज़ सक्षम करें

### चरण 2: VBA Editor खोलें
1. VBA Editor खोलने के लिए `Alt + F11` दबाएं
2. या जाएं: Developer Tab → Visual Basic

### चरण 3: Module खोजें या बनाएं
1. VBA Editor में, बाएं पैनल में मौजूदा modules देखें
2. यदि कोई module नहीं है:
   - "VBAProject (HINDI_BILL_NOTE_SHEET_2026.xlsm)" पर राइट-क्लिक करें
   - चुनें: Insert → Module
3. Module को खोलने के लिए डबल-क्लिक करें

### चरण 4: LD Calculation Code बदलें/जोड़ें
1. किसी भी मौजूदा LD calculation code को हटा दें
2. `LD_CALCULATION_VBA_CODE.vba` से पूरा कोड कॉपी करें
3. इसे module में पेस्ट करें

### चरण 5: Note Sheet Formula अपडेट करें

#### LD Display Cell खोजें
वह cell खोजें जो यह प्रदर्शित करता है:
```
Agreement clause 2 के अनुसार liquidated damages की गणना रुपया ___ है।
```

#### Formula अपडेट करें
मौजूदा formula को इससे बदलें:

```excel
="Agreement clause 2 के अनुसार liquidated damages की गणना " & 
FormatLDAmountHindi(CalculateLiquidatedDamages(
    [Work_Order_Amount_Cell],
    [Actual_Progress_Cell],
    [Start_Date_Cell],
    [Scheduled_Completion_Cell],
    [Actual_Completion_Cell]
)) & " है। वसूली योग्य LD हेतु विनिर्णय का स्पष्ट अंकन अपेक्षित है।"
```

#### Cell References के साथ उदाहरण
यदि आपकी cells हैं:
- Work Order Amount: `B16`
- Actual Progress: `B17C` (bill data से गणना की गई)
- Start Date: `B11`
- Scheduled Completion: `B12`
- Actual Completion: `B13`

तो formula होगा:
```excel
="Agreement clause 2 के अनुसार liquidated damages की गणना " & 
FormatLDAmountHindi(CalculateLiquidatedDamages(B16, B17C, B11, B12, B13)) & 
" है। वसूली योग्य LD हेतु विनिर्णय का स्पष्ट अंकन अपेक्षित है।"
```

### चरण 6: Named Ranges बनाएं (वैकल्पिक लेकिन अनुशंसित)

बेहतर पठनीयता के लिए, named ranges बनाएं:

1. Work Order Amount वाली cell चुनें → नाम दें: `WorkOrderAmount`
2. Actual Progress वाली cell चुनें → नाम दें: `ActualProgress`
3. Start Date वाली cell चुनें → नाम दें: `StartDate`
4. Scheduled Completion वाली cell चुनें → नाम दें: `ScheduledCompletion`
5. Actual Completion वाली cell चुनें → नाम दें: `ActualCompletion`

फिर उपयोग करें:
```excel
="Agreement clause 2 के अनुसार liquidated damages की गणना " & 
FormatLDAmountHindi(CalculateLiquidatedDamages(
    WorkOrderAmount, 
    ActualProgress, 
    StartDate, 
    ScheduledCompletion, 
    ActualCompletion
)) & " है। वसूली योग्य LD हेतु विनिर्णय का स्पष्ट अंकन अपेक्षित है।"
```

### चरण 7: Calculation का परीक्षण करें

#### परीक्षण केस 1: कोई देरी नहीं
- Work Order: ₹10,00,000
- Actual Progress: ₹10,00,000 (100%)
- प्रारंभ: 01/01/2024
- निर्धारित: 30/06/2024
- वास्तविक: 30/06/2024
- **अपेक्षित LD**: ₹0

#### परीक्षण केस 2: 5-दिन की देरी, 100% पूर्ण
- Work Order: ₹5,07,992
- Actual Progress: ₹5,07,992 (100%)
- प्रारंभ: 01/10/2024
- निर्धारित: 31/12/2024
- वास्तविक: 05/01/2025
- **अपेक्षित LD**: ₹4,141

#### परीक्षण केस 3: 30-दिन की देरी, 70% पूर्ण
- Work Order: ₹10,00,000
- Actual Progress: ₹7,00,000 (70%)
- प्रारंभ: 01/01/2024
- निर्धारित: 30/06/2024
- वास्तविक: 30/07/2024
- **अपेक्षित LD**: ₹30,000

### चरण 8: फ़ाइल सहेजें
1. सहेजने के लिए `Ctrl + S` दबाएं
2. VBA Editor बंद करें
3. worksheet में formulas का परीक्षण करें

---

## Formula की व्याख्या

### PWD त्रैमासिक वितरण विधि

LD गणना त्रैमासिक कार्य वितरण का उपयोग करती है:

| तिमाही | कार्य % | दंड दर | अवधि |
|---------|--------|---------|------|
| Q1 | 12.5% | 2.5% | अवधि का 0-25% |
| Q2 | 25.0% | 5.0% | अवधि का 25-50% |
| Q3 | 25.0% | 7.5% | अवधि का 50-75% |
| Q4 | 37.5% | 10.0% | अवधि का 75-100% |

### दो गणना केस

#### केस 1: कार्य अपूर्ण + विलंबित
```
LD = दंड दर × (आवश्यक प्रगति - वास्तविक प्रगति)
```

#### केस 2: कार्य 100% पूर्ण लेकिन विलंबित
```
LD = 10% × (Q4 दैनिक दर × देरी के दिन)
```
नोट: पूरी देरी Q4 में हुई मानी जाती है

---

## समस्या निवारण

### त्रुटि: "Compile Error: Sub or Function not defined"
- सुनिश्चित करें कि आपने पूरा VBA code कॉपी किया है
- जांचें कि module सहेजा गया है

### त्रुटि: "Type Mismatch"
- सत्यापित करें कि date cells में वास्तविक dates हैं (text नहीं)
- सत्यापित करें कि amount cells में numbers हैं (text नहीं)

### देरी होने पर भी LD 0 दिखाता है
- जांचें कि Actual Completion Date > Scheduled Completion Date
- सत्यापित करें कि सभी cell references सही हैं
- जांचें कि dates उचित format में हैं (DD/MM/YYYY)

### LD Amount हिंदी में प्रदर्शित नहीं हो रहा
- सुनिश्चित करें कि आप `FormatLDAmountHindi()` function का उपयोग कर रहे हैं
- जांचें कि function उसी module में है

---

## अतिरिक्त सुविधाएं

### LD Breakdown Sheet जोड़ें (वैकल्पिक)

आप विस्तृत LD गणना दिखाने वाली अलग sheet बना सकते हैं:

1. नई sheet बनाएं: "LD Calculation Details"
2. ये formulas जोड़ें:

```
कुल अवधि: =DAYS(ScheduledCompletion, StartDate)
बीते दिन: =DAYS(ActualCompletion, StartDate)
देरी के दिन: =ElapsedDays - TotalDuration

Q1 कार्य (12.5%): =WorkOrderAmount * 0.125
Q2 कार्य (25%): =WorkOrderAmount * 0.25
Q3 कार्य (25%): =WorkOrderAmount * 0.25
Q4 कार्य (37.5%): =WorkOrderAmount * 0.375

Q4 दैनिक दर: =Q4Work / Q4Duration
अनुपादित कार्य: =RequiredProgress - ActualProgress
दंड दर: =10%
LD राशि: =PenaltyRate * UnexecutedWork
```

---

## संदर्भ

- **स्रोत**: SAMPLE_ld_COMPUTATION.pdf
- **वेब टूल**: https://pwd-tools-priyanka.netlify.app/src/components/financialprogresstracker
- **Python Implementation**: core/generators/base_generator.py
- **पहल**: श्रीमती प्रेमलता जैन, AAO, PWD, उदयपुर, राजस्थान

---

## संस्करण इतिहास

- **v1.0** (25 फरवरी, 2026): PWD त्रैमासिक विधि के साथ प्रारंभिक कार्यान्वयन
- अपूर्ण और पूर्ण-लेकिन-विलंबित दोनों परिदृश्यों का समर्थन करता है
- प्रगतिशील दंड दरें (2.5%, 5%, 7.5%, 10%)

---

## सहायता

प्रश्नों या समस्याओं के लिए:
1. LD_IMPLEMENTATION_COMPLETE.md देखें
2. OUTPUT folder में test files जांचें
3. सत्यापन के लिए test_all_ld_scenarios.py चलाएं

---

**अंतिम अपडेट**: 25 फरवरी, 2026  
**स्थिति**: कार्यान्वयन के लिए तैयार ✅
