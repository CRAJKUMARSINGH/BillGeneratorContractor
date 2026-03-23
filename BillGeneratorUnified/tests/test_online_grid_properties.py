"""
Property-based tests for online_mode_grid
Tests universal properties across randomized inputs
"""
import pytest
import pandas as pd
import sys
from pathlib import Path
from hypothesis import given, strategies as st

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ui.online_mode_grid_new import _recalc


class TestAmountCalculationProperty:
    """Property tests for amount calculation correctness"""
    
    @given(
        quantity=st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False),
        rate=st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False)
    )
    def test_property_amount_calculation_correctness(self, quantity, rate):
        """
        Feature: streamlit-excel-grid-enhancement, Property 1: Amount Calculation Correctness
        
        For any work item with quantity Q and rate R, the calculated amount SHALL equal Q × R.
        
        Validates: Requirements 4.1, 4.2, 4.8
        """
        # Create DataFrame with test values
        df = pd.DataFrame([{
            'Quantity': quantity,
            'Rate': rate,
            'Amount': 0.0
        }])
        
        # Recalculate amount
        result = _recalc(df)
        expected_amount = quantity * rate
        
        # Verify amount equals quantity × rate (with floating point tolerance)
        assert abs(result.loc[0, 'Amount'] - expected_amount) < 1e-6, \
            f"Amount calculation failed: {quantity} × {rate} should equal {expected_amount}, got {result.loc[0, 'Amount']}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])


from core.ui.online_mode_grid_new import update_validation_status, can_submit


class TestValidationStatusProperty:
    """Property tests for validation status consistency"""
    
    @given(
        description=st.one_of(
            st.just(''),
            st.text(min_size=1, max_size=100).filter(lambda x: x.strip() != ''),
            st.just('   ')  # whitespace-only
        ),
        quantity=st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False),
        rate=st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False)
    )
    def test_property_validation_status_consistency(self, description, quantity, rate):
        """
        Feature: streamlit-excel-grid-enhancement, Property 2: Validation Status Consistency
        
        For any work item, the validation status SHALL be:
        - ⚪ (Empty) if description is empty/whitespace AND quantity=0 AND rate=0
        - 🟢 (Valid) if description is non-empty AND quantity>0 AND rate>0
        - 🟠 (Partial) if description is non-empty AND (quantity=0 OR rate=0)
        - 🔴 (Invalid) if description is empty/whitespace AND (quantity>0 OR rate>0)
        
        Validates: Requirements 3.5, 3.6, 3.7, 3.8
        """
        # Create DataFrame with test values
        df = pd.DataFrame([{
            'Description': description,
            'Quantity': quantity,
            'Rate': rate
        }])
        
        # Update validation status
        result = update_validation_status(df)
        status = result.loc[0, 'Status']
        
        # Determine expected status based on rules
        has_desc = description.strip() != ''
        has_qty = quantity > 0
        has_rate = rate > 0
        
        if not has_desc and not has_qty and not has_rate:
            # Empty: all fields empty
            assert status == '⚪', \
                f"Expected ⚪ (empty) for desc='{description}', qty={quantity}, rate={rate}, got {status}"
        elif has_desc and has_qty and has_rate:
            # Valid: all fields present
            assert status == '🟢', \
                f"Expected 🟢 (valid) for desc='{description}', qty={quantity}, rate={rate}, got {status}"
        elif has_desc and (not has_qty or not has_rate):
            # Partial: has description but missing qty or rate
            assert '🟠' in status, \
                f"Expected 🟠 (partial) for desc='{description}', qty={quantity}, rate={rate}, got {status}"
        elif not has_desc and (has_qty or has_rate):
            # Invalid: no description but has qty or rate
            assert '🔴' in status, \
                f"Expected 🔴 (invalid) for desc='{description}', qty={quantity}, rate={rate}, got {status}"


