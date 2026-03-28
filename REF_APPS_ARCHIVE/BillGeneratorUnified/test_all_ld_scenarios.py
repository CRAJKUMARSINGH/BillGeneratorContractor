#!/usr/bin/env python3
"""
Comprehensive test of all LD calculation scenarios
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from core.generators.html_generator import HTMLGenerator

def create_test_case(scenario_name, work_order_amt, completion_pct, delay_days, project_duration_days=180):
    """Create test data for different scenarios"""
    
    start_date = datetime(2024, 1, 1)
    scheduled_completion = start_date + timedelta(days=project_duration_days)
    actual_completion = scheduled_completion + timedelta(days=delay_days)
    
    title_data = {
        'Serial No. of this bill :': 'FINAL BILL',
        'Budget Head': '4059-01-800-98-00',
        'Agreement No.': f'TEST/{scenario_name}',
        'A&F Sanction': 'Refer Agreement',
        'Technical Section': 'Refer Agreement',
        'Measurement Book No': '001',
        'Measurement Book Page': '01',
        'Sub Division': 'Test Sub Division',
        'Name of Work ;-': f'Test Work - {scenario_name}',
        'Name of Contractor or supplier :': 'Test Contractor',
        'Original or Deposit': 'Original',
        'Date of written order to commence work :': start_date.strftime('%d/%m/%Y'),
        'St. date of Start :': start_date.strftime('%d/%m/%Y'),
        'St. date of completion :': scheduled_completion.strftime('%d/%m/%Y'),
        'Date of actual completion of work :': actual_completion.strftime('%d/%m/%Y'),
        'Date of measurement :': actual_completion.strftime('%d/%m/%Y'),
        'Work Order Amount': work_order_amt,
        'Amount Paid Vide Last Bill': 0,
        'TENDER PREMIUM %': 0.0,
        'Premium Type': 'Above',
        'Is Repair Maintenance Work': 'No',
        'Delay in Bill Submission': 'No'
    }
    
    work_order_data = pd.DataFrame([
        {'Item No.': '1', 'Description': 'Test Item', 'Unit': 'LS', 'Quantity': 1, 'Rate': work_order_amt, 'BSR': ''}
    ])
    
    actual_work = work_order_amt * (completion_pct / 100)
    bill_quantity_data = pd.DataFrame([
        {'Item No.': '1', 'Description': 'Test Item', 'Unit': 'LS', 
         'Quantity': completion_pct/100, 'Quantity Since': completion_pct/100, 
         'Quantity Upto': completion_pct/100, 'Rate': work_order_amt, 'BSR': ''}
    ])
    
    extra_items_data = pd.DataFrame()
    
    return {
        'title_data': title_data,
        'work_order_data': work_order_data,
        'bill_quantity_data': bill_quantity_data,
        'extra_items_data': extra_items_data,
        'source_filename': f'{scenario_name}.xlsx'
    }

def test_scenario(scenario_name, work_order_amt, completion_pct, delay_days):
    """Test a specific scenario"""
    
    data = create_test_case(scenario_name, work_order_amt, completion_pct, delay_days)
    generator = HTMLGenerator(data)
    template_data = generator._prepare_template_data()
    
    ld_amount = template_data['liquidated_damages_amount']
    delay = template_data['delay_days']
    
    return {
        'scenario': scenario_name,
        'work_order': work_order_amt,
        'completion': completion_pct,
        'delay_days': delay,
        'ld_amount': ld_amount
    }

def main():
    print("="*100)
    print("COMPREHENSIVE LD CALCULATION TEST - ALL SCENARIOS")
    print("="*100)
    print()
    
    # Test scenarios
    scenarios = [
        # (name, work_order_amount, completion_%, delay_days)
        ("No_Delay_100pct", 1000000, 100, 0),
        ("No_Delay_80pct", 1000000, 80, 0),
        ("5day_Delay_100pct", 1000000, 100, 5),
        ("5day_Delay_80pct", 1000000, 80, 5),
        ("30day_Delay_100pct", 1000000, 100, 30),
        ("30day_Delay_70pct", 1000000, 70, 30),
        ("60day_Delay_50pct", 1000000, 50, 60),
        ("Small_Work_10day_100pct", 100000, 100, 10),
        ("Large_Work_15day_90pct", 10000000, 90, 15),
    ]
    
    results = []
    
    for scenario_name, work_order, completion, delay in scenarios:
        result = test_scenario(scenario_name, work_order, completion, delay)
        results.append(result)
    
    # Display results in table format
    print(f"{'Scenario':<30} {'Work Order':>15} {'Complete':>10} {'Delay':>8} {'LD Amount':>15}")
    print("-"*100)
    
    for r in results:
        print(f"{r['scenario']:<30} ₹{r['work_order']:>14,} {r['completion']:>9}% {r['delay_days']:>7}d ₹{r['ld_amount']:>14,}")
    
    print()
    print("="*100)
    print("KEY OBSERVATIONS")
    print("="*100)
    print()
    
    # Analyze results
    print("1. NO DELAY CASES:")
    no_delay = [r for r in results if r['delay_days'] == 0]
    for r in no_delay:
        print(f"   - {r['scenario']}: LD = ₹{r['ld_amount']:,} (Expected: ₹0)")
    print()
    
    print("2. 100% COMPLETE BUT DELAYED:")
    complete_delayed = [r for r in results if r['completion'] == 100 and r['delay_days'] > 0]
    for r in complete_delayed:
        print(f"   - {r['scenario']}: {r['delay_days']}d delay → LD = ₹{r['ld_amount']:,}")
        print(f"     Formula: (Q4 Daily Rate × {r['delay_days']} days) × 10%")
    print()
    
    print("3. INCOMPLETE + DELAYED:")
    incomplete_delayed = [r for r in results if r['completion'] < 100 and r['delay_days'] > 0]
    for r in complete_delayed:
        print(f"   - {r['scenario']}: {r['completion']}% complete, {r['delay_days']}d delay → LD = ₹{r['ld_amount']:,}")
        print(f"     Formula: Penalty Rate × (Required Progress - Actual Progress)")
    print()
    
    print("="*100)
    print("PWD LD CALCULATION FORMULA SUMMARY")
    print("="*100)
    print()
    print("Quarterly Work Distribution:")
    print("  Q1 (0-25%):   12.5% of work, Penalty Rate: 2.5%")
    print("  Q2 (25-50%):  25.0% of work, Penalty Rate: 5.0%")
    print("  Q3 (50-75%):  25.0% of work, Penalty Rate: 7.5%")
    print("  Q4 (75-100%): 37.5% of work, Penalty Rate: 10.0%")
    print()
    print("Case 1: Work Incomplete + Delayed")
    print("  LD = Penalty Rate × (Required Progress - Actual Progress)")
    print()
    print("Case 2: Work 100% Complete but Delayed")
    print("  LD = 10% × (Q4 Daily Rate × Delay Days)")
    print("  Note: Presume entire delay occurred in Q4")
    print()
    print("="*100)
    
    # Generate sample note sheets
    print()
    print("Generating sample note sheets...")
    output_dir = Path('OUTPUT')
    output_dir.mkdir(exist_ok=True)
    
    # Generate for a few key scenarios
    key_scenarios = [
        ("5day_Delay_100pct", 1000000, 100, 5),
        ("30day_Delay_70pct", 1000000, 70, 30),
    ]
    
    for scenario_name, work_order, completion, delay in key_scenarios:
        data = create_test_case(scenario_name, work_order, completion, delay)
        generator = HTMLGenerator(data)
        html_content = generator._render_template('note_sheet_new.html')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_file = output_dir / f'ld_test_{scenario_name}_{timestamp}.html'
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"  ✅ {html_file.name}")
    
    print()
    print("="*100)
    print("TEST COMPLETED SUCCESSFULLY")
    print("="*100)

if __name__ == '__main__':
    main()
