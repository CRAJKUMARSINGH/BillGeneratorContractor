"""
Online Entry Mode UI
"""
import streamlit as st
import pandas as pd
from datetime import datetime

def show_online_mode(config):
    """Show online entry interface"""
    st.markdown("## 💻 Online Entry Mode")
    
    # Highlight data entry requirements with fluorescent green theme
    st.markdown("""
    <div style='background: linear-gradient(135deg, #ccffcc 0%, #99ff99 100%); 
                padding: 20px; 
                border-radius: 12px; 
                border: 2px dashed #00ff00; 
                margin-bottom: 25px;
                box-shadow: 0 0 15px rgba(0, 255, 0, 0.3);'>
        <h3 style='color: #006600; margin-top: 0; font-size: 1.6rem;'>
            ✏️ Fluorescent Green Manual Data Entry
        </h3>
        <p style='color: #004d00; margin-bottom: 0; font-size: 1.1rem; font-weight: bold;'>
            Please fill in all the required bill details in the forms below to generate documents
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("📝 Enter bill details manually through web forms")
    
    # Excel file upload to extract title sheet data - Enhanced styling
    st.markdown("### 📊 Extract Data from Excel")
    st.markdown("""
    <div style='background-color: #e6ffe6; padding: 15px; border-radius: 8px; border-left: 5px solid #00ff00; margin-bottom: 15px;'>
        <p style='color: #006600; margin-bottom: 0; font-weight: bold;'>
            📤 Optional: Upload Excel file to auto-extract Project Name and Contractor
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    excel_file = st.file_uploader("Upload Excel file to extract Project Name and Contractor", type=['xlsx', 'xls'])
    
    # Default values
    default_project_name = ""
    default_contractor = ""
    
    # Extract data from Excel if uploaded
    if excel_file:
        try:
            # Read all sheets
            excel_data = pd.read_excel(excel_file, sheet_name=None)
            
            # Look for title sheet (common names)
            title_sheet_names = ['Title', 'title', 'TITLE', 'Title Sheet', 'title sheet', 'Sheet1', 'Sheet 1']
            title_data = None
            
            for sheet_name in title_sheet_names:
                if sheet_name in excel_data:
                    title_data = excel_data[sheet_name]
                    break
            
            # If not found, try first sheet
            if title_data is None and excel_data:
                title_data = list(excel_data.values())[0]
            
            # Extract project name and contractor from title data
            if title_data is not None:
                # Convert to string for easier searching
                title_string = title_data.to_string()
                
                # Look for project name patterns - prioritize "Name of Work"
                project_patterns_priority = ['Name of Work']  # Highest priority
                project_patterns_secondary = ['Project Name', 'Project', 'Work Name', 'Work']
                all_project_patterns = project_patterns_priority + project_patterns_secondary
                
                contractor_patterns = ['Contractor', 'Name of Contractor', 'Contractor Name']
                
                # Search for "Name of Work" first (highest priority)
                project_found = False
                for col in title_data.columns:
                    col_str = str(col).lower()
                    if 'name of work' in col_str:
                        # Get first non-null value in this column
                        project_values = title_data[col].dropna()
                        if not project_values.empty:
                            default_project_name = str(project_values.iloc[0])
                            project_found = True
                            break
                
                # If not found in column names, search in data cells
                if not project_found:
                    # Search through all cells for "Name of Work"
                    for col in title_data.columns:
                        col_data = title_data[col].astype(str)
                        for idx, cell_value in col_data.items():
                            if 'name of work' in cell_value.lower():
                                # Look for the value in the next row or adjacent cell
                                try:
                                    # Try to get the value from the next row in the same column
                                    next_value = title_data.iloc[idx+1][col] if idx+1 < len(title_data) else None
                                    if next_value and str(next_value) != 'nan':
                                        default_project_name = str(next_value)
                                        project_found = True
                                        break
                                except:
                                    pass
                        if project_found:
                            break
                
                # If still not found, try other project patterns
                if not project_found:
                    for col in title_data.columns:
                        col_str = str(col).lower()
                        if any(pattern.lower() in col_str for pattern in project_patterns_secondary):
                            # Get first non-null value in this column
                            project_values = title_data[col].dropna()
                            if not project_values.empty:
                                default_project_name = str(project_values.iloc[0])
                                project_found = True
                                break
                
                # Search for contractor
                contractor_found = False
                for col in title_data.columns:
                    col_str = str(col).lower()
                    if any(pattern.lower() in col_str for pattern in contractor_patterns):
                        # Get first non-null value in this column
                        contractor_values = title_data[col].dropna()
                        if not contractor_values.empty:
                            default_contractor = str(contractor_values.iloc[0])
                            contractor_found = True
                            break
                
                # If contractor not found in column names, search in data
                if not contractor_found:
                    for col in title_data.columns:
                        col_data = title_data[col].astype(str)
                        for idx, cell_value in col_data.items():
                            if any(pattern.lower() in cell_value.lower() for pattern in contractor_patterns):
                                # Look for the value in the next row or adjacent cell
                                try:
                                    # Try to get the value from the next row in the same column
                                    next_value = title_data.iloc[idx+1][col] if idx+1 < len(title_data) else None
                                    if next_value and str(next_value) != 'nan':
                                        default_contractor = str(next_value)
                                        contractor_found = True
                                        break
                                except:
                                    pass
                        if contractor_found:
                            break
                
                if project_found or contractor_found:
                    st.success("✅ Successfully extracted data from Excel file")
                else:
                    st.info("ℹ️ No project name or contractor data found in the Excel file")
        except Exception as e:
            st.warning(f"Could not extract data from Excel file: {str(e)}")
    
    # Project Details
    with st.expander("📋 Project Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            project_name = st.text_input("Name of Work", value=default_project_name, placeholder="Enter name of work")
            contractor = st.text_input("Contractor Name", value=default_contractor, placeholder="Enter contractor name")
        
        with col2:
            # Keep bill date blank by default
            bill_date = st.date_input("Bill Date", value=None)
            tender_premium = st.number_input("Tender Premium (%)", min_value=0.0, max_value=100.0, value=4.0)
    
    # Work Items - Using session state for persistence
    st.markdown("### 🔨 Work Items")
    
    # Number of items input
    num_items = st.number_input("Number of Items", min_value=1, max_value=50, value=3, key="num_items_online")
    
    # Initialize session state for items
    if 'online_items' not in st.session_state:
        st.session_state.online_items = []
    
    # Adjust session state size based on num_items
    current_num_items = len(st.session_state.online_items)
    if current_num_items != num_items:
        if current_num_items < num_items:
            # Add new empty items
            for i in range(num_items - current_num_items):
                st.session_state.online_items.append({
                    'item_no': f"{current_num_items + i + 1:03d}",
                    'description': '',
                    'quantity': 0.0,
                    'rate': 0.0
                })
        else:
            # Remove excess items
            st.session_state.online_items = st.session_state.online_items[:num_items]
    
    # Create item input fields and update session state
    updated_items = []
    for i in range(int(num_items)):
        st.markdown(f"**Item {i+1}**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            item_no = st.text_input(f"Item No.", value=st.session_state.online_items[i]['item_no'], key=f"item_no_{i}")
        with col2:
            description = st.text_input(f"Description", value=st.session_state.online_items[i]['description'], key=f"desc_{i}")
        with col3:
            quantity = st.number_input(f"Quantity", min_value=0.0, value=float(st.session_state.online_items[i]['quantity']), key=f"qty_{i}")
        with col4:
            rate = st.number_input(f"Rate", min_value=0.0, value=float(st.session_state.online_items[i]['rate']), key=f"rate_{i}")
        
        # Store updated values
        updated_item = {
            'item_no': item_no,
            'description': description,
            'quantity': quantity,
            'rate': rate
        }
        updated_items.append(updated_item)
    
    # Update session state with current values
    st.session_state.online_items = updated_items
    
    # Generate button with enhanced styling
    st.markdown("""
    <div style='background: linear-gradient(135deg, #e6ffe6 0%, #ccffcc 100%); 
                padding: 20px; 
                border-radius: 12px; 
                border: 2px solid #00ff00; 
                text-align: center;
                margin-top: 20px;'>
        <h3 style='color: #006600; margin: 0;'>
            🚀 Ready to Generate Documents
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Generate Documents", type="primary", use_container_width=True):
        if not project_name:
            st.error("❌ Please enter project name")
        else:
            # Use items from session state
            items = st.session_state.online_items
            
            with st.spinner("Generating documents..."):
                st.success("✅ Documents generated successfully!")
                
                # Show summary
                st.markdown("### 📊 Summary")
                total = sum(item['quantity'] * item['rate'] for item in items)
                premium_amount = total * (tender_premium / 100)
                net_payable = total + premium_amount
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Amount", f"₹{total:,.2f}")
                col2.metric("Premium", f"₹{premium_amount:,.2f}")
                col3.metric("NET PAYABLE", f"₹{net_payable:,.2f}")
                
                # Display item details table
                st.markdown("### 📋 Item Details")
                if items:
                    item_data = []
                    for item in items:
                        # Show all items, not just those with quantity/rate > 0
                        amount = item['quantity'] * item['rate']
                        item_data.append({
                            "Item No.": item['item_no'],
                            "Description": item['description'],
                            "Quantity": item['quantity'],
                            "Rate": item['rate'],
                            "Amount": amount
                        })
                    
                    if item_data:
                        df = pd.DataFrame(item_data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No items entered.")
                else:
                    st.info("No items entered.")
                
                # Generate actual documents
                from core.generators.document_generator import DocumentGenerator
                
                # Prepare data structure similar to Excel processor output
                # Handle blank bill date
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
                        "grand_total": total,
                        "premium": {
                            "percent": tender_premium / 100,
                            "amount": premium_amount
                        },
                        "payable": net_payable,
                        "net_payable": net_payable
                    }
                }
                
                # Add items to work order data (only items with valid data)
                for item in items:
                    if item['quantity'] > 0 and item['rate'] > 0:
                        processed_data["work_order_data"].append({
                            "Item No.": item['item_no'],
                            "Description": item['description'],
                            "Unit": "NOS",
                            "Quantity": item['quantity'],
                            "Rate": item['rate'],
                            "Amount": item['quantity'] * item['rate']
                        })
                
                # Generate documents
                doc_generator = DocumentGenerator(processed_data)
                html_documents = doc_generator.generate_all_documents()
                pdf_documents = doc_generator.create_pdf_documents(html_documents)
                doc_documents = doc_generator.generate_doc_documents()
                
                # Create zip file for all documents
                import zipfile
                import io
                
                # Create in-memory zip file
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add HTML files to zip
                    for doc_name, html_content in html_documents.items():
                        # Ensure content is bytes
                        if isinstance(html_content, str):
                            content_bytes = html_content.encode('utf-8')
                        else:
                            content_bytes = html_content
                        zip_file.writestr(f"{doc_name}.html", content_bytes)
                    
                    # Add PDF files to zip
                    for doc_name, pdf_content in pdf_documents.items():
                        zip_file.writestr(f"{doc_name}.pdf", pdf_content)
                    
                    # Add DOC files to zip
                    for doc_name, doc_content in doc_documents.items():
                        zip_file.writestr(doc_name, doc_content)
                
                zip_buffer.seek(0)
                
                # Download section
                st.markdown("### 📥 Download Documents")
                
                # Zip download button
                st.download_button(
                    "📦 Download All Documents (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="online_bill_documents.zip",
                    mime="application/zip",
                    key="online_zip_download"
                )
                
                # Individual downloads
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### 📄 HTML Documents")
                    cols = st.columns(min(3, len(html_documents)))
                    
                    for idx, (doc_name, html_content) in enumerate(html_documents.items()):
                        with cols[idx % 3]:
                            # Ensure content is bytes for download
                            if isinstance(html_content, str):
                                content_bytes = html_content.encode('utf-8')
                            else:
                                content_bytes = html_content
                            st.download_button(
                                f"📄 {doc_name}",
                                data=content_bytes,
                                file_name=f"{doc_name}.html",
                                mime="text/html",
                                key=f"online_html_{idx}"
                            )
                
                with col2:
                    st.markdown("#### 📕 PDF Documents")
                    cols_pdf = st.columns(min(3, len(pdf_documents)))
                    
                    for idx, (doc_name, pdf_content) in enumerate(pdf_documents.items()):
                        with cols_pdf[idx % 3]:
                            st.download_button(
                                f"📕 {doc_name}",
                                data=pdf_content,
                                file_name=f"{doc_name}.pdf",
                                mime="application/pdf",
                                key=f"online_pdf_{idx}"
                            )
                
                with col3:
                    st.markdown("#### 📝 DOC Documents")
                    cols_doc = st.columns(min(3, len(doc_documents)))
                    
                    for idx, (doc_name, doc_content) in enumerate(doc_documents.items()):
                        with cols_doc[idx % 3]:
                            st.download_button(
                                f"📝 {doc_name}",
                                data=doc_content,
                                file_name=doc_name,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"online_doc_{idx}"
                            )