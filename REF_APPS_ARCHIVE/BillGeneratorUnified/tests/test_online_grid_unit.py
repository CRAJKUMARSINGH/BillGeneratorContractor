"""
Unit tests for online_mode_grid helper functions
Tests specific examples and edge cases
"""
import pytest
import pandas as pd
import sys
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ui.online_mode_grid_new import (
    _default_df, _safe_float, _recalc, _detect_part_rates, 
    _format_rate_display, _diff_log
)


class TestDefaultDF:
    """Tests for _default_df() function"""
    
    def test_creates_correct_number_of_rows(self):
        """Test that _default_df creates correct number of rows"""
        df = _default_df(5)
        assert len(df) == 5
    
    def test_creates_correct_columns(self):
        """Test that _default_df creates correct column structure"""
        df = _default_df(3)
        expected_columns = ['Item No', 'Description', 'Unit', 'Quantity', 'Rate', 'Amount']
        assert list(df.columns) == expected_columns
    
    def test_item_numbers_formatted_correctly(self):
        """Test that item numbers are zero-padded"""
        df = _default_df(5, offset=0)
        assert df['Item No'].tolist() == ['001', '002', '003', '004', '005']
    
    def test_item_numbers_with_offset(self):
        """Test that offset works correctly"""
        df = _default_df(3, offset=10)
        assert df['Item No'].tolist() == ['011', '012', '013']
    
    def test_default_values(self):
        """Test that default values are correct"""
        df = _default_df(1)
        row = df.iloc[0]
        assert row['Description'] == ''
        assert row['Unit'] == 'NOS'
        assert row['Quantity'] == 0.0
        assert row['Rate'] == 0.0
        assert row['Amount'] == 0.0
    
    def test_empty_dataframe(self):
        """Test creating empty dataframe with 0 rows"""
        df = _default_df(0)
        assert len(df) == 0
        assert list(df.columns) == ['Item No', 'Description', 'Unit', 'Quantity', 'Rate', 'Amount']


class TestSafeFloat:
    """Tests for _safe_float() function"""
    
    def test_converts_valid_float(self):
        """Test conversion of valid float"""
        assert _safe_float(3.14) == 3.14
    
    def test_converts_valid_int(self):
        """Test conversion of valid int"""
        assert _safe_float(42) == 42.0
    
    def test_converts_valid_string(self):
        """Test conversion of valid string"""
        assert _safe_float("123.45") == 123.45
    
    def test_handles_none(self):
        """Test handling of None"""
        assert _safe_float(None) == 0.0
    
    def test_handles_empty_string(self):
        """Test handling of empty string"""
        assert _safe_float("") == 0.0
    
    def test_handles_invalid_string(self):
        """Test handling of invalid string"""
        assert _safe_float("abc") == 0.0
    
    def test_handles_infinity(self):
        """Test handling of infinity"""
        result = _safe_float(float('inf'))
        assert result == float('inf')
    
    def test_custom_default(self):
        """Test custom default value"""
        assert _safe_float("invalid", default=99.9) == 99.9
    
    def test_handles_nan(self):
        """Test handling of NaN"""
        result = _safe_float(float('nan'))
        # NaN != NaN, so check using isnan
        import math
        assert math.isnan(result)


