"""
SIMPLE WORK ORDER PROCESSOR APP
For layman contractors who just write item codes and quantities on paper

This app:
1. Asks for work order folder (scanned images)
2. Reads handwritten quantities from qty.txt
3. Creates Excel file with all quantities
4. Shows what was found
"""

import streamlit as st
from pathlib import Path
import pandas as pd
import pytesseract
from PIL import Image
import json
import os
import sys

# Page config
st.set_page_config(
    page_title="Simple Work Order Processor",
    page_icon="📄",
    layout="wide"
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    .step-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        margin-bottom: 1rem;
    }
    .success-card {
        background: #d4edda;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin-bottom: 1rem;
    }
    .info-card {
        background: #d1ecf1;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #17a2b8;
        margin-bottom: 1rem;
    }
    .file-list {
        background: #e9ecef;
        padding: 1rem;
        border-radius: 5px;
        font-family: monospace;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📄 Simple Work Order Processor</h1>
    <p>For layman contractors - just write item codes and quantities on paper</p>
</div>
""", unsafe_allow_html=True)

# Introduction
st.markdown("""
<div class="info-card">
    <h3>🎯 How it works</h3>
    <p>This app helps contractors who work with scanned work orders and handwritten quantities.</p>
    <p><strong>What you need:</strong></p>
    <ol>
        <li>📸 <strong>Work Order:</strong> Scanned images (PDF/JPEG) of your work order</li>
        <li>✍️ <strong>Quantities:</strong> A text file named <code>qty.txt</code> with item codes and quantities</li>
    </ol>
    <p><strong>Format of qty.txt:</strong></p>
    <pre style="background: white; padding: 1rem; border-radius: 5px;">
1.1.2 6
1.1.3 19
1.3.3 2
3.4.2 22
4.1.23 5
18.13 1</pre>
</div>
""", unsafe_allow_html=True)

# Step 1: Select work order folder
st.markdown("""
<div class="step-card">
    <h3>1️⃣ Select Work Order Folder</h3>
    <p>Choose the folder containing your scanned work order images and qty.txt file.</p>
</div>
""", unsafe_allow_html=True)

# Folder selection
col1, col2 = st.columns([3, 1])
with col1:
    folder_path = st.text_input(
        "Work Order Folder Path",
        value="INPUT/work_order_samples/work_01_27022026",
        help="Path to folder containing scanned images and qty.txt"
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    process_btn = st.button("🚀 Process Work Order", type="primary", use_container_width=True)

# Initialize session state
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'quantities' not in st.session_state:
    st.session_state.quantities = {}
if 'excel_file' not in st.session_state:
    st.session_state.excel_file = None
if 'ocr_text' not in st.session_state:
    st.session_state.ocr_text = ""

def read_quantities(folder_path):
    """Read quantities from qty.txt file"""
    folder = Path(folder_path)
    qty_file = folder / "qty.txt"
    
    if not qty_file.exists():
        st.error(f"❌ ERROR: qty.txt not found in {folder}")
        st.info(f"Please make sure qty.txt exists with format:")
        st.code("1.1.2 6\n1.1.3 19\n...")
        return None
    
    quantities = {}
    with open(qty_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                item_num = parts[0]
                try:
                    qty = float(parts[1])
                    quantities[item_num] = qty
                except ValueError:
                    st.warning(f"⚠️ Could not parse quantity on line {line_num}: {line}")
            else:
                st.warning(f"⚠️ Invalid format on line {line_num}: {line}")
    
    return quantities

def read_work_order_images(folder_path):
    """Read text from work order images using OCR"""
    folder = Path(folder_path)
    
    # Look for image files
    image_extensions = ['*.jpeg', '*.jpg', '*.png', '*.bmp', '*.tiff']
    image_files = []
    for ext in image_extensions:
        image_files.extend(sorted(folder.glob(ext)))
    
    if not image_files:
        st.info("ℹ️ No image files found in work order folder")
        st.info("Supported formats: JPEG, PNG, BMP, TIFF")
        return ""
    
    all_text = ""
    progress_bar = st.progress(0)
    
    for idx, img_file in enumerate(image_files):
        try:
            img = Image.open(img_file)
            text = pytesseract.image_to_string(img, lang='eng+hin')
            all_text += f"\n{'='*40}\nFile: {img_file.name}\n{'='*40}\n{text}\n"
        except Exception as e:
            st.warning(f"⚠️ Error reading {img_file.name}: {e}")
        
        progress_bar.progress((idx + 1) / len(image_files))
    
    return all_text

def find_item_descriptions(ocr_text, item_numbers):
    """Try to find descriptions for item numbers in OCR text"""
    descriptions = {}
    
    for item_num in item_numbers:
        # Look for item number in text
        lines = ocr_text.split('\n')
        for i, line in enumerate(lines):
            if item_num in line:
                # Try to get description from surrounding lines
                description = line.strip()
                # Look for next few lines that might contain description
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not any(char.isdigit() for char in next_line[:10]):
                        description += " " + next_line
                        break
                descriptions[item_num] = description[:200]  # Limit length
                break
    
    return descriptions

def create_excel_file(quantities, descriptions, output_path, source_folder):
    """Create Excel file with quantities and descriptions"""
    data = []
    
    for item_num, qty in quantities.items():
        desc = descriptions.get(item_num, f"Item {item_num}")
        data.append({
            'Item Number': item_num,
            'Description': desc,
            'Quantity': qty,
            'Unit': 'nos',
            'Rate': 0.0,
            'Amount': 0.0
        })
    
    df = pd.DataFrame(data)
    
    # Save to Excel
    output_file = Path(output_path)
    output_file.parent.mkdir(exist_ok=True)
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Bill Quantities')
        
        # Add summary sheet
        summary_data = {
            'Total Items': [len(quantities)],
            'Total Quantity': [sum(quantities.values())],
            'Source Folder': [str(source_folder)],
            'Generated On': [pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, index=False, sheet_name='Summary')
    
    return df, output_file

# Process button clicked
if process_btn:
    with st.spinner("🔍 Checking work order folder..."):
        folder = Path(folder_path)
        
        if not folder.exists():
            st.error(f"❌ Folder not found: {folder_path}")
            st.stop()
        
        # Show files in folder
        st.markdown("### 📁 Files in folder:")
        files = sorted(list(folder.iterdir()))
        file_list = "\n".join([f"• {f.name}" for f in files])
        st.markdown(f'<div class="file-list">{file_list}</div>', unsafe_allow_html=True)
        
        # Step 1: Read quantities
        st.markdown("### 1️⃣ Reading quantities from qty.txt...")
        quantities = read_quantities(folder_path)
        
        if quantities:
            st.success(f"✅ Found {len(quantities)} items with quantities")
            
            # Show quantities in a nice table
            qty_df = pd.DataFrame(list(quantities.items()), columns=['Item Number', 'Quantity'])
            st.dataframe(qty_df, use_container_width=True)
            
            # Step 2: Read work order images
            st.markdown("### 2️⃣ Reading work order images with OCR...")
            ocr_text = read_work_order_images(folder_path)
            
            if ocr_text:
                st.success(f"✅ Extracted {len(ocr_text)} characters of text")
                
                # Save OCR text
                ocr_file = Path("OUTPUT") / "ocr_extracted_text.txt"
                ocr_file.parent.mkdir(exist_ok=True)
                with open(ocr_file, 'w', encoding='utf-8') as f:
                    f.write(ocr_text)
                
                # Step 3: Find item descriptions
                st.markdown("### 3️⃣ Finding item descriptions in work order...")
                descriptions = find_item_descriptions(ocr_text, quantities.keys())
                
                if descriptions:
                    st.success(f"✅ Found descriptions for {len(descriptions)} items")
                else:
                    st.info("ℹ️ Could not find specific item descriptions in work order")
                    st.info("Using generic descriptions instead")
                
                # Step 4: Create Excel file
                st.markdown("### 4️⃣ Creating Excel file...")
                output_path = "OUTPUT/work_order_with_quantities.xlsx"
                df, excel_file = create_excel_file(quantities, descriptions, output_path, folder_path)
                
                st.success(f"✅ Excel file created: {excel_file}")
                
                # Show preview
                st.markdown("#### 📊 Excel Preview:")
                st.dataframe(df, use_container_width=True)
                
                # Step 5: Download section
                st.markdown("---")
                st.markdown("### 📥 Download Results")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Download Excel
                    with open(excel_file, 'rb') as f:
                        excel_bytes = f.read()
                    st.download_button(
                        label="📊 Download Excel",
                        data=excel_bytes,
                        file_name=excel_file.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col2:
                    # Download OCR text
                    with open(ocr_file, 'r', encoding='utf-8') as f:
                        ocr_content = f.read()
                    st.download_button(
                        label="📄 Download OCR Text",
                        data=ocr_content,
                        file_name=ocr_file.name,
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with col3:
                    # Download quantities as JSON
                    quantities_json = json.dumps(quantities, indent=2)
                    st.download_button(
                        label="📋 Download Quantities (JSON)",
                        data=quantities_json,
                        file_name="quantities.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                # Save to session state
                st.session_state.processed = True
                st.session_state.quantities = quantities
                st.session_state.excel_file = excel_file
                st.session_state.ocr_text = ocr_text
                
                # Success message
                st.markdown("""
                <div class="success-card">
                    <h3>🎉 Processing Complete!</h3>
                    <p>Your work order has been successfully processed.</p>
                    <p><strong>Next steps:</strong></p>
                    <ol>
                        <li>Open the Excel file and fill in rates</li>
                        <li>Amounts will be calculated automatically</li>
                        <li>Save and use for billing</li>
                    </ol>
                </div>
                """, unsafe_allow_html=True)
                
                # Show output folder
                output_folder = Path("OUTPUT")
                if output_folder.exists():
                    st.markdown("### 📁 Output Files:")
                    output_files = sorted(list(output_folder.iterdir()))
                    output_list = "\n".join([f"• {f.name}" for f in output_files])
                    st.markdown(f'<div class="file-list">{output_list}</div>', unsafe_allow_html=True)

# Sidebar information
with st.sidebar:
    st.markdown("## ℹ️ About")
    st.markdown("""
    This app is designed for contractors who:
    
    - Work with scanned work orders
    - Write quantities on paper
    - Need simple Excel output
    
    **How to use:**
    1. Put scanned images in a folder
    2. Create `qty.txt` with item codes and quantities
    3. Enter folder path above
    4. Click "Process Work Order"
    
    **Example qty.txt:**
    ```
    1.1.2 6
    1.1.3 19
    1.3.3 2
    3.4.2 22
    4.1.23 5
    18.13 1
    ```
    """)
    
    st.markdown("---")
    st.markdown("## 🛠️ Technical Info")
    st.markdown("""
    **Features:**
    - OCR for scanned images
    - Automatic quantity reading
    - Excel generation
    - Item description matching
    
    **Supported formats:**
    - Images: JPEG, PNG, BMP, TIFF
    - Quantities: qty.txt text file
    - Output: Excel (.xlsx)
    """)
    
    # Check dependencies
    st.markdown("---")
    st.markdown("## 🔧 Dependencies")
    
    deps_ok = True
    try:
        import pytesseract
        st.success("✅ pytesseract")
    except:
        st.error("❌ pytesseract")
        deps_ok = False
    
    try:
        import pandas
        st.success("✅ pandas")
    except:
        st.error("❌ pandas")
        deps_ok = False
    
    try:
        import PIL
        st.success("✅ PIL (Pillow)")
    except:
        st.error("❌ PIL (Pillow)")
        deps_ok = False
    
    if not deps_ok:
        st.error("Some dependencies are missing. Run: `pip install pytesseract pandas pillow`")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; font-size: 0.9rem;">
    <p>Simple Work Order Processor • For layman contractors • Made with ❤️</p>
</div>
""", unsafe_allow_html=True)