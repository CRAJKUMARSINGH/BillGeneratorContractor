# VBA Code Update Instructions for Hindi Bill Note Sheet

## File to Update
**HINDI_BILL_NOTE_SHEET_2026.xlsm**

---

## Step-by-Step Instructions

### Step 1: Open the Excel File
1. Navigate to: `C:\Users\Rajkumar\BillGeneratorUnified\ATTACHED_ASSETS\Notesheet`
2. Open: `HINDI_BILL_NOTE_SHEET_2026.xlsm`
3. Enable macros if prompted

### Step 2: Open VBA Editor
1. Press `Alt + F11` to open VBA Editor
2. Or go to: Developer Tab → Visual Basic

### Step 3: Locate or Create Module
1. In VBA Editor, look for existing modules in the left panel
2. If no module exists:
   - Right-click on "VBAProject (HINDI_BILL_NOTE_SHEET_2026.xlsm)"
   - Select: Insert → Module
3. Double-click the module to open it

### Step 4: Replace/Add the LD Calculation Code
1. Delete any existing LD calculation code
2. Copy the entire code from `LD_CALCULATION_VBA_CODE.vba`
3. Paste it into the module

### Step 5: Update the Note Sheet Formula

#### Find the LD Display Cell
Look for the cell that displays:
```
Agreement clause 2 के अनुसार liquidated damages की गणना रुपया ___ है।
```

#### Update the Formula
Replace the existing formula with:

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

#### Example with Cell References
If your cells are:
- Work Order Amount: `B16`
- Actual Progress: `B17C` (calculated from bill data)
- Start Date: `B11`
- Scheduled Completion: `B12`
- Actual Completion: `B13`

Then the formula would be:
```excel
="Agreement clause 2 के अनुसार liquidated damages की गणना " & 
FormatLDAmountHindi(CalculateLiquidatedDamages(B16, B17C, B11, B12, B13)) & 
" है। वसूली योग्य LD हेतु विनिर्णय का स्पष्ट अंकन अपेक्षित है।"
```

### Step 6: Create Named Ranges (Optional but Recommended)

For better readability, create named ranges:

1. Select cell with Work Order Amount → Name it: `WorkOrderAmount`
2. Select cell with Actual Progress → Name it: `ActualProgress`
3. Select cell with Start Date → Name it: `StartDate`
4. Select cell with Scheduled Completion → Name it: `ScheduledCompletion`
5. Select cell with Actual Completion → Name it: `ActualCompletion`

Then use:
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

### Step 7: Test the Calculation

#### Test Case 1: No Delay
- Work Order: ₹10,00,000
- Actual Progress: ₹10,00,000 (100%)
- Start: 01/01/2024
- Scheduled: 30/06/2024
- Actual: 30/06/2024
- **Expected LD**: ₹0

#### Test Case 2: 5-Day Delay, 100% Complete
- Work Order: ₹5,07,992
- Actual Progress: ₹5,07,992 (100%)
- Start: 01/10/2024
- Scheduled: 31/12/2024
- Actual: 05/01/2025
- **Expected LD**: ₹4,141

#### Test Case 3: 30-Day Delay, 70% Complete
- Work Order: ₹10,00,000
- Actual Progress: ₹7,00,000 (70%)
- Start: 01/01/2024
- Scheduled: 30/06/2024
- Actual: 30/07/2024
- **Expected LD**: ₹30,000

### Step 8: Save the File
1. Press `Ctrl + S` to save
2. Close VBA Editor
3. Test the formulas in the worksheet

---

## Formula Explanation

### PWD Quarterly Distribution Method

The LD calculation uses quarterly work distribution:

| Quarter | Work % | Penalty Rate | Period |
|---------|--------|--------------|--------|
| Q1 | 12.5% | 2.5% | 0-25% of duration |
| Q2 | 25.0% | 5.0% | 25-50% of duration |
| Q3 | 25.0% | 7.5% | 50-75% of duration |
| Q4 | 37.5% | 10.0% | 75-100% of duration |

### Two Calculation Cases

#### Case 1: Work Incomplete + Delayed
```
LD = Penalty Rate × (Required Progress - Actual Progress)
```

#### Case 2: Work 100% Complete but Delayed
```
LD = 10% × (Q4 Daily Rate × Delay Days)
```
Note: Presume entire delay occurred in Q4

---

## Troubleshooting

### Error: "Compile Error: Sub or Function not defined"
- Make sure you copied the entire VBA code
- Check that the module is saved

### Error: "Type Mismatch"
- Verify that date cells contain actual dates (not text)
- Verify that amount cells contain numbers (not text)

### LD Shows 0 When There's Delay
- Check that Actual Completion Date > Scheduled Completion Date
- Verify all cell references are correct
- Check that dates are in proper format (DD/MM/YYYY)

### LD Amount Not Displaying in Hindi
- Make sure you're using `FormatLDAmountHindi()` function
- Check that the function is in the same module

---

## Additional Features

### Add LD Breakdown Sheet (Optional)

You can create a separate sheet showing detailed LD calculation:

1. Create new sheet: "LD Calculation Details"
2. Add these formulas:

```
Total Duration: =DAYS(ScheduledCompletion, StartDate)
Elapsed Days: =DAYS(ActualCompletion, StartDate)
Delay Days: =ElapsedDays - TotalDuration

Q1 Work (12.5%): =WorkOrderAmount * 0.125
Q2 Work (25%): =WorkOrderAmount * 0.25
Q3 Work (25%): =WorkOrderAmount * 0.25
Q4 Work (37.5%): =WorkOrderAmount * 0.375

Q4 Daily Rate: =Q4Work / Q4Duration
Unexecuted Work: =RequiredProgress - ActualProgress
Penalty Rate: =10%
LD Amount: =PenaltyRate * UnexecutedWork
```

---

## Reference

- **Source**: SAMPLE_ld_COMPUTATION.pdf
- **Web Tool**: https://pwd-tools-priyanka.netlify.app/src/components/financialprogresstracker
- **Python Implementation**: core/generators/base_generator.py
- **Initiative by**: Mrs. Premlata Jain, AAO, PWD, Udaipur, Rajasthan

---

## Version History

- **v1.0** (Feb 25, 2026): Initial implementation with PWD quarterly method
- Supports both incomplete and complete-but-delayed scenarios
- Progressive penalty rates (2.5%, 5%, 7.5%, 10%)

---

## Support

For questions or issues:
1. Refer to LD_IMPLEMENTATION_COMPLETE.md
2. Check test files in OUTPUT folder
3. Run test_all_ld_scenarios.py for verification

---

**Last Updated**: February 25, 2026  
**Status**: Ready for Implementation ✅
