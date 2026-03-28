"""
Online Entry Mode UI - Enhanced with 2025 Design Trends
Features: Glassmorphism, Dark Mode, Neumorphism, Bento Grid, Micro-interactions
Integrated with cursor.com simple work order processor improvements
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import json
from pathlib import Path

# Import cursor.com improvements
try:
    from simple_work_order_processor import read_quantities, read_work_order_images, find_item_descriptions
    CURSOR_FEATURES_AVAILABLE = True
except:
    CURSOR_FEATURES_AVAILABLE = False

def apply_2025_design_trends():
    """Apply cutting-edge 2025 design trends"""
    st.markdown("""
    <style>
        /* ========== GLASSMORPHISM - Premium Look ========== */
        .glass-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            padding: 2rem;
            margin: 1rem 0;
        }
        
        .glass-header {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.8), rgba(118, 75, 162, 0.8));
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            padding: 2.5rem;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            animation: fadeInDown 0.8s ease-out;
        }
        
        /* ========== DARK MODE + NEON ACCENTS ========== */
        .dark-card {
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
            border-radius: 15px;
            padding: 1.5rem;
            border: 1px solid rgba(102, 126, 234, 0.3);
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.2);
            margin: 1rem 0;
        }
        
        .neon-text {
            color: #00f5ff;
            text-shadow: 0 0 10px #00f5ff, 0 0 20px #00f5ff, 0 0 30px #00f5ff;
            animation: neonGlow 2s ease-in-out infinite alternate;
        }
        
        .neon-border {
            border: 2px solid #00f5ff;
            box-shadow: 0 0 10px #00f5ff, inset 0 0 10px #00f5ff;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        
        /* ========== NEUMORPHISM - Soft UI ========== */
        .neuro-card {
            background: #e0e5ec;
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 9px 9px 16px rgba(163, 177, 198, 0.6),
                       -9px -9px 16px rgba(255, 255, 255, 0.5);
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        
        .neuro-card:hover {
            box-shadow: 6px 6px 12px rgba(163, 177, 198, 0.6),
                       -6px -6px 12px rgba(255, 255, 255, 0.5);
        }
        
        .neuro-button {
            background: #e0e5ec;
            border: none;
            border-radius: 15px;
            padding: 1rem 2rem;
            box-shadow: 5px 5px 10px rgba(163, 177, 198, 0.6),
                       -5px -5px 10px rgba(255, 255, 255, 0.5);
            transition: all 0.2s ease;
            cursor: pointer;
        }
        
        .neuro-button:active {
            box-shadow: inset 5px 5px 10px rgba(163, 177, 198, 0.6),
                       inset -5px -5px 10px rgba(255, 255, 255, 0.5);
        }
        
        /* ========== BENTO GRID LAYOUT ========== */
        .bento-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        .bento-item {
            background: white;
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .bento-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
        
        /* ========== MICRO-INTERACTIONS ========== */
        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes neonGlow {
            from {
                text-shadow: 0 0 10px #00f5ff, 0 0 20px #00f5ff, 0 0 30px #00f5ff;
            }
            to {
                text-shadow: 0 0 20px #00f5ff, 0 0 30px #00f5ff, 0 0 40px #00f5ff, 0 0 50px #00f5ff;
            }
        }
        
        @keyframes pulse {
            0%, 100% {
                transform: scale(1);
            }
            50% {
                transform: scale(1.05);
            }
        }
        
        .animate-pulse {
            animation: pulse 2s ease-in-out infinite;
        }
        
        .animate-fade-in {
            animation: fadeInUp 0.6s ease-out;
        }
        
        /* ========== ENHANCED BUTTONS ========== */
        .stButton>button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 15px;
            padding: 1rem 2rem;
            font-weight: 600;
            font-size: 1.1rem;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .stButton>button:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
            background: linear-gradient(135deg, #764ba2 0%, #f093fb 100%);
        }
        
        .stButton>button:active {
            transform: translateY(-1px);
        }
        
        .stButton>button::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.5);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .stButton>button:hover::before {
            width: 300px;
            height: 300px;
        }
        
        /* ========== ENHANCED INPUT FIELDS ========== */
        .stTextInput>div>div>input,
        .stNumberInput>div>div>input {
            border-radius: 12px;
            border: 2px solid #e0e5ec;
            padding: 0.75rem 1rem;
            transition: all 0.3s ease;
            background: white;
        }
        
        .stTextInput>div>div>input:focus,
        .stNumberInput>div>div>input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            transform: translateY(-2px);
        }
        
        /* ========== METRIC CARDS WITH GRADIENT ========== */
        [data-testid="stMetricValue"] {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        /* ========== PROGRESS INDICATORS ========== */
        .progress-ring {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: conic-gradient(#667eea 0deg, #764ba2 180deg, #f093fb 360deg);
            display: flex;
            align-items: center;
            justify-content: center;
            animation: rotate 3s linear infinite;
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        /* ========== TOOLTIP ENHANCEMENTS ========== */
        .tooltip {
            position: relative;
            display: inline-block;
        }
        
        .tooltip .tooltiptext {
            visibility: hidden;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            border-radius: 10px;
            padding: 10px 15px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -75px;
            opacity: 0;
            transition: opacity 0.3s, transform 0.3s;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
            transform: translateY(-5px);
        }
        
        /* ========== SPATIAL DESIGN - 3D ELEMENTS ========== */
        .card-3d {
            transform-style: preserve-3d;
            transition: transform 0.6s;
        }
        
        .card-3d:hover {
            transform: rotateY(10deg) rotateX(10deg);
        }
        
        /* ========== RESPONSIVE DESIGN ========== */
        @media (max-width: 768px) {
            .glass-header {
                padding: 1.5rem;
            }
            
            .bento-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    """, unsafe_allow_html=True)

def show_online_mode_enhanced(config):
    """Enhanced online entry interface with 2025 design trends"""
    
    # Apply 2025 design trends
    apply_2025_design_trends()
    
    # Glassmorphism Header
    st.markdown("""
    <div class="glass-header">
        <h1 style='font-size: 2.5rem; margin: 0; font-weight: 800;'>
            💻 Online Entry Mode
        </h1>
        <p style='font-size: 1.2rem; margin: 0.5rem 0 0 0; opacity: 0.95;'>
            ✨ World-Class Bill Generation Interface | 2025 Design Trends
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature status banner
    if CURSOR_FEATURES_AVAILABLE:
        st.markdown("""
        <div class="neon-border animate-fade-in">
            <h3 class="neon-text" style='margin: 0; text-align: center;'>
                🚀 Cursor.com AI Features Integrated
            </h3>
            <p style='text-align: center; color: #00f5ff; margin: 0.5rem 0 0 0;'>
                OCR Processing • Smart Quantity Reading • Auto Description Matching
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Tabs for different input methods
    tab1, tab2, tab3 = st.tabs(["📝 Manual Entry", "📊 Excel Import", "📸 Smart OCR (Cursor.com)"])
    
    with tab1:
        show_manual_entry_mode(config)
    
    with tab2:
        show_excel_import_mode(config)
    
    with tab3:
        if CURSOR_FEATURES_AVAILABLE:
            show_smart_ocr_mode(config)
        else:
            st.info("🔧 Install cursor.com features to enable Smart OCR mode")
            st.code("pip install pytesseract pillow")

def show_manual_entry_mode(config):
    """Manual entry with enhanced UI"""
    
    # Bento Grid for Project Details
    st.markdown("""
    <div class="neuro-card animate-fade-in">
        <h3 style='color: #667eea; margin-top: 0;'>📋 Project Details</h3>
        <p style='color: #636e72;'>Enter basic project information</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        project_name = st.text_input(
            "Name of Work",
            placeholder="Enter project name...",
            help="Full name of the construction project"
        )
        contractor = st.text_input(
            "Contractor Name",
            placeholder="Enter contractor name...",
            help="Name of the contractor executing the work"
        )
    
    with col2:
        bill_date = st.date_input(
            "Bill Date",
            value=None,
            help="Date of bill generation"
        )
        tender_premium = st.number_input(
            "Tender Premium (%)",
            min_value=0.0,
            max_value=100.0,
            value=4.0,
            step=0.1,
            help="Tender premium percentage"
        )
    
    # Work Items Section with Bento Grid
    st.markdown("""
    <div class="glass-card animate-fade-in">
        <h3 style='color: #667eea; margin-top: 0;'>🔨 Work Items</h3>
        <p style='color: #636e72;'>Add and manage work items</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Number of items with slider
    col1, col2 = st.columns([3, 1])
    with col1:
        num_items = st.slider(
            "Number of Items",
            min_value=1,
            max_value=50,
            value=5,
            help="Slide to adjust number of items"
        )
    with col2:
        st.metric("Items", num_items, delta=None)
    
    # Initialize session state
    if 'online_items_enhanced' not in st.session_state:
        st.session_state.online_items_enhanced = []
    
    # Adjust items
    current_num = len(st.session_state.online_items_enhanced)
    if current_num != num_items:
        if current_num < num_items:
            for i in range(num_items - current_num):
                st.session_state.online_items_enhanced.append({
                    'item_no': f"{current_num + i + 1}",
                    'description': '',
                    'quantity': 0.0,
                    'rate': 0.0
                })
        else:
            st.session_state.online_items_enhanced = st.session_state.online_items_enhanced[:num_items]
    
    # Item input with enhanced styling
    updated_items = []
    for i in range(int(num_items)):
        with st.expander(f"📦 Item {i+1}", expanded=(i < 3)):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                item_no = st.text_input(
                    "Item No.",
                    value=st.session_state.online_items_enhanced[i]['item_no'],
                    key=f"enh_item_no_{i}",
                    placeholder="e.g., 1.1.2"
                )
            with col2:
                description = st.text_area(
                    "Description",
                    value=st.session_state.online_items_enhanced[i]['description'],
                    key=f"enh_desc_{i}",
                    height=100,
                    placeholder="Enter item description..."
                )
            with col3:
                quantity = st.number_input(
                    "Quantity",
                    min_value=0.0,
                    value=float(st.session_state.online_items_enhanced[i]['quantity']),
                    key=f"enh_qty_{i}",
                    step=0.1
                )
            with col4:
                rate = st.number_input(
                    "Rate (₹)",
                    min_value=0.0,
                    value=float(st.session_state.online_items_enhanced[i]['rate']),
                    key=f"enh_rate_{i}",
                    step=0.01
                )
            
            # Calculate and show amount
            amount = quantity * rate
            if amount > 0:
                st.success(f"💰 Amount: ₹{amount:,.2f}")
            
            updated_items.append({
                'item_no': item_no,
                'description': description,
                'quantity': quantity,
                'rate': rate
            })
    
    st.session_state.online_items_enhanced = updated_items
    
    # Generate button with animation
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Generate Documents", type="primary", use_container_width=True):
            generate_documents_enhanced(project_name, contractor, bill_date, tender_premium, updated_items, config)

def show_excel_import_mode(config):
    """Excel import with enhanced UI"""
    
    st.markdown("""
    <div class="dark-card animate-fade-in">
        <h3 style='color: #00f5ff; margin-top: 0;'>📊 Excel Import Mode</h3>
        <p style='color: #b2bec3;'>Upload Excel file to auto-extract project data</p>
    </div>
    """, unsafe_allow_html=True)
    
    excel_file = st.file_uploader(
        "Upload Excel File",
        type=['xlsx', 'xls'],
        help="Upload Excel file with project details"
    )
    
    if excel_file:
        with st.spinner("🔍 Analyzing Excel file..."):
            try:
                excel_data = pd.read_excel(excel_file, sheet_name=None)
                
                st.success("✅ Excel file loaded successfully!")
                
                # Show sheets
                st.markdown("### 📑 Available Sheets")
                sheet_names = list(excel_data.keys())
                
                cols = st.columns(min(4, len(sheet_names)))
                for idx, sheet_name in enumerate(sheet_names):
                    with cols[idx % 4]:
                        st.info(f"📄 {sheet_name}")
                
                # Extract data (similar to original logic)
                # ... (implementation continues)
                
            except Exception as e:
                st.error(f"❌ Error reading Excel: {e}")

def show_smart_ocr_mode(config):
    """Smart OCR mode using cursor.com improvements"""
    
    st.markdown("""
    <div class="glass-card animate-fade-in">
        <h3 style='color: #667eea; margin-top: 0;'>📸 Smart OCR Mode</h3>
        <p style='color: #636e72;'>Upload scanned work orders and qty.txt for automatic processing</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("🤖 This mode uses cursor.com AI improvements for intelligent document processing")
    
    # File upload
    uploaded_images = st.file_uploader(
        "Upload Work Order Images",
        type=['jpg', 'jpeg', 'png', 'bmp', 'tiff'],
        accept_multiple_files=True,
        help="Upload scanned work order images"
    )
    
    qty_file = st.file_uploader(
        "Upload qty.txt",
        type=['txt'],
        help="Upload quantities file (format: item_code quantity)"
    )
    
    if uploaded_images and qty_file:
        if st.button("🔍 Process with AI", type="primary"):
            with st.spinner("🤖 AI Processing in progress..."):
                # Save uploaded files temporarily
                temp_dir = Path("temp_ocr")
                temp_dir.mkdir(exist_ok=True)
                
                # Save images
                for img in uploaded_images:
                    img_path = temp_dir / img.name
                    with open(img_path, 'wb') as f:
                        f.write(img.getbuffer())
                
                # Save qty.txt
                qty_path = temp_dir / "qty.txt"
                with open(qty_path, 'wb') as f:
                    f.write(qty_file.getbuffer())
                
                # Process using cursor.com functions
                quantities = read_quantities(str(temp_dir))
                ocr_text = read_work_order_images(str(temp_dir))
                descriptions = find_item_descriptions(ocr_text, quantities.keys())
                
                # Show results
                st.success("✅ AI Processing Complete!")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Items Found", len(quantities))
                col2.metric("Total Quantity", sum(quantities.values()))
                col3.metric("Descriptions", len(descriptions))
                
                # Show data
                st.markdown("### 📊 Extracted Data")
                data = []
                for item_no, qty in quantities.items():
                    desc = descriptions.get(item_no, f"Item {item_no}")
                    data.append({
                        "Item No.": item_no,
                        "Description": desc,
                        "Quantity": qty
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
                
                # Cleanup
                import shutil
                shutil.rmtree(temp_dir)

def generate_documents_enhanced(project_name, contractor, bill_date, tender_premium, items, config):
    """Generate documents with enhanced feedback"""
    
    if not project_name:
        st.error("❌ Please enter project name")
        return
    
    with st.spinner("🎨 Generating documents with world-class design..."):
        # Calculate totals
        total = sum(item['quantity'] * item['rate'] for item in items if item['quantity'] > 0 and item['rate'] > 0)
        premium_amount = total * (tender_premium / 100)
        net_payable = total + premium_amount
        
        # Show metrics with animation
        st.markdown("""
        <div class="bento-grid animate-fade-in">
            <div class="bento-item">
                <h4 style='color: #667eea; margin: 0;'>Total Amount</h4>
                <p style='font-size: 2rem; font-weight: 700; color: #2d3436; margin: 0.5rem 0 0 0;'>
                    ₹{:,.2f}
                </p>
            </div>
            <div class="bento-item">
                <h4 style='color: #00b894; margin: 0;'>Premium</h4>
                <p style='font-size: 2rem; font-weight: 700; color: #2d3436; margin: 0.5rem 0 0 0;'>
                    ₹{:,.2f}
                </p>
            </div>
            <div class="bento-item animate-pulse">
                <h4 style='color: #d63031; margin: 0;'>NET PAYABLE</h4>
                <p style='font-size: 2rem; font-weight: 700; color: #d63031; margin: 0.5rem 0 0 0;'>
                    ₹{:,.2f}
                </p>
            </div>
        </div>
        """.format(total, premium_amount, net_payable), unsafe_allow_html=True)
        
        # Generate documents (use existing logic)
        from core.generators.document_generator import DocumentGenerator
        
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
        
        doc_generator = DocumentGenerator(processed_data)
        html_documents = doc_generator.generate_all_documents()
        pdf_documents = doc_generator.create_pdf_documents(html_documents)
        
        st.success("✅ Documents generated successfully!")
        
        # Download section with enhanced UI
        st.markdown("""
        <div class="glass-card">
            <h3 style='color: #667eea; margin-top: 0;'>📥 Download Documents</h3>
            <p style='color: #636e72;'>Your documents are ready for download</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create download buttons
        cols = st.columns(len(html_documents))
        for idx, (doc_name, html_content) in enumerate(html_documents.items()):
            with cols[idx]:
                content_bytes = html_content.encode('utf-8') if isinstance(html_content, str) else html_content
                st.download_button(
                    f"📄 {doc_name}",
                    data=content_bytes,
                    file_name=f"{doc_name}.html",
                    mime="text/html",
                    key=f"enh_html_{idx}"
                )

# Main function to show enhanced mode
def show_online_mode(config):
    """Entry point for online mode"""
    show_online_mode_enhanced(config)
