"""
HTML Generator - Generate HTML documents from processed data
"""
import pandas as pd
from typing import Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from core.generators.base_generator import BaseGenerator
from core.processors.hierarchical_filter import filter_zero_hierarchy, parse_hierarchical_items, HierarchicalItem

class HTMLGenerator(BaseGenerator):
    """Generates HTML documents from processed Excel data using Jinja2 templates"""
    
    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        # Prepare data for templates
        self.template_data = self._prepare_template_data()
    
    def filter_zero_hierarchy(self, items: list) -> list:
        """
        Recursively filter items where all descendants have zero quantities
        
        Rules:
        - If item has qty > 0, keep it
        - If any descendant has qty > 0, keep parent
        - If all descendants are zero, remove parent
        """
        filtered_items = []
        
        for item in items:
            # Check if item or any descendant has non-zero quantity
            if self._has_nonzero_in_hierarchy(item):
                # Recursively filter children
                if 'children' in item and item['children']:
                    item['children'] = self.filter_zero_hierarchy(item['children'])
                filtered_items.append(item)
        
        return filtered_items
    
    def _has_nonzero_in_hierarchy(self, item: Dict) -> bool:
        """Check if item or any descendant has non-zero quantity"""
        # Check current item
        if item.get('quantity_since', 0) > 0 or item.get('quantity_upto', 0) > 0 or item.get('quantity', 0) > 0:
            return True
        
        # Check children recursively
        for child in item.get('children', []):
            if self._has_nonzero_in_hierarchy(child):
                return True
        
        return False
    
    def filter_zero_items_pandas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Use pandas boolean masking for faster filtering"""
        # Filter rows where quantity > 0 OR has children with quantity > 0
        if df is None or df.empty:
            return df
            
        # Make a copy to avoid modifying the original dataframe
        df_copy = df.copy()
        
        # Add Parent_Item column if it doesn't exist
        if 'Parent_Item' not in df_copy.columns:
            df_copy['Parent_Item'] = df_copy['Item No.'].apply(lambda x: '.'.join(x.split('.')[:-1]) if pd.notna(x) and '.' in str(x) else None)
        
        # Create mask for items with quantity > 0
        quantity_mask = (df_copy['Quantity'] > 0)
        
        # Create mask for items that are parents of items with quantity > 0
        parent_mask = df_copy['Item No.'].isin(
            df_copy[df_copy['Quantity'] > 0]['Parent_Item']
        )
        
        # Combine masks
        mask = quantity_mask | parent_mask
        
        return df_copy[mask]
    
    def _prepare_template_data(self) -> Dict[str, Any]:
        """Prepare data structure for Jinja2 templates with enhanced first 20 rows handling"""
        # Calculate totals and prepare structured data
        work_items = []
        total_amount = 0
        
        # IMPORTANT: First Page uses Bill Quantity data, NOT Work Order data
        # Process bill quantity data - check if it's a valid DataFrame
        if isinstance(self.bill_quantity_data, pd.DataFrame) and not self.bill_quantity_data.empty:
            for index, row in self.bill_quantity_data.iterrows():
                quantity_since = self._safe_float(row.get('Quantity Since', row.get('Quantity', 0)))
                rate = self._safe_float(row.get('Rate', 0))
                amount = quantity_since * rate
                total_amount += amount
                
                # Use BSR column as remark (there's no separate Remark column)
                bsr = row.get('BSR', '')
                
                # If BSR is not blank, use it as remark (without prefix)
                if pd.notna(bsr) and str(bsr).strip():
                    combined_remark = str(bsr).strip()
                else:
                    combined_remark = ''
                
                work_items.append({
                    'unit': row.get('Unit', ''),
                    'quantity_since': quantity_since,
                    'quantity_upto': self._safe_float(row.get('Quantity Upto', quantity_since)),
                    'item_no': self._safe_serial_no(row.get('Item No.', row.get('Item', ''))),
                    'description': row.get('Description', ''),
                    'rate': rate,
                    'amount_upto': amount,
                    'amount_since': amount,
                    'remark': combined_remark,
                    'children': []  # Initialize children for hierarchy
                })
        elif isinstance(self.work_order_data, pd.DataFrame) and not self.work_order_data.empty:
            # Fallback to work order data if bill quantity data is not available
            for index, row in self.work_order_data.iterrows():
                quantity_since = self._safe_float(row.get('Quantity Since', row.get('Quantity', 0)))
                rate = self._safe_float(row.get('Rate', 0))
                amount = quantity_since * rate
                total_amount += amount
                
                # Use BSR column as remark (if available in work order)
                bsr = row.get('BSR', '')
                
                # If BSR is not blank, use it as remark (without prefix)
                if pd.notna(bsr) and str(bsr).strip():
                    combined_remark = str(bsr).strip()
                else:
                    combined_remark = ''
                
                work_items.append({
                    'unit': row.get('Unit', ''),
                    'quantity_since': quantity_since,
                    'quantity_upto': self._safe_float(row.get('Quantity Upto', quantity_since)),
                    'item_no': self._safe_serial_no(row.get('Item No.', row.get('Item', ''))),
                    'description': row.get('Description', ''),
                    'rate': rate,
                    'amount_upto': amount,
                    'amount_since': amount,
                    'remark': combined_remark,
                    'children': []  # Initialize children for hierarchy
                })
        
        # Process extra items
        extra_items = []
        extra_total = 0
        extra_grand_total = 0  # This will include premium
        extra_premium = 0  # Initialize
        
        if isinstance(self.extra_items_data, pd.DataFrame) and not self.extra_items_data.empty:
            # Extra Items sheet has irregular structure
            # Structure: Row 5 = headers (S.No., Particulars, Qty., unit, Rate, Amount)
            # Rows 6-11 = actual items (E-01, E-02, etc.)
            # Row 12 = Total, Row 13 = Add Tender Premium, Row 14 = Grand Total
            
            # Parse individual extra item rows
            # Start from row index 5 (after header row at index 4)
            for index, row in self.extra_items_data.iterrows():
                if index < 5:  # Skip header rows
                    continue
                
                # Get item number from column 0 (Unnamed: 0)
                item_no = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
                
                # Stop when we reach Total/Grand Total rows (item_no will be NaN or empty)
                if not item_no or item_no == 'nan' or 'total' in item_no.lower():
                    break
                
                # Check if this is an actual extra item (E-01, E-02, etc.)
                if item_no.startswith('E-') or item_no.startswith('e-'):
                    # Column 1 (Unnamed: 1): BSR Reference
                    bsr = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ''
                    
                    # Column 2 (Unnamed: 2): Description
                    description = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ''
                    
                    # Column 3 (EXTRA ITEM SLIP): Quantity
                    quantity = self._safe_float(row.iloc[3] if len(row) > 3 else 0)
                    
                    # Column 4 (Unnamed: 4): Unit
                    unit = str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else ''
                    
                    # Column 5 (Unnamed: 5): Rate
                    rate = self._safe_float(row.iloc[5] if len(row) > 5 else 0)
                    
                    # Column 6 (Unnamed: 6): Amount
                    amount = self._safe_float(row.iloc[6] if len(row) > 6 else 0)
                    
                    # Column 7 (Unnamed: 7): Remarks (if exists, otherwise use BSR)
                    remark_col = str(row.iloc[7]) if len(row) > 7 and pd.notna(row.iloc[7]) else ''
                    
                    # Use BSR if remark is empty, otherwise use remark
                    if remark_col.strip():
                        remark = remark_col.strip()
                    elif bsr.strip():
                        remark = bsr.strip()
                    else:
                        remark = ''
                    
                    # Add to extra items list
                    extra_items.append({
                        'unit': unit,
                        'quantity': quantity,
                        'item_no': item_no,
                        'description': description,
                        'rate': rate,
                        'amount': amount,
                        'remark': remark,
                        'children': []  # Initialize children for hierarchy
                    })
                    
                    extra_total += amount
            
            # Now find Grand Total from the sheet for verification
            for index, row in self.extra_items_data.iterrows():
                row_text = ' '.join([str(v) for v in row.values if pd.notna(v)]).strip()
                if 'Grand Total' in row_text or 'grand total' in row_text.lower():
                    # Found Grand Total row - extract the amount from column 6
                    if len(row) > 6 and pd.notna(row.iloc[6]):
                        extra_grand_total = float(row.iloc[6])
                    break
            
            # Calculate premium (difference between grand total and total)
            if extra_grand_total > 0 and extra_total > 0:
                extra_premium = extra_grand_total - extra_total
            else:
                # Fallback: calculate premium from title data
                tender_premium_percent = self._safe_float(self.title_data.get('TENDER PREMIUM %', 0))
                extra_premium = extra_total * (tender_premium_percent / 100)
                extra_grand_total = extra_total + extra_premium
        
        # CRITICAL FIX: Do NOT filter items here - filtering removes parent items
        # The template will handle display logic based on quantities
        # Hierarchical structure is maintained in the Excel data itself (NaN item numbers for sub-items)
        work_items_filtered = work_items  # No filtering
        extra_items_filtered = extra_items  # No filtering
        
        # Calculate premiums for work order items
        tender_premium_percent = self._safe_float(self.title_data.get('TENDER PREMIUM %', 0))
        premium_type = str(self.title_data.get('Premium Type', 'Above')).strip().lower()
        
        premium_amount = total_amount * (tender_premium_percent / 100)
        
        # IMPORTANT: grand_total is sum of items WITHOUT premium
        # Premium is added separately to get payable_amount
        grand_total = total_amount
        
        # Apply premium based on type: Above = add, Below = subtract
        if premium_type == 'below':
            payable_amount = grand_total - premium_amount
            premium_amount = -premium_amount  # Make it negative for display
        else:  # Default to 'above'
            payable_amount = grand_total + premium_amount
        
        # IMPORTANT: Add extra items to get the total bill amount
        # This is what should appear in First Page, Deviation, and Certificate III
        total_bill_amount = payable_amount + extra_grand_total
        
        # Calculate deductions and final amounts (based on total including extra items)
        liquidated_damages = self._safe_float(self.title_data.get('Liquidated Damages', 0))
        sd_amount = total_bill_amount * 0.10  # Security Deposit 10%
        it_amount = total_bill_amount * 0.02  # Income Tax 2%
        gst_amount = total_bill_amount * 0.02  # GST 2%
        
        # IMPORTANT: GST must always be even number - round up if odd
        gst_amount_rounded = round(gst_amount)
        if gst_amount_rounded % 2 != 0:  # If odd, add 1 to make it even
            gst_amount_rounded += 1
        gst_amount = float(gst_amount_rounded)
        
        lc_amount = total_bill_amount * 0.01  # Labour Cess 1%
        total_deductions = sd_amount + it_amount + gst_amount + lc_amount + liquidated_damages
        
        # Get last bill amount
        last_bill_amount = self._safe_float(self.title_data.get('Amount Paid Vide Last Bill', 
                                                                 self.title_data.get('amount_paid_last_bill', 0)))
        net_payable = total_bill_amount - last_bill_amount
        
        # Calculate totals data structure
        totals = {
            'grand_total': grand_total,  # Sum of items WITHOUT premium
            'work_order_amount': total_amount,
            'tender_premium_percent': tender_premium_percent / 100,
            'tender_premium_amount': premium_amount,
            'final_total': payable_amount,
            'extra_items_sum': extra_grand_total,
            'sd_amount': sd_amount,
            'it_amount': it_amount,
            'gst_amount': gst_amount,
            'lc_amount': lc_amount,
            'liquidated_damages': liquidated_damages,
            'total_deductions': total_deductions,
            'last_bill_amount': last_bill_amount,
            'net_payable': net_payable,
            'payable': payable_amount,  # Grand Total + Premium
            'excess_amount': 0,  # Will be calculated from deviation data
            'excess_premium': 0,
            'excess_total': 0,
            'saving_amount': 0,
            'saving_premium': 0,
            'saving_total': 0,
            'net_difference': 0,
            'premium': {
                'percent': tender_premium_percent / 100 if tender_premium_percent > 0 else 0,
                'amount': premium_amount
            }
        }
        
        # Prepare items data structure for templates (using filtered items)
        items = []
        extra_items_only = []  # Separate list for Extra Items template
        
        for item in work_items_filtered:
            # Skip rows with all zeros (empty rows)
            qty_since = item.get('quantity_since', 0) or 0
            qty_upto = item.get('quantity_upto', 0) or 0
            rate = item.get('rate', 0) or 0
            amount_upto = item.get('amount_upto', 0) or 0
            amount_since = item.get('amount_since', 0) or 0
            description = str(item.get('description', '')).strip()
            
            # CRITICAL: Only add if quantity is non-zero OR it's a parent item (has description but no rate)
            # This filters out zero-quantity items while keeping parent/header items
            is_parent_item = (rate == 0 and description != '')
            has_quantity = (qty_since != 0 or qty_upto != 0)
            
            if has_quantity or is_parent_item:
                items.append({
                    'unit': item['unit'],
                    'quantity_since_last': qty_since,
                    'quantity_upto_date': qty_upto,
                    'serial_no': item['item_no'],
                    'description': description,
                    'rate': rate,
                    'amount': amount_upto,
                    'amount_previous': amount_since,
                    'remark': item['remark']
                })
        
        # Add separator row before extra items if there are any
        if extra_items_filtered:
            items.append({
                'unit': '',
                'quantity_since_last': 0,
                'quantity_upto_date': 0,
                'serial_no': '',
                'description': 'EXTRA ITEM/S',
                'rate': 0,
                'amount': 0,
                'amount_previous': 0,
                'remark': '',
                'is_separator': True,  # Flag to identify separator row
                'bold': True,
                'underline': True
            })
        
        # Add filtered extra items to the items list
        for item in extra_items_filtered:
            qty = item.get('quantity', 0) or 0
            rate = item.get('rate', 0) or 0
            amount = item.get('amount', 0) or 0
            description = str(item.get('description', '')).strip()
            
            # CRITICAL: Only add if quantity is non-zero
            # Extra items with zero quantity should not appear
            if qty != 0:
                extra_item_data = {
                    'unit': item['unit'],
                    'quantity_since_last': qty,
                    'quantity_upto_date': qty,
                    'serial_no': item['item_no'],
                    'description': description,
                    'rate': rate,
                    'amount': amount,
                    'amount_previous': amount,
                    'remark': item['remark']
                }
                items.append(extra_item_data)
                extra_items_only.append(extra_item_data)  # Add to extra items only list
        
        # Prepare deviation data (DO NOT use filtered items - show ALL items with non-zero bill qty)
        deviation_items = []
        
        # IMPORTANT: Deviation compares Work Order quantities vs Bill Quantity quantities
        # Use Bill Quantity data for actual executed quantities
        if isinstance(self.bill_quantity_data, pd.DataFrame) and not self.bill_quantity_data.empty:
            # Process bill quantity data for deviation - match row by row with work order
            for index, row in self.bill_quantity_data.iterrows():
                item_no = str(row.get('Item No.', row.get('Item', '')))
                qty_bill = self._safe_float(row.get('Quantity', 0))
                rate = self._safe_float(row.get('Rate', 0))
                description = str(row.get('Description', '')).strip()
                
                # CRITICAL: Skip summary rows (Total, Add Tender Premium, Grand Total)
                description_lower = description.lower()
                is_summary_row = (
                    description_lower == 'total' or
                    'premium' in description_lower or
                    'grand total' in description_lower
                )
                
                if is_summary_row:
                    continue  # Skip this row
                
                # Get corresponding Work Order quantity by matching row index
                qty_wo = 0.0
                if isinstance(self.work_order_data, pd.DataFrame) and not self.work_order_data.empty:
                    if index < len(self.work_order_data):
                        wo_row = self.work_order_data.iloc[index]
                        qty_wo = self._safe_float(wo_row.get('Quantity', 0))
                
                # CRITICAL FIX: Include item if:
                # 1. It has non-zero bill quantity OR non-zero work order quantity
                # 2. OR it's a parent item (rate=0 but has description) - needed for hierarchical structure
                is_parent_item = (rate == 0 and description != '')
                has_quantity = (qty_bill > 0 or qty_wo > 0)
                
                if has_quantity or is_parent_item:
                    amt_wo = qty_wo * rate
                    amt_bill = qty_bill * rate
                    
                    # Deviation remarks are for excess/saving reasons, not BSR
                    # BSR is only for First Page
                    remark = ''
                    
                    deviation_items.append({
                        'serial_no': self._safe_serial_no(row.get('Item No.', row.get('Item', ''))),
                        'description': description,
                        'unit': row.get('Unit', ''),
                        'qty_wo': qty_wo,
                        'rate': rate,
                        'amt_wo': amt_wo,
                        'qty_bill': qty_bill,
                        'amt_bill': amt_bill,
                        'excess_qty': max(0, qty_bill - qty_wo),
                        'excess_amt': max(0, amt_bill - amt_wo),
                        'saving_qty': max(0, qty_wo - qty_bill),
                        'saving_amt': max(0, amt_wo - amt_bill),
                        'remark': remark
                    })
        
        # Add separator row before extra items in deviation if there are any
        if extra_items_filtered:
            deviation_items.append({
                'serial_no': '',
                'description': 'EXTRA ITEM/S',
                'unit': '',
                'qty_wo': 0,
                'rate': 0,
                'amt_wo': 0,
                'qty_bill': 0,
                'amt_bill': 0,
                'excess_qty': 0,
                'excess_amt': 0,
                'saving_qty': 0,
                'saving_amt': 0,
                'remark': '',
                'is_separator': True,
                'bold': True,
                'underline': True
            })
        
        # Add extra items to deviation (they have qty_wo=0 since they're not in work order)
        for item in extra_items_filtered:
            qty = item.get('quantity', 0) or 0
            rate = item.get('rate', 0) or 0
            amount = item.get('amount', 0) or 0
            description = str(item.get('description', '')).strip()
            
            # Only add if there's actual data
            if qty != 0 or rate != 0 or amount != 0 or description:
                deviation_items.append({
                    'serial_no': item['item_no'],
                    'description': description,
                    'unit': item['unit'],
                    'qty_wo': 0,  # Not in work order
                    'rate': rate,
                    'amt_wo': 0,  # Not in work order
                    'qty_bill': qty,
                    'amt_bill': amount,
                    'excess_qty': qty,  # All quantity is excess since not in WO
                    'excess_amt': amount,  # All amount is excess since not in WO
                    'saving_qty': 0,
                    'saving_amt': 0,
                    'remark': ''  # Extra items remarks should be blank
                })
        
        # Calculate deviation totals from deviation_items
        total_wo_amt = sum(item['amt_wo'] for item in deviation_items if not item.get('is_separator'))
        total_bill_amt = sum(item['amt_bill'] for item in deviation_items if not item.get('is_separator'))
        total_excess_amt = sum(item['excess_amt'] for item in deviation_items if not item.get('is_separator'))
        total_saving_amt = sum(item['saving_amt'] for item in deviation_items if not item.get('is_separator'))
        
        # Calculate premium for each column
        premium_wo = total_wo_amt * (tender_premium_percent / 100)
        premium_bill = total_bill_amt * (tender_premium_percent / 100)
        premium_excess = total_excess_amt * (tender_premium_percent / 100)
        premium_saving = total_saving_amt * (tender_premium_percent / 100)
        
        # Grand totals with premium
        grand_total_wo = total_wo_amt + premium_wo
        grand_total_bill = total_bill_amt + premium_bill
        grand_total_excess = total_excess_amt + premium_excess
        grand_total_saving = total_saving_amt + premium_saving
        
        # Net difference and percentage calculations
        net_difference = grand_total_bill - grand_total_wo
        is_saving = net_difference < 0
        
        # Overall percentage deviation (Bill vs WO)
        percentage_deviation = (net_difference / grand_total_wo * 100) if grand_total_wo > 0 else 0
        
        # Excess percentage (Excess / WO)
        excess_percentage = (grand_total_excess / grand_total_wo * 100) if grand_total_wo > 0 else 0
        
        # Saving percentage (Saving / WO)
        saving_percentage = (grand_total_saving / grand_total_wo * 100) if grand_total_wo > 0 else 0
        
        # Prepare summary data
        summary = {
            'work_order_total': total_wo_amt,
            'executed_total': total_bill_amt,
            'overall_excess': total_excess_amt,
            'overall_saving': total_saving_amt,
            'tender_premium_f': premium_wo,
            'tender_premium_h': premium_bill,
            'tender_premium_j': premium_excess,
            'tender_premium_l': premium_saving,
            'grand_total_f': grand_total_wo,
            'grand_total_h': grand_total_bill,
            'grand_total_j': grand_total_excess,
            'grand_total_l': grand_total_saving,
            'net_difference': abs(net_difference),
            'percentage_deviation': abs(percentage_deviation),
            'excess_percentage': excess_percentage,
            'saving_percentage': saving_percentage,
            'is_saving': is_saving,
            'premium': {
                'percent': tender_premium_percent / 100 if tender_premium_percent > 0 else 0,
                'amount': premium_amount
            }
        }
        
        # Ensure all data is available for templates with enhanced first 20 rows handling
        template_data = {
            'title_data': self.title_data,
            'work_items': work_items_filtered,  # Use filtered items
            'extra_items': extra_items_filtered,  # Use filtered items
            'extra_items_only': extra_items_only,  # ONLY extra items for Extra Items template
            'totals': totals,
            'current_date': datetime.now().strftime('%d/%m/%Y'),
            'total_amount': total_amount,
            'tender_premium_percent': tender_premium_percent,
            'premium_amount': premium_amount,
            'grand_total': payable_amount,
            'extra_total': extra_total,
            'extra_premium': extra_premium,
            'extra_grand_total': extra_grand_total,
            'final_total': payable_amount + extra_grand_total,
            'payable_words': self._number_to_words(int(net_payable)),
            'notes': ['Work completed as per schedule', 'All measurements verified', 'Quality as per specifications'],
            'items': items,
            'deviation_items': deviation_items,
            'summary': summary,
            'agreement_no': self.title_data.get('Work Order No', ''),
            'name_of_work': self.title_data.get('Project Name', ''),
            'name_of_firm': self.title_data.get('Contractor Name', ''),
            'date_commencement': self.title_data.get('Date of Commencement', ''),
            'date_completion': self.title_data.get('Date of Completion', ''),
            'actual_completion': self.title_data.get('Actual Date of Completion', ''),
            'work_order_amount': total_amount,
            'bill_grand_total': payable_amount,
            'extra_items_sum': extra_grand_total,
            'delay_days': self._calculate_delay_days(),
            'header': [],
            'measurement_officer': self.title_data.get('Measurement Officer', 'Junior Engineer'),
            'measurement_date': self.title_data.get('Measurement Date', datetime.now().strftime('%d/%m/%Y')),
            'measurement_book_page': self.title_data.get('Measurement Book Page', '04-20'),
            'measurement_book_no': self.title_data.get('Measurement Book No', '887'),
            'officer_name': self.title_data.get('Officer Name', 'Name of Officer'),
            'officer_designation': self.title_data.get('Officer Designation', 'Assistant Engineer'),
            'bill_date': self.title_data.get('Bill Date', '__/__/____'),
            'authorising_officer_name': self.title_data.get('Authorising Officer Name', 'Name of Authorising Officer'),
            'authorising_officer_designation': self.title_data.get('Authorising Officer Designation', 'Executive Engineer'),
            'authorisation_date': self.title_data.get('Authorisation Date', '__/__/____'),
            'payable_amount': net_payable,
            'amount_words': self._number_to_words(int(payable_amount + extra_grand_total)),
            # Enhanced first 20 rows data for validation
            'first_20_rows_processed': self.title_data.get('_first_20_rows_processed', False),
            'first_20_rows_count': self.title_data.get('_first_20_rows_count', 0),
            # Source filename for reference
            'source_filename': self.data.get('source_filename', 'Unknown')
        }
        
        # No title image data URI needed - using direct HTML title instead
        
        # Add header data if available
        if 'header' in self.title_data:
            template_data['header'] = self.title_data['header']
        
        return template_data
    
    def _render_template(self, template_name: str) -> str:
        """Render a Jinja2 template with the prepared data"""
        try:
            # Use cached template
            template = self.get_template(template_name)
            # Pass both the template data and the original data to the template
            render_data = {'data': self.template_data}
            render_data.update(self.template_data)
            return template.render(**render_data)
        except Exception as e:
            print(f"Failed to render template {template_name}: {e}")
            raise
    
    def generate_all_documents(self) -> Dict[str, str]:
        """
        Generate all required documents using Jinja2 templates with parallel processing
        
        Returns:
            Dictionary containing all generated documents in HTML format
        """
        documents = {}
        
        try:
            # Check if this is a FINAL bill
            bill_serial = self.title_data.get('Serial No. of this bill :', self.title_data.get('Serial No. of this bill', ''))
            is_final_bill = 'final' in str(bill_serial).lower()
            
            # Define document specifications for parallel processing
            document_specs = [
                ('First Page Summary', 'first_page.html'),
                ('BILL SCRUTINY SHEET', 'note_sheet_new.html'),
                ('Certificate II', 'certificate_ii.html'),
                ('Certificate III', 'certificate_iii.html'),
            ]
            
            # Only generate Deviation Statement for FINAL bills
            if is_final_bill:
                document_specs.insert(1, ('Deviation Statement', 'deviation_statement.html'))
            
            # Only generate Extra Items document if there are extra items - ADD AT END
            if self._has_extra_items():
                document_specs.append(('Extra Items Statement', 'extra_items.html'))
            
            # Parallel generation using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Submit all rendering tasks
                futures = {
                    executor.submit(self._render_template, template): name 
                    for name, template in document_specs
                }
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(futures):
                    name = futures[future]
                    try:
                        documents[name] = future.result()
                    except Exception as e:
                        print(f"Failed to generate document {name}: {e}")
                        # Fallback to sequential generation if parallel fails
                        template_name = dict(document_specs)[name]
                        documents[name] = self._render_template(template_name)
                        
        except Exception as e:
            print(f"Parallel template rendering failed, falling back to sequential generation: {e}")
            # Fallback to sequential generation if parallel processing fails
            try:
                # Check if this is a FINAL bill
                bill_serial = self.title_data.get('Serial No. of this bill :', self.title_data.get('Serial No. of this bill', ''))
                is_final_bill = 'final' in str(bill_serial).lower()
                
                documents['First Page Summary'] = self._render_template('first_page.html')
                
                # Only generate Deviation Statement for FINAL bills
                if is_final_bill:
                    documents['Deviation Statement'] = self._render_template('deviation_statement.html')
                
                documents['BILL SCRUTINY SHEET'] = self._render_template('note_sheet_new.html')
                
                # Only generate Extra Items document if there are extra items
                if self._has_extra_items():
                    documents['Extra Items Statement'] = self._render_template('extra_items.html')
                
                documents['Certificate II'] = self._render_template('certificate_ii.html')
                documents['Certificate III'] = self._render_template('certificate_iii.html')
            except Exception as fallback_error:
                print(f"Sequential template rendering also failed: {fallback_error}")
                # Check if this is a FINAL bill
                bill_serial = self.title_data.get('Serial No. of this bill :', self.title_data.get('Serial No. of this bill', ''))
                is_final_bill = 'final' in str(bill_serial).lower()
                
                # Final fallback to programmatic generation
                documents['First Page Summary'] = self._generate_first_page()
                
                # Only generate Deviation Statement for FINAL bills
                if is_final_bill:
                    documents['Deviation Statement'] = self._generate_deviation_statement()
                
                documents['BILL SCRUTINY SHEET'] = self._generate_final_bill_scrutiny()
                
                # Only generate Extra Items document if there are extra items
                if self._has_extra_items():
                    documents['Extra Items Statement'] = self._generate_extra_items_statement()
                
                documents['Certificate II'] = self._generate_certificate_ii()
                documents['Certificate III'] = self._generate_certificate_iii()
        
        return documents
    
    def _generate_first_page(self) -> str:
        """Generate First Page Summary document"""
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>First Page Summary</title>
            <style>
                @page {{ 
                    size: A4; 
                    margin: 10mm;
                }}
                * {{ box-sizing: border-box; }}
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 10mm;
                    font-size: 10pt; 
                }}
                .header {{ text-align: center; margin-bottom: 8px; }}
                .subtitle {{ font-size: 11pt; margin: 3px 0; }}
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 6px 0; 
                    table-layout: fixed;
                }}
                thead {{ display: table-header-group; }}
                tr, img {{ break-inside: avoid; }}
                th, td {{ 
                    border: 1px solid #000; 
                    padding: 4px; 
                    text-align: left; 
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    vertical-align: top;
                }}
                th {{ background-color: #f0f0f0; font-weight: bold; }}
                .amount {{ text-align: right; }}
                .total-row {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="subtitle">First Page Summary</div>
                <div class="subtitle">Date: {current_date}</div>
            </div>
            
            <h3>Project Information</h3>
            <table>
                <tr><td><strong>Project Name:</strong></td><td>{self.title_data.get('Project Name', 'N/A')}</td></tr>
                <tr><td><strong>Contract No:</strong></td><td>{self.title_data.get('Contract No', 'N/A')}</td></tr>
                <tr><td><strong>Work Order No:</strong></td><td>{self.title_data.get('Work Order No', 'N/A')}</td></tr>
            </table>
            
            <h3>Work Items Summary</h3>
            <table>
                <thead>
                    <tr>
                        <th style="width: 10.06mm;">Unit</th>
                        <th style="width: 13.76mm;">Quantity executed (or supplied) since last certificate</th>
                        <th style="width: 13.76mm;">Quantity executed (or supplied) upto date as per MB</th>
                        <th style="width: 9.55mm;">S. No.</th>
                        <th style="width: 63.83mm;">Item of Work supplies (Grouped under "sub-head" and "sub work" of estimate)</th>
                        <th style="width: 13.16mm;">Rate</th>
                        <th style="width: 19.53mm;">Upto date Amount</th>
                        <th style="width: 15.15mm;">Amount Since previous bill (Total for each sub-head)</th>
                        <th style="width: 11.96mm;">Remarks</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Get tender premium percentage from title data first (needed for calculations)
        tender_premium_percent = self._safe_float(self.title_data.get('TENDER PREMIUM %', 
                                                                       self.title_data.get('Tender Premium %', 0)))
        
        # Add work order items - CRITICAL: Use Bill Quantity data for executed quantities
        total_amount = 0
        running_total = 0
        
        # Use Bill Quantity data if available, otherwise fallback to Work Order data
        data_source = self.bill_quantity_data if isinstance(self.bill_quantity_data, pd.DataFrame) and not self.bill_quantity_data.empty else self.work_order_data
        
        for index, row in data_source.iterrows():
            description = str(row.get('Description', '')).strip()
            
            # Check if this is a summary row (Total, Add Tender Premium, Grand Total)
            is_total_row = description.lower() == 'total'
            is_premium_row = 'premium' in description.lower() and 'add' in description.lower()
            is_grand_total_row = 'grand' in description.lower() and 'total' in description.lower()
            
            if is_total_row:
                # This is the TOTAL row - show running total
                qty_since_display = ""
                qty_upto_display = ""
                rate_display = ""
                amt_upto_display = f"{running_total:.2f}"
                amt_since_display = f"{running_total:.2f}"
                total_amount = running_total
            elif is_premium_row:
                # This is the TENDER PREMIUM row
                premium_amount = running_total * (tender_premium_percent / 100)
                qty_since_display = ""
                qty_upto_display = ""
                rate_display = f"{tender_premium_percent:.2f}%"
                amt_upto_display = f"{premium_amount:.2f}"
                amt_since_display = f"{premium_amount:.2f}"
                total_amount += premium_amount
                running_total += premium_amount
            elif is_grand_total_row:
                # This is the GRAND TOTAL row
                qty_since_display = ""
                qty_upto_display = ""
                rate_display = ""
                amt_upto_display = f"{running_total:.2f}"
                amt_since_display = f"{running_total:.2f}"
            else:
                # Regular work item - CRITICAL FIX: Get quantities from Bill Quantity sheet
                # Find matching row in bill_quantity_data
                bq_row = None
                if isinstance(self.bill_quantity_data, pd.DataFrame) and not self.bill_quantity_data.empty:
                    wo_item = row.get('Item No.', row.get('Item', ''))
                    bq_item_col = 'Item No.' if 'Item No.' in self.bill_quantity_data.columns else 'Item'
                    matching_rows = self.bill_quantity_data[
                        self.bill_quantity_data[bq_item_col] == wo_item
                    ]
                    if isinstance(matching_rows, pd.DataFrame) and not matching_rows.empty:
                        bq_row = matching_rows.iloc[0]
                
                # Use Bill Quantity data for executed quantities, fallback to Work Order if not found
                if bq_row is not None:
                    qty_since = self._safe_float(bq_row.get('Quantity Since', bq_row.get('Quantity', 0)))
                    qty_upto = self._safe_float(bq_row.get('Quantity Upto', qty_since))
                else:
                    # Fallback to work order quantities if bill quantity not found
                    qty_since = self._safe_float(row.get('Quantity Since', row.get('Quantity', 0)))
                    qty_upto = self._safe_float(row.get('Quantity Upto', qty_since))
                
                rate = self._safe_float(row.get('Rate', 0))
                amt_upto = qty_upto * rate
                amt_since = qty_since * rate
                
                # Update running totals
                running_total += amt_upto
                total_amount += amt_upto
                
                # Format for display (empty string if zero)
                qty_since_display = f"{qty_since:.2f}" if qty_since != 0 else ""
                qty_upto_display = f"{qty_upto:.2f}" if qty_upto != 0 else ""
                rate_display = f"{rate:.2f}" if rate != 0 else ""
                amt_upto_display = f"{amt_upto:.2f}" if amt_upto != 0 else ""
                amt_since_display = f"{amt_since:.2f}" if amt_since != 0 else ""
            
            html_content += f"""
                    <tr>
                        <td>{row.get('Unit', '')}</td>
                        <td class="amount">{qty_since_display}</td>
                        <td class="amount">{qty_upto_display}</td>
                        <td>{self._safe_serial_no(row.get('Item No.', row.get('Item', '')))}</td>
                        <td>{description}</td>
                        <td class="amount">{rate_display}</td>
                        <td class="amount">{amt_upto_display}</td>
                        <td class="amount">{amt_since_display}</td>
                        <td>{row.get('Remark', '')}</td>
                    </tr>
            """
        
        html_content += f"""
                </tbody>
            </table>
            
            <!-- Closure Lines -->
            <div style="margin-top: 40px; width: 100%; display: table;">
                <div style="display: table-row;">
                    <div style="display: table-cell; width: 50%; padding: 10px; vertical-align: top;">
                        <div style="border-top: 2px solid #000; padding-top: 5px; text-align: center;">
                            <strong>Prepared by</strong><br>
                            <span style="font-size: 8pt;">Assistant Engineer</span><br>
                            <span style="font-size: 8pt;">Date: {current_date}</span>
                        </div>
                    </div>
                    <div style="display: table-cell; width: 50%; padding: 10px; vertical-align: top;">
                        <div style="border-top: 2px solid #000; padding-top: 5px; text-align: center;">
                            <strong>Checked & Approved by</strong><br>
                            <span style="font-size: 8pt;">Executive Engineer</span><br>
                            <span style="font-size: 8pt;">Date: {current_date}</span>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_deviation_statement(self) -> str:
        """Generate Deviation Statement document"""
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Deviation Statement</title>
            <style>
                @page {{ 
                    size: A4 landscape; 
                    margin: 10mm;
                }}
                * {{ box-sizing: border-box; }}
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 10mm;
                    font-size: 9pt; 
                }}
                .header {{ text-align: center; margin-bottom: 8px; }}
                .subtitle {{ font-size: 10pt; margin: 3px 0; }}
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 4px 0; 
                    table-layout: fixed;
                }}
                thead {{ display: table-header-group; }}
                tr, img {{ break-inside: avoid; }}
                th, td {{ 
                    border: 1px solid #000; 
                    padding: 3px; 
                    text-align: left; 
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    font-size: 8.5pt;
                }}
                th {{ background-color: #f0f0f0; font-weight: bold; }}
                .amount {{ text-align: right; }}
                
                /* Column-specific widths for Deviation Statement (percentages) */
                th:nth-child(1), td:nth-child(1) {{ width: 2.20%; }}   /* Item No */
                th:nth-child(2), td:nth-child(2) {{ width: 43.22%; }}  /* Description */
                th:nth-child(3), td:nth-child(3) {{ width: 3.85%; }}   /* Unit */
                th:nth-child(4), td:nth-child(4) {{ width: 3.85%; }}   /* Qty WO */
                th:nth-child(5), td:nth-child(5) {{ width: 3.85%; }}   /* Rate */
                th:nth-child(6), td:nth-child(6) {{ width: 3.85%; }}   /* Amt WO */
                th:nth-child(7), td:nth-child(7) {{ width: 3.85%; }}   /* Qty Exec */
                th:nth-child(8), td:nth-child(8) {{ width: 3.85%; }}   /* Amt Exec */
                th:nth-child(9), td:nth-child(9) {{ width: 3.85%; }}   /* Excess Qty */
                th:nth-child(10), td:nth-child(10) {{ width: 3.85%; }} /* Excess Amt */
                th:nth-child(11), td:nth-child(11) {{ width: 3.85%; }} /* Saving Qty */
                th:nth-child(12), td:nth-child(12) {{ width: 3.85%; }} /* Saving Amt */
                th:nth-child(13), td:nth-child(13) {{ width: 17.58%; }} /* Remarks */
            </style>
        </head>
        <body>
            <div class="header">
                <div class="subtitle">Deviation Statement</div>
                <div class="subtitle">Date: {current_date}</div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th style="width: 6mm;">ITEM No.</th>
                        <th style="width: 118mm;">Description</th>
                        <th style="width: 10.5mm;">Unit</th>
                        <th style="width: 10.5mm;">Qty as per Work Order</th>
                        <th style="width: 10.5mm;">Rate</th>
                        <th style="width: 10.5mm;">Amt as per Work Order Rs.</th>
                        <th style="width: 10.5mm;">Qty Executed</th>
                        <th style="width: 10.5mm;">Amt as per Executed Rs.</th>
                        <th style="width: 10.5mm;">Excess Qty</th>
                        <th style="width: 10.5mm;">Excess Amt Rs.</th>
                        <th style="width: 10.5mm;">Saving Qty</th>
                        <th style="width: 10.5mm;">Saving Amt Rs.</th>
                        <th style="width: 48mm;">REMARKS/ REASON.</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Compare work order with bill quantity data
        for index, wo_row in self.work_order_data.iterrows():
            bq_row = None
            if isinstance(self.bill_quantity_data, pd.DataFrame) and not self.bill_quantity_data.empty:
                wo_item = wo_row.get('Item No.', wo_row.get('Item', ''))
                bq_item_col = 'Item No.' if 'Item No.' in self.bill_quantity_data.columns else 'Item'
                matching_rows = self.bill_quantity_data[
                    self.bill_quantity_data[bq_item_col] == wo_item
                ]
                if isinstance(matching_rows, pd.DataFrame) and not matching_rows.empty:
                    bq_row = matching_rows.iloc[0]
            
            wo_qty = self._safe_float(wo_row.get('Quantity Since', wo_row.get('Quantity', 0)))
            wo_rate = self._safe_float(wo_row.get('Rate', 0))
            wo_amount = wo_qty * wo_rate
            
            bq_qty = self._safe_float(bq_row.get('Quantity', 0)) if bq_row is not None else 0
            bq_amount = bq_qty * wo_rate
            
            excess_qty = max(0, bq_qty - wo_qty)
            excess_amt = excess_qty * wo_rate
            saving_qty = max(0, wo_qty - bq_qty)
            saving_amt = saving_qty * wo_rate
            
            wo_qty_display = f"{wo_qty:.2f}" if wo_qty > 0 else ""
            wo_rate_display = f"{wo_rate:.2f}" if wo_rate > 0 else ""
            wo_amount_display = f"{wo_amount:.2f}" if wo_amount > 0 else ""
            bq_qty_display = f"{bq_qty:.2f}" if bq_qty > 0 else ""
            bq_amount_display = f"{bq_amount:.2f}" if bq_amount > 0 else ""
            excess_qty_display = f"{excess_qty:.2f}" if excess_qty > 0 else ""
            excess_amt_display = f"{excess_amt:.2f}" if excess_amt > 0 else ""
            saving_qty_display = f"{saving_qty:.2f}" if saving_qty > 0 else ""
            saving_amt_display = f"{saving_amt:.2f}" if saving_amt > 0 else ""
            
            html_content += f"""
                    <tr>
                        <td>{self._safe_serial_no(wo_row.get('Item No.', wo_row.get('Item', '')))}</td>
                        <td>{wo_row.get('Description', '')}</td>
                        <td>{wo_row.get('Unit', '')}</td>
                        <td class="amount">{wo_qty_display}</td>
                        <td class="amount">{wo_rate_display}</td>
                        <td class="amount">{wo_amount_display}</td>
                        <td class="amount">{bq_qty_display}</td>
                        <td class="amount">{bq_amount_display}</td>
                        <td class="amount">{excess_qty_display}</td>
                        <td class="amount">{excess_amt_display}</td>
                        <td class="amount">{saving_qty_display}</td>
                        <td class="amount">{saving_amt_display}</td>
                        <td>{wo_row.get('Remark', '')}</td>
                    </tr>
            """
        
        html_content += f"""
                </tbody>
            </table>
            
            <!-- Closure Lines -->
            <div style="margin-top: 40px; width: 100%; display: table;">
                <div style="display: table-row;">
                    <div style="display: table-cell; width: 50%; padding: 10px; vertical-align: top;">
                        <div style="border-top: 2px solid #000; padding-top: 5px; text-align: center;">
                            <strong>Prepared by</strong><br>
                            <span style="font-size: 8pt;">Assistant Engineer</span><br>
                            <span style="font-size: 8pt;">Date: {current_date}</span>
                        </div>
                    </div>
                    <div style="display: table-cell; width: 50%; padding: 10px; vertical-align: top;">
                        <div style="border-top: 2px solid #000; padding-top: 5px; text-align: center;">
                            <strong>Checked & Approved by</strong><br>
                            <span style="font-size: 8pt;">Executive Engineer</span><br>
                            <span style="font-size: 8pt;">Date: {current_date}</span>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_final_bill_scrutiny(self) -> str:
        """Generate Bill Scrutiny Sheet"""
        current_date = datetime.now().strftime('%d/%m/%Y')
        bill_number = self.title_data.get('Bill Number', 'Bill Number Not Available')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>BILL SCRUTINY SHEET</title>
            <style>
                @page {{ 
                    size: A4; 
                    margin: 10mm;
                }}
                * {{ box-sizing: border-box; }}
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 10mm;
                    font-size: 10pt; 
                }}
                .header {{ text-align: center; margin-bottom: 8px; }}
                .subtitle {{ font-size: 11pt; margin: 3px 0; }}
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 6px 0; 
                    table-layout: fixed;
                }}
                thead {{ display: table-header-group; }}
                tr, img {{ break-inside: avoid; }}
                th, td {{ 
                    border: 1px solid #000; 
                    padding: 4px; 
                    text-align: left; 
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                }}
                th {{ background-color: #f0f0f0; font-weight: bold; }}
                .amount {{ text-align: right; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="subtitle">BILL SCRUTINY SHEET - {bill_number}</div>
                <div class="subtitle">Date: {current_date}</div>
            </div>
            
            <h3>Bill Summary</h3>
            <table>
                <thead>
                    <tr>
                        <th style="width: 10%;">Item No.</th>
                        <th style="width: 40%;">Description</th>
                        <th style="width: 10%;">Unit</th>
                        <th style="width: 13%;">Quantity</th>
                        <th style="width: 13%;">Rate</th>
                        <th style="width: 14%;">Amount</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        total_amount = 0
        if isinstance(self.bill_quantity_data, pd.DataFrame) and not self.bill_quantity_data.empty:
            for index, row in self.bill_quantity_data.iterrows():
                quantity = self._safe_float(row.get('Quantity', 0))
                rate = self._safe_float(row.get('Rate', 0))
                amount = quantity * rate
                total_amount += amount
                
                html_content += f"""
                        <tr>
                            <td>{self._safe_serial_no(row.get('Item No.', row.get('Item', '')))}</td>
                            <td>{row.get('Description', '')}</td>
                            <td>{self._format_unit_or_text(row.get('Unit', ''))}</td>
                            <td class="amount">{self._format_number(quantity)}</td>
                            <td class="amount">{self._format_number(rate)}</td>
                            <td class="amount">{self._format_number(amount)}</td>
                        </tr>
                """
        else:
            html_content += """
                    <tr>
                        <td colspan="6">No bill quantity data available</td>
                    </tr>
            """
        
        html_content += f"""
                    <tr style="font-weight: bold;">
                        <td colspan="5">TOTAL</td>
                        <td class="amount">{total_amount:.0f}</td>
                    </tr>
                </tbody>
            </table>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_extra_items_statement(self) -> str:
        """Generate Extra Items Statement"""
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Extra Items Statement</title>
            <style>
                @page {{ 
                    size: A4; 
                    margin: 10mm;
                }}
                * {{ box-sizing: border-box; }}
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 10mm;
                    font-size: 10pt; 
                }}
                .header {{ text-align: center; margin-bottom: 8px; }}
                .subtitle {{ font-size: 11pt; margin: 3px 0; }}
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 6px 0; 
                    table-layout: fixed;
                }}
                thead {{ display: table-header-group; }}
                tr, img {{ break-inside: avoid; }}
                th, td {{ 
                    border: 1px solid #000; 
                    padding: 4px; 
                    text-align: left; 
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                }}
                th {{ background-color: #f0f0f0; font-weight: bold; }}
                .amount {{ text-align: right; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="subtitle">Extra Items Statement</div>
                <div class="subtitle">Date: {current_date}</div>
            </div>
            
            <h3>Extra Items</h3>
            <table>
                <thead>
                    <tr>
                        <th style="width: 10%;">Item No.</th>
                        <th style="width: 50%;">Description</th>
                        <th style="width: 10%;">Unit</th>
                        <th style="width: 10%;">Quantity</th>
                        <th style="width: 10%;">Rate</th>
                        <th style="width: 10%;">Amount</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        total_amount = 0
        if isinstance(self.extra_items_data, pd.DataFrame) and not self.extra_items_data.empty:
            for index, row in self.extra_items_data.iterrows():
                quantity = self._safe_float(row.get('Quantity', 0))
                rate = self._safe_float(row.get('Rate', 0))
                amount = quantity * rate
                total_amount += amount
                
                html_content += f"""
                        <tr>
                            <td>{self._safe_serial_no(row.get('Item No.', row.get('Item', '')))}</td>
                            <td>{row.get('Description', '')}</td>
                            <td>{self._format_unit_or_text(row.get('Unit', ''))}</td>
                            <td class="amount">{self._format_number(quantity)}</td>
                            <td class="amount">{self._format_number(rate)}</td>
                            <td class="amount">{self._format_number(amount)}</td>
                        </tr>
                """
        else:
            html_content += """
                    <tr>
                        <td colspan="6">No extra items data available</td>
                    </tr>
            """
        
        html_content += f"""
                    <tr style="font-weight: bold;">
                        <td colspan="5">TOTAL</td>
                        <td class="amount">{total_amount:.2f}</td>
                    </tr>
                </tbody>
            </table>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_certificate_ii(self) -> str:
        """Generate Certificate II document"""
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Certificate II - Work Completion Certificate</title>
            <style>
                @page {{ 
                    size: A4; 
                    margin: 15mm;
                }}
                * {{ box-sizing: border-box; }}
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 15mm;
                    font-size: 11pt; 
                    line-height: 1.6;
                }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .title {{ font-size: 14pt; font-weight: bold; margin-bottom: 30px; }}
                .content {{ text-align: justify; margin-bottom: 30px; }}
                .signature-block {{ 
                    margin-top: 50px; 
                    display: flex; 
                    justify-content: space-between;
                }}
                .signature {{ 
                    width: 45%; 
                    text-align: center;
                }}
                .signature-line {{ 
                    margin-top: 60px; 
                    border-top: 1px solid #000; 
                    padding-top: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">CERTIFICATE II</div>
                <div class="title">WORK COMPLETION CERTIFICATE</div>
            </div>
            
            <div class="content">
                <p>This is to certify that the work mentioned in the agreement/bill has been completed/executed as per the terms 
                and conditions of the agreement and measurement book. The quality of work is found satisfactory.</p>
                
                <p>The bills have been scrutinized and found correct and in order. The work has been executed as per specifications 
                and the measurements recorded are correct.</p>
                
                <p>All materials used are as per approved standards and specifications. The work has been carried out under my 
                personal supervision and knowledge.</p>
            </div>
            
            <div class="signature-block">
                <div class="signature">
                    <div>Prepared by</div>
                    <div class="signature-line">
                        Assistant Engineer<br>
                        Date: {current_date}
                    </div>
                </div>
                <div class="signature">
                    <div>Approved by</div>
                    <div class="signature-line">
                        Executive Engineer<br>
                        Date: {current_date}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_certificate_iii(self) -> str:
        """Generate Certificate III document"""
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Certificate III - Payment Certification</title>
            <style>
                @page {{ 
                    size: A4; 
                    margin: 15mm;
                }}
                * {{ box-sizing: border-box; }}
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 15mm;
                    font-size: 11pt; 
                    line-height: 1.6;
                }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .title {{ font-size: 14pt; font-weight: bold; margin-bottom: 30px; }}
                .content {{ text-align: justify; margin-bottom: 30px; }}
                .signature-block {{ 
                    margin-top: 50px; 
                    display: flex; 
                    justify-content: space-between;
                }}
                .signature {{ 
                    width: 45%; 
                    text-align: center;
                }}
                .signature-line {{ 
                    margin-top: 60px; 
                    border-top: 1px solid #000; 
                    padding-top: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">CERTIFICATE III</div>
                <div class="title">PAYMENT CERTIFICATION</div>
            </div>
            
            <div class="content">
                <p>This is to certify that the payment claimed in the bill is correct and in order. The work has been executed 
                satisfactorily and measurements are correct as per records.</p>
                
                <p>The bills have been thoroughly examined and verified. All deductions as per rules have been made. The payment 
                is recommended subject to budget provision and availability of funds.</p>
                
                <p>The work has been completed/executed as per agreement terms and conditions. No adverse remarks are reported 
                against the contractor.</p>
            </div>
            
            <div class="signature-block">
                <div class="signature">
                    <div>Prepared by</div>
                    <div class="signature-line">
                        Assistant Engineer<br>
                        Date: {current_date}
                    </div>
                </div>
                <div class="signature">
                    <div>Approved by</div>
                    <div class="signature-line">
                        Executive Engineer<br>
                        Date: {current_date}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content