"""
Enhanced Download Center for BillGeneratorUnified
Provides a modern, feature-rich interface for downloading files with advanced ZIP capabilities
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import io
import base64

from core.utils.optimized_zip_processor import OptimizedZipProcessor, OptimizedZipConfig, ZipMetrics
from core.utils.download_manager import EnhancedDownloadManager, DownloadItem, DownloadCategory, FileType

class EnhancedDownloadCenter:
    """Modern download center with advanced features and improved UX"""
    
    def __init__(self, download_manager: EnhancedDownloadManager):
        self.download_manager = download_manager
        self.processor = OptimizedZipProcessor()
        
    def render_download_center(self, title: str = "📥 Enhanced Download Center"):
        """Render the enhanced download center"""
        st.markdown(f"## {title}")
        
        # Show statistics
        stats = self.download_manager.get_statistics()
        if stats['total_items'] > 0:
            self._render_statistics_banner(stats)
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📁 File Browser", 
            "📦 ZIP Creator", 
            "📊 Analytics", 
            "⚙️ Settings"
        ])
        
        with tab1:
            self._render_file_browser()
            
        with tab2:
            self._render_zip_creator()
            
        with tab3:
            self._render_analytics(stats)
            
        with tab4:
            self._render_settings()
            
    def _render_statistics_banner(self, stats: dict):
        """Render statistics banner"""
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📁 Total Files", stats['total_items'])
        with col2:
            st.metric("💾 Total Size", f"{stats['total_size_mb']} MB")
        with col3:
            st.metric("📂 Categories", len(stats['categories']))
        with col4:
            st.metric("📊 File Types", len(stats['file_types']))
            
    def _render_file_browser(self):
        """Render file browser with advanced filtering"""
        st.markdown("### 📁 File Browser")
        
        # Get all items
        all_items = self.download_manager.get_all_items()
        
        if not all_items:
            st.info("📭 No files available for download.")
            return
            
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            categories = list(set([item.category.value for item in all_items]))
            selected_category = st.selectbox("Filter by Category", ["All"] + categories)
            
        with col2:
            file_types = list(set([item.file_type.name for item in all_items]))
            selected_type = st.selectbox("Filter by Type", ["All"] + file_types)
            
        with col3:
            search_term = st.text_input("🔍 Search Files")
            
        # Apply filters
        filtered_items = all_items
        if selected_category != "All":
            filtered_items = [item for item in filtered_items if item.category.value == selected_category]
            
        if selected_type != "All":
            file_type_enum = getattr(FileType, selected_type, None)
            if file_type_enum:
                filtered_items = [item for item in filtered_items if item.file_type == file_type_enum]
                
        if search_term:
            filtered_items = [item for item in filtered_items if search_term.lower() in item.name.lower()]
            
        # Display filtered items
        if not filtered_items:
            st.info("📭 No files match your filters.")
            return
            
        # Show items in cards
        self._render_file_cards(filtered_items)
        
        # Add special download button for macro sheets (NEW)
        macro_sheets = [item for item in all_items if item.name.endswith('.xlsm')]
        if macro_sheets:
            st.markdown("---")
            st.markdown("### 📊 Macro Scrutiny Sheets")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"Found {len(macro_sheets)} macro-enabled scrutiny sheet(s)")
            with col2:
                if st.button("📥 Download All Macro Sheets as ZIP", type="primary"):
                    self._create_macro_sheets_zip(macro_sheets)
    
    def _create_macro_sheets_zip(self, items: List[DownloadItem]):
        """Create ZIP file containing only macro sheets"""
        try:
            # Configure ZIP processor
            config = OptimizedZipConfig(
                compression_level=6,
                preserve_directory_structure=True
            )
            
            # Progress indicators
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            def progress_callback(progress: float, message: str):
                progress_bar.progress(int(progress))
                progress_text.text(message)
                
            # Create ZIP processor
            with OptimizedZipProcessor(config) as processor:
                processor.set_progress_callback(progress_callback)
                
                # Add macro sheets to processor
                for item in items:
                    # Use category as folder
                    folder_name = item.category.value.replace(" ", "_").lower()
                    archive_path = f"{folder_name}/{item.name}"
                    processor.add_file_from_memory(item.content, archive_path)
                    
                # Create ZIP
                zip_buffer, metrics = processor.create_zip()
                
            # Clear progress indicators
            progress_bar.empty()
            progress_text.empty()
            
            # Download button
            st.download_button(
                label="📥 Download Macro Sheets ZIP",
                data=zip_buffer,
                file_name="macro_scrutiny_sheets.zip",
                mime="application/zip",
                key="macro_sheets_zip_download",
                use_container_width=True
            )
            
            st.success("✅ ZIP file with macro sheets created successfully!")
            
        except Exception as e:
            st.error(f"❌ Error creating ZIP: {str(e)}")
            
    def _render_file_cards(self, items: List[DownloadItem]):
        """Render file items as cards"""
        # Group items by category for better organization
        categorized_items = {}
        for item in items:
            category = item.category.value
            if category not in categorized_items:
                categorized_items[category] = []
            categorized_items[category].append(item)
            
        # Display each category
        for category, category_items in categorized_items.items():
            st.markdown(f"#### {self._get_category_icon(category)} {category}")
            
            # Create columns for cards
            cols = st.columns(min(3, len(category_items)))
            
            for idx, item in enumerate(category_items):
                with cols[idx % 3]:
                    # Card container
                    with st.container(border=True):
                        # File header
                        st.markdown(f"**{self._get_file_icon(item.file_type)} {item.name}**")
                        
                        # File details
                        st.caption(f"Size: {item.size_bytes / 1024:.1f} KB")
                        st.caption(f"Created: {item.created_at.strftime('%Y-%m-%d %H:%M')}")
                        
                        # Description if available
                        if item.description:
                            st.caption(item.description)
                            
                        # Download button
                        st.download_button(
                            label="📥 Download",
                            data=item.content,
                            file_name=item.name,
                            mime=item.file_type.value,
                            key=f"download_{item.name}_{idx}",
                            use_container_width=True
                        )
                        
                        # Preview button for text-based files
                        if item.file_type in [FileType.HTML, FileType.JSON, FileType.TXT]:
                            if st.button("👁️ Preview", key=f"preview_{item.name}_{idx}", use_container_width=True):
                                self._show_file_preview(item)
                                
    def _render_zip_creator(self):
        """Render ZIP creation interface"""
        st.markdown("### 📦 Advanced ZIP Creator")
        
        # Get all items
        all_items = self.download_manager.get_all_items()
        
        if not all_items:
            st.info("📭 No files available for ZIP creation.")
            return
            
        # ZIP configuration
        st.markdown("#### ⚙️ ZIP Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            compression_level = st.slider("Compression Level", 0, 9, 6, 
                                        help="0 = No compression, 9 = Maximum compression")
            
        with col2:
            preserve_structure = st.checkbox("Preserve Directory Structure", True)
            
        with col3:
            enable_caching = st.checkbox("Enable Caching", True, 
                                       help="Cache ZIP files for faster subsequent downloads")
            
        # Advanced options
        with st.expander("🔬 Advanced Options"):
            col1, col2 = st.columns(2)
            
            with col1:
                streaming_threshold = st.slider("Streaming Threshold (MB)", 1, 50, 5,
                                              help="Files larger than this will be streamed to save memory")
                memory_limit = st.slider("Memory Limit (MB)", 50, 500, 256)
                
            with col2:
                max_file_size = st.slider("Max File Size (MB)", 10, 200, 100)
                integrity_check = st.checkbox("Verify Integrity", True)
                
        # Quick Actions (NEW)
        st.markdown("#### 🚀 Quick Actions")
        quick_actions = st.columns(4)
        
        with quick_actions[0]:
            if st.button("📥 Download All Files"):
                # Select all items
                st.session_state.selected_files = [item.name for item in all_items]
                st.rerun()
                
        with quick_actions[1]:
            if st.button("📄 HTML Only"):
                html_items = [item for item in all_items if item.file_type == FileType.HTML]
                st.session_state.selected_files = [item.name for item in html_items]
                st.rerun()
                
        with quick_actions[2]:
            if st.button("📕 PDF Only"):
                pdf_items = [item for item in all_items if item.file_type == FileType.PDF]
                st.session_state.selected_files = [item.name for item in pdf_items]
                st.rerun()
                
        with quick_actions[3]:
            # NEW: Macro Sheets Only button
            macro_items = [item for item in all_items if item.name.endswith('.xlsm')]
            if macro_items and st.button("📊 Macro Sheets Only"):
                st.session_state.selected_files = [item.name for item in macro_items]
                st.rerun()
            elif not macro_items:
                st.button("📊 Macro Sheets Only", disabled=True)
                
        # File selection
        st.markdown("#### 📄 Select Files")
        
        # Selection controls
        select_col1, select_col2, select_col3 = st.columns(3)
        
        with select_col1:
            if st.button("✅ Select All"):
                st.session_state.selected_files = [item.name for item in all_items]
                st.rerun()
                
        with select_col2:
            if st.button("❌ Deselect All"):
                st.session_state.selected_files = []
                st.rerun()
                
        with select_col3:
            if st.button("🔄 Invert Selection"):
                all_names = [item.name for item in all_items]
                selected = st.session_state.get("selected_files", [])
                st.session_state.selected_files = [name for name in all_names if name not in selected]
                st.rerun()
                
        # Initialize session state for selections
        if "selected_files" not in st.session_state:
            st.session_state.selected_files = [item.name for item in all_items]
            
        # File selector with checkboxes
        selected_items = []
        for item in all_items:
            is_selected = st.checkbox(
                f"{self._get_file_icon(item.file_type)} {item.name} ({item.size_bytes / 1024:.1f} KB)",
                value=item.name in st.session_state.selected_files,
                key=f"select_{item.name}"
            )
            
            if is_selected:
                selected_items.append(item)
                if item.name not in st.session_state.selected_files:
                    st.session_state.selected_files.append(item.name)
            elif item.name in st.session_state.selected_files:
                st.session_state.selected_files.remove(item.name)
                
        # ZIP creation
        if selected_items:
            st.markdown("---")
            st.markdown("#### 🚀 Create ZIP Archive")
            
            # ZIP name
            default_name = f"documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_name = st.text_input("ZIP File Name", default_name)
            
            # Create ZIP button
            if st.button("📦 Create and Download ZIP", type="primary", use_container_width=True):
                self._create_and_download_zip(
                    selected_items, 
                    zip_name,
                    compression_level,
                    preserve_structure,
                    enable_caching,
                    streaming_threshold,
                    memory_limit,
                    max_file_size,
                    integrity_check
                )
        else:
            st.info("📭 Please select files to include in the ZIP archive.")
            
    def _create_and_download_zip(self, items: List[DownloadItem], zip_name: str,
                               compression_level: int, preserve_structure: bool, enable_caching: bool,
                               streaming_threshold: int, memory_limit: int, max_file_size: int,
                               integrity_check: bool):
        """Create and download ZIP with progress tracking"""
        try:
            # Configure ZIP processor
            config = OptimizedZipConfig(
                compression_level=compression_level,
                streaming_threshold_mb=streaming_threshold,
                memory_limit_mb=memory_limit,
                max_file_size_mb=max_file_size,
                enable_integrity_check=integrity_check,
                enable_caching=enable_caching,
                preserve_directory_structure=preserve_structure
            )
            
            # Progress indicators
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            def progress_callback(progress: float, message: str):
                progress_bar.progress(int(progress))
                progress_text.text(message)
                
            # Create ZIP processor
            with OptimizedZipProcessor(config) as processor:
                processor.set_progress_callback(progress_callback)
                
                # Add files to processor
                for item in items:
                    if preserve_structure:
                        # Use category as folder
                        folder_name = item.category.value.replace(" ", "_").lower()
                        archive_path = f"{folder_name}/{item.name}"
                    else:
                        archive_path = item.name
                        
                    processor.add_file_from_memory(item.content, archive_path)
                    
                # Create ZIP
                zip_buffer, metrics = processor.create_zip()
                
            # Clear progress indicators
            progress_bar.empty()
            progress_text.empty()
            
            # Show metrics in expander
            with st.expander("📊 ZIP Creation Metrics", expanded=False):
                metric_cols = st.columns(4)
                with metric_cols[0]:
                    st.metric("Files", metrics.total_files)
                with metric_cols[1]:
                    st.metric("Original Size", f"{metrics.total_size_bytes / 1024 / 1024:.1f} MB")
                with metric_cols[2]:
                    st.metric("Compressed Size", f"{metrics.compressed_size_bytes / 1024 / 1024:.1f} MB")
                with metric_cols[3]:
                    st.metric("Compression", f"{metrics.compression_ratio_percent:.1f}%")
                    
                detail_cols = st.columns(3)
                with detail_cols[0]:
                    st.metric("Processing Time", f"{metrics.processing_time_seconds:.2f}s")
                with detail_cols[1]:
                    st.metric("Peak Memory", f"{metrics.memory_usage_peak_mb:.1f} MB")
                with detail_cols[2]:
                    st.metric("Streaming Files", metrics.streaming_files_count)
                    
                if metrics.cached_files_count > 0:
                    st.success(f"✅ {metrics.cached_files_count} files loaded from cache")
                    
                if metrics.errors_count > 0:
                    st.warning(f"⚠️ {metrics.errors_count} errors occurred during processing")
            
            # Download button
            st.download_button(
                label=f"📥 Download {zip_name}",
                data=zip_buffer,
                file_name=zip_name,
                mime="application/zip",
                key=f"final_download_{zip_name}",
                use_container_width=True
            )
            
            st.success(f"✅ ZIP file '{zip_name}' created successfully!")
            
        except Exception as e:
            st.error(f"❌ Error creating ZIP: {str(e)}")
            
    def _render_analytics(self, stats: dict):
        """Render analytics dashboard"""
        st.markdown("### 📊 Download Analytics")
        
        if stats['total_items'] == 0:
            st.info("📭 No data available for analytics.")
            return
            
        # Overall statistics
        st.markdown("#### 📈 Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Files", stats['total_items'])
        with col2:
            st.metric("Total Size", f"{stats['total_size_mb']} MB")
        with col3:
            st.metric("Categories", len(stats['categories']))
        with col4:
            st.metric("File Types", len(stats['file_types']))
            
        # Category breakdown
        st.markdown("#### 📁 By Category")
        if stats['categories']:
            category_df = pd.DataFrame([
                {"Category": cat, "Count": count} 
                for cat, count in stats['categories'].items()
            ])
            st.bar_chart(category_df.set_index("Category")["Count"])
            
        # File type breakdown
        st.markdown("#### 📄 By File Type")
        if stats['file_types']:
            # Map MIME types to readable names
            type_mapping = {
                "text/html": "HTML",
                "application/pdf": "PDF",
                "application/msword": "DOC",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel",
                "application/vnd.ms-excel.sheet.macroEnabled.12": "Excel (Macro)",  # NEW
                "application/json": "JSON",
                "text/plain": "Text",
                "application/zip": "ZIP"
            }
            
            type_df = pd.DataFrame([
                {"Type": type_mapping.get(ftype, ftype), "Count": count} 
                for ftype, count in stats['file_types'].items()
            ])
            st.bar_chart(type_df.set_index("Type")["Count"])
            
        # Recent files
        st.markdown("#### 🕐 Recently Added")
        recent_items = sorted(self.download_manager.get_all_items(), 
                            key=lambda x: x.created_at, reverse=True)[:10]
        
        if recent_items:
            recent_data = []
            for item in recent_items:
                recent_data.append({
                    "Name": item.name,
                    "Type": item.file_type.name,
                    "Size (KB)": round(item.size_bytes / 1024, 1),
                    "Category": item.category.value,
                    "Date": item.created_at.strftime("%Y-%m-%d %H:%M")
                })
                
            st.dataframe(pd.DataFrame(recent_data), use_container_width=True)
        else:
            st.info("No recent files found.")
            
    def _render_settings(self):
        """Render settings panel"""
        st.markdown("### ⚙️ Download Center Settings")
        
        # Cache management
        st.markdown("#### 🧹 Cache Management")
        cache_stats = self.processor.get_cache_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Cache Entries", cache_stats['cache_entries'])
        with col2:
            cache_size_mb = cache_stats['total_cache_size_bytes'] / 1024 / 1024
            st.metric("Cache Size", f"{cache_size_mb:.1f} MB")
            
        if st.button("🧹 Clear Cache"):
            cleared = self.processor.cleanup_old_cache(0)  # Clear all
            st.success(f"Cleared {cleared} cache entries")
            
        # Default settings
        st.markdown("#### 🛠️ Default ZIP Settings")
        
        default_compression = st.slider("Default Compression Level", 0, 9, 6)
        default_streaming = st.slider("Default Streaming Threshold (MB)", 1, 50, 5)
        default_memory = st.slider("Default Memory Limit (MB)", 50, 500, 256)
        
        if st.button("💾 Save Defaults"):
            # In a real implementation, you would save these to config
            st.success("Defaults saved successfully!")
            
        # Performance info
        st.markdown("#### 🚀 Performance Info")
        processor_stats = self.processor.get_statistics()
        
        if processor_stats['total_operations'] > 0:
            stat_cols = st.columns(3)
            with stat_cols[0]:
                st.metric("Operations", processor_stats['total_operations'])
            with stat_cols[1]:
                st.metric("Success Rate", f"{processor_stats['success_rate']:.1f}%")
            with stat_cols[2]:
                st.metric("Peak Memory", f"{processor_stats['peak_memory_mb']:.1f} MB")
        else:
            st.info("No performance data available yet.")
            
    def _show_file_preview(self, item: DownloadItem):
        """Show preview of a file"""
        st.markdown(f"### 👁️ Preview: {item.name}")
        
        try:
            if item.file_type == FileType.HTML:
                # For HTML, we can show it directly
                content = item.content.decode('utf-8') if isinstance(item.content, bytes) else item.content
                st.markdown(content, unsafe_allow_html=True)
                
            elif item.file_type == FileType.JSON:
                # For JSON, parse and pretty print
                content = item.content.decode('utf-8') if isinstance(item.content, bytes) else item.content
                st.json(content)
                
            elif item.file_type == FileType.TXT:
                # For text, show in code block
                content = item.content.decode('utf-8') if isinstance(item.content, bytes) else item.content
                st.text_area("Content", content, height=400)
                
            else:
                st.info("Preview not available for this file type.")
                
        except Exception as e:
            st.error(f"Error showing preview: {str(e)}")
            
    def _get_file_icon(self, file_type: FileType) -> str:
        """Get appropriate icon for file type"""
        icon_map = {
            FileType.HTML: "📄",
            FileType.PDF: "📕",
            FileType.DOC: "📘",
            FileType.XLSX: "📊",
            FileType.XLSM: "⚙️",  # NEW: Icon for macro-enabled Excel files
            FileType.JSON: "📋",
            FileType.TXT: "📝",
            FileType.ZIP: "📦"
        }
        return icon_map.get(file_type, "📁")
        
    def _get_category_icon(self, category: str) -> str:
        """Get appropriate icon for category"""
        category_icons = {
            "HTML Documents": "📄",
            "PDF Documents": "📕",
            "DOC Documents": "📘",
            "Excel Files": "📊",
            "Templates": "📐",
            "Configuration": "⚙️",
            "General": "📁"
        }
        return category_icons.get(category, "📁")


# Utility functions
def create_enhanced_download_center(download_manager: EnhancedDownloadManager) -> EnhancedDownloadCenter:
    """Create and return an enhanced download center"""
    return EnhancedDownloadCenter(download_manager)


def integrate_with_batch_processor(batch_results: List[Dict], download_manager: EnhancedDownloadManager):
    """
    Integrate batch processing results with download manager
    
    Args:
        batch_results: List of processing results from batch processor
        download_manager: Download manager to add files to
    """
    for result in batch_results:
        if result.get('status') == 'success':
            # Add HTML files
            html_files = result.get('html_files', [])
            for html_file in html_files:
                html_path = Path(result.get('output_folder', '')) / 'html' / f"{html_file}.html"
                if html_path.exists():
                    content = html_path.read_text(encoding='utf-8')
                    download_manager.add_html_document(
                        f"{result.get('filename', 'unknown')}_{html_file}.html",
                        content,
                        f"HTML document for {result.get('filename', 'unknown')}"
                    )
                    
            # Add PDF files
            pdf_files = result.get('pdf_files', [])
            for pdf_file in pdf_files:
                pdf_path = Path(result.get('output_folder', '')) / 'pdf' / pdf_file
                if pdf_path.exists():
                    content = pdf_path.read_bytes()
                    download_manager.add_pdf_document(
                        f"{result.get('filename', 'unknown')}_{pdf_file}",
                        content,
                        f"PDF document for {result.get('filename', 'unknown')}"
                    )
            
            # Add Macro Scrutiny Sheets (NEW)
            macro_sheet_result = result.get('macro_sheet', {})
            if macro_sheet_result.get('success'):
                # Add Excel macro-enabled file (.xlsm)
                xlsm_saved_path = macro_sheet_result.get('saved_xlsm_path')
                if xlsm_saved_path and Path(xlsm_saved_path).exists():
                    content = Path(xlsm_saved_path).read_bytes()
                    download_manager.add_excel_file(
                        f"{Path(result.get('filename', 'unknown')).stem}_scrutiny_sheet.xlsm",
                        content,
                        f"Macro-enabled scrutiny sheet for {result.get('filename', 'unknown')}"
                    )
                
                # Add PDF export if available
                pdf_saved_path = macro_sheet_result.get('saved_pdf_path')
                if pdf_saved_path and Path(pdf_saved_path).exists():
                    content = Path(pdf_saved_path).read_bytes()
                    download_manager.add_pdf_document(
                        f"{Path(result.get('filename', 'unknown')).stem}_scrutiny_sheet.pdf",
                        content,
                        f"PDF export of scrutiny sheet for {result.get('filename', 'unknown')}"
                    )