class TestRecalc:
    """Tests for _recalc() function"""
    
    def test_recalculates_amount(self):
        """Test that Amount is recalculated correctly"""
        df = pd.DataFrame([
            {'Quantity': 10.0, 'Rate': 100.0, 'Amount': 0.0},
            {'Quantity': 5.0, 'Rate': 50.0, 'Amount': 0.0}
        ])
        result = _recalc(df)
        assert result.loc[0, 'Amount'] == 1000.0
        assert result.loc[1, 'Amount'] == 250.0
    
    def test_handles_zero_quantity(self):
        """Test recalculation with zero quantity"""
        df = pd.DataFrame([
            {'Quantity': 0.0, 'Rate': 100.0, 'Amount': 999.0}
        ])
        result = _recalc(df)
        assert result.loc[0, 'Amount'] == 0.0
    
    def test_handles_zero_rate(self):
        """Test recalculation with zero rate"""
        df = pd.DataFrame([
            {'Quantity': 10.0, 'Rate': 0.0, 'Amount': 999.0}
        ])
        result = _recalc(df)
        assert result.loc[0, 'Amount'] == 0.0
    
    def test_handles_negative_values(self):
        """Test recalculation with negative values"""
        df = pd.DataFrame([
            {'Quantity': -5.0, 'Rate': 100.0, 'Amount': 0.0}
        ])
        result = _recalc(df)
        assert result.loc[0, 'Amount'] == -500.0
    
    def test_handles_large_numbers(self):
        """Test recalculation with large numbers"""
        df = pd.DataFrame([
            {'Quantity': 1000000.0, 'Rate': 1000000.0, 'Amount': 0.0}
        ])
        result = _recalc(df)
        assert result.loc[0, 'Amount'] == 1000000000000.0
    
    def test_handles_decimal_precision(self):
        """Test recalculation with decimal precision"""
        df = pd.DataFrame([
            {'Quantity': 0.01, 'Rate': 0.01, 'Amount': 0.0}
        ])
        result = _recalc(df)
        assert abs(result.loc[0, 'Amount'] - 0.0001) < 1e-10
    
    def test_does_not_modify_original(self):
        """Test that original dataframe is not modified"""
        df = pd.DataFrame([
            {'Quantity': 10.0, 'Rate': 100.0, 'Amount': 0.0}
        ])
        original_amount = df.loc[0, 'Amount']
        result = _recalc(df)
        assert df.loc[0, 'Amount'] == original_amount  # Original unchanged
        assert result.loc[0, 'Amount'] == 1000.0  # Result changed
    
    def test_handles_empty_dataframe(self):
        """Test recalculation with empty dataframe"""
        df = pd.DataFrame(columns=['Quantity', 'Rate', 'Amount'])
        result = _recalc(df)
        assert len(result) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


from core.ui.online_mode_grid_new import update_validation_status, can_submit


class TestValidationStatus:
    """Tests for update_validation_status() function"""
    
    def test_empty_row_marked_as_empty(self):
        """Test that empty rows are marked with ⚪"""
        df = pd.DataFrame([{
            'Description': '',
            'Quantity': 0.0,
            'Rate': 0.0
        }])
        result = update_validation_status(df)
        assert result.loc[0, 'Status'] == '⚪'
    
    def test_valid_row_marked_as_valid(self):
        """Test that complete rows are marked with 🟢"""
        df = pd.DataFrame([{
            'Description': 'Test Item',
            'Quantity': 10.0,
            'Rate': 100.0
        }])
        result = update_validation_status(df)
        assert result.loc[0, 'Status'] == '🟢'
    
    def test_partial_row_marked_as_partial(self):
        """Test that partial rows are marked with 🟠"""
        df = pd.DataFrame([{
            'Description': 'Test Item',
            'Quantity': 0.0,
            'Rate': 100.0
        }])
        result = update_validation_status(df)
        assert '🟠' in result.loc[0, 'Status']
    
    def test_invalid_row_marked_as_invalid(self):
        """Test that invalid rows are marked with 🔴"""
        df = pd.DataFrame([{
            'Description': '',
            'Quantity': 10.0,
            'Rate': 100.0
        }])
        result = update_validation_status(df)
        assert '🔴' in result.loc[0, 'Status']
    
    def test_whitespace_description_treated_as_empty(self):
        """Test that whitespace-only descriptions are treated as empty"""
        df = pd.DataFrame([{
            'Description': '   ',
            'Quantity': 10.0,
            'Rate': 100.0
        }])
        result = update_validation_status(df)
        assert '🔴' in result.loc[0, 'Status']
    
    def test_zero_quantity_with_description(self):
        """Test row with description but zero quantity"""
        df = pd.DataFrame([{
            'Description': 'Test Item',
            'Quantity': 0.0,
            'Rate': 100.0
        }])
        result = update_validation_status(df)
        assert '🟠' in result.loc[0, 'Status']
    
    def test_zero_rate_with_description(self):
        """Test row with description but zero rate"""
        df = pd.DataFrame([{
            'Description': 'Test Item',
            'Quantity': 10.0,
            'Rate': 0.0
        }])
        result = update_validation_status(df)
        assert '🟠' in result.loc[0, 'Status']
    
    def test_adds_status_column_if_missing(self):
        """Test that Status column is added if it doesn't exist"""
        df = pd.DataFrame([{
            'Description': 'Test',
            'Quantity': 10.0,
            'Rate': 100.0
        }])
        result = update_validation_status(df)
        assert 'Status' in result.columns
        assert result.columns[0] == 'Status'  # Should be first column
    
    def test_handles_empty_dataframe(self):
        """Test handling of empty dataframe"""
        df = pd.DataFrame(columns=['Description', 'Quantity', 'Rate'])
        result = update_validation_status(df)
        assert len(result) == 0
    
    def test_handles_none_dataframe(self):
        """Test handling of None dataframe"""
        result = update_validation_status(None)
        assert result is None


