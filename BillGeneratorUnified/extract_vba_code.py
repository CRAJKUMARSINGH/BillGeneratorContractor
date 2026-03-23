#!/usr/bin/env python3
"""
Extract VBA code from Excel file
"""
try:
    import oletools.olevba as olevba
    
    file_path = 'ATTACHED_ASSETS/Notesheet/HINDI_BILL_NOTE_SHEET_2026.xlsm'
    
    print("Extracting VBA code from:", file_path)
    print("="*80)
    
    vba = olevba.VBA_Parser(file_path)
    
    if vba.detect_vba_macros():
        print("\nVBA Macros found!\n")
        
        for (filename, stream_path, vba_filename, vba_code) in vba.extract_macros():
            print(f"\n{'='*80}")
            print(f"Module: {vba_filename}")
            print(f"{'='*80}")
            print(vba_code)
            print()
    else:
        print("No VBA macros found")
    
    vba.close()
    
except ImportError:
    print("oletools not installed. Installing...")
    import subprocess
    subprocess.run(['pip', 'install', 'oletools'], check=True)
    print("\nPlease run the script again.")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
