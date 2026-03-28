"""
Online Entry Mode with Excel-Like Grid
Phase 2 Implementation: Replace form-based UI with Excel-like editable grid
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import io
import zipfile
from core.ui.hybrid_mode import ChangeLogger
from core.utils.excel_exporter import ExcelExporter
from core.utils.safe_conversions import safe_quantity, safe_rate
import time

def show_online_mode_grid(config):
    """Show online entry interface with Excel-like grid"""
    st.markdown("## 💻 Online Entry Mode (Excel-Like Grid)")
    
    # Feature flag notice
    st.markdown("""
    <div style='background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
                padding: 15px; 
                border-radius: 8px; 
                border-left: 5px solid #2196f3; 
                margin-bottom: 20px;'>
        <p style='color: #0d47a1; margin: 0; font-size: 0.95rem;'>
            <strong>🆕 NEW: Excel-Like Grid Interface</strong><br>
            Phase 2 implementation with keyboard navigation, inline editing, and Excel-like UX
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'online_grid_data' not in st.session_state:
        st.session_state.online_grid_data = {
            'project_name': '',
            'contractor': '',
            'bill_date': None,
            'tender_premium': 4.0,
            'items_df': None,
            'excel_uploaded': False,
            'history': [],
            'history_idx': -1
        }
    
    # Initialize change logger
    ChangeLogger.initialize()
    
    # Step 1: Project Details
    st.markdown("### 📋 Step 1: Project Details")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Excel upload for data extraction
        st.markdown("""
        <div style='background-color: #e8f5e9; padding: 12px; border-radius: 6px; margin-bottom: 15px;'>
            <p style='color: #2e7d32; margin: 0; font-size: 0.9rem;'>
                <strong>📤 Quick Start:</strong> Upload Excel file to auto-extract project details and items
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        excel_file = st.file_uploader(
            "Upload Excel file (optional)",
            type=['xlsx', 'xls', 'xlsm'],
            help="Upload to auto-extract project name, contractor, and work items"
        )
        
        if excel_file and not st.session_state.online_grid_data['excel_uploaded']:
            with st.spinner("Extracting data from Excel..."):
                extracted_data = extract_data_from_excel(excel_file)
                
                if extracted_data:
                    st.session_state.online_grid_data['project_name'] = extracted_data.get('project_name', '')
                    st.session_state.online_grid_data['contractor'] = extracted_data.get('contractor', '')
                    st.session_state.online_grid_data['items_df'] = extracted_data.get('items_df', None)
                    st.session_state.online_grid_data['excel_uploaded'] = True
                    st.success("✅ Data extracted successfully!")
                    st.rerun()
    
    with col2:
        if st.button("🔄 Reset Form", help="Clear all data and start fresh"):
            st.session_state.online_grid_data = {
                'project_name': '',
                'contractor': '',
                'bill_date': None,
                'tender_premium': 4.0,
                'items_df': None,
                'excel_uploaded': False,
                'history': [],
                'history_idx': -1
            }
            ChangeLogger.clear()
            st.rerun()
    
    # Project details form
    col1, col2 = st.columns(2)
    
    with col1:
        project_name = st.text_input(
            "Name of Work *",
            value=st.session_state.online_grid_data['project_name'],
            placeholder="Enter project name",
            help="Required field"
        )
        st.session_state.online_grid_data['project_name'] = project_name
        
        contractor = st.text_input(
            "Contractor Name",
            value=st.session_state.online_grid_data['contractor'],
            placeholder="Enter contractor name (optional)"
        )
        st.session_state.online_grid_data['contractor'] = contractor
    
    with col2:
        bill_date = st.date_input(
            "Bill Date",
            value=st.session_state.online_grid_data['bill_date'],
            help="Leave blank if not applicable"
        )
        st.session_state.online_grid_data['bill_date'] = bill_date
        
        tender_premium = st.number_input(
            "Tender Premium (%)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.online_grid_data['tender_premium'],
            step=0.5,
            help="Percentage to add to total amount"
        )
        st.session_state.online_grid_data['tender_premium'] = tender_premium
    
    # Step 2: Excel-Like Grid for Items
    st.markdown("---")
    st.markdown("### 📊 Step 2: Work Items (Excel-Like Grid)")
    
    # Instructions
    st.markdown("""
    <div style='background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); 
                padding: 15px; 
                border-radius: 8px; 
                border-left: 5px solid #ff9800; 
                margin-bottom: 15px;'>
        <p style='color: #e65100; margin: 0; font-size: 0.95rem;'>
            <strong>💡 Excel-Like Editing:</strong>
        </p>
        <ul style='color: #ef6c00; margin: 5px 0 0 20px; font-size: 0.9rem;'>
            <li>Click any cell to edit</li>
            <li>Use Tab or Enter to navigate</li>
            <li>Add/delete rows using buttons below grid</li>
            <li>Changes are tracked automatically</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize items dataframe if not exists
    if st.session_state.online_grid_data['items_df'] is None:
        st.session_state.online_grid_data['items_df'] = create_default_items_df(5)
        # Initialize history
        st.session_state.online_grid_data['history'] = [st.session_state.online_grid_data['items_df'].copy()]
        st.session_state.online_grid_data['history_idx'] = 0
    
    # Undo / Redo controls
    col_u1, col_u2, col_u3, col_u4 = st.columns([1, 1, 4, 2])
    
    history_idx = st.session_state.online_grid_data['history_idx']
    history_len = len(st.session_state.online_grid_data['history'])
    
    with col_u1:
        can_undo = history_idx > 0
        if st.button("↩️ Undo", disabled=not can_undo, use_container_width=True, help="Undo last grid change"):
            if can_undo:
                st.session_state.online_grid_data['history_idx'] -= 1
                idx = st.session_state.online_grid_data['history_idx']
                st.session_state.online_grid_data['items_df'] = st.session_state.online_grid_data['history'][idx].copy()
                st.rerun()
                
    with col_u2:
        can_redo = history_idx < history_len - 1
        if st.button("↪️ Redo", disabled=not can_redo, use_container_width=True, help="Redo previously undone change"):
            if can_redo:
                st.session_state.online_grid_data['history_idx'] += 1
                idx = st.session_state.online_grid_data['history_idx']
                st.session_state.online_grid_data['items_df'] = st.session_state.online_grid_data['history'][idx].copy()
                st.rerun()
                
    with col_u4:
        # Performance Testing Expander
        with st.expander("⚡ Performance Benchmark"):
            st.markdown("<small>Generate large datasets to test grid performance.</small>", unsafe_allow_html=True)
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                if st.button("100", help="Generate 100 rows", key="btn_100"):
                    _generate_benchmark_data(100)
            with col_b2:
                if st.button("500", help="Generate 500 rows", key="btn_500"):
                    _generate_benchmark_data(500)
            with col_b3:
                if st.button("1K", help="Generate 1000 rows", key="btn_1000"):
                    _generate_benchmark_data(1000)

    # Display current item count
    current_items = update_validation_status(st.session_state.online_grid_data['items_df'])
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.info(f"📦 Total Items: {len(current_items)} | Active Items: {len(current_items[current_items['Quantity'] > 0])}")
    
    with col2:
        if st.button("➕ Add 5 Rows", use_container_width=True):
            new_rows = create_default_items_df(5, start_index=len(current_items))
            new_df = pd.concat([current_items, new_rows], ignore_index=True)
            _save_history(new_df)
            st.rerun()
    
    with col3:
        if st.button("➕ Add 10 Rows", use_container_width=True):
            new_rows = create_default_items_df(10, start_index=len(current_items))
            new_df = pd.concat([current_items, new_rows], ignore_index=True)
            _save_history(new_df)
            st.rerun()
    
    # Track render time for performance metrics
    render_start = time.time()
    
    # Excel-like data editor
    edited_df = st.data_editor(
        current_items,
        use_container_width=True,
        num_rows="dynamic",
        height=min(600, max(400, len(current_items) * 35 + 40)),  # Dynamic height with bounds
        column_config={
            "Status": st.column_config.TextColumn(
                "Status",
                width="small",
                help="🟢 Valid | 🟠 Partial | 🔴 Error | ⚪ Empty",
                disabled=True
            ),
            "Item No": st.column_config.TextColumn(
                "Item No",
                width="small",
                help="Item number",
                required=True
            ),
            "Description": st.column_config.TextColumn(
                "Description",
                width="large",
                help="Item description",
                required=True
            ),
            "Unit": st.column_config.SelectboxColumn(
                "Unit",
                width="small",
                help="Unit of measurement",
                options=["NOS", "CUM", "SQM", "RMT", "MT", "KG", "LTR", "SET", "LS"],
                required=True
            ),
            "Quantity": st.column_config.NumberColumn(
                "📝 Quantity",
                width="small",
                help="⬅️ EDIT: Enter quantity",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                required=True
            ),
            "Rate": st.column_config.NumberColumn(
                "📝 Rate (₹)",
                width="small",
                help="⬅️ EDIT: Enter rate",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                required=True
            ),
            "Amount": st.column_config.NumberColumn(
                "Amount (₹)",
                width="medium",
                help="Auto-calculated: Quantity × Rate",
                format="₹%.2f",
                disabled=True
            )
        },
        hide_index=True,
        key=f"online_grid_editor_{history_idx}" # Force re-render on undo/redo
    )
    
    render_time = time.time() - render_start
    if len(current_items) >= 100:
        st.caption(f"⚡ Grid rendered {len(current_items)} rows in {render_time:.2f} seconds")
    
    # Recalculate amounts and update status
    edited_df['Amount'] = edited_df['Quantity'] * edited_df['Rate']
    edited_df = update_validation_status(edited_df)
    
    # Check if grid data actually changed manually by user
    data_changed = False
    
    # Track changes (compare with previous state)
    if 'items_df' in st.session_state.online_grid_data:
        prev_df = st.session_state.online_grid_data['items_df']
        
        # Check for length changes (row added/deleted via data_editor UI)
        if len(edited_df) != len(prev_df):
            data_changed = True
        else:
            # Check for cell changes
            for idx in edited_df.index:
                if idx < len(prev_df):
                    item_no = edited_df.loc[idx, 'Item No']
                    
                    # Check description change
                    if prev_df.loc[idx, 'Description'] != edited_df.loc[idx, 'Description']:
                        data_changed = True
                        
                    # Check unit change
                    if prev_df.loc[idx, 'Unit'] != edited_df.loc[idx, 'Unit']:
                        data_changed = True
                    
                    # Check quantity change
                    old_qty = prev_df.loc[idx, 'Quantity']
                    new_qty = edited_df.loc[idx, 'Quantity']
                    if old_qty != new_qty:
                        data_changed = True
                        reason = "Zero-Qty Activation" if old_qty == 0 else "Quantity Adjustment"
                        ChangeLogger.log_change(
                            item_no=item_no,
                            field='Quantity',
                            old_value=f"{old_qty:.2f}",
                            new_value=f"{new_qty:.2f}",
                            reason=reason
                        )
                    
                    # Check rate change
                    old_rate = prev_df.loc[idx, 'Rate']
                    new_rate = edited_df.loc[idx, 'Rate']
                    if old_rate != new_rate:
                        data_changed = True
                        reason = "Rate Adjustment"
                        ChangeLogger.log_change(
                            item_no=item_no,
                            field='Rate',
                            old_value=f"₹{old_rate:.2f}",
                            new_value=f"₹{new_rate:.2f}",
                            reason=reason
                        )
    
    # Only update session state and history if data actually changed
    if data_changed:
        _save_history(edited_df)
        st.rerun()
    else:
        # Just update the dataframe in state without adding to history
        st.session_state.online_grid_data['items_df'] = edited_df
    
    # Step 3: Summary and Generation
    st.markdown("---")
    st.markdown("### 📊 Step 3: Summary & Document Generation")
    
    # Track invalid rows from active ones to prevent generation if errors exist
    active_mask = (edited_df['Quantity'] > 0) | (edited_df['Rate'] > 0) | (edited_df['Description'].str.strip() != '')
    active_df = edited_df[active_mask]
    
    invalid_active = len(active_df[active_df['Status'].str.contains('🔴|🟠')])
    
    # Calculate totals
    valid_items = edited_df[(edited_df['Quantity'] > 0) & (edited_df['Rate'] > 0) & (edited_df['Description'].str.strip() != '')]
    total_amount = valid_items['Amount'].sum()
    premium_amount = total_amount * (tender_premium / 100)
    net_payable = total_amount + premium_amount
    
    # Display summary
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Amount", f"₹{total_amount:,.2f}")
    col2.metric("Premium", f"₹{premium_amount:,.2f}", delta=f"{tender_premium}%")
    col3.metric("NET PAYABLE", f"₹{net_payable:,.2f}")
    
    if invalid_active > 0:
        col4.metric("Active Items", f"{len(valid_items)}/{len(edited_df)}", delta=f"{invalid_active} Invalid", delta_color="inverse")
    else:
        col4.metric("Active Items", f"{len(valid_items)}/{len(edited_df)}")
    
    # Show change log if changes exist
    changes = ChangeLogger.get_changes()
    if len(changes) > 0:
        with st.expander(f"📝 Change Log ({len(changes)} changes)", expanded=False):
            change_df = ChangeLogger.export_to_dataframe()
            st.dataframe(change_df, use_container_width=True, hide_index=True)
    
    # Generation options
    st.markdown("#### 📄 Document Generation Options")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        generate_html = st.checkbox("📄 HTML", value=True)
    with col2:
        generate_pdf = st.checkbox("📕 PDF", value=True)
    with col3:
        generate_docx = st.checkbox("📝 DOCX", value=False)
    
    # Generate button
    if st.button("🚀 Generate Documents", type="primary", use_container_width=True):
        if not project_name:
            st.error("❌ Please enter project name in Step 1")
        elif len(valid_items) == 0:
            st.error("❌ Please add at least one complete valid item (Description, Qty > 0, Rate > 0)")
        elif invalid_active > 0:
            st.error(f"❌ Cannot generate: Found {invalid_active} invalid active items. Please fix items marked with 🔴 or 🟠.")
            st.info("💡 A valid item must have a Description, Quantity > 0, AND Rate > 0.")
        else:
            generate_documents(
                project_name=project_name,
                contractor=contractor,
                bill_date=bill_date,
                tender_premium=tender_premium,
                items_df=valid_items,
                generate_html=generate_html,
                generate_pdf=generate_pdf,
                generate_docx=generate_docx
            )
            
            
def _save_history(new_df):
    """Helper to save a new state to undo history"""
    history = st.session_state.online_grid_data['history']
    current_idx = st.session_state.online_grid_data['history_idx']
    
    # Slice off any "redo" history that's now invalid
    history = history[:current_idx + 1]
    
    # Append new state
    history.append(new_df.copy())
    
    # Keep max 20 states to prevent memory bloat
    if len(history) > 20:
        history = history[-20:]
    
    st.session_state.online_grid_data['history'] = history
    st.session_state.online_grid_data['history_idx'] = len(history) - 1
    st.session_state.online_grid_data['items_df'] = new_df.copy()

def _generate_benchmark_data(num_rows):
    """Helper to generate benchmark dummy data"""
    df = create_default_items_df(num_rows)
    for i in range(num_rows):
        df.loc[i, 'Description'] = f"Benchmark Item {i+1}"
        df.loc[i, 'Quantity'] = (i % 10) + 1.0
        df.loc[i, 'Rate'] = (i % 100) * 10.0 + 50.0
    
    df['Amount'] = df['Quantity'] * df['Rate']
    _save_history(df)
    st.rerun()

def update_validation_status(df):
    """Updates the 'Status' column based on row validity rules"""
    if df is None or df.empty:
        return df
        
    df = df.copy()
    if 'Status' not in df.columns:
        df.insert(0, 'Status', '⚪')
        
    for idx, row in df.iterrows():
        qty = float(row.get('Quantity', 0))
        rate = float(row.get('Rate', 0))
        desc = str(row.get('Description', '')).strip()
        
        is_active = qty > 0 or rate > 0 or desc != ''
        
        if not is_active:
            status = '⚪' # Empty / Ignored
        elif desc and qty > 0 and rate > 0:
            status = '🟢' # Fully valid
        elif desc == '' and (qty > 0 or rate > 0):
            status = '🔴 No Desc' # Error: has qty/rate but no description
        elif desc != '' and (qty == 0 or rate == 0):
            status = '🟠 Miss Q/R' # Partial: has description but missing qty or rate
        else:
            status = '🔴 Inv' # Catch-all invalid
            
        df.loc[idx, 'Status'] = status
        
    return df


def extract_data_from_excel(excel_file):
    """Extract project details and items from Excel file"""
    try:
        from core.processors.excel_processor import ExcelProcessor
        
        processor = ExcelProcessor()
        processed_data = processor.process_excel(excel_file)
        
        result = {}
        
        # Extract project name and contractor from title data
        if 'title_data' in processed_data:
            title_data = processed_data['title_data']
            result['project_name'] = title_data.get('Name of Work', '')
            result['contractor'] = title_data.get('Contractor', '')
        
        # Extract items from work order data
        if 'work_order_data' in processed_data:
            wo_df = processed_data['work_order_data']
            
            if not wo_df.empty:
                items_list = []
                for idx, row in wo_df.iterrows():
                    # Safe float conversion using utility functions
                    qty = safe_quantity(row.get('Quantity', 0))
                    rate = safe_rate(row.get('Rate', 0))
                    
                    items_list.append({
                        'Item No': row.get('Item No.', f"{idx+1:03d}"),
                        'Description': row.get('Description', ''),
                        'Unit': row.get('Unit', 'NOS'),
                        'Quantity': qty,
                        'Rate': rate,
                        'Amount': qty * rate
                    })
                
                result['items_df'] = pd.DataFrame(items_list)
        
        return result
    
    except Exception as e:
        st.error(f"Error extracting data from Excel: {str(e)}")
        return None


def create_default_items_df(num_items=5, start_index=0):
    """Create default items dataframe"""
    items = []
    for i in range(num_items):
        items.append({
            'Status': '⚪',
            'Item No': f"{start_index + i + 1:03d}",
            'Description': '',
            'Unit': 'NOS',
            'Quantity': 0.0,
            'Rate': 0.0,
            'Amount': 0.0
        })
    
    return pd.DataFrame(items)


def generate_documents(project_name, contractor, bill_date, tender_premium, items_df, 
                      generate_html=True, generate_pdf=True, generate_docx=False):
    """Generate documents from online grid data"""
    with st.spinner("Generating documents..."):
        try:
            from core.generators.document_generator import DocumentGenerator
            
            # Prepare data structure
            bill_date_str = bill_date.strftime('%d/%m/%Y') if bill_date else ""
            
            processed_data = {
                "title_data": {
                    "Name of Work": project_name,
                    "Contractor": contractor,
                    "Bill Date": bill_date_str,
                    "Tender Premium %": tender_premium
                },
                "work_order_data": [],
                "totals": {
                    "grand_total": items_df['Amount'].sum(),
                    "premium": {
                        "percent": tender_premium / 100,
                        "amount": items_df['Amount'].sum() * (tender_premium / 100)
                    },
                    "payable": items_df['Amount'].sum() * (1 + tender_premium / 100),
                    "net_payable": items_df['Amount'].sum() * (1 + tender_premium / 100)
                }
            }
            
            # Add items to work order data
            for idx, row in items_df.iterrows():
                processed_data["work_order_data"].append({
                    "Item No.": row['Item No'],
                    "Description": row['Description'],
                    "Unit": row['Unit'],
                    "Quantity": row['Quantity'],
                    "Rate": row['Rate'],
                    "Amount": row['Amount']
                })
            
            # Generate documents
            doc_generator = DocumentGenerator(processed_data)
            html_documents = doc_generator.generate_all_documents()
            
            pdf_documents = {}
            if generate_pdf:
                pdf_documents = doc_generator.create_pdf_documents(html_documents)
            
            doc_documents = {}
            if generate_docx:
                doc_documents = doc_generator.generate_doc_documents()
            
            st.success("✅ Documents generated successfully!")
            
            # Create ZIP file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                if generate_html:
                    for doc_name, html_content in html_documents.items():
                        content_bytes = html_content.encode('utf-8') if isinstance(html_content, str) else html_content
                        zip_file.writestr(f"html/{doc_name}.html", content_bytes)
                
                if generate_pdf:
                    for doc_name, pdf_content in pdf_documents.items():
                        zip_file.writestr(f"pdf/{doc_name}.pdf", pdf_content)
                
                if generate_docx:
                    for doc_name, doc_content in doc_documents.items():
                        zip_file.writestr(f"word/{doc_name}", doc_content)
                
                # Add Excel export with change log
                try:
                    excel_output = ExcelExporter.create_new_excel(
                        edited_df=items_df,
                        title_data=processed_data['title_data'],
                        include_formatting=True
                    )
                    
                    # Add change log if exists
                    changes = ChangeLogger.get_changes()
                    if len(changes) > 0:
                        change_df = ChangeLogger.export_to_dataframe()
                        excel_output = ExcelExporter.add_change_log_sheet(excel_output, change_df)
                    
                    zip_file.writestr("excel/bill_data.xlsx", excel_output.getvalue())
                except Exception as e:
                    st.warning(f"Could not add Excel to ZIP: {str(e)}")
            
            zip_buffer.seek(0)
            
            # Download section
            st.markdown("### 📥 Download Documents")
            
            # ZIP download
            st.download_button(
                "📦 Download All (ZIP)",
                data=zip_buffer.getvalue(),
                file_name=f"online_bill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                use_container_width=True
            )
            
            # Individual downloads
            col1, col2, col3 = st.columns(3)
            
            if generate_html and html_documents:
                with col1:
                    st.markdown("#### 📄 HTML")
                    for doc_name, html_content in html_documents.items():
                        content_bytes = html_content.encode('utf-8') if isinstance(html_content, str) else html_content
                        st.download_button(
                            f"📄 {doc_name}",
                            data=content_bytes,
                            file_name=f"{doc_name}.html",
                            mime="text/html",
                            key=f"html_{doc_name}"
                        )
            
            if generate_pdf and pdf_documents:
                with col2:
                    st.markdown("#### 📕 PDF")
                    for doc_name, pdf_content in pdf_documents.items():
                        st.download_button(
                            f"📕 {doc_name}",
                            data=pdf_content,
                            file_name=f"{doc_name}.pdf",
                            mime="application/pdf",
                            key=f"pdf_{doc_name}"
                        )
            
            if generate_docx and doc_documents:
                with col3:
                    st.markdown("#### 📝 DOCX")
                    for doc_name, doc_content in doc_documents.items():
                        st.download_button(
                            f"📝 {doc_name}",
                            data=doc_content,
                            file_name=doc_name,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"docx_{doc_name}"
                        )
        
        except Exception as e:
            st.error(f"Error generating documents: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