class TestCanSubmit:
    """Tests for can_submit() function"""
    
    def test_can_submit_with_valid_items(self):
        """Test that submission is allowed with valid items"""
        df = pd.DataFrame([
            {'Status': '🟢', 'Description': 'Item 1', 'Quantity': 10.0, 'Rate': 100.0},
            {'Status': '⚪', 'Description': '', 'Quantity': 0.0, 'Rate': 0.0}
        ])
        can, msg = can_submit(df)
        assert can is True
        assert msg == ""
    
    def test_cannot_submit_with_invalid_items(self):
        """Test that submission is blocked with invalid items"""
        df = pd.DataFrame([
            {'Status': '🟢', 'Description': 'Item 1', 'Quantity': 10.0, 'Rate': 100.0},
            {'Status': '🔴 No Desc', 'Description': '', 'Quantity': 10.0, 'Rate': 100.0}
        ])
        can, msg = can_submit(df)
        assert can is False
        assert 'invalid' in msg.lower()
    
    def test_cannot_submit_with_partial_items(self):
        """Test that submission is blocked with partial items"""
        df = pd.DataFrame([
            {'Status': '🟢', 'Description': 'Item 1', 'Quantity': 10.0, 'Rate': 100.0},
            {'Status': '🟠 Miss Q/R', 'Description': 'Item 2', 'Quantity': 0.0, 'Rate': 100.0}
        ])
        can, msg = can_submit(df)
        assert can is False
        assert 'invalid' in msg.lower()
    
    def test_cannot_submit_with_only_empty_items(self):
        """Test that submission is blocked with only empty items"""
        df = pd.DataFrame([
            {'Status': '⚪', 'Description': '', 'Quantity': 0.0, 'Rate': 0.0},
            {'Status': '⚪', 'Description': '', 'Quantity': 0.0, 'Rate': 0.0}
        ])
        can, msg = can_submit(df)
        assert can is False
        assert 'active' in msg.lower()
    
    def test_cannot_submit_with_empty_dataframe(self):
        """Test that submission is blocked with empty dataframe"""
        df = pd.DataFrame(columns=['Status', 'Description', 'Quantity', 'Rate'])
        can, msg = can_submit(df)
        assert can is False
    
    def test_cannot_submit_with_none_dataframe(self):
        """Test that submission is blocked with None dataframe"""
        can, msg = can_submit(None)
        assert can is False
    
    def test_can_submit_ignores_empty_rows(self):
        """Test that empty rows are ignored in validation"""
        df = pd.DataFrame([
            {'Status': '🟢', 'Description': 'Item 1', 'Quantity': 10.0, 'Rate': 100.0},
            {'Status': '⚪', 'Description': '', 'Quantity': 0.0, 'Rate': 0.0},
            {'Status': '⚪', 'Description': '', 'Quantity': 0.0, 'Rate': 0.0}
        ])
        can, msg = can_submit(df)
        assert can is True



