"""
Document Upload Mode UI
Provides sequential upload interface for work orders, bill quantities, and extra items
"""
import streamlit as st
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.utils.work_order_organizer import WorkOrderOrganizer
from core.processors.document.document_processor import DocumentProcessor


class DocumentUploadUI:
    """UI component for document upload mode"""
    
    def __init__(self):
        """Initialize document upload UI"""
        self.organizer = WorkOrderOrganizer()
        self.processor = DocumentProcessor()
    
    def show_document_mode(self, config) -> None:
        """
        Display document upload mode in Streamlit
        
        Args:
            config: Application configuration object
        """
        st.title("📄 AI-Powered Document Upload")
        st.markdown("---")
        
        # Introduction
        st.info("""
        **Upload your documents and let AI extract the data automatically!**
        
        This mode uses OCR and handwriting recognition to process:
        - 📋 Work Order (scanned PDF or images)
        - ✍️ Bill Quantities (handwritten page)
        - ➕ Extra Items (optional handwritten page)
        """)
        
        # Initialize session state
        if 'doc_session_id' not in st.session_state:
            st.session_state.doc_session_id = None
            st.session_state.doc_work_order_files = []
            st.session_state.doc_bill_qty_file = None
            st.session_state.doc_extra_items_file = None
            st.session_state.doc_processing_complete = False
        
        # Step 1: Create work order session
        st.subheader("Step 1: Create New Work Order")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🆕 Start New Work Order", type="primary", use_container_width=True):
                session_id = self.create_work_order_session()
                st.session_state.doc_session_id = session_id
                st.success(f"✅ Created work order: {session_id}")
                st.rerun()
        
        with col2:
            if st.session_state.doc_session_id:
                st.metric("Work Order ID", st.session_state.doc_session_id)
        
        if not st.session_state.doc_session_id:
            st.warning("👆 Please create a new work order to begin")
            return
        
        st.markdown("---")
        
        # Step 2: Upload work order
        st.subheader("Step 2: Upload Work Order")
        work_order_files = self.prompt_work_order_upload()
        
        if work_order_files:
            st.session_state.doc_work_order_files = work_order_files
            st.success(f"✅ {len(work_order_files)} work order file(s) uploaded")
        
        if not st.session_state.doc_work_order_files:
            st.info("📋 Please upload work order PDF or images")
            return
        
        st.markdown("---")
        
        # Step 3: Upload bill quantities
        st.subheader("Step 3: Upload Bill Quantities")
        bill_qty_file = self.prompt_bill_quantities_upload()
        
        if bill_qty_file:
            st.session_state.doc_bill_qty_file = bill_qty_file
            st.success("✅ Bill quantities file uploaded")
        
        if not st.session_state.doc_bill_qty_file:
            st.info("✍️ Please upload handwritten bill quantities page")
            return
        
        st.markdown("---")
        
        # Step 4: Upload extra items (optional)
        st.subheader("Step 4: Extra Items (Optional)")
        extra_items_file = self.prompt_extra_items_upload()
        
        if extra_items_file:
            st.session_state.doc_extra_items_file = extra_items_file
            st.success("✅ Extra items file uploaded")
        
        st.markdown("---")
        
        # Step 5: Process documents
        st.subheader("Step 5: Process Documents")
        
        if st.button("🚀 Process All Documents", type="primary", use_container_width=True):
            with st.spinner("Processing documents with AI..."):
                try:
                    # Process workflow
                    result = self.processor.process_complete_workflow(
                        work_order_files=st.session_state.doc_work_order_files,
                        bill_quantities_file=st.session_state.doc_bill_qty_file,
                        extra_items_file=st.session_state.doc_extra_items_file
                    )
                    
                    st.session_state.doc_processing_result = result
                    st.session_state.doc_processing_complete = True
                    
                    st.success("✅ Processing complete!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error during processing: {e}")
        
        # Show results if processing complete
        if st.session_state.doc_processing_complete:
            st.markdown("---")
            st.subheader("📊 Extraction Results")
            
            result = st.session_state.doc_processing_result
            
            # Show summary
            st.metric("Total Items", len(result.items))
            
            # Show items in table
            if result.items:
                st.dataframe([
                    {
                        'Item #': item.item_number,
                        'Description': item.description[:50] + '...' if len(item.description) > 50 else item.description,
                        'Unit': item.unit,
                        'Quantity': item.quantity,
                        'Confidence': f"{item.confidence_score:.0%}"
                    }
                    for item in result.items
                ])
            
            # Generate bill button
            if st.button("📄 Generate Bill Documents", type="primary", use_container_width=True):
                st.info("🚧 Bill generation integration coming soon!")
    
    def create_work_order_session(self) -> str:
        """
        Create new work order folder with auto-generated ID and date
        
        Returns:
            Work order session ID (e.g., "work_01_27022026")
        """
        # Get next work order ID
        work_order_id = self.organizer.get_next_work_order_id()
        
        # Create folder with today's date
        folder = self.organizer.create_work_order_folder(work_order_id)
        
        # Save metadata
        metadata = {
            'created_at': datetime.now().isoformat(),
            'work_order_id': work_order_id,
            'status': 'created'
        }
        self.organizer.save_metadata(folder, metadata)
        
        return folder.name
    
    def prompt_work_order_upload(self) -> List[Path]:
        """
        Prompt user to upload work order PDF or images
        
        Returns:
            List of uploaded file paths
        """
        uploaded_files = st.file_uploader(
            "Upload Work Order (PDF or Images)",
            type=['pdf', 'jpg', 'jpeg', 'png', 'tiff'],
            accept_multiple_files=True,
            key="work_order_uploader"
        )
        
        if uploaded_files:
            # Save files
            folder = Path("INPUT/work_order_samples") / st.session_state.doc_session_id
            saved_paths = []
            
            for uploaded_file in uploaded_files:
                file_path = self.organizer.save_uploaded_file(
                    uploaded_file.read(),
                    uploaded_file.name,
                    folder,
                    "work_order"
                )
                saved_paths.append(file_path)
            
            return saved_paths
        
        return []
    
    def prompt_bill_quantities_upload(self) -> Optional[Path]:
        """
        Prompt user to upload bill quantities page
        
        Returns:
            Uploaded file path or None
        """
        uploaded_file = st.file_uploader(
            "Upload Bill Quantities (Handwritten Page)",
            type=['jpg', 'jpeg', 'png', 'tiff'],
            key="bill_qty_uploader"
        )
        
        if uploaded_file:
            # Save file
            folder = Path("INPUT/work_order_samples") / st.session_state.doc_session_id
            file_path = self.organizer.save_uploaded_file(
                uploaded_file.read(),
                uploaded_file.name,
                folder,
                "bill_quantities"
            )
            return file_path
        
        return None
    
    def prompt_extra_items_upload(self) -> Optional[Path]:
        """
        Conditionally prompt for extra items page
        
        Returns:
            Uploaded file path or None
        """
        has_extra = st.checkbox("Do you have extra items?", key="has_extra_items")
        
        if has_extra:
            uploaded_file = st.file_uploader(
                "Upload Extra Items (Handwritten Page)",
                type=['jpg', 'jpeg', 'png', 'tiff'],
                key="extra_items_uploader"
            )
            
            if uploaded_file:
                # Save file
                folder = Path("INPUT/work_order_samples") / st.session_state.doc_session_id
                file_path = self.organizer.save_uploaded_file(
                    uploaded_file.read(),
                    uploaded_file.name,
                    folder,
                    "extra_items"
                )
                return file_path
        
        return None
