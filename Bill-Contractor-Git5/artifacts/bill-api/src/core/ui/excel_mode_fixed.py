"""
Fixed Excel Upload Mode - Uses Correct Template Flow
Excel → Process → HTML Templates → WeasyPrint PDF
With automatic cache cleaning and centralized output management
"""
import streamlit as st
from pathlib import Path
import io
from datetime import datetime
import zipfile
import gc

# Import utilities
from core.utils.output_manager import get_output_manager
from core.utils.cache_cleaner import CacheCleaner

def show_excel_mode(config):
    """Show Excel upload interface with correct template flow"""
    st.markdown("## 📊 Excel Upload Mode")

    # Session state for preview/edit workflow
    if 'excel_mode_stage' not in st.session_state:
        st.session_state.excel_mode_stage = 'idle'  # idle | edit | generated
    if 'excel_processed_data' not in st.session_state:
        st.session_state.excel_processed_data = None
    if 'excel_html_documents' not in st.session_state:
        st.session_state.excel_html_documents = None
    if 'excel_html_documents_edited' not in st.session_state:
        st.session_state.excel_html_documents_edited = None
    if 'excel_bill_df_current' not in st.session_state:
        st.session_state.excel_bill_df_current = None
    if 'excel_extra_df_current' not in st.session_state:
        st.session_state.excel_extra_df_current = None
    if 'excel_word_documents' not in st.session_state:
        st.session_state.excel_word_documents = None
    if 'excel_file_prefix' not in st.session_state:
        st.session_state.excel_file_prefix = None
    if 'excel_save_to_output' not in st.session_state:
        st.session_state.excel_save_to_output = True
    if 'excel_generate_html' not in st.session_state:
        st.session_state.excel_generate_html = True
    if 'excel_generate_pdf' not in st.session_state:
        st.session_state.excel_generate_pdf = True
    if 'excel_generate_word' not in st.session_state:
        st.session_state.excel_generate_word = True
    if 'excel_preview_edit' not in st.session_state:
        st.session_state.excel_preview_edit = False
    if 'excel_doc_index' not in st.session_state:
        st.session_state.excel_doc_index = 0
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 📝 Instructions
        1. Upload your Excel file
        2. Select output options
        3. Generate documents
        4. Download results
        """)
    
    with col2:
        st.info("""
        **Features:**
        - 10mm margins
        - Landscape support
        - No table shrinking
        - Perfect templates
        """)
    
    # Batch Run Button - Prominent at top
    st.markdown("---")
    batch_col1, batch_col2 = st.columns([3, 1])
    with batch_col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.5rem; 
                    border-radius: 10px; 
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);'>
            <h3 style='color: white; margin: 0;'>⚡ Batch Processing Available</h3>
            <p style='color: white; margin: 0.5rem 0 0 0; opacity: 0.9;'>
                Process multiple Excel files at once in Batch Mode
            </p>
        </div>
        """, unsafe_allow_html=True)
    with batch_col2:
        if st.button("📦 Go to Batch Mode", type="secondary", use_container_width=True):
            st.info("💡 Switch to 'Batch Processing' mode from the sidebar")
    
    st.markdown("---")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Excel File",
        type=['xlsx', 'xls', 'xlsm'],
        help="Upload your PWD bill Excel file"
    )
    
    if uploaded_file:
        st.success(f"✅ File uploaded: {uploaded_file.name}")

        # If a different file is uploaded, reset preview/edit state
        current_prefix = uploaded_file.name.split('.')[0]
        if st.session_state.excel_file_prefix and st.session_state.excel_file_prefix != current_prefix:
            st.session_state.excel_mode_stage = 'idle'
            st.session_state.excel_processed_data = None
            st.session_state.excel_html_documents = None
            st.session_state.excel_html_documents_edited = None
            st.session_state.excel_word_documents = None
            if 'excel_pdf_documents' in st.session_state:
                st.session_state.excel_pdf_documents = None
            st.session_state.excel_doc_index = 0
        st.session_state.excel_file_prefix = current_prefix
        
        # Options in a nice card
        st.markdown("""
        <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
            <h4 style='margin: 0 0 0.5rem 0; color: #2d3436;'>📋 Output Options</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            generate_html = st.checkbox("📄 HTML", value=st.session_state.excel_generate_html)
        with col2:
            generate_pdf = st.checkbox("📕 PDF", value=st.session_state.excel_generate_pdf)
        with col3:
            generate_word = st.checkbox("📝 DOCX", value=st.session_state.excel_generate_word)
        with col4:
            save_to_output = st.checkbox("💾 Save", value=st.session_state.excel_save_to_output, 
                                        help="Save to OUTPUT folder")

        # Persist selections
        st.session_state.excel_generate_html = generate_html
        st.session_state.excel_generate_pdf = generate_pdf
        st.session_state.excel_generate_word = generate_word
        st.session_state.excel_save_to_output = save_to_output

        # Optional preview/edit step (only meaningful if generating PDF or Word)
        preview_edit = False
        if generate_pdf or generate_word:
            preview_edit = st.checkbox(
                "📝 Preview & Edit before conversion",
                value=st.session_state.excel_preview_edit,
                help="Shows an Excel-like editable table and HTML preview before converting to PDF/DOCX"
            )
        st.session_state.excel_preview_edit = preview_edit
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        def _coerce_number(v):
            try:
                if v is None:
                    return 0.0
                if isinstance(v, str) and v.strip() == "":
                    return 0.0
                return float(v)
            except Exception:
                return 0.0

        def _is_summary_description(desc: str) -> bool:
            d = (desc or "").strip().lower()
            if not d:
                return False
            return (
                d == "total"
                or "grand total" in d
                or "tender premium" in d
                or ("premium" in d and ("add" in d or "less" in d))
            )

        def _recompute_amount_columns(df):
            """
            Recompute derived Amount columns based on code logic:
            - Amount = Quantity * Rate (row-wise)
            Skips summary rows (Total / Premium / Grand Total) so manual summary lines remain intact.
            """
            import pandas as pd

            if not isinstance(df, pd.DataFrame) or df.empty:
                return df
            if 'Quantity' not in df.columns or 'Rate' not in df.columns:
                return df

            out = df.copy()

            # Ensure numeric
            qty = pd.to_numeric(out['Quantity'], errors='coerce').fillna(0.0)
            rate = pd.to_numeric(out['Rate'], errors='coerce').fillna(0.0)

            # Identify summary rows by Description (if available)
            if 'Description' in out.columns:
                is_summary = out['Description'].astype(str).apply(_is_summary_description)
            else:
                is_summary = False

            computed_amount = qty * rate

            # Only overwrite Amount for non-summary rows when column exists, otherwise create it
            if 'Amount' in out.columns:
                if hasattr(is_summary, '__iter__'):
                    out.loc[~is_summary, 'Amount'] = computed_amount.loc[~is_summary]
                else:
                    out['Amount'] = computed_amount
            else:
                out['Amount'] = computed_amount

            return out

        def _compute_bill_metrics(bill_df, title_updates):
            """Compute simple totals (sum + premium) for live display in editor."""
            import pandas as pd

            if not isinstance(bill_df, pd.DataFrame) or bill_df.empty:
                return {
                    'items_sum': 0.0,
                    'premium_percent': float(_coerce_number((title_updates or {}).get('TENDER PREMIUM %', 0))),
                    'premium_amount': 0.0,
                    'payable': 0.0,
                }

            df = bill_df.copy()
            df = _recompute_amount_columns(df)

            if 'Description' in df.columns:
                is_summary = df['Description'].astype(str).apply(_is_summary_description)
            else:
                is_summary = False

            if 'Amount' in df.columns:
                amounts = pd.to_numeric(df['Amount'], errors='coerce').fillna(0.0)
            else:
                qty = pd.to_numeric(df.get('Quantity', 0), errors='coerce').fillna(0.0)
                rate = pd.to_numeric(df.get('Rate', 0), errors='coerce').fillna(0.0)
                amounts = qty * rate

            items_sum = float(amounts.loc[~is_summary].sum()) if hasattr(is_summary, '__iter__') else float(amounts.sum())
            premium_percent = float(_coerce_number((title_updates or {}).get('TENDER PREMIUM %', 0)))
            premium_type = str((title_updates or {}).get('Premium Type', 'Above')).strip().lower()
            premium_amount = items_sum * (premium_percent / 100.0)
            payable = items_sum - premium_amount if premium_type == 'below' else items_sum + premium_amount

            return {
                'items_sum': items_sum,
                'premium_percent': premium_percent,
                'premium_amount': (-premium_amount if premium_type == 'below' else premium_amount),
                'payable': payable,
            }

        def _compute_simple_sum(df) -> float:
            """Sum non-summary Amounts (or Qty×Rate) for quick preview."""
            import pandas as pd

            if not isinstance(df, pd.DataFrame) or df.empty:
                return 0.0
            df2 = _recompute_amount_columns(df)
            if 'Description' in df2.columns:
                is_summary = df2['Description'].astype(str).apply(_is_summary_description)
            else:
                is_summary = False

            if 'Amount' in df2.columns:
                amounts = pd.to_numeric(df2['Amount'], errors='coerce').fillna(0.0)
            else:
                qty = pd.to_numeric(df2.get('Quantity', 0), errors='coerce').fillna(0.0)
                rate = pd.to_numeric(df2.get('Rate', 0), errors='coerce').fillna(0.0)
                amounts = qty * rate

            return float(amounts.loc[~is_summary].sum()) if hasattr(is_summary, '__iter__') else float(amounts.sum())

        def _apply_edits_to_processed_data(processed_data, title_updates, bill_df, extra_df):
            """Return a new processed_data dict with updated title + DataFrames."""
            import pandas as pd

            updated = dict(processed_data or {})
            title_data = dict(updated.get('title_data', {}) or {})
            for k, v in (title_updates or {}).items():
                title_data[k] = v
            updated['title_data'] = title_data

            # Ensure DataFrames
            if isinstance(bill_df, pd.DataFrame):
                updated['bill_quantity_data'] = _recompute_amount_columns(bill_df)
            if isinstance(extra_df, pd.DataFrame):
                # Extra Items sheet can be irregular; only recompute if it looks like a standard table
                updated['extra_items_data'] = _recompute_amount_columns(extra_df)
            return updated

        def _render_preview_editor(processed_data):
            """Excel-like editor UI that returns edited title fields and edited DataFrames."""
            import pandas as pd

            st.markdown("### 🧾 Preview & Edit (Excel-like)")
            st.info("Edit values below, then generate HTML preview. PDF conversion happens only after you confirm.")

            title_data = dict((processed_data or {}).get('title_data', {}) or {})
            bill_df = (processed_data or {}).get('bill_quantity_data', pd.DataFrame())
            extra_df = (processed_data or {}).get('extra_items_data', pd.DataFrame())

            # Title fields (safe subset)
            st.markdown("#### 🏷️ Key Bill Fields")
            t1, t2, t3 = st.columns(3)
            with t1:
                contractor_name = st.text_input("Contractor Name", value=str(title_data.get('Contractor Name', '')))
                work_order_no = st.text_input("Work Order No", value=str(title_data.get('Work Order No', '')))
                bill_date = st.text_input("Bill Date", value=str(title_data.get('Bill Date', title_data.get('bill_date', '__/__/____'))))
            with t2:
                project_name = st.text_input("Project Name", value=str(title_data.get('Project Name', '')))
                bill_serial = st.text_input("Serial No. of this bill", value=str(title_data.get('Serial No. of this bill :', title_data.get('Serial No. of this bill', ''))))
                premium_percent = st.number_input("Tender Premium %", value=float(_coerce_number(title_data.get('TENDER PREMIUM %', 0))), step=0.25)
            with t3:
                amount_paid_last = st.number_input("Amount Paid Vide Last Bill", value=float(_coerce_number(title_data.get('Amount Paid Vide Last Bill', title_data.get('amount_paid_last_bill', 0)))), step=100.0)
                liquidated = st.number_input("Liquidated Damages", value=float(_coerce_number(title_data.get('Liquidated Damages', 0))), step=100.0)
                premium_type = st.selectbox("Premium Type", options=["Above", "Below"], index=0 if str(title_data.get('Premium Type', 'Above')).strip().lower() != 'below' else 1)

            title_updates = {
                'Contractor Name': contractor_name,
                'Work Order No': work_order_no,
                'Bill Date': bill_date,
                'Project Name': project_name,
                'Serial No. of this bill :': bill_serial,
                'TENDER PREMIUM %': premium_percent,
                'Amount Paid Vide Last Bill': amount_paid_last,
                'Liquidated Damages': liquidated,
                'Premium Type': premium_type,
            }

            st.markdown("---")
            st.markdown("#### 📋 Bill Quantity (Editable Grid)")
            if isinstance(bill_df, pd.DataFrame) and not bill_df.empty:
                # Live computed metrics (based on current data)
                metrics = _compute_bill_metrics(bill_df, title_updates)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Items Sum", f"{metrics['items_sum']:.2f}")
                m2.metric("Premium %", f"{metrics['premium_percent']:.2f}%")
                m3.metric("Premium Amt", f"{metrics['premium_amount']:.2f}")
                m4.metric("Payable (Sum ± Premium)", f"{metrics['payable']:.2f}")

                auto_recalc = st.checkbox(
                    "Auto-recalculate Amount columns (Qty×Rate)",
                    value=True,
                    help="When enabled, Amount will be recomputed from Quantity×Rate before preview/PDF."
                )

                bill_df_for_edit = _recompute_amount_columns(bill_df) if auto_recalc else bill_df
                edited_bill_df = st.data_editor(
                    bill_df_for_edit,
                    use_container_width=True,
                    num_rows="dynamic",
                    key="bill_qty_editor"
                )
                # Apply recompute on the edited version too (so preview generation always matches)
                if auto_recalc:
                    edited_bill_df = _recompute_amount_columns(edited_bill_df)
            else:
                st.warning("No Bill Quantity data found to edit.")
                edited_bill_df = bill_df

            st.markdown("---")
            st.markdown("#### ➕ Extra Items (Editable Grid)")
            if isinstance(extra_df, pd.DataFrame) and not extra_df.empty:
                # Only enable auto-compute if the sheet looks like a standard table
                has_qty_rate = ('Quantity' in extra_df.columns) and ('Rate' in extra_df.columns)
                has_desc = 'Description' in extra_df.columns

                if has_qty_rate:
                    extra_sum = _compute_simple_sum(extra_df)
                    e1, e2 = st.columns(2)
                    e1.metric("Extra Items Sum", f"{extra_sum:.2f}")
                    e2.info("Auto-compute applies only to normal table rows (not summary lines).")

                    extra_auto_recalc = st.checkbox(
                        "Auto-recalculate Extra Items Amount (Qty×Rate)",
                        value=True,
                        help="Recomputes Amount from Quantity×Rate for extra items."
                    )
                    extra_df_for_edit = _recompute_amount_columns(extra_df) if extra_auto_recalc else extra_df
                else:
                    st.info("Extra Items sheet is irregular (no standard Quantity/Rate columns). Editing will be manual.")
                    extra_auto_recalc = False
                    extra_df_for_edit = extra_df

                edited_extra_df = st.data_editor(
                    extra_df_for_edit,
                    use_container_width=True,
                    num_rows="dynamic",
                    key="extra_items_editor"
                )
                if extra_auto_recalc:
                    edited_extra_df = _recompute_amount_columns(edited_extra_df)
            else:
                st.info("No Extra Items sheet detected (this is okay).")
                edited_extra_df = extra_df

            return title_updates, edited_bill_df, edited_extra_df

        # Generate button - large and prominent
        if st.button("🚀 Generate All Documents", type="primary", use_container_width=True):
            # Clean cache before processing
            CacheCleaner.clean_cache(verbose=False)
            
            with st.spinner("Processing..."):
                try:
                    # Get output manager (only if saving to OUTPUT folder)
                    output_mgr = get_output_manager() if save_to_output else None
                    
                    # Get file prefix for subfolder
                    file_prefix = uploaded_file.name.split('.')[0]
                    st.session_state.excel_file_prefix = file_prefix
                    
                    # Create subfolder for this file if saving to OUTPUT
                    if save_to_output and output_mgr:
                        output_mgr.set_source_file(file_prefix)
                    
                    # Step 1: Process Excel
                    from core.processors.excel_processor import ExcelProcessor
                    processor = ExcelProcessor()
                    processed_data = processor.process_excel(uploaded_file)
                    st.session_state.excel_processed_data = processed_data
                    
                    st.success("✅ Excel processed successfully!")

                    # If preview/edit enabled, switch to edit stage and stop here
                    if preview_edit:
                        st.session_state.excel_mode_stage = 'edit'
                        st.session_state.excel_html_documents = None
                        st.session_state.excel_word_documents = None
                        st.rerun()

                    # Otherwise continue existing direct generation flow (no edits)
                    # Step 2: Generate HTML using templates
                    from core.generators.document_generator import DocumentGenerator
                    doc_gen = DocumentGenerator(processed_data)
                    html_documents = doc_gen.generate_all_documents()
                    st.success(f"✅ Generated {len(html_documents)} HTML documents")

                    # Step 3: Generate Word documents if requested
                    word_documents = {}
                    saved_files = []
                    if generate_word:
                        from core.generators.word_generator import WordGenerator
                        word_gen = WordGenerator()
                        word_documents = word_gen.generate_all_docx(html_documents)

                        # Save to OUTPUT folder if requested
                        if save_to_output and output_mgr:
                            for doc_name, docx_bytes in word_documents.items():
                                saved_path = output_mgr.save_file(docx_bytes, doc_name, 'docx')
                                saved_files.append(saved_path)
                        st.success(f"✅ Generated {len(word_documents)} Word documents")

                    # Step 4: Convert to PDF if requested
                    pdf_documents = {}
                    if generate_pdf:
                        from core.generators.pdf_generator_fixed import FixedPDFGenerator
                        pdf_generator = FixedPDFGenerator(margin_mm=10)
                        progress_bar = st.progress(0)
                        for idx, (doc_name, html_content) in enumerate(html_documents.items()):
                            landscape = 'deviation' in doc_name.lower()
                            pdf_bytes = pdf_generator.auto_convert(html_content, landscape=landscape, doc_name=doc_name)
                            pdf_documents[doc_name] = pdf_bytes
                            if save_to_output and output_mgr:
                                saved_path = output_mgr.save_file(pdf_bytes, doc_name, 'pdf')
                                saved_files.append(saved_path)
                            progress_bar.progress((idx + 1) / len(html_documents))
                        del pdf_generator
                        gc.collect()
                        st.success(f"✅ Generated {len(pdf_documents)} PDF documents")

                    # Save HTML files if requested
                    if generate_html and save_to_output and output_mgr:
                        for doc_name, html_content in html_documents.items():
                            saved_path = output_mgr.save_text_file(html_content, doc_name, 'html')
                            saved_files.append(saved_path)

                    # Display download options
                    st.markdown("---")
                    st.markdown("### 📥 Download Documents")
                    if save_to_output and saved_files:
                        subfolder_name = output_mgr.current_subfolder.name if output_mgr.current_subfolder else "OUTPUT"
                        st.info(f"📁 Files saved to: OUTPUT/{subfolder_name}/ ({len(saved_files)} files)")
                    else:
                        st.info("📥 Files ready for download to your browser's download folder")

                    if generate_html:
                        st.markdown("#### HTML Documents")
                        for doc_name, html_content in html_documents.items():
                            st.download_button(
                                label=f"📄 {doc_name}",
                                data=html_content,
                                file_name=f"{doc_name}.html",
                                mime="text/html",
                                key=f"html_{doc_name}"
                            )

                    if generate_pdf:
                        st.markdown("#### PDF Documents")
                        for doc_name, pdf_bytes in pdf_documents.items():
                            orientation = "🔄 Landscape" if 'deviation' in doc_name.lower() else "📄 Portrait"
                            st.download_button(
                                label=f"📕 {doc_name} ({orientation})",
                                data=pdf_bytes,
                                file_name=f"{doc_name}.pdf",
                                mime="application/pdf",
                                key=f"pdf_{doc_name}"
                            )

                    if generate_word:
                        st.markdown("#### 📝 Word Documents")
                        for doc_name, docx_bytes in word_documents.items():
                            st.download_button(
                                label=f"📝 {doc_name}",
                                data=docx_bytes,
                                file_name=f"{doc_name}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"docx_{doc_name}"
                            )

                    # Multi-format export section
                    st.markdown("---")
                    st.markdown("#### 📊 Data Export (CSV & JSON)")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Export to CSV
                        try:
                            import pandas as pd
                            # Create CSV from processed data
                            items_data = []
                            if 'items' in processed_data:
                                for item in processed_data['items']:
                                    items_data.append({
                                        'Item No': item.get('item_no', ''),
                                        'Description': item.get('description', ''),
                                        'Quantity': item.get('quantity', 0),
                                        'Rate': item.get('rate', 0),
                                        'Unit': item.get('unit', ''),
                                        'Amount': item.get('quantity', 0) * item.get('rate', 0)
                                    })
                            
                            if items_data:
                                df = pd.DataFrame(items_data)
                                csv_data = df.to_csv(index=False)
                                
                                st.download_button(
                                    label="📄 Download CSV",
                                    data=csv_data,
                                    file_name=f"{file_prefix}_bill_data.csv",
                                    mime="text/csv",
                                    key="csv_export",
                                    use_container_width=True
                                )
                            else:
                                st.info("No item data available for CSV export")
                        except Exception as e:
                            st.error(f"CSV export error: {str(e)}")
                    
                    with col2:
                        # Export to JSON
                        try:
                            import json
                            # Create JSON from processed data
                            json_data = {
                                'bill_info': {
                                    'file_name': uploaded_file.name,
                                    'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'bill_serial': processed_data.get('bill_serial', ''),
                                    'contractor_name': processed_data.get('contractor_name', ''),
                                    'work_name': processed_data.get('work_name', '')
                                },
                                'totals': processed_data.get('totals', {}),
                                'items': processed_data.get('items', []),
                                'extra_items': processed_data.get('extra_items', [])
                            }
                            
                            json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
                            
                            st.download_button(
                                label="📋 Download JSON",
                                data=json_str,
                                file_name=f"{file_prefix}_bill_data.json",
                                mime="application/json",
                                key="json_export",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"JSON export error: {str(e)}")
                    
                    # ZIP download
                    st.markdown("---")
                    if (generate_pdf or generate_html or generate_word):
                        st.markdown("#### 📦 Bulk Download")
                        
                        # Create ZIP for browser download
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            if generate_pdf:
                                for doc_name, pdf_bytes in pdf_documents.items():
                                    zip_file.writestr(f"pdf/{doc_name}.pdf", pdf_bytes)
                            if generate_html:
                                for doc_name, html_content in html_documents.items():
                                    zip_file.writestr(f"html/{doc_name}.html", html_content)
                            if generate_word:
                                for doc_name, docx_bytes in word_documents.items():
                                    zip_file.writestr(f"word/{doc_name}.docx", docx_bytes)
                            
                            # Add CSV and JSON to ZIP
                            try:
                                import pandas as pd
                                import json
                                
                                # Add CSV
                                items_data = []
                                if 'items' in processed_data:
                                    for item in processed_data['items']:
                                        items_data.append({
                                            'Item No': item.get('item_no', ''),
                                            'Description': item.get('description', ''),
                                            'Quantity': item.get('quantity', 0),
                                            'Rate': item.get('rate', 0),
                                            'Unit': item.get('unit', ''),
                                            'Amount': item.get('quantity', 0) * item.get('rate', 0)
                                        })
                                
                                if items_data:
                                    df = pd.DataFrame(items_data)
                                    csv_data = df.to_csv(index=False)
                                    zip_file.writestr(f"data/{file_prefix}_bill_data.csv", csv_data)
                                
                                # Add JSON
                                json_data = {
                                    'bill_info': {
                                        'file_name': uploaded_file.name,
                                        'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        'bill_serial': processed_data.get('bill_serial', ''),
                                        'contractor_name': processed_data.get('contractor_name', ''),
                                        'work_name': processed_data.get('work_name', '')
                                    },
                                    'totals': processed_data.get('totals', {}),
                                    'items': processed_data.get('items', []),
                                    'extra_items': processed_data.get('extra_items', [])
                                }
                                json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
                                zip_file.writestr(f"data/{file_prefix}_bill_data.json", json_str)
                            except Exception as e:
                                print(f"Error adding data files to ZIP: {e}")
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        file_prefix = uploaded_file.name.split('.')[0]
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.download_button(
                                label="📦 Download All (ZIP)",
                                data=zip_buffer.getvalue(),
                                file_name=f"{file_prefix}_documents_{timestamp}.zip",
                                mime="application/zip",
                                key="zip_all"
                            )
                        
                        # If saved to OUTPUT, offer ZIP of subfolder
                        if save_to_output and output_mgr and output_mgr.current_subfolder:
                            with col2:
                                zip_bytes, zip_filename = output_mgr.create_zip()
                                st.download_button(
                                    label="📦 Download Subfolder (ZIP)",
                                    data=zip_bytes,
                                    file_name=zip_filename,
                                    mime="application/zip",
                                    key="zip_subfolder",
                                    help=f"Download all files from {output_mgr.current_subfolder.name}"
                                )
                    
                    # Clean up memory
                    del html_documents
                    del pdf_documents
                    if generate_word:
                        del word_documents
                    del processed_data
                    del doc_gen
                    gc.collect()
                    
                    # Clean cache after processing
                    CacheCleaner.clean_cache(verbose=False)
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    if hasattr(config, 'ui') and hasattr(config.ui, 'show_debug') and config.ui.show_debug:
                        import traceback
                        st.code(traceback.format_exc())

        # Preview/Edit stage (after processing, before conversion)
        if st.session_state.excel_mode_stage == 'edit' and st.session_state.excel_processed_data is not None:
            st.markdown("---")
            title_updates, edited_bill_df, edited_extra_df = _render_preview_editor(st.session_state.excel_processed_data)

            col_a, col_b, col_c = st.columns([2, 2, 3])
            with col_a:
                if st.button("🧩 Generate HTML Preview (from edits)", type="primary", use_container_width=True):
                    with st.spinner("Generating HTML from edited data..."):
                        try:
                            # Build updated processed data
                            updated_processed = _apply_edits_to_processed_data(
                                st.session_state.excel_processed_data,
                                title_updates,
                                edited_bill_df,
                                edited_extra_df
                            )

                            from core.generators.document_generator import DocumentGenerator
                            doc_gen = DocumentGenerator(updated_processed)
                            html_documents = doc_gen.generate_all_documents()
                            st.session_state.excel_html_documents = html_documents
                            st.session_state.excel_html_documents_edited = dict(html_documents)
                            st.session_state.excel_processed_data = updated_processed  # persist edits
                            st.session_state.excel_bill_df_current = edited_bill_df
                            st.session_state.excel_extra_df_current = edited_extra_df

                            # Optionally generate Word at the same time (from edited HTML)
                            word_documents = {}
                            if st.session_state.excel_generate_word:
                                from core.generators.word_generator import WordGenerator
                                word_gen = WordGenerator()
                                word_documents = word_gen.generate_all_docx(html_documents)
                            st.session_state.excel_word_documents = word_documents

                            st.session_state.excel_mode_stage = 'generated'
                            st.session_state.excel_doc_index = 0
                            st.success(f"✅ HTML preview ready ({len(html_documents)} documents)")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to generate HTML preview: {e}")

            with col_b:
                if st.button("🔁 Re-process Excel (discard edits)", use_container_width=True):
                    st.session_state.excel_mode_stage = 'idle'
                    st.session_state.excel_processed_data = None
                    st.session_state.excel_html_documents = None
                    st.session_state.excel_word_documents = None
                    st.rerun()

            with col_c:
                st.info("Tip: Generate HTML preview first, then convert to PDF when satisfied.")

        # Generated stage: show HTML previews + conversion buttons
        if st.session_state.excel_mode_stage == 'generated' and st.session_state.excel_html_documents:
            st.markdown("---")
            st.markdown("### 👀 Output Preview & Edit (before PDF)")

            # Ensure edited dict exists
            if st.session_state.excel_html_documents_edited is None:
                st.session_state.excel_html_documents_edited = dict(st.session_state.excel_html_documents)

            # Shared fields regeneration: keep all docs consistent when First Page fields change
            st.markdown("#### 🔁 Update shared fields (propagates to all outputs)")
            st.caption("Use this when a First Page value should update everywhere (Deviation, Scrutiny, Certificates, etc.).")

            if 'excel_shared_snapshot' not in st.session_state:
                st.session_state.excel_shared_snapshot = {}
            if 'excel_auto_sync_shared' not in st.session_state:
                st.session_state.excel_auto_sync_shared = True

            title_data_now = dict((st.session_state.excel_processed_data or {}).get('title_data', {}) or {})
            sf1, sf2, sf3, sf4 = st.columns([2, 2, 2, 2])
            with sf1:
                sf_contractor = st.text_input("Contractor Name (global)", value=str(title_data_now.get('Contractor Name', '')), key="sf_contractor")
                sf_work_order = st.text_input("Work Order No (global)", value=str(title_data_now.get('Work Order No', '')), key="sf_work_order")
            with sf2:
                sf_project = st.text_input("Project Name (global)", value=str(title_data_now.get('Project Name', '')), key="sf_project")
                sf_bill_date = st.text_input("Bill Date (global)", value=str(title_data_now.get('Bill Date', title_data_now.get('bill_date', '__/__/____'))), key="sf_bill_date")
            with sf3:
                sf_bill_serial = st.text_input(
                    "Serial No. of this bill (global)",
                    value=str(title_data_now.get('Serial No. of this bill :', title_data_now.get('Serial No. of this bill', ''))),
                    key="sf_bill_serial"
                )
                sf_premium_percent = st.number_input(
                    "Tender Premium % (global)",
                    value=float(_coerce_number(title_data_now.get('TENDER PREMIUM %', 0))),
                    step=0.25,
                    key="sf_premium_percent"
                )
            with sf4:
                sf_premium_type = st.selectbox(
                    "Premium Type (global)",
                    options=["Above", "Below"],
                    index=0 if str(title_data_now.get('Premium Type', 'Above')).strip().lower() != 'below' else 1,
                    key="sf_premium_type"
                )
                reset_manual_html = st.checkbox(
                    "Reset manual per-page HTML edits on regenerate",
                    value=True,
                    help="If you edited HTML per-page, regeneration will overwrite those edits to keep everything consistent."
                )
                st.session_state.excel_auto_sync_shared = st.checkbox(
                    "Auto-sync shared fields instantly",
                    value=st.session_state.excel_auto_sync_shared,
                    help="When enabled, changing a shared field will immediately update all outputs. Premium changes trigger full regeneration."
                )

            shared_updates = {
                'Contractor Name': sf_contractor,
                'Work Order No': sf_work_order,
                'Project Name': sf_project,
                'Bill Date': sf_bill_date,
                'Serial No. of this bill :': sf_bill_serial,
                'TENDER PREMIUM %': sf_premium_percent,
                'Premium Type': sf_premium_type,
            }

            # Auto-sync behavior:
            # - For text fields: do safe string replace across all HTML docs (fast).
            # - For premium fields: regenerate all docs (affects computed totals/cells).
            snap = st.session_state.excel_shared_snapshot or {}
            text_keys = ['Contractor Name', 'Work Order No', 'Project Name', 'Bill Date', 'Serial No. of this bill :']
            premium_keys = ['TENDER PREMIUM %', 'Premium Type']

            def _apply_text_replacements(prev_map, new_map):
                if not st.session_state.excel_html_documents_edited:
                    return
                for k in text_keys:
                    prev = str(prev_map.get(k, '') or '')
                    newv = str(new_map.get(k, '') or '')
                    if prev and newv and prev != newv:
                        for dn, html in list(st.session_state.excel_html_documents_edited.items()):
                            if isinstance(html, str):
                                st.session_state.excel_html_documents_edited[dn] = html.replace(prev, newv)

            premium_changed = any(snap.get(k) != shared_updates.get(k) for k in premium_keys)
            text_changed = any(str(snap.get(k, '') or '') != str(shared_updates.get(k, '') or '') for k in text_keys)

            if st.session_state.excel_auto_sync_shared and (text_changed or premium_changed) and snap:
                # Update fast text replacements immediately
                if text_changed and not premium_changed:
                    _apply_text_replacements(snap, shared_updates)
                    # Also update title_data so future regenerations stay consistent
                    st.session_state.excel_processed_data = _apply_edits_to_processed_data(
                        st.session_state.excel_processed_data,
                        shared_updates,
                        st.session_state.excel_bill_df_current,
                        st.session_state.excel_extra_df_current
                    )
                    st.session_state.excel_word_documents = None
                    if 'excel_pdf_documents' in st.session_state:
                        st.session_state.excel_pdf_documents = None
                # Premium changes need full regeneration to keep all computed cells aligned
                if premium_changed:
                    with st.spinner("Auto-sync: regenerating documents (premium change affects totals)..."):
                        try:
                            updated_processed = _apply_edits_to_processed_data(
                                st.session_state.excel_processed_data,
                                shared_updates,
                                st.session_state.excel_bill_df_current,
                                st.session_state.excel_extra_df_current
                            )
                            from core.generators.document_generator import DocumentGenerator
                            doc_gen = DocumentGenerator(updated_processed)
                            html_documents = doc_gen.generate_all_documents()
                            st.session_state.excel_processed_data = updated_processed
                            st.session_state.excel_html_documents = html_documents
                            st.session_state.excel_html_documents_edited = dict(html_documents) if reset_manual_html else dict(html_documents)
                            st.session_state.excel_word_documents = None
                            if 'excel_pdf_documents' in st.session_state:
                                st.session_state.excel_pdf_documents = None
                        except Exception as e:
                            st.error(f"❌ Auto-regeneration failed: {e}")
                    st.rerun()

            # Initialize/refresh snapshot after possible changes
            st.session_state.excel_shared_snapshot = dict(shared_updates)

            if st.button("🔁 Apply shared field changes to ALL outputs", type="secondary", use_container_width=True):
                with st.spinner("Regenerating all documents with updated shared fields..."):
                    try:
                        updated_processed = _apply_edits_to_processed_data(
                            st.session_state.excel_processed_data,
                            shared_updates,
                            st.session_state.excel_bill_df_current,
                            st.session_state.excel_extra_df_current
                        )
                        from core.generators.document_generator import DocumentGenerator
                        doc_gen = DocumentGenerator(updated_processed)
                        html_documents = doc_gen.generate_all_documents()
                        st.session_state.excel_processed_data = updated_processed
                        st.session_state.excel_html_documents = html_documents
                        if reset_manual_html:
                            st.session_state.excel_html_documents_edited = dict(html_documents)
                        else:
                            # Keep existing edited docs where possible, fall back to regenerated
                            merged = dict(html_documents)
                            for k, v in (st.session_state.excel_html_documents_edited or {}).items():
                                if k in merged:
                                    merged[k] = v
                            st.session_state.excel_html_documents_edited = merged
                        st.session_state.excel_word_documents = None  # needs regen if desired
                        if 'excel_pdf_documents' in st.session_state:
                            st.session_state.excel_pdf_documents = None
                        st.success("✅ Updated. All outputs are now consistent.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Regeneration failed: {e}")

            enable_per_doc_editing = st.checkbox(
                "Enable per-document editing (recommended)",
                value=True,
                help="Edit each of the generated outputs individually before downloading / converting to PDF"
            )

            import streamlit.components.v1 as components
            html_docs_view = st.session_state.excel_html_documents_edited if enable_per_doc_editing else st.session_state.excel_html_documents

            # Show editable pages one-by-one (Prev/Next)
            doc_names = list(html_docs_view.keys())
            if not doc_names:
                st.warning("No documents to preview.")
            else:
                # Keep index in range
                if st.session_state.excel_doc_index >= len(doc_names):
                    st.session_state.excel_doc_index = 0

                nav1, nav2, nav3, nav4 = st.columns([1, 1, 3, 1])
                with nav1:
                    if st.button("⬅️ Previous", use_container_width=True, disabled=(len(doc_names) <= 1)):
                        st.session_state.excel_doc_index = (st.session_state.excel_doc_index - 1) % len(doc_names)
                        st.rerun()
                with nav2:
                    if st.button("Next ➡️", use_container_width=True, disabled=(len(doc_names) <= 1)):
                        st.session_state.excel_doc_index = (st.session_state.excel_doc_index + 1) % len(doc_names)
                        st.rerun()
                with nav3:
                    selected_name = st.selectbox(
                        "Select document",
                        options=doc_names,
                        index=st.session_state.excel_doc_index,
                        key="doc_select_one_by_one"
                    )
                    st.session_state.excel_doc_index = doc_names.index(selected_name)
                with nav4:
                    st.metric("Page", f"{st.session_state.excel_doc_index + 1}/{len(doc_names)}")

                doc_name = doc_names[st.session_state.excel_doc_index]
                html_content = html_docs_view[doc_name]

                st.markdown(f"#### 📄 {doc_name}")
                tab_preview, tab_edit = st.tabs(["Preview", "Edit HTML"])
                with tab_preview:
                    components.html(html_content, height=650, scrolling=True)
                with tab_edit:
                    if enable_per_doc_editing:
                        edited_html = st.text_area(
                            "HTML (editable)",
                            value=html_content,
                            height=420,
                            key=f"html_editor_single_{doc_name}"
                        )
                        colx, coly = st.columns([1, 2])
                        with colx:
                            if st.button("💾 Save edits", key=f"save_html_single_{doc_name}", use_container_width=True):
                                st.session_state.excel_html_documents_edited[doc_name] = edited_html
                                st.success("Saved.")
                                st.rerun()
                        with coly:
                            if st.button("↩️ Reset to generated", key=f"reset_html_single_{doc_name}", use_container_width=True):
                                st.session_state.excel_html_documents_edited[doc_name] = st.session_state.excel_html_documents.get(doc_name, edited_html)
                                st.info("Reset.")
                                st.rerun()
                    else:
                        st.info("Per-document editing is disabled above.")

            st.markdown("---")
            st.markdown("### ✅ Finalize & Download")

            # Prepare output manager if needed
            output_mgr = get_output_manager() if st.session_state.excel_save_to_output else None
            if st.session_state.excel_save_to_output and output_mgr and st.session_state.excel_file_prefix:
                output_mgr.set_source_file(st.session_state.excel_file_prefix)

            saved_files = []

            # HTML downloads (and optional save)
            if st.session_state.excel_generate_html:
                st.markdown("#### HTML Documents")
                html_docs_for_output = st.session_state.excel_html_documents_edited or st.session_state.excel_html_documents
                for doc_name, html_content in html_docs_for_output.items():
                    st.download_button(
                        label=f"📄 {doc_name}",
                        data=html_content,
                        file_name=f"{doc_name}.html",
                        mime="text/html",
                        key=f"html_preview_{doc_name}"
                    )
                    if st.session_state.excel_save_to_output and output_mgr:
                        saved_files.append(output_mgr.save_text_file(html_content, doc_name, 'html'))

            # Word downloads (and optional save)
            if st.session_state.excel_generate_word:
                st.markdown("#### 📝 Word Documents")
                if st.button("📝 Generate DOCX from current (edited) HTML", use_container_width=True):
                    with st.spinner("Generating DOCX..."):
                        try:
                            from core.generators.word_generator import WordGenerator
                            html_docs_for_word = st.session_state.excel_html_documents_edited or st.session_state.excel_html_documents
                            word_gen = WordGenerator()
                            st.session_state.excel_word_documents = word_gen.generate_all_docx(html_docs_for_word)
                            st.success(f"✅ DOCX generated ({len(st.session_state.excel_word_documents)} documents)")
                        except Exception as e:
                            st.error(f"❌ DOCX generation failed: {e}")

                if st.session_state.excel_word_documents:
                    for doc_name, docx_bytes in st.session_state.excel_word_documents.items():
                        st.download_button(
                            label=f"📝 {doc_name}",
                            data=docx_bytes,
                            file_name=f"{doc_name}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"docx_preview_{doc_name}"
                        )
                        if st.session_state.excel_save_to_output and output_mgr:
                            saved_files.append(output_mgr.save_file(docx_bytes, doc_name, 'docx'))

            # PDF conversion is explicit: only after preview
            if st.session_state.excel_generate_pdf:
                st.markdown("#### PDF Documents")
                if st.button("📕 Convert Preview to PDF", type="primary", use_container_width=True):
                    with st.spinner("Converting to PDF..."):
                        try:
                            from core.generators.pdf_generator_fixed import FixedPDFGenerator
                            pdf_generator = FixedPDFGenerator(margin_mm=10)
                            pdf_documents = {}
                            progress_bar = st.progress(0)
                            html_docs = st.session_state.excel_html_documents_edited or st.session_state.excel_html_documents
                            for idx, (doc_name, html_content) in enumerate(html_docs.items()):
                                landscape = 'deviation' in doc_name.lower()
                                pdf_bytes = pdf_generator.auto_convert(html_content, landscape=landscape, doc_name=doc_name)
                                pdf_documents[doc_name] = pdf_bytes
                                progress_bar.progress((idx + 1) / len(html_docs))
                                if st.session_state.excel_save_to_output and output_mgr:
                                    saved_files.append(output_mgr.save_file(pdf_bytes, doc_name, 'pdf'))

                            st.session_state.excel_pdf_documents = pdf_documents
                            st.success(f"✅ PDF generated ({len(pdf_documents)} documents)")
                        except Exception as e:
                            st.error(f"❌ PDF conversion failed: {e}")

                if 'excel_pdf_documents' in st.session_state and st.session_state.excel_pdf_documents:
                    for doc_name, pdf_bytes in st.session_state.excel_pdf_documents.items():
                        orientation = "🔄 Landscape" if 'deviation' in doc_name.lower() else "📄 Portrait"
                        st.download_button(
                            label=f"📕 {doc_name} ({orientation})",
                            data=pdf_bytes,
                            file_name=f"{doc_name}.pdf",
                            mime="application/pdf",
                            key=f"pdf_preview_{doc_name}"
                        )

            if st.session_state.excel_save_to_output and saved_files and output_mgr:
                subfolder_name = output_mgr.current_subfolder.name if output_mgr.current_subfolder else "OUTPUT"
                st.info(f"📁 Files saved to: OUTPUT/{subfolder_name}/ ({len(saved_files)} files)")
