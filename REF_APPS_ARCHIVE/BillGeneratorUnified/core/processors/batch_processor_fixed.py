"""
Fixed Batch Processor - Uses Correct Template Flow
Processes multiple Excel files with proper PDF generation
With automatic cache cleaning and centralized output management
"""
import streamlit as st
from pathlib import Path
import io
import zipfile
from datetime import datetime
import time
import gc

# Import utilities
from core.utils.output_manager import get_output_manager
from core.utils.cache_cleaner import CacheCleaner

def show_batch_mode(config):
    """Show batch processing interface with correct template flow"""
    st.markdown("## 📦 Batch Processing Mode")
    
    # Prominent header
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; 
                border-radius: 12px; 
                text-align: center;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                margin-bottom: 2rem;'>
        <h2 style='color: white; margin: 0; font-size: 2rem;'>⚡ Batch Processing</h2>
        <p style='color: white; margin: 0.5rem 0 0 0; opacity: 0.95; font-size: 1.1rem;'>
            Process multiple Excel files simultaneously with high-speed generation
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload with better styling
    uploaded_files = st.file_uploader(
        "📁 Upload Multiple Excel Files",
        type=['xlsx', 'xls', 'xlsm'],
        accept_multiple_files=True,
        help="Select multiple PWD bill Excel files for batch processing"
    )
    
    if uploaded_files:
        # Success message with file count
        st.markdown(f"""
        <div style='background: #d4edda; 
                    padding: 1rem; 
                    border-radius: 8px; 
                    border-left: 4px solid #00b894;
                    margin: 1rem 0;'>
            <strong style='color: #155724;'>✅ {len(uploaded_files)} files ready for processing</strong>
        </div>
        """, unsafe_allow_html=True)
        
        # Show file list in a nice card
        with st.expander("📂 View Uploaded Files", expanded=False):
            for idx, file in enumerate(uploaded_files, 1):
                st.markdown(f"**{idx}.** {file.name}")
        
        st.markdown("---")
        
        # Options in organized sections
        st.markdown("### ⚙️ Processing Options")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            generate_html = st.checkbox("📄 HTML", value=True)
        with col2:
            generate_pdf = st.checkbox("📕 PDF", value=True)
        with col3:
            generate_word = st.checkbox("📝 DOCX", value=True)
        with col4:
            create_folders = st.checkbox("📁 Folders", value=True, 
                                        help="Create separate folder per file")
        
        save_to_output = st.checkbox("💾 Save to OUTPUT folder", value=True,
                                    help="Uncheck to download ZIP only")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Large prominent batch run button
        if st.button("⚡ RUN BATCH PROCESSING", type="primary", use_container_width=True):
            # Clean cache before processing
            CacheCleaner.clean_cache(verbose=False)
            
            # Get output manager (only if saving to OUTPUT folder)
            output_mgr = get_output_manager() if save_to_output else None
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            all_pdfs = []
            all_htmls = []
            all_words = []
            total_files = len(uploaded_files)
            results = []
            saved_files = []
            
            for idx, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {idx+1}/{total_files}: {uploaded_file.name}")
                
                try:
                    # Step 1: Process Excel
                    from core.processors.excel_processor import ExcelProcessor
                    processor = ExcelProcessor()
                    processed_data = processor.process_excel(uploaded_file)
                    
                    # Get file prefix for subfolder
                    file_prefix = uploaded_file.name.split('.')[0]
                    
                    # Create subfolder for this file if saving to OUTPUT
                    if save_to_output and output_mgr:
                        output_mgr.set_source_file(file_prefix)
                    
                    # Step 2: Generate HTML using templates
                    from core.generators.document_generator import DocumentGenerator
                    doc_gen = DocumentGenerator(processed_data)
                    html_documents = doc_gen.generate_all_documents()
                    
                    # Step 3: Generate Word documents if requested
                    if generate_word:
                        from core.generators.word_generator import WordGenerator
                        word_gen = WordGenerator()
                        word_documents = word_gen.generate_all_docx(html_documents)
                        
                        for doc_name, docx_bytes in word_documents.items():
                            word_filename = f"{file_prefix}_{doc_name}.docx"
                            all_words.append((word_filename, docx_bytes))
                            
                            # Save to OUTPUT folder if requested
                            if save_to_output and output_mgr:
                                saved_path = output_mgr.save_file(
                                    docx_bytes,
                                    doc_name,
                                    'docx'
                                )
                                saved_files.append(saved_path)
                    
                    # Step 4: Convert to PDF if requested
                    if generate_pdf:
                        from core.generators.pdf_generator_fixed import FixedPDFGenerator
                        pdf_generator = FixedPDFGenerator(margin_mm=10)
                        
                        for doc_name, html_content in html_documents.items():
                            landscape = 'deviation' in doc_name.lower()
                            pdf_bytes = pdf_generator.auto_convert(
                                html_content,
                                landscape=landscape,
                                doc_name=doc_name
                            )
                            
                            pdf_filename = f"{file_prefix}_{doc_name}.pdf"
                            all_pdfs.append((pdf_filename, pdf_bytes))
                            
                            # Save to OUTPUT folder if requested
                            if save_to_output and output_mgr:
                                saved_path = output_mgr.save_file(
                                    pdf_bytes,
                                    doc_name,  # Just doc name, no prefix (folder has it)
                                    'pdf'
                                )
                                saved_files.append(saved_path)
                            
                            if generate_html:
                                html_filename = f"{file_prefix}_{doc_name}.html"
                                all_htmls.append((html_filename, html_content))
                                
                                # Save HTML to OUTPUT folder if requested
                                if save_to_output and output_mgr:
                                    saved_path = output_mgr.save_text_file(
                                        html_content,
                                        doc_name,  # Just doc name, no prefix (folder has it)
                                        'html'
                                    )
                                    saved_files.append(saved_path)
                        
                        # Clean up memory
                        del pdf_generator
                        gc.collect()
                    
                    # Clean up after each file
                    del html_documents
                    del processed_data
                    del doc_gen
                    gc.collect()
                    
                    results.append({
                        'file': uploaded_file.name,
                        'status': 'success',
                        'docs': len(all_pdfs) // (idx + 1) if all_pdfs else 0
                    })
                    
                    # Clean cache every 10 files
                    if (idx + 1) % 10 == 0:
                        CacheCleaner.clean_cache(verbose=False)
                    
                except Exception as e:
                    st.error(f"❌ Failed: {uploaded_file.name} - {str(e)}")
                    results.append({
                        'file': uploaded_file.name,
                        'status': 'error',
                        'error': str(e)
                    })
                
                progress_bar.progress((idx + 1) / total_files)
            
            status_text.text("✅ Batch processing complete!")
            
            # Show results summary
            st.markdown("---")
            st.markdown("### 📊 Processing Results")
            
            success_count = sum(1 for r in results if r['status'] == 'success')
            error_count = len(results) - success_count
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Files", len(results))
            col2.metric("Success", success_count)
            col3.metric("Errors", error_count)
            
            # Show saved files location if applicable
            if save_to_output and saved_files:
                st.info(f"📁 All files saved to: OUTPUT/ folder ({len(saved_files)} files)")
            else:
                st.info(f"📥 Files ready for download to your browser's download folder")
            
            # Show detailed results
            with st.expander("📋 Detailed Results", expanded=False):
                for result in results:
                    if result['status'] == 'success':
                        st.success(f"✅ {result['file']}")
                    else:
                        st.error(f"❌ {result['file']}: {result.get('error', 'Unknown error')}")
            
            # Create ZIP download
            if all_pdfs:
                st.markdown("---")
                st.markdown("### 📥 Download Results")
                
                with st.spinner("Creating ZIP archive..."):
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        # Add PDFs
                        for pdf_name, pdf_bytes in all_pdfs:
                            if create_folders:
                                # Organize by file
                                file_prefix = pdf_name.split('_')[0]
                                zip_file.writestr(f"{file_prefix}/pdf/{pdf_name}", pdf_bytes)
                            else:
                                zip_file.writestr(f"pdf/{pdf_name}", pdf_bytes)
                        
                        # Add HTMLs
                        if generate_html:
                            for html_name, html_content in all_htmls:
                                if create_folders:
                                    # Organize by file
                                    file_prefix = html_name.split('_')[0]
                                    zip_file.writestr(f"{file_prefix}/html/{html_name}", html_content)
                                else:
                                    zip_file.writestr(f"html/{html_name}", html_content)
                        
                        # Add Word documents
                        if generate_word:
                            for word_name, word_bytes in all_words:
                                if create_folders:
                                    file_prefix = word_name.split('_')[0]
                                    zip_file.writestr(f"{file_prefix}/word/{word_name}", word_bytes)
                                else:
                                    zip_file.writestr(f"word/{word_name}", word_bytes)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Calculate total documents
                total_docs = len(all_pdfs) + len(all_htmls) + len(all_words)
                doc_summary = []
                if all_pdfs:
                    doc_summary.append(f"{len(all_pdfs)} PDFs")
                if all_htmls:
                    doc_summary.append(f"{len(all_htmls)} HTMLs")
                if all_words:
                    doc_summary.append(f"{len(all_words)} Word docs")
                
                st.download_button(
                    label=f"📦 Download All Documents ({' + '.join(doc_summary)})",
                    data=zip_buffer.getvalue(),
                    file_name=f"batch_output_{timestamp}.zip",
                    mime="application/zip",
                    type="primary",
                    key="batch_zip_download"
                )
                
                st.success(f"✅ Generated {total_docs} documents from {total_files} files")
                
                # Celebrate!
                st.balloons()
            
            # Clean up memory
            del all_pdfs
            del all_htmls
            del all_words
            gc.collect()
            
            # Clean cache after processing
            CacheCleaner.clean_cache(verbose=False)
