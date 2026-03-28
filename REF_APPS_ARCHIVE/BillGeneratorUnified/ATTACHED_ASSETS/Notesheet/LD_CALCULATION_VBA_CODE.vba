' ============================================================================
' PWD LIQUIDATED DAMAGES CALCULATION - VBA CODE
' Based on PWD Quarterly Distribution Method
' Updated: February 25, 2026
' ============================================================================

Function CalculateLiquidatedDamages(WorkOrderAmount As Double, _
                                    ActualProgress As Double, _
                                    StartDate As Date, _
                                    ScheduledCompletionDate As Date, _
                                    ActualCompletionDate As Date) As Double
    
    ' PWD Quarterly LD Calculation Formula
    ' LD = Penalty Rate × Unexecuted Work
    ' Where Unexecuted Work is calculated based on quarterly distribution
    
    Dim TotalDuration As Long
    Dim ElapsedDays As Long
    Dim DelayDays As Long
    
    ' Quarterly distribution percentages
    Dim Q1_Percent As Double: Q1_Percent = 0.125  ' 12.5%
    Dim Q2_Percent As Double: Q2_Percent = 0.25   ' 25%
    Dim Q3_Percent As Double: Q3_Percent = 0.25   ' 25%
    Dim Q4_Percent As Double: Q4_Percent = 0.375  ' 37.5%
    
    ' Penalty rates by quarter
    Dim Q1_PenaltyRate As Double: Q1_PenaltyRate = 0.025  ' 2.5%
    Dim Q2_PenaltyRate As Double: Q2_PenaltyRate = 0.05   ' 5%
    Dim Q3_PenaltyRate As Double: Q3_PenaltyRate = 0.075  ' 7.5%
    Dim Q4_PenaltyRate As Double: Q4_PenaltyRate = 0.1    ' 10%
    
    ' Calculate durations
    TotalDuration = DateDiff("d", StartDate, ScheduledCompletionDate)
    ElapsedDays = DateDiff("d", StartDate, ActualCompletionDate)
    DelayDays = ElapsedDays - TotalDuration
    
    ' If no delay, return 0
    If DelayDays <= 0 Then
        CalculateLiquidatedDamages = 0
        Exit Function
    End If
    
    ' Calculate quarter boundaries
    Dim Q1_End As Long: Q1_End = Int(TotalDuration * 0.25)
    Dim Q2_End As Long: Q2_End = Int(TotalDuration * 0.5)
    Dim Q3_End As Long: Q3_End = Int(TotalDuration * 0.75)
    Dim Q4_End As Long: Q4_End = TotalDuration
    
    ' Calculate quarter lengths
    Dim Q1_Length As Long: Q1_Length = Q1_End
    Dim Q2_Length As Long: Q2_Length = Q2_End - Q1_End
    Dim Q3_Length As Long: Q3_Length = Q3_End - Q2_End
    Dim Q4_Length As Long: Q4_Length = Q4_End - Q3_End
    
    ' Calculate work distribution
    Dim Q1_Work As Double: Q1_Work = WorkOrderAmount * Q1_Percent
    Dim Q2_Work As Double: Q2_Work = WorkOrderAmount * Q2_Percent
    Dim Q3_Work As Double: Q3_Work = WorkOrderAmount * Q3_Percent
    Dim Q4_Work As Double: Q4_Work = WorkOrderAmount * Q4_Percent
    
    ' Calculate daily progress rates
    Dim Q1_Daily As Double: Q1_Daily = Q1_Work / Q1_Length
    Dim Q2_Daily As Double: Q2_Daily = Q2_Work / Q2_Length
    Dim Q3_Daily As Double: Q3_Daily = Q3_Work / Q3_Length
    Dim Q4_Daily As Double: Q4_Daily = Q4_Work / Q4_Length
    
    ' Calculate required progress based on elapsed days
    Dim RequiredProgress As Double
    Dim PenaltyRate As Double
    Dim CurrentQuarter As String
    
    If ElapsedDays <= Q1_End Then
        ' In Q1
        RequiredProgress = ElapsedDays * Q1_Daily
        PenaltyRate = Q1_PenaltyRate
        CurrentQuarter = "Q1"
    ElseIf ElapsedDays <= Q2_End Then
        ' In Q2
        Dim DaysInQ2 As Long: DaysInQ2 = ElapsedDays - Q1_End
        RequiredProgress = Q1_Work + (DaysInQ2 * Q2_Daily)
        PenaltyRate = Q2_PenaltyRate
        CurrentQuarter = "Q2"
    ElseIf ElapsedDays <= Q3_End Then
        ' In Q3
        Dim DaysInQ3 As Long: DaysInQ3 = ElapsedDays - Q2_End
        RequiredProgress = Q1_Work + Q2_Work + (DaysInQ3 * Q3_Daily)
        PenaltyRate = Q3_PenaltyRate
        CurrentQuarter = "Q3"
    Else
        ' In Q4 or beyond
        Dim DaysInQ4 As Long
        If ElapsedDays - Q3_End > Q4_Length Then
            DaysInQ4 = Q4_Length
        Else
            DaysInQ4 = ElapsedDays - Q3_End
        End If
        RequiredProgress = Q1_Work + Q2_Work + Q3_Work + (DaysInQ4 * Q4_Daily)
        PenaltyRate = Q4_PenaltyRate
        CurrentQuarter = "Q4"
    End If
    
    ' Calculate unexecuted work
    Dim UnexecutedWork As Double
    UnexecutedWork = RequiredProgress - ActualProgress
    
    ' Special case: If work is 100% complete but delayed
    ' Presume entire delay occurred in Q4 (final quarter)
    ' LD = (Q4 Daily Rate × Delay Days) × Q4 Penalty Rate (10%)
    If UnexecutedWork <= 0 And ElapsedDays > TotalDuration Then
        ' Work is complete but delayed beyond scheduled completion
        Dim DelayBeyondCompletion As Long
        DelayBeyondCompletion = ElapsedDays - TotalDuration
        
        ' Use Q4 daily rate and Q4 penalty rate (presume delay in Q4)
        UnexecutedWork = Q4_Daily * DelayBeyondCompletion
        PenaltyRate = Q4_PenaltyRate  ' 10%
    ElseIf UnexecutedWork <= 0 Then
        ' Work complete and on time - no LD
        CalculateLiquidatedDamages = 0
        Exit Function
    End If
    
    ' Calculate liquidated damages
    Dim LD_Amount As Double
    LD_Amount = PenaltyRate * UnexecutedWork
    
    ' Return rounded amount
    CalculateLiquidatedDamages = Application.WorksheetFunction.Round(LD_Amount, 0)
    