class TestDiffLog:
    """Tests for _diff_log() function"""
    
    def test_detects_quantity_change(self):
        """Test that quantity changes are detected"""
        old_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.0, 'Rate': 100.0}
        ])
        new_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 15.0, 'Rate': 100.0}
        ])
        
        changes = _diff_log(old_df, new_df)
        
        assert len(changes) == 1
        assert changes[0]['Item No'] == '001'
        assert changes[0]['Field'] == 'Quantity'
        assert changes[0]['Old'] == 10.0
        assert changes[0]['New'] == 15.0
        assert changes[0]['Reason'] == 'Qty Change'
        assert 'Timestamp' in changes[0]
    
    def test_detects_rate_change(self):
        """Test that rate changes are detected"""
        old_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.0, 'Rate': 100.0}
        ])
        new_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.0, 'Rate': 150.0}
        ])
        
        changes = _diff_log(old_df, new_df)
        
        assert len(changes) == 1
        assert changes[0]['Item No'] == '001'
        assert changes[0]['Field'] == 'Rate'
        assert changes[0]['Old'] == 100.0
        assert changes[0]['New'] == 150.0
        assert changes[0]['Reason'] == 'Rate Increase'
    
    def test_detects_zero_qty_activation(self):
        """Test that zero to non-zero quantity is detected as activation"""
        old_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 0.0, 'Rate': 100.0}
        ])
        new_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.0, 'Rate': 100.0}
        ])
        
        changes = _diff_log(old_df, new_df)
        
        assert len(changes) == 1
        assert changes[0]['Reason'] == 'Zero-Qty Activation'
    
    def test_detects_rate_reduction(self):
        """Test that rate decrease is detected as reduction"""
        old_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.0, 'Rate': 100.0}
        ])
        new_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.0, 'Rate': 80.0}
        ])
        
        changes = _diff_log(old_df, new_df)
        
        assert len(changes) == 1
        assert changes[0]['Reason'] == 'Rate Reduction'
    
    def test_detects_multiple_changes(self):
        """Test that both quantity and rate changes are detected"""
        old_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.0, 'Rate': 100.0}
        ])
        new_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 15.0, 'Rate': 120.0}
        ])
        
        changes = _diff_log(old_df, new_df)
        
        assert len(changes) == 2
        assert any(c['Field'] == 'Quantity' for c in changes)
        assert any(c['Field'] == 'Rate' for c in changes)
    
    def test_no_changes_when_identical(self):
        """Test that no changes are logged when DataFrames are identical"""
        old_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.0, 'Rate': 100.0}
        ])
        new_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.0, 'Rate': 100.0}
        ])
        
        changes = _diff_log(old_df, new_df)
        
        assert len(changes) == 0
    
    def test_handles_multiple_rows(self):
        """Test change detection across multiple rows"""
        old_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.0, 'Rate': 100.0},
            {'Item No': '002', 'Quantity': 5.0, 'Rate': 50.0},
            {'Item No': '003', 'Quantity': 0.0, 'Rate': 0.0}
        ])
        new_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 15.0, 'Rate': 100.0},  # Qty changed
            {'Item No': '002', 'Quantity': 5.0, 'Rate': 50.0},    # No change
            {'Item No': '003', 'Quantity': 10.0, 'Rate': 75.0}    # Both changed
        ])
        
        changes = _diff_log(old_df, new_df)
        
        # Should detect: 001 qty change, 003 qty activation, 003 rate increase
        assert len(changes) == 3
        assert any(c['Item No'] == '001' and c['Field'] == 'Quantity' for c in changes)
        assert any(c['Item No'] == '003' and c['Field'] == 'Quantity' for c in changes)
        assert any(c['Item No'] == '003' and c['Field'] == 'Rate' for c in changes)
    
    def test_handles_empty_dataframes(self):
        """Test handling of empty DataFrames"""
        old_df = pd.DataFrame(columns=['Item No', 'Quantity', 'Rate'])
        new_df = pd.DataFrame(columns=['Item No', 'Quantity', 'Rate'])
        
        changes = _diff_log(old_df, new_df)
        
        assert len(changes) == 0
    
    def test_handles_none_dataframes(self):
        """Test handling of None DataFrames"""
        changes = _diff_log(None, None)
        assert len(changes) == 0
        
        old_df = pd.DataFrame([{'Item No': '001', 'Quantity': 10.0, 'Rate': 100.0}])
        changes = _diff_log(old_df, None)
        assert len(changes) == 0
        
        changes = _diff_log(None, old_df)
        assert len(changes) == 0
    
    def test_handles_different_row_counts(self):
        """Test that only common rows are compared"""
        old_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.0, 'Rate': 100.0}
        ])
        new_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 15.0, 'Rate': 100.0},
            {'Item No': '002', 'Quantity': 5.0, 'Rate': 50.0}
        ])
        
        changes = _diff_log(old_df, new_df)
        
        # Should only detect change in row 001 (row 002 is new, not a change)
        assert len(changes) == 1
        assert changes[0]['Item No'] == '001'
    
    def test_rounds_values_correctly(self):
        """Test that values are rounded to 3 decimal places"""
        old_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.123456, 'Rate': 100.987654}
        ])
        new_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 15.654321, 'Rate': 120.111111}
        ])
        
        changes = _diff_log(old_df, new_df)
        
        qty_change = next(c for c in changes if c['Field'] == 'Quantity')
        rate_change = next(c for c in changes if c['Field'] == 'Rate')
        
        assert qty_change['Old'] == 10.123
        assert qty_change['New'] == 15.654
        assert rate_change['Old'] == 100.988
        assert rate_change['New'] == 120.111
    
    def test_ignores_tiny_differences(self):
        """Test that floating point precision errors are ignored"""
        old_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.0, 'Rate': 100.0}
        ])
        new_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.0000000001, 'Rate': 100.0000000001}
        ])
        
        changes = _diff_log(old_df, new_df)
        
        # Should detect no changes (difference < 1e-9)
        assert len(changes) == 0
    
    def test_detects_qty_set_to_zero(self):
        """Test that non-zero to zero quantity is detected"""
        old_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 10.0, 'Rate': 100.0}
        ])
        new_df = pd.DataFrame([
            {'Item No': '001', 'Quantity': 0.0, 'Rate': 100.0}
        ])
        
        changes = _diff_log(old_df, new_df)
        
        assert len(changes) == 1
        assert changes[0]['Reason'] == 'Qty Set to Zero'



