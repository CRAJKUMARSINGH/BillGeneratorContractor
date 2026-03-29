"""
Streamlit Integration for Optimized PDF Generator
Handles Streamlit Cloud deployment constraints and provides user-friendly interface
"""

import logging
import os
from typing import Any, Dict, Optional

import streamlit as st

# Import the optimized PDF generator
try:
    from core.pdf_generator_optimized import PDFGenerator
except ImportError:
    # Fallback for direct execution
    from pdf_generator_optimized import PDFGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamlitPDFManager:
    """
    Manages PDF generation in Streamlit environment
    Handles cloud deployment constraints and provides UI components
    """
    
    def __init__(self):
        """Initialize Streamlit PDF Manager"""
        self.is_cloud = self._detect_cloud_environment()
        self.temp_dir = self._setup_temp_directory()
        
    def _detect_cloud_environment(self) -> bool:
        """Detect if running in Streamlit Cloud"""
        return (
            os.getenv('STREAMLIT_CLOUD', 'false').lower() == 'true' or
            os.getenv('STREAMLIT_SHARING_MODE') is not None or
            not os.path.exists('/usr/local/bin/wkhtmltopdf')
        )
    
    def _setup_temp_directory(self) -> str:
        """Setup temporary directory for PDF generation"""
        temp_dir = os.path.join(os.getcwd(), 'temp_pdfs')
        os.makedirs(temp_dir, exist_ok=True)

        # Opportunistic cleanup to control disk/memory usage
        # Remove stray files older than 2 hours and cap directory size
        try:
            self._cleanup_temp_directory(temp_dir, max_age_seconds=2 * 60 * 60, max_files=500)
        except Exception:
            # Best-effort only; never fail app startup due to cleanup
            pass

        return temp_dir

    def _cleanup_temp_directory(self, directory: str, max_age_seconds: int = 7200, max_files: int = 500) -> None:
        """
        Remove old files to keep temp directory tidy and bounded.

        Args:
            directory: Path to the temp directory
            max_age_seconds: Delete files older than this age
            max_files: If more than this count, delete oldest beyond the cap
        """
        try:
            entries = []
            for name in os.listdir(directory):
                path = os.path.join(directory, name)
                if not os.path.isfile(path):
                    continue
                try:
                    mtime = os.path.getmtime(path)
                    entries.append((mtime, path))
                except OSError:
                    continue

            # Delete by age
            import time
            cutoff = time.time() - max_age_seconds
            for mtime, path in entries:
                if mtime < cutoff:
                    try:
                        os.remove(path)
                    except OSError:
                        pass

            # Enforce file count cap (recompute after age-based removals)
            entries = [(os.path.getmtime(os.path.join(directory, n)), os.path.join(directory, n))
                       for n in os.listdir(directory)
                       if os.path.isfile(os.path.join(directory, n))]
            if len(entries) > max_files:
                entries.sort()  # oldest first
                for _, path in entries[: len(entries) - max_files]:
                    try:
                        os.remove(path)
                    except OSError:
                        pass
        except Exception:
            # Never propagate cleanup errors
            pass
    
    def create_pdf_configuration_ui(self) -> Dict[str, Any]:
        """
        Create Streamlit UI for PDF configuration
        Returns configuration dict
        """
        st.sidebar.header("📄 PDF Configuration")
        
        # Orientation selector
        orientation = st.sidebar.selectbox(
            "Page Orientation",
            options=['portrait', 'landscape'],
            index=0,
            help="Select page orientation for the PDF document"
        )
        
        # Margin configuration
        st.sidebar.subheader("Margins (mm)")
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            margin_top = st.number_input("Top", min_value=5, max_value=25, value=12, step=1)
            margin_left = st.number_input("Left", min_value=5, max_value=25, value=12, step=1)
        
        with col2:
            margin_bottom = st.number_input("Bottom", min_value=5, max_value=25, value=12, step=1)
            margin_right = st.number_input("Right", min_value=5, max_value=25, value=12, step=1)
        
        margins = {
            'top': margin_top,
            'right': margin_right,
            'bottom': margin_bottom,
            'left': margin_left
        }
        
        # Page utilization info
        if orientation == 'portrait':
            content_width = 210 - margin_left - margin_right
            content_height = 297 - margin_top - margin_bottom
        else:
            content_width = 297 - margin_left - margin_right
            content_height = 210 - margin_top - margin_bottom
        
        st.sidebar.info(
            f"**Content Area:**\n"
            f"Width: {content_width:.1f}mm\n"
            f"Height: {content_height:.1f}mm\n"
            f"Utilization: {((content_width * content_height) / (210 * 297) * 100):.1f}%"
        )
        
        return {
            'orientation': orientation,
            'margins': margins
        }
    
    def generate_bill_pdf(self,
                         bill_data: Dict[str, Any],
                         config: Dict[str, Any],
                         output_filename: str = "infrastructure_bill.pdf") -> Optional[str]:
        """
        Generate infrastructure bill PDF
        
        Args:
            bill_data: Dictionary containing bill information
            config: PDF configuration from UI
            output_filename: Name for the output PDF file
        
        Returns:
            Path to generated PDF or None if failed
        """
        try:
            # Create PDF generator with configuration
            generator = PDFGenerator(
                orientation=config['orientation'],
                custom_margins=config['margins']
            )
            
            # Generate HTML content
            html_content = self._create_bill_html(generator, bill_data)
            
            # Generate PDF
            output_path = os.path.join(self.temp_dir, output_filename)
            
            with st.spinner('Generating PDF... Please wait.'):
                success = generator.generate_pdf(html_content, output_path)
            
            if success:
                logger.info(f"PDF generated successfully: {output_path}")
                return output_path
            else:
                st.error("PDF generation failed. Please check the logs.")
                return None
                
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            st.error(f"Error: {str(e)}")
            return None
    
    def _create_bill_html(self, generator: PDFGenerator, bill_data: Dict[str, Any]) -> str:
        """Create HTML content for bill"""
        
        # Extract bill data
        title = bill_data.get('title', 'INFRASTRUCTURE BILL')
        subtitle = bill_data.get('subtitle', '')
        items = bill_data.get('items', [])
        summary = bill_data.get('summary', {})
        footer = bill_data.get('footer', '')
        
        # Build table HTML
        table_html = """
        <table>
            <thead>
                <tr>
                    <th style="width: 5%;">S.No.</th>
                    <th style="width: 40%;">Description of Work</th>
                    <th style="width: 8%;">Unit</th>
                    <th style="width: 12%;">Quantity</th>
                    <th style="width: 15%;">Rate (₹)</th>
                    <th style="width: 20%;">Amount (₹)</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for idx, item in enumerate(items, 1):
            table_html += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{item.get('description', '')}</td>
                    <td>{item.get('unit', '')}</td>
                    <td class="numeric">{item.get('quantity', '')}</td>
                    <td class="numeric">{item.get('rate', '')}</td>
                    <td class="numeric">{item.get('amount', '')}</td>
                </tr>
            """
        
        table_html += """
            </tbody>
        </table>
        """
        
        # Build summary HTML
        summary_html = '<div class="summary-section">'
        
        if 'subtotal' in summary:
            summary_html += f"""
                <div class="summary-row">
                    <span class="summary-label">Sub Total:</span>
                    <span class="summary-value">₹ {summary['subtotal']}</span>
                </div>
            """
        
        if 'premium' in summary:
            summary_html += f"""
                <div class="summary-row">
                    <span class="summary-label">{summary.get('premium_label', 'Tender Premium')}:</span>
                    <span class="summary-value">₹ {summary['premium']}</span>
                </div>
            """
        
        if 'gst' in summary:
            summary_html += f"""
                <div class="summary-row">
                    <span class="summary-label">{summary.get('gst_label', 'GST @ 18%')}:</span>
                    <span class="summary-value">₹ {summary['gst']}</span>
                </div>
            """
        
        if 'grand_total' in summary:
            summary_html += f"""
                <div class="grand-total">
                    <div style="display: flex; justify-content: space-between;">
                        <span>GRAND TOTAL:</span>
                        <span>₹ {summary['grand_total']}</span>
                    </div>
                </div>
            """
        
        summary_html += '</div>'
        
        # Build signature section
        signature_html = """
        <div class="signature-section">
            <div class="signature-box">
                <div class="signature-line">
                    <strong>Contractor's Signature</strong><br>
                    Date: ______________
                </div>
            </div>
            <div class="signature-box">
                <div class="signature-line">
                    <strong>Engineer-in-Charge</strong><br>
                    Date: ______________
            </div>
            </div>
        </div>
        """
        
        # Combine all content
        content = table_html + summary_html + signature_html
        
        # Generate complete HTML
        html = generator.generate_html_template(
            title=title,
            subtitle=subtitle,
            content=content,
            footer=footer
        )
        
        return html
    
    def display_pdf_download_button(self, pdf_path: str, button_text: str = "📥 Download PDF"):
        """Display download button for generated PDF"""
        try:
            with open(pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
            
            st.download_button(
                label=button_text,
                data=pdf_bytes,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            logger.error(f"Error creating download button: {e}")
            st.error("Failed to create download button")
    
    def display_environment_info(self):
        """Display deployment environment information"""
        with st.expander("ℹ️ System Information", expanded=False):
            st.write(f"**Cloud Mode:** {'Yes' if self.is_cloud else 'No'}")
            
            # Check available PDF engines
            generator = PDFGenerator()
            st.write(f"**Available PDF Engines:** {', '.join(generator.available_engines)}")
            
            if not generator.available_engines:
                st.warning("⚠️ No PDF engines detected! Please install required packages.")
            
            st.write(f"**Temporary Directory:** {self.temp_dir}")


# Example Streamlit app
def main():
    """Example Streamlit app using the PDF manager"""
    
    st.set_page_config(
        page_title="Infrastructure Bill Generator",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("🏗️ Infrastructure Bill Generator")
    st.markdown("Generate professional infrastructure bills with precise A4 formatting")
    
    # Initialize PDF manager
    pdf_manager = StreamlitPDFManager()
    
    # Display environment info
    pdf_manager.display_environment_info()
    
    # Get PDF configuration
    config = pdf_manager.create_pdf_configuration_ui()
    
    # Main content area
    st.header("Bill Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        bill_title = st.text_input(
            "Bill Title",
            value="CONTRACTOR RUNNING BILL - JANUARY 2025"
        )
    
    with col2:
        bill_subtitle = st.text_input(
            "Subtitle",
            value="Work Order No: WO/2024-25/1234 | Project: Highway Construction"
        )
    
    # Sample data for demonstration
    st.subheader("Work Items")
    
    sample_items = [
        {
            'description': 'Earthwork in excavation by mechanical means',
            'unit': 'Cum',
            'quantity': '1,250.00',
            'rate': '185.50',
            'amount': '2,31,875.00'
        },
        {
            'description': 'Providing and laying cement concrete 1:2:4',
            'unit': 'Cum',
            'quantity': '850.00',
            'rate': '4,850.00',
            'amount': '4,12,250.00'
        },
        {
            'description': 'Reinforcement steel (Fe 500)',
            'unit': 'MT',
            'quantity': '25.50',
            'rate': '62,000.00',
            'amount': '15,81,000.00'
        }
    ]
    
    # Display items in a table
    st.table(sample_items)
    
    # Summary data
    summary_data = {
        'subtotal': '22,25,125.00',
        'premium': '1,11,256.25',
        'gst': '4,19,498.66',
        'grand_total': '27,55,879.91'
    }
    
    # Create bill data structure
    bill_data = {
        'title': bill_title,
        'subtitle': bill_subtitle,
        'items': sample_items,
        'summary': summary_data,
        'footer': "This is a computer-generated document. No signature required."
    }
    
    # Generate PDF button
    if st.button("Generate PDF", type="primary", use_container_width=True):
        with st.spinner("Generating your professional bill..."):
            pdf_path = pdf_manager.generate_bill_pdf(bill_data, config)
            
            if pdf_path:
                st.success("✅ PDF generated successfully!")
                pdf_manager.display_pdf_download_button(pdf_path)
            else:
                st.error("❌ Failed to generate PDF")


# For testing purposes
if __name__ == "__main__":
    main()