End Function

' ============================================================================
' HELPER FUNCTION: Format LD Amount in Hindi
' ============================================================================
Function FormatLDAmountHindi(LD_Amount As Double) As String
    ' Format the LD amount with Indian numbering system
    Dim FormattedAmount As String
    
    If LD_Amount = 0 Then
        FormatLDAmountHindi = "शून्य"
    Else
        ' Format with comma separators (Indian style)
        FormattedAmount = Format(LD_Amount, "#,##0")
        FormatLDAmountHindi = "रुपया " & FormattedAmount
    End If
End Function

' ============================================================================
' EXAMPLE USAGE IN WORKSHEET
' ============================================================================
' In your Excel sheet, you can use this formula:
' =CalculateLiquidatedDamages(WorkOrderAmount, ActualProgress, StartDate, ScheduledDate, ActualDate)
'
' For the Hindi note sheet text:
' ="Agreement clause 2 के अनुसार liquidated damages की गणना " & FormatLDAmountHindi(LD_Amount) & " है। वसूली योग्य LD हेतु विनिर्णय का स्पष्ट अंकन अपेक्षित है।"
' ============================================================================

' ============================================================================
' CALCULATION EXAMPLE
' ============================================================================
' Work Order Amount: ₹10,00,000
' Actual Progress: ₹2,64,600 (26.46% complete)
' Start Date: 01/01/2024
' Scheduled Completion: 30/06/2024 (181 days)
' Actual Completion: 30/07/2024 (211 days - 30 days delay)
'
' Result:
' - Total Duration: 181 days
' - Elapsed Days: 211 days
' - Current Quarter: Q4
' - Q4 Work (37.5%): ₹3,75,000
' - Q4 Daily Rate: ₹8,152/day
' - Required Progress: ₹10,00,000
' - Actual Progress: ₹2,64,600
' - Unexecuted Work: ₹7,35,400
' - Q4 Penalty Rate: 10%
' - LD = ₹7,35,400 × 10% = ₹73,540
' ============================================================================

' ============================================================================
' QUARTERLY DISTRIBUTION REFERENCE
' ============================================================================
' Quarter | Work % | Penalty Rate | Days
' --------|--------|--------------|------
' Q1      | 12.5%  | 2.5%         | 0-25% of duration
' Q2      | 25.0%  | 5.0%         | 25-50% of duration
' Q3      | 25.0%  | 7.5%         | 50-75% of duration
' Q4      | 37.5%  | 10.0%        | 75-100% of duration
' ============================================================================

' ============================================================================
' SPECIAL CASES
' ============================================================================
' 1. Work Incomplete + Delayed:
'    - Calculate required progress based on elapsed time
'    - LD = Penalty Rate × (Required Progress - Actual Progress)
'
' 2. Work 100% Complete but Delayed:
'    - Presume entire delay occurred in Q4
'    - LD = 10% × (Q4 Daily Rate × Delay Days)
' ============================================================================