class TestSubmitButtonProperty:
    """Property tests for submit button state correctness"""
    
    @given(
        items=st.lists(
            st.tuples(
                st.text(min_size=0, max_size=50),  # description
                st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False),  # quantity
                st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False)   # rate
            ),
            min_size=1,
            max_size=20
        )
    )
    def test_property_submit_button_correctness(self, items):
        """
        Feature: streamlit-excel-grid-enhancement, Property 3: Submit Button State Correctness
        
        The submit button SHALL be enabled if and only if:
        - At least one item has status 🟢 (valid), AND
        - No active items (non-⚪) have status 🔴 (invalid) or 🟠 (partial)
        
        Validates: Requirements 3.7, 3.8
        """
        # Create DataFrame from generated items
        df = pd.DataFrame([
            {
                'Description': desc,
                'Quantity': qty,
                'Rate': rate
            }
            for desc, qty, rate in items
        ])
        
        # Update validation status
        df = update_validation_status(df)
        
        # Check submit button state
        can, msg = can_submit(df)
        
        # Determine expected state
        has_valid = any(df['Status'] == '🟢')
        has_invalid = any(('🔴' in str(s) or '🟠' in str(s)) for s in df['Status'])
        
        expected_can_submit = has_valid and not has_invalid
        
        assert can == expected_can_submit, \
            f"Submit button state mismatch: expected {expected_can_submit}, got {can}. " \
            f"Has valid: {has_valid}, Has invalid: {has_invalid}. Message: {msg}"



from core.ui.online_mode_grid_new import _diff_log


class TestChangeLogProperty:
    """Property tests for change log completeness"""
    
    @given(
        old_qty=st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False),
        new_qty=st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False),
        old_rate=st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False),
        new_rate=st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False)
    )
    def test_property_change_log_completeness(self, old_qty, new_qty, old_rate, new_rate):
        """
        Feature: streamlit-excel-grid-enhancement, Property 4: Change Log Completeness
        
        For any edit to a work item, ALL changes SHALL be logged with:
        - Item No
        - Field name (Quantity or Rate)
        - Old value
        - New value
        - Reason (auto-generated based on change type)
        - Timestamp
        
        Validates: Requirements 8.3, 8.4, 8.5, 9.1, 9.2, 9.3
        """
        # Create old and new DataFrames
        old_df = pd.DataFrame([{
            'Item No': '001',
            'Quantity': old_qty,
            'Rate': old_rate
        }])
        new_df = pd.DataFrame([{
            'Item No': '001',
            'Quantity': new_qty,
            'Rate': new_rate
        }])
        
        # Get change log
        changes = _diff_log(old_df, new_df)
        
        # Determine expected number of changes
        qty_changed = abs(old_qty - new_qty) > 1e-9
        rate_changed = abs(old_rate - new_rate) > 1e-9
        expected_count = int(qty_changed) + int(rate_changed)
        
        # Verify correct number of changes logged
        assert len(changes) == expected_count, \
            f"Expected {expected_count} changes, got {len(changes)}"
        
        # Verify all changes have required fields
        for change in changes:
            assert 'Item No' in change, "Missing Item No"
            assert 'Field' in change, "Missing Field"
            assert 'Old' in change, "Missing Old value"
            assert 'New' in change, "Missing New value"
            assert 'Reason' in change, "Missing Reason"
            assert 'Timestamp' in change, "Missing Timestamp"
            
            # Verify field is either Quantity or Rate
            assert change['Field'] in ['Quantity', 'Rate'], \
                f"Invalid field: {change['Field']}"
            
            # Verify reason is one of the expected types
            valid_reasons = [
                'Zero-Qty Activation', 'Qty Set to Zero', 'Qty Change',
                'Rate Reduction', 'Rate Increase', 'Rate Change'
            ]
            assert change['Reason'] in valid_reasons, \
                f"Invalid reason: {change['Reason']}"
            
            # Verify timestamp format (HH:MM:SS)
            assert len(change['Timestamp']) == 8, \
                f"Invalid timestamp format: {change['Timestamp']}"
            assert change['Timestamp'].count(':') == 2, \
                f"Invalid timestamp format: {change['Timestamp']}"



from core.ui.online_mode_grid_new import _detect_part_rates