from core.ui.online_mode_grid_new import _init_session_state, _is_new_upload


class TestSessionStateManagement:
    """Tests for session state management functions"""
    
    def test_init_session_state_has_all_keys(self):
        """Test that initialization creates all required keys"""
        state = _init_session_state()
        
        required_keys = [
            'project_name', 'contractor', 'bill_date', 'tender_premium',
            'df', 'last_upload', 'change_log', 'prev_df'
        ]
        
        for key in required_keys:
            assert key in state, f"Missing key: {key}"
    
    def test_init_session_state_default_values(self):
        """Test that initialization sets correct default values"""
        state = _init_session_state()
        
        assert state['project_name'] == ""
        assert state['contractor'] == ""
        assert state['bill_date'] is None
        assert state['tender_premium'] == 4.0
        assert state['last_upload'] is None
        assert state['change_log'] == []
        assert state['prev_df'] is None
    
    def test_init_session_state_creates_default_df(self):
        """Test that initialization creates a default DataFrame"""
        state = _init_session_state()
        
        assert 'df' in state
        assert isinstance(state['df'], pd.DataFrame)
        assert len(state['df']) == 5  # Default 5 rows
        assert list(state['df'].columns) == ['Item No', 'Description', 'Unit', 'Quantity', 'Rate', 'Amount']
    
    def test_is_new_upload_with_none_current(self):
        """Test that None current filename returns False"""
        assert _is_new_upload(None, None) is False
        assert _is_new_upload(None, "file.xlsx") is False
    
    def test_is_new_upload_with_none_last(self):
        """Test that any filename is new when last_upload is None"""
        assert _is_new_upload("file.xlsx", None) is True
        assert _is_new_upload("test.xlsx", None) is True
    
    def test_is_new_upload_same_filename(self):
        """Test that same filename is not considered new"""
        assert _is_new_upload("file.xlsx", "file.xlsx") is False
        assert _is_new_upload("test.xlsm", "test.xlsm") is False
    
    def test_is_new_upload_different_filename(self):
        """Test that different filename is considered new"""
        assert _is_new_upload("file1.xlsx", "file2.xlsx") is True
        assert _is_new_upload("new.xlsx", "old.xlsx") is True
    
    def test_is_new_upload_case_sensitive(self):
        """Test that filename comparison is case-sensitive"""
        # This depends on the OS, but we test the function behavior
        result = _is_new_upload("File.xlsx", "file.xlsx")
        # Should be True (different case = different file)
        assert result is True



