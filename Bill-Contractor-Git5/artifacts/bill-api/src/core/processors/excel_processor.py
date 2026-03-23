import pandas as pd
from typing import Dict, Any
import io
from core.processors.hierarchical_filter import apply_hierarchical_filtering

class ExcelProcessor:
    """Process Excel files and extract bill data"""
    
    def __init__(self):
        self.required_sheets = ['Title', 'Work Order', 'Bill Quantity']
        self.optional_sheets = ['Extra Items', 'Deviation']
        
        # Define column mappings for different naming conventions
        self.column_mappings = {
            'Work Order': {
                'Item No.': 'Item',  # Map expected to actual
                'Item': 'Item',
                'Description': 'Description',
                'Unit': 'Unit',
                'Quantity': 'Quantity',
                'Rate': 'Rate'
            },
            'Bill Quantity': {
                'Item No.': 'Item',  # Map expected to actual
                'Item': 'Item',
                'Description': 'Description',
                'Unit': 'Unit',
                'Quantity': 'Quantity',
                'Rate': 'Rate'
            },
            'Extra Items': {
                'Item No.': 'Item',  # Map expected to actual
                'Item': 'Item',
                'Description': 'Description',
                'Unit': 'Unit',
                'Quantity': 'Quantity',
                'Rate': 'Rate'
            }
        }
    
    def process_excel(self, file, required_cols_only=True) -> Dict[str, Any]:
        """
        Process Excel file and extract all necessary data with optimization
        
        Args:
            file: Uploaded file object or file path
            required_cols_only: Whether to load only required columns for better performance
            
        Returns:
            Dictionary containing processed data
        """
        # Store filename for reference
        filename = None
        if hasattr(file, 'name'):
            filename = file.name
        elif isinstance(file, (str, type(None))):
            filename = str(file) if file else None
        else:
            filename = "uploaded_file.xlsx"
        
        # Read Excel file
        if hasattr(file, 'read'):
            # It's a file-like object (BytesIO or file object)
            if isinstance(file, io.BytesIO):
                # It's already a BytesIO object
                excel_data = pd.ExcelFile(file, engine='openpyxl')
            else:
                # It's a file object
                file_bytes = file.read()
                # Reset file pointer if possible
                if hasattr(file, 'seek') and hasattr(file, 'tell'):
                    file.seek(0)
                
                # Try to determine the file type from the first bytes
                if file_bytes.startswith(b'PK'):
                    # Likely an .xlsx file
                    excel_data = pd.ExcelFile(io.BytesIO(file_bytes), engine='openpyxl')
                else:
                    # Likely an .xls file
                    excel_data = pd.ExcelFile(io.BytesIO(file_bytes), engine='xlrd')
        else:
            # It's a file path
            # Determine engine based on file extension
            file_str = str(file).lower()
            if file_str.endswith('.xlsx') or file_str.endswith('.xlsm'):
                excel_data = pd.ExcelFile(file, engine='openpyxl')
            else:
                excel_data = pd.ExcelFile(file, engine='xlrd')
        
        # Define required columns per sheet for optimization
        required_cols = {
            'Work Order': ['Item No.', 'Description', 'Unit', 'Quantity', 'Rate', 'Amount', 'BSR'],
            'Bill Quantity': ['Item No.', 'Description', 'Unit', 'Quantity', 'Rate', 'Amount', 'BSR'],
            'Extra Items': ['Item No.', 'Description', 'Unit', 'Quantity', 'Rate', 'Amount', 'BSR'],
        }
        
        processed_data = {}
        
        # Process Title sheet
        if 'Title' in excel_data.sheet_names:
            title_df = pd.read_excel(excel_data, 'Title', header=None)
            processed_data['title_data'] = self._process_title_sheet(title_df)
        else:
            processed_data['title_data'] = {}
        
        # Process Work Order sheet with column selection
        if 'Work Order' in excel_data.sheet_names:
            cols = required_cols['Work Order'] if required_cols_only else None
            work_order_df = self._read_sheet_with_flexible_columns(
                excel_data, 'Work Order', cols, self.column_mappings['Work Order']
            )
            processed_data['work_order_data'] = work_order_df
        else:
            processed_data['work_order_data'] = pd.DataFrame()
        
        # Process Bill Quantity sheet with column selection
        if 'Bill Quantity' in excel_data.sheet_names:
            cols = required_cols['Bill Quantity'] if required_cols_only else None
            bill_qty_df = self._read_sheet_with_flexible_columns(
                excel_data, 'Bill Quantity', cols, self.column_mappings['Bill Quantity']
            )
            processed_data['bill_quantity_data'] = bill_qty_df
        else:
            processed_data['bill_quantity_data'] = pd.DataFrame()
        
        # Process Extra Items sheet (optional) with column selection
        if 'Extra Items' in excel_data.sheet_names:
            cols = required_cols['Extra Items'] if required_cols_only else None
            extra_items_df = self._read_sheet_with_flexible_columns(
                excel_data, 'Extra Items', cols, self.column_mappings['Extra Items']
            )
            processed_data['extra_items_data'] = extra_items_df
        else:
            processed_data['extra_items_data'] = pd.DataFrame()
        
        # Process Deviation sheet (optional)
        if 'Deviation' in excel_data.sheet_names:
            deviation_df = pd.read_excel(excel_data, 'Deviation')
            processed_data['deviation_data'] = deviation_df
        else:
            processed_data['deviation_data'] = pd.DataFrame()
        
        # Apply hierarchical filtering
        filtered_data = apply_hierarchical_filtering(
            work_order_data=processed_data['work_order_data'],
            bill_quantity_data=processed_data['bill_quantity_data']
        )
        processed_data.update(filtered_data)
        
        # Add source filename for reference
        processed_data['source_filename'] = filename
        
        return processed_data
    
    def _read_sheet_with_flexible_columns(self, excel_data, sheet_name, required_cols, column_mapping):
        """
        Read Excel sheet with flexible column handling to support different naming conventions
        
        Args:
            excel_data: ExcelFile object
            sheet_name: Name of the sheet to read
            required_cols: List of required column names (expected names)
            column_mapping: Dictionary mapping expected names to actual names
            
        Returns:
            DataFrame with standardized column names
        """
        try:
            # First, read the sheet to see what columns are available
            df_sample = pd.read_excel(excel_data, sheet_name, nrows=1)
            available_columns = list(df_sample.columns)
            
            # Special handling for Extra Items sheet which has irregular structure
            if sheet_name == 'Extra Items':
                # For Extra Items, we'll just read the whole sheet without column selection
                df = pd.read_excel(excel_data, sheet_name)
                return df  # Don't rename columns for Extra Items as it has a different structure
            
            # If we're not selecting specific columns, just read the whole sheet
            if required_cols is None:
                df = pd.read_excel(excel_data, sheet_name)
                # Rename columns to standard names if needed
                return self._standardize_column_names(df, column_mapping)
            
            # Otherwise, map required columns to actual column names
            actual_cols = []
            for expected_col in required_cols:
                if expected_col in column_mapping:
                    actual_col_name = column_mapping[expected_col]
                    # Check if the actual column exists in the sheet
                    if actual_col_name in available_columns:
                        actual_cols.append(actual_col_name)
                    else:
                        # Try to find a column that might match (case-insensitive partial match)
                        found = False
                        for col in available_columns:
                            if expected_col.lower() in col.lower() or col.lower() in expected_col.lower():
                                actual_cols.append(col)
                                found = True
                                break
                        if not found:
                            # If we can't find it, we'll still try to read with the expected name
                            # This will raise an error which we'll catch below
                            actual_cols.append(expected_col)
                else:
                    actual_cols.append(expected_col)
            
            # Read the sheet with the mapped column names
            df = pd.read_excel(excel_data, sheet_name, usecols=actual_cols)
            
            # Rename columns to standard names
            return self._standardize_column_names(df, column_mapping)
            
        except ValueError as e:
            # If there's an error with column selection, fall back to reading all columns
            print(f"Warning: Column selection failed for sheet '{sheet_name}', reading all columns. Error: {e}")
            df = pd.read_excel(excel_data, sheet_name)
            # Don't rename columns for Extra Items as it has a different structure
            if sheet_name == 'Extra Items':
                return df
            return self._standardize_column_names(df, column_mapping)
    
    def _standardize_column_names(self, df, column_mapping):
        """
        Standardize column names to expected format
        
        Args:
            df: DataFrame with actual column names
            column_mapping: Dictionary mapping expected names to actual names
            
        Returns:
            DataFrame with standardized column names
        """
        # Create reverse mapping (actual -> expected)
        reverse_mapping = {v: k for k, v in column_mapping.items()}
        
        # Rename columns
        renamed_columns = {}
        for col in df.columns:
            if col in reverse_mapping:
                renamed_columns[col] = reverse_mapping[col]
            else:
                # Keep the original name if no mapping exists
                renamed_columns[col] = col
        
        df_renamed = df.rename(columns=renamed_columns)
        
        # Ensure Item No. column is treated as string
        if 'Item No.' in df_renamed.columns:
            df_renamed['Item No.'] = df_renamed['Item No.'].astype(str)
        
        return df_renamed
    
    def _process_title_sheet(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Process Title sheet which contains key-value pairs
        
        Expected format:
        Column 0: Key names
        Column 1: Values
        """
        title_data = {}
        
        # Date field keys that should be formatted
        date_fields = [
            'Date of written order to commence work :',
            'Date of written order to commence work',
            'St. date of Start :',
            'St. date of Start',
            'St. date of completion :',
            'St. date of completion',
            'Date of actual completion of work :',
            'Date of actual completion of work',
            'Date of measurement :',
            'Date of measurement',
        ]
        
        # Process all rows but specifically track first 20 for validation
        first_20_rows = {}
        
        for index, row in df.iterrows():
            if len(row) >= 2:
                key = str(row[0]).strip() if pd.notna(row[0]) else None
                value = row[1] if pd.notna(row[1]) else None
                
                if key and key != 'nan':
                    # Format date fields to remove timestamp
                    if key in date_fields and value is not None:
                        if isinstance(value, pd.Timestamp):
                            value = value.strftime('%d/%m/%Y')
                        elif hasattr(value, 'strftime'):
                            value = value.strftime('%d/%m/%Y')
                        else:
                            # Try to parse as string if it contains timestamp
                            value_str = str(value)
                            if ' ' in value_str and ':' in value_str:
                                # Has timestamp, extract date part only
                                try:
                                    from datetime import datetime
                                    dt = pd.to_datetime(value_str)
                                    value = dt.strftime('%d/%m/%Y')
                                except:
                                    # Keep original if parsing fails
                                    pass
                    
                    title_data[key] = value
                    
                    # Track first 20 rows for validation purposes
                    if index < 20:
                        first_20_rows[key] = value
        
        # Add metadata about first 20 rows processing
        title_data['_first_20_rows_processed'] = True
        title_data['_first_20_rows_count'] = len(first_20_rows)
        
        return title_data