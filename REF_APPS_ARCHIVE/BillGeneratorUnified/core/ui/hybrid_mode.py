"""
Hybrid Mode: Excel Upload + Rate Editor
Allows uploading Excel to extract work order data, then editing rates for part-rate payments
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import io
import zipfile
import json
from core.utils.excel_exporter import ExcelExporter
from core.utils.safe_conversions import safe_float, safe_quantity, safe_rate

# PHASE 1.2: Change Log / Audit Trail System
class ChangeLogger:
    """Track all modifications for audit trail"""
    
    @staticmethod
    def initialize():
        """Initialize change log in session state"""
        if 'change_log' not in st.session_state:
            st.session_state.change_log = []
    
    @staticmethod
    def log_change(item_no, field, old_value, new_value, reason="Manual Edit"):
        """Log a change with timestamp"""
        change_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'item_no': item_no,
            'field': field,
            'old_value': old_value,
            'new_value': new_value,
            'reason': reason,
            'user': 'Admin'  # Can be extended for multi-user
        }
        st.session_state.change_log.append(change_entry)
    
    @staticmethod
    def get_changes():
        """Get all changes"""
        return st.session_state.get('change_log', [])
    
    @staticmethod
    def get_changes_for_item(item_no):
        """Get changes for specific item"""
        return [c for c in st.session_state.get('change_log', []) if c['item_no'] == item_no]
    
    @staticmethod
    def export_to_dataframe():
        """Export change log to DataFrame"""
        changes = st.session_state.get('change_log', [])
        if changes:
            return pd.DataFrame(changes)
        return pd.DataFrame(columns=['timestamp', 'item_no', 'field', 'old_value', 'new_value', 'reason', 'user'])
    
    @staticmethod
    def export_to_json():
        """Export change log to JSON"""
        return json.dumps(st.session_state.get('change_log', []), indent=2)
    
    @staticmethod
    def clear():
        """Clear change log"""
        st.session_state.change_log = []

def show_hybrid_mode(config):
    """Show hybrid Excel upload + rate editor interface"""
    
    # PHASE 1.2: Initialize change logger
    ChangeLogger.initialize()
    
    st.markdown("## 🔄 Hybrid Mode: Excel Upload + Rate Editor")
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
                padding: 20px; 
                border-radius: 12px; 
                border-left: 5px solid #2196f3; 
                margin-bottom: 20px;'>
        <h3 style='color: #0d47a1; margin-top: 0;'>
            📋 Upload Excel → Edit Rates → Generate Documents
        </h3>
        <p style='color: #1565c0; margin-bottom: 0;'>
            Perfect for part-rate payments where bill rate differs from work order rate
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Step 1: Upload Excel File
    st.markdown("### 📤 Step 1: Upload Excel File")
    uploaded_file = st.file_uploader(
        "Upload Excel file to extract work order data",
        type=['xlsx', 'xls', 'xlsm'],
        help="Upload your PWD bill Excel file with work order data"
    )
    
    if uploaded_file:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        try:
            # Process Excel file - handle both old and new deployments
            try:
                from core.processors.excel_processor import ExcelProcessor
                processor = ExcelProcessor()
                processed_data = processor.process_excel(uploaded_file)
            except Exception as e:
                # Fallback: Save uploaded file temporarily and process
                import tempfile
                import os
                
                # Create temporary file
                suffix = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                try:
                    processor = ExcelProcessor()
                    # Read from temp file
                    import io
                    with open(tmp_path, 'rb') as f:
                        processed_data = processor.process_excel(io.BytesIO(f.read()))
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
            
            # Extract sheets from processed data
            result_data = {}
            if 'work_order_data' in processed_data:
                # Convert to DataFrame if needed
                import pandas as pd
                if isinstance(processed_data['work_order_data'], pd.DataFrame):
                    result_data['Work Order'] = processed_data['work_order_data']
                elif isinstance(processed_data['work_order_data'], list):
                    result_data['Work Order'] = pd.DataFrame(processed_data['work_order_data'])
            
            if 'bill_quantity_data' in processed_data:
                import pandas as pd
                if isinstance(processed_data['bill_quantity_data'], pd.DataFrame):
                    result_data['Bill Quantity'] = processed_data['bill_quantity_data']
                elif isinstance(processed_data['bill_quantity_data'], list):
                    result_data['Bill Quantity'] = pd.DataFrame(processed_data['bill_quantity_data'])
            
            if 'extra_items_data' in processed_data:
                import pandas as pd
                if isinstance(processed_data['extra_items_data'], pd.DataFrame):
                    result_data['Extra Items'] = processed_data['extra_items_data']
                elif isinstance(processed_data['extra_items_data'], list):
                    result_data['Extra Items'] = pd.DataFrame(processed_data['extra_items_data'])
            
            # Extract title data
            title_data = processed_data.get('title_data', {})
            
            work_order_df = result_data.get('Work Order')
            bill_quantity_df = result_data.get('Bill Quantity')
            extra_items_df = result_data.get('Extra Items')
            
            # Store in session state
            if 'hybrid_data' not in st.session_state:
                st.session_state.hybrid_data = {}
            
            st.session_state.hybrid_data['title_data'] = title_data
            st.session_state.hybrid_data['work_order_df'] = work_order_df
            st.session_state.hybrid_data['bill_quantity_df'] = bill_quantity_df
            st.session_state.hybrid_data['extra_items_df'] = extra_items_df
            st.session_state.hybrid_data['source_filename'] = uploaded_file.name
            
            st.success("✅ Excel data extracted successfully!")
            
            # Display title information
            st.markdown("### 📋 Project Information")
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**Work Name:** {title_data.get('Name of Work', 'N/A')}")
                st.info(f"**Contractor:** {title_data.get('Name of Contractor', 'N/A')}")
            
            with col2:
                st.info(f"**Agreement No:** {title_data.get('Agreement No.', 'N/A')}")
                st.info(f"**Bill No:** {title_data.get('Bill No.', 'N/A')}")
            
            # Step 2: Edit Rates
            st.markdown("---")
            st.markdown("### ✏️ Step 2: Edit Rates (Part-Rate Payments)")
            
            st.markdown("""
            <div style='background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 5px solid #ffc107; margin-bottom: 15px;'>
                <p style='color: #856404; margin: 0;'>
                    <strong>💡 Tips:</strong>
                </p>
                <ul style='color: #856404; margin: 5px 0 0 20px;'>
                    <li>Edit "Bill Quantity" to add quantities to items with zero qty</li>
                    <li>Edit "Bill Rate" for part-rate payments</li>
                    <li>Items with zero bill quantity will be excluded from documents</li>
                    <li>Work Order data is preserved for reference</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if work_order_df is not None and not work_order_df.empty:
                # Prepare editable dataframe
                if 'edited_items' not in st.session_state.hybrid_data:
                    # Initialize with work order data
                    items_list = []
                    for idx, row in work_order_df.iterrows():
                        item_no = row.get('Item No.', f"{idx+1:03d}")
                        
                        # Get full description including sub-items
                        description = row.get('Description of Item', row.get('Description', ''))
                        
                        # Check for sub-item columns (common patterns)
                        sub_item_cols = [col for col in work_order_df.columns if 'sub' in col.lower() or 'detail' in col.lower()]
                        if sub_item_cols:
                            sub_items = []
                            for sub_col in sub_item_cols:
                                sub_val = row.get(sub_col, '')
                                if sub_val and str(sub_val).strip() and str(sub_val) != 'nan':
                                    sub_items.append(str(sub_val).strip())
                            if sub_items:
                                description = f"{description}\n" + "\n".join([f"  • {item}" for item in sub_items])
                        
                        unit = row.get('Unit', 'NOS')
                        
                        # Safe float conversion using utility functions
                        wo_quantity = safe_quantity(row.get('Quantity', 0))
                        wo_rate = safe_rate(row.get('Rate', 0))
                        
                        # Get bill quantity if available
                        bill_qty = 0.0  # Default to 0 for items not in bill quantity sheet
                        if bill_quantity_df is not None and not bill_quantity_df.empty:
                            if idx < len(bill_quantity_df):
                                bill_row = bill_quantity_df.iloc[idx]
                                bill_qty_value = bill_row.get('Quantity', 0)
                                # Only use bill quantity if it's a valid number > 0
                                if bill_qty_value and str(bill_qty_value) != 'nan':
                                    bill_qty = safe_quantity(bill_qty_value)
                        
                        items_list.append({
                            'Item No': item_no,
                            'Description': description,
                            'Unit': unit,
                            'WO Quantity': wo_quantity,
                            'Bill Quantity': bill_qty,
                            'WO Rate': wo_rate,
                            'Bill Rate': wo_rate,  # Default to WO rate
                            'WO Amount': wo_quantity * wo_rate,
                            'Bill Amount': bill_qty * wo_rate
                        })
                    
                    st.session_state.hybrid_data['edited_items'] = pd.DataFrame(items_list)
                    st.session_state.hybrid_data['show_all_items'] = True  # Default to showing all items
                
                # Display editable table
                st.markdown("""
                <div style='background: #e8f5e9; padding: 10px; border-radius: 8px; margin-bottom: 10px;'>
                    <p style='color: #2e7d32; margin: 0; font-size: 0.9rem;'>
                        <strong>💡 Tips:</strong> 
                        • Hover over description cells to see complete text with sub-items<br>
                        • Set Bill Quantity > 0 to include items not in bill quantity sheet<br>
                        • Edit Bill Rate for part-rate payments
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Options
                col1, col2 = st.columns(2)
                with col1:
                    show_detailed = st.checkbox("📋 Show Detailed Description View", value=False, help="Display full descriptions with sub-items in expandable format")
                with col2:
                    show_all_items = st.checkbox("📦 Show All Work Order Items", value=True, help="Show all items from work order, even if not in bill quantity sheet")
                
                if show_detailed:
                    st.markdown("#### 📋 Detailed Item Descriptions")
                    for idx, row in st.session_state.hybrid_data['edited_items'].iterrows():
                        with st.expander(f"**{row['Item No']}** - {row['Description'][:50]}..."):
                            st.markdown(f"""
                            **Item No:** {row['Item No']}
                            
                            **Full Description:**
                            ```
                            {row['Description']}
                            ```
                            
                            **Details:**
                            - Unit: {row['Unit']}
                            - WO Quantity: {row['WO Quantity']:.2f}
                            - Bill Quantity: {row['Bill Quantity']:.2f}
                            - WO Rate: ₹{row['WO Rate']:.2f}
                            - Bill Rate: ₹{row['Bill Rate']:.2f}
                            - Bill Amount: ₹{row['Bill Amount']:.2f}
                            """)
                    st.markdown("---")
                
                # Filter items based on show_all_items checkbox
                display_df = st.session_state.hybrid_data['edited_items'].copy()
                
                if not show_all_items:
                    # Only show items with bill quantity > 0
                    display_df = display_df[display_df['Bill Quantity'] > 0]
                    if len(display_df) == 0:
                        st.warning("⚠️ No items with bill quantity > 0. Enable 'Show All Work Order Items' to add items.")
                
                # Excel-style editor with enhanced configuration
                st.markdown("### 📊 Excel-Style Spreadsheet Editor")
                st.markdown("""
                <div style='background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
                            padding: 15px; 
                            border-radius: 10px; 
                            border-left: 5px solid #4caf50; 
                            margin-bottom: 15px;'>
                    <p style='color: #1b5e20; margin: 0; font-size: 1rem; font-weight: 600;'>
                        💡 Excel-Like Editing:
                    </p>
                    <ul style='color: #2e7d32; margin: 5px 0 0 20px; font-size: 0.9rem;'>
                        <li>Click any cell to edit (editable columns highlighted)</li>
                        <li>Use Tab or Enter to navigate between cells</li>
                        <li>Changes save automatically</li>
                        <li>Add/delete rows using buttons at bottom</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
                edited_df = st.data_editor(
                    display_df,
                    use_container_width=True,
                    num_rows="dynamic",
                    height=600,  # Taller for Excel-like feel
                    column_config={
                        "Item No": st.column_config.TextColumn(
                            "Item No", 
                            width="small",
                            help="Item number from work order",
                            disabled=True
                        ),
                        "Description": st.column_config.TextColumn(
                            "Description", 
                            width="large", 
                            help="Full description with sub-items"
                        ),
                        "Unit": st.column_config.TextColumn(
                            "Unit", 
                            width="small",
                            help="Unit of measurement"
                        ),
                        "WO Quantity": st.column_config.NumberColumn(
                            "WO Qty", 
                            format="%.2f", 
                            disabled=True,
                            help="Work Order Quantity (read-only)"
                        ),
                        "Bill Quantity": st.column_config.NumberColumn(
                            "📝 Bill Qty", 
                            format="%.2f",
                            help="⬅️ EDIT: Bill quantity (can differ from WO)",
                            min_value=0,
                            step=0.01
                        ),
                        "WO Rate": st.column_config.NumberColumn(
                            "WO Rate", 
                            format="₹%.2f", 
                            disabled=True,
                            help="Work Order Rate (read-only)"
                        ),
                        "Bill Rate": st.column_config.NumberColumn(
                            "📝 Bill Rate", 
                            format="₹%.2f", 
                            help="⬅️ EDIT: Bill rate for part-rate payment",
                            min_value=0,
                            step=0.01
                        ),
                        "WO Amount": st.column_config.NumberColumn(
                            "WO Amount", 
                            format="₹%.2f", 
                            disabled=True,
                            help="Work Order Amount (read-only)"
                        ),
                        "Bill Amount": st.column_config.NumberColumn(
                            "Bill Amount", 
                            format="₹%.2f", 
                            disabled=True,
                            help="Bill Amount (auto-calculated)"
                        )
                    },
                    hide_index=True,
                    key="hybrid_editor"
                )
                
                # Recalculate amounts based on edited rates
                edited_df['Bill Amount'] = edited_df['Bill Quantity'] * edited_df['Bill Rate']
                edited_df['WO Amount'] = edited_df['WO Quantity'] * edited_df['WO Rate']
                
                # PHASE 1.2: Track changes in change log
                # Compare with previous state to detect changes
                if 'edited_items' in st.session_state.hybrid_data:
                    prev_df = st.session_state.hybrid_data['edited_items']
                    
                    # Check for quantity changes
                    for idx in edited_df.index:
                        if idx in prev_df.index:
                            item_no = edited_df.loc[idx, 'Item No']
                            
                            # Check Bill Quantity change
                            old_qty = prev_df.loc[idx, 'Bill Quantity']
                            new_qty = edited_df.loc[idx, 'Bill Quantity']
                            if old_qty != new_qty:
                                reason = "Zero-Qty Activation" if old_qty == 0 else "Quantity Adjustment"
                                ChangeLogger.log_change(
                                    item_no=item_no,
                                    field='Bill Quantity',
                                    old_value=f"{old_qty:.2f}",
                                    new_value=f"{new_qty:.2f}",
                                    reason=reason
                                )
                            
                            # Check Bill Rate change
                            old_rate = prev_df.loc[idx, 'Bill Rate']
                            new_rate = edited_df.loc[idx, 'Bill Rate']
                            if old_rate != new_rate:
                                reason = "Part Rate Payment" if new_rate < edited_df.loc[idx, 'WO Rate'] else "Rate Adjustment"
                                ChangeLogger.log_change(
                                    item_no=item_no,
                                    field='Bill Rate',
                                    old_value=f"₹{old_rate:.2f}",
                                    new_value=f"₹{new_rate:.2f}",
                                    reason=reason
                                )
                
                # PHASE 1.1: Add Part-Rate tracking and display
                # Track which items have part-rate (bill rate < WO rate)
                edited_df['Is Part Rate'] = edited_df['Bill Rate'] < edited_df['WO Rate']
                
                # Create display column for rate with (Part Rate) label
                edited_df['Rate Display'] = edited_df.apply(
                    lambda row: f"₹{row['Bill Rate']:.2f} (Part Rate)" 
                    if row['Is Part Rate'] 
                    else f"₹{row['Bill Rate']:.2f}",
                    axis=1
                )
                
                # Also update description to include (Part Rate) if not already there
                for idx in edited_df[edited_df['Is Part Rate']].index:
                    desc = edited_df.loc[idx, 'Description']
                    if '(Part Rate)' not in desc:
                        edited_df.loc[idx, 'Description'] = f"{desc} (Part Rate)"
                
                # Update session state - merge changes back to full dataframe
                if not show_all_items:
                    # Merge edited items back into full dataframe
                    full_df = st.session_state.hybrid_data['edited_items'].copy()
                    for idx in edited_df.index:
                        full_df.loc[idx] = edited_df.loc[idx]
                    st.session_state.hybrid_data['edited_items'] = full_df
                else:
                    st.session_state.hybrid_data['edited_items'] = edited_df
                
                # Show summary
                st.markdown("### 📊 Summary")
                
                # Use full dataframe for summary
                summary_df = st.session_state.hybrid_data['edited_items']
                
                # Count items by status
                zero_qty_items = summary_df[summary_df['Bill Quantity'] == 0]
                active_items = summary_df[summary_df['Bill Quantity'] > 0]
                
                col1, col2, col3, col4 = st.columns(4)
                
                wo_total = summary_df['WO Amount'].sum()
                bill_total = summary_df['Bill Amount'].sum()
                difference = wo_total - bill_total
                percentage = (bill_total / wo_total * 100) if wo_total > 0 else 0
                
                col1.metric("Work Order Total", f"₹{wo_total:,.2f}")
                col2.metric("Bill Total", f"₹{bill_total:,.2f}")
                col3.metric("Difference", f"₹{difference:,.2f}", delta=f"-{difference:,.2f}" if difference > 0 else f"+{abs(difference):,.2f}")
                col4.metric("Bill %", f"{percentage:.1f}%")
                
                # Show item status
                st.markdown("#### 📋 Item Status")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Items", len(summary_df))
                col2.metric("Active Items", len(active_items), help="Items with Bill Quantity > 0")
                col3.metric("Zero Qty Items", len(zero_qty_items), help="Items with Bill Quantity = 0 (can be activated)")
                
                # PHASE 1.1: Show Part-Rate items count
                part_rate_items = summary_df[summary_df.get('Is Part Rate', False) == True] if 'Is Part Rate' in summary_df.columns else pd.DataFrame()
                col4.metric("Part-Rate Items", len(part_rate_items), help="Items with Bill Rate < WO Rate")
                
                # Show part-rate items if any
                if len(part_rate_items) > 0:
                    with st.expander(f"💰 {len(part_rate_items)} Part-Rate Items (Click to view)"):
                        st.markdown("""
                        <div style='background: #e3f2fd; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                            <p style='color: #0d47a1; margin: 0; font-size: 0.9rem;'>
                                <strong>Part-Rate Payment:</strong> These items have bill rate lower than work order rate.
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        part_rate_display = part_rate_items[['Item No', 'Description', 'WO Rate', 'Bill Rate', 'Rate Display']].copy()
                        part_rate_display['Savings'] = (part_rate_items['WO Rate'] - part_rate_items['Bill Rate']) * part_rate_items['Bill Quantity']
                        st.dataframe(part_rate_display, use_container_width=True, hide_index=True)
                        
                        total_savings = part_rate_display['Savings'].sum()
                        st.success(f"💰 Total Savings from Part-Rate: ₹{total_savings:,.2f}")
                
                # Show zero quantity items if any
                if len(zero_qty_items) > 0:
                    with st.expander(f"⚠️ {len(zero_qty_items)} Items with Zero Quantity (Click to view)"):
                        st.markdown("""
                        <div style='background: #fff3cd; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                            <p style='color: #856404; margin: 0; font-size: 0.9rem;'>
                                These items have zero bill quantity. Edit the "Bill Quantity" column above to add them to the bill.
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        zero_display = zero_qty_items[['Item No', 'Description', 'WO Quantity', 'WO Rate']].copy()
                        zero_display['WO Amount'] = zero_qty_items['WO Amount']
                        st.dataframe(zero_display, use_container_width=True, hide_index=True)
                
                # Show item count
                items_in_bill = len(summary_df[summary_df['Bill Quantity'] > 0])
                total_items = len(summary_df)
                st.info(f"📦 Items in Bill: {items_in_bill} / {total_items} work order items")
                
                # PHASE 1.2: Show Change Log / Audit Trail
                st.markdown("---")
                st.markdown("#### 📝 Change Log / Audit Trail")
                
                changes = ChangeLogger.get_changes()
                
                if len(changes) > 0:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.info(f"📊 Total Changes Recorded: {len(changes)}")
                    
                    with col2:
                        if st.button("🗑️ Clear Log", help="Clear all change history"):
                            ChangeLogger.clear()
                            st.rerun()
                    
                    # Show change log in expandable section
                    with st.expander(f"📋 View All Changes ({len(changes)} entries)", expanded=False):
                        st.markdown("""
                        <div style='background: #fff3e0; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                            <p style='color: #e65100; margin: 0; font-size: 0.9rem;'>
                                <strong>Audit Trail:</strong> All modifications are tracked with timestamp, original value, new value, and reason.
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display as DataFrame
                        change_df = ChangeLogger.export_to_dataframe()
                        st.dataframe(
                            change_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
                                "item_no": st.column_config.TextColumn("Item No", width="small"),
                                "field": st.column_config.TextColumn("Field", width="small"),
                                "old_value": st.column_config.TextColumn("Old Value", width="small"),
                                "new_value": st.column_config.TextColumn("New Value", width="small"),
                                "reason": st.column_config.TextColumn("Reason", width="medium"),
                                "user": st.column_config.TextColumn("User", width="small")
                            }
                        )
                        
                        # Export options
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Export as CSV
                            csv = change_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download as CSV",
                                data=csv,
                                file_name=f"change_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        
                        with col2:
                            # Export as JSON
                            json_data = ChangeLogger.export_to_json()
                            st.download_button(
                                label="📥 Download as JSON",
                                data=json_data,
                                file_name=f"change_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json"
                            )
                else:
                    st.info("ℹ️ No changes recorded yet. Edit quantities or rates to start tracking changes.")
                
                # Handle Extra Items
                st.markdown("---")
                st.markdown("### ➕ Extra Items (Optional)")
                
                if extra_items_df is not None and not extra_items_df.empty:
                    st.info(f"Found {len(extra_items_df)} extra items in Excel file")
                    
                    if 'edited_extra_items' not in st.session_state.hybrid_data:
                        extra_list = []
                        for idx, row in extra_items_df.iterrows():
                            # Safe float conversion for extra items
                            extra_qty = safe_quantity(row.get('Quantity', 0))
                            extra_rate = safe_rate(row.get('Rate', 0))
                            
                            extra_list.append({
                                'Item No': row.get('Item No.', f"E{idx+1:03d}"),
                                'Description': row.get('Description of Item', row.get('Description', '')),
                                'Unit': row.get('Unit', 'NOS'),
                                'Quantity': extra_qty,
                                'Rate': extra_rate,
                                'Amount': extra_qty * extra_rate
                            })
                        st.session_state.hybrid_data['edited_extra_items'] = pd.DataFrame(extra_list)
                    
                    edited_extra_df = st.data_editor(
                        st.session_state.hybrid_data['edited_extra_items'],
                        use_container_width=True,
                        num_rows="dynamic",
                        column_config={
                            "Item No": st.column_config.TextColumn("Item No", width="small"),
                            "Description": st.column_config.TextColumn("Description", width="large"),
                            "Unit": st.column_config.TextColumn("Unit", width="small"),
                            "Quantity": st.column_config.NumberColumn("Quantity", format="%.2f"),
                            "Rate": st.column_config.NumberColumn("Rate (₹)", format="%.2f"),
                            "Amount": st.column_config.NumberColumn("Amount (₹)", format="%.2f", disabled=True)
                        },
                        hide_index=True,
                        key="hybrid_extra_editor"
                    )
                    
                    edited_extra_df['Amount'] = edited_extra_df['Quantity'] * edited_extra_df['Rate']
                    st.session_state.hybrid_data['edited_extra_items'] = edited_extra_df
                    
                    extra_total = edited_extra_df['Amount'].sum()
                    st.metric("Extra Items Total", f"₹{extra_total:,.2f}")
                else:
                    st.info("No extra items found. You can add them manually if needed.")
                    if st.button("➕ Add Extra Items"):
                        st.session_state.hybrid_data['edited_extra_items'] = pd.DataFrame({
                            'Item No': ['E001'],
                            'Description': [''],
                            'Unit': ['NOS'],
                            'Quantity': [0.0],
                            'Rate': [0.0],
                            'Amount': [0.0]
                        })
                        st.rerun()
                
                # Step 3: Generate Documents
                st.markdown("---")
                st.markdown("### 🚀 Step 3: Generate Documents")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    generate_html = st.checkbox("📄 HTML", value=True)
                with col2:
                    generate_pdf = st.checkbox("📕 PDF", value=True)
                with col3:
                    generate_word = st.checkbox("📝 DOCX", value=False)
                
                if st.button("🚀 Generate All Documents", type="primary", use_container_width=True):
                    with st.spinner("Generating documents with edited rates..."):
                        try:
                            # Prepare data for document generation
                            from core.generators.html_generator import HTMLGenerator
                            
                            # CRITICAL FIX: HTMLGenerator expects DataFrames, not lists
                            # Filter to only include items with Bill Quantity > 0
                            active_items_df = edited_df[edited_df['Bill Quantity'] > 0].copy()
                            
                            # Prepare work order data (convert hybrid format to standard format)
                            work_order_list = []
                            bill_quantity_list = []
                            
                            for idx, row in active_items_df.iterrows():
                                # Standard format for work order
                                work_order_list.append({
                                    'Item No.': row['Item No'],
                                    'Description': row['Description'],
                                    'Unit': row['Unit'],
                                    'Quantity': row['WO Quantity'],
                                    'Rate': row['WO Rate'],
                                    'Amount': row['WO Amount']
                                })
                                
                                # Standard format for bill quantity
                                bill_quantity_list.append({
                                    'Item No.': row['Item No'],
                                    'Description': row['Description'],
                                    'Unit': row['Unit'],
                                    'Quantity': row['Bill Quantity'],
                                    'Rate': row['Bill Rate'],
                                    'Amount': row['Bill Amount']
                                })
                            
                            # Convert to DataFrames
                            work_order_df = pd.DataFrame(work_order_list)
                            bill_quantity_df = pd.DataFrame(bill_quantity_list)
                            
                            # Handle extra items
                            extra_items_df = pd.DataFrame()
                            if 'edited_extra_items' in st.session_state.hybrid_data:
                                extra_df = st.session_state.hybrid_data['edited_extra_items']
                                if not extra_df.empty:
                                    # Convert to standard format
                                    extra_list = []
                                    for idx, row in extra_df.iterrows():
                                        extra_list.append({
                                            'Item No.': row['Item No'],
                                            'Description': row['Description'],
                                            'Unit': row['Unit'],
                                            'Quantity': row['Quantity'],
                                            'Rate': row['Rate'],
                                            'Amount': row['Amount']
                                        })
                                    extra_items_df = pd.DataFrame(extra_list)
                            
                            data = {
                                'title_data': title_data,
                                'work_order_data': work_order_df,
                                'bill_quantity_data': bill_quantity_df,
                                'extra_items_data': extra_items_df,
                                'source_filename': uploaded_file.name,
                                'hybrid_mode': True  # Flag to indicate hybrid mode
                            }
                            
                            # Generate HTML
                            generator = HTMLGenerator(data)
                            html_documents = generator.generate_all_documents()
                            
                            st.success(f"✅ Generated {len(html_documents)} HTML documents")
                            
                            # Generate PDF if requested
                            pdf_documents = {}
                            if generate_pdf:
                                from core.generators.pdf_generator_fixed import FixedPDFGenerator
                                pdf_generator = FixedPDFGenerator(margin_mm=10)
                                
                                progress_bar = st.progress(0)
                                for idx, (doc_name, html_content) in enumerate(html_documents.items()):
                                    landscape = 'deviation' in doc_name.lower()
                                    pdf_bytes = pdf_generator.auto_convert(html_content, landscape=landscape, doc_name=doc_name)
                                    pdf_documents[doc_name] = pdf_bytes
                                    progress_bar.progress((idx + 1) / len(html_documents))
                                
                                st.success(f"✅ Generated {len(pdf_documents)} PDF documents")
                            
                            # Generate Word if requested
                            word_documents = {}
                            if generate_word:
                                from core.generators.word_generator import WordGenerator
                                word_gen = WordGenerator()
                                word_documents = word_gen.generate_all_docx(html_documents)
                                st.success(f"✅ Generated {len(word_documents)} Word documents")
                            
                            # Download section
                            st.markdown("---")
                            st.markdown("### 📥 Download Documents")
                            
                            # PHASE 1.3: Excel Export with Formatting
                            st.markdown("#### 📊 Excel Export (Round-Trip)")
                            st.markdown("""
                            <div style='background: #e8f5e9; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                                <p style='color: #2e7d32; margin: 0; font-size: 0.9rem;'>
                                    <strong>💡 Excel Round-Trip:</strong> Download your edited data back to Excel with formatting preserved.
                                    Includes change log sheet for audit trail.
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Export edited data to new Excel file
                                try:
                                    excel_output = ExcelExporter.create_new_excel(
                                        edited_df=edited_df,
                                        title_data=title_data,
                                        include_formatting=True
                                    )
                                    
                                    # Add change log sheet if changes exist
                                    changes = ChangeLogger.get_changes()
                                    if len(changes) > 0:
                                        change_df = ChangeLogger.export_to_dataframe()
                                        excel_output = ExcelExporter.add_change_log_sheet(excel_output, change_df)
                                    
                                    st.download_button(
                                        "📊 Download Edited Excel",
                                        data=excel_output.getvalue(),
                                        file_name=f"edited_bill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        use_container_width=True,
                                        help="Download edited data as Excel file with formatting and change log"
                                    )
                                except Exception as e:
                                    st.error(f"Excel export error: {str(e)}")
                            
                            with col2:
                                # Export with original file formatting (if available)
                                if uploaded_file is not None:
                                    try:
                                        # Reset file pointer
                                        uploaded_file.seek(0)
                                        
                                        excel_output_original = ExcelExporter.export_with_formatting(
                                            original_file=uploaded_file,
                                            edited_df=edited_df,
                                            sheet_name='Bill Quantity',
                                            preserve_formulas=True
                                        )
                                        
                                        st.download_button(
                                            "📊 Download with Original Formatting",
                                            data=excel_output_original.getvalue(),
                                            file_name=f"updated_{uploaded_file.name}",
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                            use_container_width=True,
                                            help="Update original Excel file preserving all formatting"
                                        )
                                    except Exception as e:
                                        st.warning(f"Could not preserve original formatting: {str(e)}")
                            
                            st.markdown("---")
                            
                            # Create ZIP
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                if generate_html:
                                    for doc_name, html_content in html_documents.items():
                                        zip_file.writestr(f"html/{doc_name}.html", html_content)
                                if generate_pdf:
                                    for doc_name, pdf_bytes in pdf_documents.items():
                                        zip_file.writestr(f"pdf/{doc_name}.pdf", pdf_bytes)
                                if generate_word:
                                    for doc_name, docx_bytes in word_documents.items():
                                        zip_file.writestr(f"word/{doc_name}.docx", docx_bytes)
                            
                            zip_buffer.seek(0)
                            
                            # ZIP download
                            st.download_button(
                                "📦 Download All (ZIP)",
                                data=zip_buffer.getvalue(),
                                file_name=f"hybrid_documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                            
                            # Individual downloads
                            if generate_html:
                                st.markdown("#### 📄 HTML Documents")
                                for doc_name, html_content in html_documents.items():
                                    st.download_button(
                                        f"📄 {doc_name}",
                                        data=html_content,
                                        file_name=f"{doc_name}.html",
                                        mime="text/html",
                                        key=f"html_{doc_name}"
                                    )
                            
                            if generate_pdf:
                                st.markdown("#### 📕 PDF Documents")
                                for doc_name, pdf_bytes in pdf_documents.items():
                                    st.download_button(
                                        f"📕 {doc_name}",
                                        data=pdf_bytes,
                                        file_name=f"{doc_name}.pdf",
                                        mime="application/pdf",
                                        key=f"pdf_{doc_name}"
                                    )
                            
                            if generate_word:
                                st.markdown("#### 📝 Word Documents")
                                for doc_name, docx_bytes in word_documents.items():
                                    st.download_button(
                                        f"📝 {doc_name}",
                                        data=docx_bytes,
                                        file_name=f"{doc_name}.docx",
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        key=f"docx_{doc_name}"
                                    )
                        
                        except Exception as e:
                            st.error(f"❌ Error generating documents: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
            
            else:
                st.warning("⚠️ No work order data found in Excel file")
        
        except Exception as e:
            st.error(f"❌ Error processing Excel file: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    else:
        st.info("👆 Upload an Excel file to get started")
        
        # Show example
        with st.expander("📖 How to use Hybrid Mode"):
            st.markdown("""
            ### Step-by-Step Guide
            
            1. **Upload Excel File**
               - Upload your PWD bill Excel file
               - System extracts work order data automatically
            
            2. **Edit Rates**
               - Review the extracted items in the table
               - Edit "Bill Rate" column for part-rate payments
               - Work Order Rate is preserved for reference
               - Bill Amount is calculated automatically
            
            3. **Generate Documents**
               - Select output formats (HTML, PDF, DOCX)
               - Click "Generate All Documents"
               - Download individual files or ZIP
            
            ### Use Cases
            
            - **Part-Rate Payment**: Bill rate is less than work order rate
            - **Rate Corrections**: Fix incorrect rates from Excel
            - **Custom Billing**: Apply different rates for specific items
            
            ### Example
            
            | Item | WO Rate | Bill Rate | Reason |
            |------|---------|-----------|--------|
            | 001  | ₹500    | ₹300      | 60% part-rate payment |
            | 002  | ₹1000   | ₹1000     | Full rate |
            | 003  | ₹750    | ₹500      | Revised rate |
            """)