class TestPartRateDetection:
    """Tests for part-rate detection functions"""
    
    def test_detect_part_rates_empty_df(self):
        """Test part-rate detection with empty DataFrame"""
        df = pd.DataFrame()
        work_order_rates = {}
        result = _detect_part_rates(df, work_order_rates)
        assert result.empty
    
    def test_detect_part_rates_no_work_order_rates(self):
        """Test part-rate detection with no work-order rates"""
        df = pd.DataFrame([{
            "Item No": "001",
            "Description": "Test Item",
            "Unit": "NOS",
            "Quantity": 10.0,
            "Rate": 100.0,
            "Amount": 1000.0,
        }])
        work_order_rates = {}
        result = _detect_part_rates(df, work_order_rates)
        assert 'Part_Rate' in result.columns
        assert result.loc[0, 'Part_Rate'] == False
    
    def test_detect_part_rates_rate_below_work_order(self):
        """Test part-rate detection when rate is below work-order rate"""
        df = pd.DataFrame([{
            "Item No": "001",
            "Description": "Test Item",
            "Unit": "NOS",
            "Quantity": 10.0,
            "Rate": 95.0,  # Below work-order rate of 100
            "Amount": 950.0,
        }])
        work_order_rates = {"001": 100.0}
        result = _detect_part_rates(df, work_order_rates)
        assert result.loc[0, 'Part_Rate'] == True
    
    def test_detect_part_rates_rate_equal_work_order(self):
        """Test part-rate detection when rate equals work-order rate"""
        df = pd.DataFrame([{
            "Item No": "001",
            "Description": "Test Item",
            "Unit": "NOS",
            "Quantity": 10.0,
            "Rate": 100.0,  # Equal to work-order rate
            "Amount": 1000.0,
        }])
        work_order_rates = {"001": 100.0}
        result = _detect_part_rates(df, work_order_rates)
        assert result.loc[0, 'Part_Rate'] == False
    
    def test_detect_part_rates_rate_above_work_order(self):
        """Test part-rate detection when rate is above work-order rate"""
        df = pd.DataFrame([{
            "Item No": "001",
            "Description": "Test Item",
            "Unit": "NOS",
            "Quantity": 10.0,
            "Rate": 105.0,  # Above work-order rate
            "Amount": 1050.0,
        }])
        work_order_rates = {"001": 100.0}
        result = _detect_part_rates(df, work_order_rates)
        assert result.loc[0, 'Part_Rate'] == False
    
    def test_detect_part_rates_multiple_items(self):
        """Test part-rate detection with multiple items"""
        df = pd.DataFrame([
            {
                "Item No": "001",
                "Description": "Item 1",
                "Unit": "NOS",
                "Quantity": 10.0,
                "Rate": 95.0,  # Part-rate
                "Amount": 950.0,
            },
            {
                "Item No": "002",
                "Description": "Item 2",
                "Unit": "NOS",
                "Quantity": 5.0,
                "Rate": 200.0,  # Standard rate
                "Amount": 1000.0,
            },
            {
                "Item No": "003",
                "Description": "Item 3",
                "Unit": "NOS",
                "Quantity": 8.0,
                "Rate": 75.0,  # Part-rate
                "Amount": 600.0,
            },
        ])
        work_order_rates = {"001": 100.0, "002": 200.0, "003": 100.0}
        result = _detect_part_rates(df, work_order_rates)
        assert result.loc[0, 'Part_Rate'] == True
        assert result.loc[1, 'Part_Rate'] == False
        assert result.loc[2, 'Part_Rate'] == True
    
    def test_detect_part_rates_tolerance(self):
        """Test part-rate detection with small tolerance (0.01)"""
        df = pd.DataFrame([
            {
                "Item No": "001",
                "Description": "Item 1",
                "Unit": "NOS",
                "Quantity": 10.0,
                "Rate": 99.98,  # Below tolerance (100 - 0.01 = 99.99)
                "Amount": 999.8,
            },
            {
                "Item No": "002",
                "Description": "Item 2",
                "Unit": "NOS",
                "Quantity": 10.0,
                "Rate": 99.995,  # Within tolerance (>= 99.99)
                "Amount": 999.95,
            },
        ])
        work_order_rates = {"001": 100.0, "002": 100.0}
        result = _detect_part_rates(df, work_order_rates)
        assert result.loc[0, 'Part_Rate'] == True  # 99.98 < 100 - 0.01
        assert result.loc[1, 'Part_Rate'] == False  # 99.995 >= 100 - 0.01
    
    def test_format_rate_display_standard_rate(self):
        """Test rate display formatting for standard rate"""
        result = _format_rate_display(100.0, False)
        assert result == "₹100.00"
    
    def test_format_rate_display_part_rate(self):
        """Test rate display formatting for part-rate"""
        result = _format_rate_display(95.0, True)
        assert result == "₹95.00 (Part Rate)"
    
    def test_format_rate_display_decimal_precision(self):
        """Test rate display formatting with decimal precision"""
        result = _format_rate_display(123.456, False)
        assert result == "₹123.46"  # Rounded to 2 decimals
    
    def test_diff_log_part_rate_change(self):
        """Test change log includes part-rate information"""
        old_df = pd.DataFrame([{
            "Item No": "001",
            "Description": "Test Item",
            "Unit": "NOS",
            "Quantity": 10.0,
            "Rate": 100.0,
            "Amount": 1000.0,
        }])
        new_df = pd.DataFrame([{
            "Item No": "001",
            "Description": "Test Item",
            "Unit": "NOS",
            "Quantity": 10.0,
            "Rate": 95.0,  # Reduced to part-rate
            "Amount": 950.0,
        }])
        work_order_rates = {"001": 100.0}
        
        changes = _diff_log(old_df, new_df, work_order_rates)
        
        assert len(changes) == 1
        assert changes[0]["Item No"] == "001"
        assert changes[0]["Field"] == "Rate"
        assert changes[0]["Old"] == 100.0
        assert changes[0]["New"] == 95.0
        assert changes[0]["Reason"] == "Part-Rate Applied"
        assert changes[0]["Work_Order_Rate"] == 100.0
    
    def test_diff_log_rate_reduction_not_part_rate(self):
        """Test change log for rate reduction that's not a part-rate"""
        old_df = pd.DataFrame([{
            "Item No": "001",
            "Description": "Test Item",
            "Unit": "NOS",
            "Quantity": 10.0,
            "Rate": 100.0,
            "Amount": 1000.0,
        }])
        new_df = pd.DataFrame([{
            "Item No": "001",
            "Description": "Test Item",
            "Unit": "NOS",
            "Quantity": 10.0,
            "Rate": 95.0,  # Reduced but no work-order rate
            "Amount": 950.0,
        }])
        work_order_rates = {}  # No work-order rate
        
        changes = _diff_log(old_df, new_df, work_order_rates)
        
        assert len(changes) == 1
        assert changes[0]["Reason"] == "Rate Reduction"
        assert "Work_Order_Rate" not in changes[0]
