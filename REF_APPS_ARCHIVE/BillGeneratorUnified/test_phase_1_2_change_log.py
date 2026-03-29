#!/usr/bin/env python3
"""
PHASE 1.2 TEST: Change Log / Audit Trail
Tests that all modifications are tracked with timestamp, old/new values, and reason
"""
import sys
from pathlib import Path
import pandas as pd
import io
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Mock Streamlit session_state for testing
class MockSessionState:
    def __init__(self):
        self.change_log = []
    
    def __contains__(self, key):
        return hasattr(self, key)
    
    def get(self, key, default=None):
        return getattr(self, key, default)

# Import ChangeLogger after mocking
import streamlit as st
st.session_state = MockSessionState()

from core.ui.hybrid_mode import ChangeLogger

def test_change_logger():
    """Test change logger functionality"""
    print("="*80)
    print("PHASE 1.2 TEST: CHANGE LOG / AUDIT TRAIL")
    print("="*80)
    print()
    
    # Initialize
    ChangeLogger.initialize()
    print("✅ Change logger initialized")
    print()
    
    # TEST 1: Log quantity change
    print("TEST 1: Log Quantity Changes")
    print("-" * 80)
    
    ChangeLogger.log_change(
        item_no='001',
        field='Bill Quantity',
        old_value='0.00',
        new_value='50.00',
        reason='Zero-Qty Activation'
    )
    print("  ✅ Logged: Item 001 quantity change (0.00 → 50.00)")
    
    ChangeLogger.log_change(
        item_no='002',
        field='Bill Quantity',
        old_value='100.00',
        new_value='150.00',
        reason='Quantity Adjustment'
    )
    print("  ✅ Logged: Item 002 quantity change (100.00 → 150.00)")
    print()
    
    # TEST 2: Log rate changes
    print("TEST 2: Log Rate Changes")
    print("-" * 80)
    
    ChangeLogger.log_change(
        item_no='003',
        field='Bill Rate',
        old_value='₹100.00',
        new_value='₹95.00',
        reason='Part Rate Payment'
    )
    print("  ✅ Logged: Item 003 rate change (₹100.00 → ₹95.00)")
    
    ChangeLogger.log_change(
        item_no='004',
        field='Bill Rate',
        old_value='₹200.00',
        new_value='₹195.00',
        reason='Part Rate Payment'
    )
    print("  ✅ Logged: Item 004 rate change (₹200.00 → ₹195.00)")
    print()
    
    # TEST 3: Retrieve changes
    print("TEST 3: Retrieve Changes")
    print("-" * 80)
    
    all_changes = ChangeLogger.get_changes()
    print(f"  Total changes: {len(all_changes)}")
    
    if len(all_changes) != 4:
        print(f"  ❌ Expected 4 changes, got {len(all_changes)}")
        return False
    
    print("  ✅ All 4 changes retrieved")
    print()
    
    # TEST 4: Get changes for specific item
    print("TEST 4: Get Changes for Specific Item")
    print("-" * 80)
    
    item_001_changes = ChangeLogger.get_changes_for_item('001')
    print(f"  Item 001 changes: {len(item_001_changes)}")
    
    if len(item_001_changes) != 1:
        print(f"  ❌ Expected 1 change for item 001, got {len(item_001_changes)}")
        return False
    
    print("  ✅ Correct number of changes for item 001")
    print()
    
    # TEST 5: Verify change structure
    print("TEST 5: Verify Change Structure")
    print("-" * 80)
    
    change = all_changes[0]
    required_fields = ['timestamp', 'item_no', 'field', 'old_value', 'new_value', 'reason', 'user']
    
    all_fields_present = True
    for field in required_fields:
        if field not in change:
            print(f"  ❌ Missing field: {field}")
            all_fields_present = False
        else:
            print(f"  ✅ Field present: {field} = {change[field]}")
    
    if not all_fields_present:
        return False
    
    print()
    
    # TEST 6: Export to DataFrame
    print("TEST 6: Export to DataFrame")
    print("-" * 80)
    
    df = ChangeLogger.export_to_dataframe()
    print(f"  DataFrame shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    
    if len(df) != 4:
        print(f"  ❌ Expected 4 rows, got {len(df)}")
        return False
    
    print("  ✅ DataFrame export successful")
    print()
    
    # Display DataFrame
    print("  Change Log DataFrame:")
    print(df.to_string(index=False))
    print()
    
    # TEST 7: Export to JSON
    print("TEST 7: Export to JSON")
    print("-" * 80)
    
    json_data = ChangeLogger.export_to_json()
    print(f"  JSON length: {len(json_data)} characters")
    
    if len(json_data) < 100:
        print(f"  ❌ JSON too short, might be empty")
        return False
    
    print("  ✅ JSON export successful")
    print()
    print("  Sample JSON (first 200 chars):")
    print(f"  {json_data[:200]}...")
    print()
    
    # TEST 8: Clear log
    print("TEST 8: Clear Log")
    print("-" * 80)
    
    ChangeLogger.clear()
    changes_after_clear = ChangeLogger.get_changes()
    
    if len(changes_after_clear) != 0:
        print(f"  ❌ Expected 0 changes after clear, got {len(changes_after_clear)}")
        return False
    
    print("  ✅ Log cleared successfully")
    print()
    
    # SUMMARY
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    print()
    print("✅ ALL TESTS PASSED")
    print()
    print("Verified:")
    print("  ✅ Change logging works")
    print("  ✅ Timestamp recorded")
    print("  ✅ Old/new values tracked")
    print("  ✅ Reason captured")
    print("  ✅ User recorded")
    print("  ✅ Item-specific retrieval works")
    print("  ✅ DataFrame export works")
    print("  ✅ JSON export works")
    print("  ✅ Clear log works")
    print()
    
    return True

if __name__ == '__main__':
    success = test_change_logger()
    sys.exit(0 if success else 1)
