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
        
        # Options in a nice card
        st.markdown("""
        <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
            <h4 style='margin: 0 0 0.5rem 0; color: #2d3436;'>📋 Output Options</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            generate_html = st.checkbox("📄 HTML", value=True)
        with col2:
            generate_pdf = st.checkbox("📕 PDF", value=True)
        with col3:
            generate_word = st.checkbox("📝 DOCX", value=True)
        with col4:
            save_to_output = st.checkbox("💾 Save", value=True, 
                                        help="Save to OUTPUT folder")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
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
                    
                    # Create subfolder for this file if saving to OUTPUT
                    if save_to_output and output_mgr:
                        output_mgr.set_source_file(file_prefix)
                    
                    # Step 1: Process Excel
                    from core.processors.excel_processor import ExcelProcessor
                    processor = ExcelProcessor()
                    processed_data = processor.process_excel(uploaded_file)
                    
                    st.success("✅ Excel processed successfully!")
                    
                    # Step 2: Generate HTML using templates
                    from core.generators.document_generator import DocumentGenerator
                    doc_gen = DocumentGenerator(processed_data)
                    html_documents = doc_gen.generate_all_documents()
                    
                    st.success(f"✅ Generated {len(html_documents)} HTML documents")
                    
                    # Initialize saved_files list before any usage
                    saved_files = []
                    
                    # Step 3: Generate Word documents if requested
                    word_documents = {}
                    if generate_word:
                        from core.generators.word_generator import WordGenerator
                        word_gen = WordGenerator()
                        word_documents = word_gen.generate_all_docx(html_documents)
                        
                        # Save to OUTPUT folder if requested
                        if save_to_output and output_mgr:
                            for doc_name, docx_bytes in word_documents.items():
                                saved_path = output_mgr.save_file(
                                    docx_bytes,
                                    doc_name,
                                    'docx'
                                )
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
                            pdf_bytes = pdf_generator.auto_convert(
                                html_content,
                                landscape=landscape,
                                doc_name=doc_name
                            )
                            pdf_documents[doc_name] = pdf_bytes
                            
                            # Save to OUTPUT folder if requested
                            if save_to_output and output_mgr:
                                saved_path = output_mgr.save_file(
                                    pdf_bytes,
                                    doc_name,  # Just doc name, no prefix (folder has it)
                                    'pdf'
                                )
                                saved_files.append(saved_path)
                            
                            progress_bar.progress((idx + 1) / len(html_documents))
                        
                        # Explicitly clean up large objects
                        del pdf_generator
                        gc.collect()
                        
                        st.success(f"✅ Generated {len(pdf_documents)} PDF documents")
                    
                    # Save HTML files if requested
                    if generate_html and save_to_output and output_mgr:
                        for doc_name, html_content in html_documents.items():
                            saved_path = output_mgr.save_text_file(
                                html_content,
                                doc_name,  # Just doc name, no prefix (folder has it)
                                'html'
                            )
                            saved_files.append(saved_path)
                    
                    # Display download options
                    st.markdown("---")
                    st.markdown("### 📥 Download Documents")
                    
                    # Show saved files location if applicable
                    if save_to_output and saved_files:
                        subfolder_name = output_mgr.current_subfolder.name if output_mgr.current_subfolder else "OUTPUT"
                        st.info(f"📁 Files saved to: OUTPUT/{subfolder_name}/ ({len(saved_files)} files)")
                    else:
                        st.info(f"📥 Files ready for download to your browser's download folder")
                    
                    # Individual downloads
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