class TestPartRateProperty:
    """Property tests for part-rate calculation"""
    
    @given(
        work_order_rate=st.floats(min_value=1, max_value=1e6, allow_nan=False, allow_infinity=False),
        rate_multiplier=st.floats(min_value=0.5, max_value=1.5, allow_nan=False, allow_infinity=False),
        quantity=st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False)
    )
    def test_property_part_rate_calculation(self, work_order_rate, rate_multiplier, quantity):
        """
        Feature: streamlit-excel-grid-enhancement, Property 16: Part-Rate Calculation
        
        For any work item where the current rate is below the original work-order rate,
        the item SHALL be marked as part-rate and calculations SHALL use the reduced rate.
        
        Part-rate detection rule:
        - Part-rate if current_rate < (work_order_rate - 0.01)
        - Standard rate otherwise
        
        Validates: Requirements 8.6
        """
        # Calculate current rate based on multiplier
        current_rate = work_order_rate * rate_multiplier
        
        # Create DataFrame with test values
        df = pd.DataFrame([{
            'Item No': '001',
            'Description': 'Test Item',
            'Unit': 'NOS',
            'Quantity': quantity,
            'Rate': current_rate,
            'Amount': quantity * current_rate
        }])
        
        work_order_rates = {'001': work_order_rate}
        
        # Detect part-rates
        result = _detect_part_rates(df, work_order_rates)
        
        # Determine expected part-rate status
        # Part-rate if current rate is below work-order rate by more than tolerance (0.01)
        expected_is_part_rate = current_rate < (work_order_rate - 0.01)
        
        # Verify part-rate detection
        assert 'Part_Rate' in result.columns, "Part_Rate column missing"
        actual_is_part_rate = result.loc[0, 'Part_Rate']
        
        assert actual_is_part_rate == expected_is_part_rate, \
            f"Part-rate detection failed: work_order_rate={work_order_rate:.2f}, " \
            f"current_rate={current_rate:.2f}, multiplier={rate_multiplier:.2f}, " \
            f"expected_part_rate={expected_is_part_rate}, got={actual_is_part_rate}"
        
        # Verify amount calculation uses current rate (not work-order rate)
        expected_amount = quantity * current_rate
        actual_amount = result.loc[0, 'Amount']
        
        assert abs(actual_amount - expected_amount) < 1e-6, \
            f"Amount calculation failed: {quantity} × {current_rate} should equal {expected_amount}, " \
            f"got {actual_amount}"
    
    @given(
        items=st.lists(
            st.tuples(
                st.floats(min_value=1, max_value=1e6, allow_nan=False, allow_infinity=False),  # work_order_rate
                st.floats(min_value=0.5, max_value=1.5, allow_nan=False, allow_infinity=False)  # rate_multiplier
            ),
            min_size=1,
            max_size=10
        )
    )
    def test_property_part_rate_multiple_items(self, items):
        """
        Feature: streamlit-excel-grid-enhancement, Property 16: Part-Rate Calculation (Multiple Items)
        
        For multiple work items, each item's part-rate status SHALL be determined independently
        based on its own work-order rate comparison.
        
        Validates: Requirements 8.6
        """
        # Create DataFrame from generated items with unique item numbers
        df_data = []
        work_order_rates = {}
        
        for idx, (work_order_rate, rate_multiplier) in enumerate(items):
            item_no = f"{idx+1:03d}"  # Generate unique item numbers: 001, 002, 003, etc.
            current_rate = work_order_rate * rate_multiplier
            df_data.append({
                'Item No': item_no,
                'Description': f'Item {item_no}',
                'Unit': 'NOS',
                'Quantity': 10.0,
                'Rate': current_rate,
                'Amount': 10.0 * current_rate
            })
            work_order_rates[item_no] = work_order_rate
        
        df = pd.DataFrame(df_data)
        
        # Detect part-rates
        result = _detect_part_rates(df, work_order_rates)
        
        # Verify each item's part-rate status
        for idx, (work_order_rate, rate_multiplier) in enumerate(items):
            item_no = f"{idx+1:03d}"
            current_rate = work_order_rate * rate_multiplier
            expected_is_part_rate = current_rate < (work_order_rate - 0.01)
            actual_is_part_rate = result.loc[idx, 'Part_Rate']
            
            assert actual_is_part_rate == expected_is_part_rate, \
                f"Item {item_no}: Part-rate detection failed: " \
                f"work_order_rate={work_order_rate:.2f}, current_rate={current_rate:.2f}, " \
                f"expected={expected_is_part_rate}, got={actual_is_part_rate}"
