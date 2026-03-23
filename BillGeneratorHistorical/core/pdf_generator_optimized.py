"""
Optimized PDF Generator for Infrastructure Bills
Addresses: A4 page utilization, 10-15mm margins, landscape/portrait support
Elegant HTML to PDF conversion with statutory compliance
"""

import logging
import os
from typing import Dict, Literal, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFGenerator:
    """
    Professional PDF Generator with precise A4 layout control
    
    Features:
    - Exact 10-15mm margins for A4 pages
    - Landscape and portrait orientation support
    - Multiple PDF engine support with intelligent fallback
    - Cloud deployment compatible
    - Statutory format compliance
    """
    
    # A4 dimensions in mm
    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297
    
    # Margin specifications (in mm)
    MARGIN_TOP = 10
    MARGIN_RIGHT = 10
    MARGIN_BOTTOM = 10
    MARGIN_LEFT = 10
    
    def __init__(self, 
                 orientation: Literal['portrait', 'landscape'] = 'portrait',
                 custom_margins: Optional[Dict[str, int]] = None):
        """
        Initialize PDF Generator
        
        Args:
            orientation: 'portrait' or 'landscape'
            custom_margins: Optional dict with keys: top, right, bottom, left (in mm)
        """
        self.orientation = orientation
        
        # Set margins
        if custom_margins:
            self.margin_top = custom_margins.get('top', self.MARGIN_TOP)
            self.margin_right = custom_margins.get('right', self.MARGIN_RIGHT)
            self.margin_bottom = custom_margins.get('bottom', self.MARGIN_BOTTOM)
            self.margin_left = custom_margins.get('left', self.MARGIN_LEFT)
        else:
            self.margin_top = self.MARGIN_TOP
            self.margin_right = self.MARGIN_RIGHT
            self.margin_bottom = self.MARGIN_BOTTOM
            self.margin_left = self.MARGIN_LEFT
        
        # Calculate content dimensions
        if orientation == 'landscape':
            self.page_width = self.A4_HEIGHT_MM
            self.page_height = self.A4_WIDTH_MM
        else:
            self.page_width = self.A4_WIDTH_MM
            self.page_height = self.A4_HEIGHT_MM
        
        self.content_width = self.page_width - self.margin_left - self.margin_right
        self.content_height = self.page_height - self.margin_top - self.margin_bottom
        
        # Detect available PDF engines
        self.available_engines = self._detect_engines()
        logger.info(f"Available PDF engines: {self.available_engines}")
    
    def _detect_engines(self) -> list:
        """Detect available PDF generation engines"""
        engines = []
        
        # Check for Chrome/Chromium (BEST - No shrinking!)
        import shutil
        chrome_paths = [
            shutil.which('google-chrome'),
            shutil.which('chrome'),
            shutil.which('chromium'),
            shutil.which('chromium-browser'),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        for chrome_path in chrome_paths:
            if chrome_path and os.path.exists(chrome_path):
                engines.append('chrome')
                break
        
        # Check for pdfkit/wkhtmltopdf
        try:
            import pdfkit
            engines.append('pdfkit')
        except ImportError:
            pass
        
        # Check for WeasyPrint
        try:
            import weasyprint
            engines.append('weasyprint')
        except ImportError:
            pass
        
        # Check for ReportLab
        try:
            from reportlab.pdfgen import canvas
            engines.append('reportlab')
        except ImportError:
            pass
        
        # Check for xhtml2pdf
        try:
            from xhtml2pdf import pisa
            engines.append('xhtml2pdf')
        except ImportError:
            pass
        
        return engines
    
    def get_base_css(self) -> str:
        """
        Generate base CSS with precise A4 page layout and margins
        Ensures proper page utilization with 10-15mm margins
        """
        css = f"""
        @page {{
            size: A4 {self.orientation};
            margin-top: {self.margin_top}mm;
            margin-right: {self.margin_right}mm;
            margin-bottom: {self.margin_bottom}mm;
            margin-left: {self.margin_left}mm;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Arial', 'Helvetica', sans-serif;
            font-size: 10pt;
            line-height: 1.4;
            color: #000;
            background: white;
        }}
        
        .page-container {{
            width: 100%;
            height: 100%;
            position: relative;
        }}
        
        /* Content area dimensions to maximize A4 page usage */
        .content-area {{
            width: {self.content_width}mm;
            min-height: {self.content_height}mm;
        }}
        
        /* Header styling */
        .document-header {{
            width: 100%;
            padding: 8px 0;
            border-bottom: 2px solid #333;
            margin-bottom: 10px;
        }}
        
        .document-title {{
            font-size: 16pt;
            font-weight: bold;
            text-align: center;
            margin-bottom: 5px;
            text-transform: uppercase;
        }}
        
        .document-subtitle {{
            font-size: 11pt;
            text-align: center;
            margin-bottom: 3px;
        }}
        
        /* Table styling for bills */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 8px 0;
            font-size: 9pt;
        }}
        
        table th {{
            background-color: #2c3e50;
            color: white;
            padding: 6px 4px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #000;
        }}
        
        table td {{
            padding: 5px 4px;
            border: 1px solid #333;
            vertical-align: top;
        }}
        
        table tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        /* Numeric alignment */
        .numeric {{
            text-align: right;
            font-family: 'Courier New', monospace;
        }}
        
        /* Summary sections */
        .summary-section {{
            width: 100%;
            margin-top: 15px;
            page-break-inside: avoid;
        }}
        
        .summary-row {{
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #ddd;
        }}
        
        .summary-label {{
            font-weight: bold;
            flex: 1;
        }}
        
        .summary-value {{
            flex: 1;
            text-align: right;
            font-family: 'Courier New', monospace;
        }}
        
        .grand-total {{
            background-color: #2c3e50;
            color: white;
            padding: 8px 10px;
            margin-top: 10px;
            font-weight: bold;
            font-size: 12pt;
        }}
        
        /* Signature section */
        .signature-section {{
            margin-top: 30px;
            page-break-inside: avoid;
        }}
        
        .signature-box {{
            display: inline-block;
            width: 45%;
            text-align: center;
            margin: 20px 2%;
        }}
        
        .signature-line {{
            border-top: 1px solid #000;
            margin-top: 40px;
            padding-top: 5px;
        }}
        
        /* Footer */
        .document-footer {{
            width: 100%;
            text-align: center;
            font-size: 8pt;
            color: #666;
            margin-top: 15px;
            padding-top: 8px;
            border-top: 1px solid #ccc;
        }}
        
        /* Page break utilities */
        .page-break {{
            page-break-after: always;
        }}
        
        .no-break {{
            page-break-inside: avoid;
        }}
        
        /* Print optimization */
        @media print {{
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            
            .page-container {{
                page-break-after: always;
            }}
            
            .page-container:last-child {{
                page-break-after: auto;
            }}
        }}
        """
        return css
    
    def generate_html_template(self, 
                              title: str,
                              subtitle: str = "",
                              content: str = "",
                              footer: str = "",
                              custom_css: str = "") -> str:
        """
        Generate complete HTML with proper structure for PDF conversion
        
        Args:
            title: Document title
            subtitle: Optional subtitle
            content: Main content HTML
            footer: Footer text
            custom_css: Additional CSS styles
        
        Returns:
            Complete HTML string ready for PDF conversion
        """
        base_css = self.get_base_css()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {base_css}
        {custom_css}
    </style>
</head>
<body>
    <div class="page-container">
        <div class="content-area">
            <div class="document-header">
                <div class="document-title">{title}</div>
                {f'<div class="document-subtitle">{subtitle}</div>' if subtitle else ''}
            </div>
            
            <div class="document-content">
                {content}
            </div>
            
            {f'<div class="document-footer">{footer}</div>' if footer else ''}
        </div>
    </div>
</body>
</html>"""
        return html
    
    def html_to_pdf_weasyprint(self, html_content: str, output_path: str) -> bool:
        """Generate PDF using WeasyPrint (best quality)"""
        try:
            from weasyprint import CSS, HTML
            from weasyprint.text.fonts import FontConfiguration
            
            font_config = FontConfiguration()
            
            # Create CSS with proper page setup
            css_string = f"""
            @page {{
                size: A4 {self.orientation};
                margin-top: {self.margin_top}mm;
                margin-right: {self.margin_right}mm;
                margin-bottom: {self.margin_bottom}mm;
                margin-left: {self.margin_left}mm;
            }}
            """
            
            html_doc = HTML(string=html_content)
            css_doc = CSS(string=css_string, font_config=font_config)
            
            html_doc.write_pdf(
                output_path,
                stylesheets=[css_doc],
                font_config=font_config
            )
            
            logger.info(f"PDF generated successfully using WeasyPrint: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"WeasyPrint generation failed: {e}")
            return False
    
    def html_to_pdf_reportlab(self, html_content: str, output_path: str) -> bool:
        """Generate PDF using ReportLab (fallback with HTML parsing)"""
        try:
            from bs4 import BeautifulSoup
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import (Paragraph, SimpleDocTemplate,
                                            Table, TableStyle)

            # Set page size
            if self.orientation == 'landscape':
                page_size = landscape(A4)
            else:
                page_size = A4
            
            # Create document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=page_size,
                topMargin=self.margin_top*mm,
                rightMargin=self.margin_right*mm,
                bottomMargin=self.margin_bottom*mm,
                leftMargin=self.margin_left*mm
            )
            
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            story = []
            
            # Extract and convert content
            for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'table', 'div']):
                if element.name == 'h1':
                    style = getSampleStyleSheet()['Heading1']
                    story.append(Paragraph(element.get_text(), style))
                elif element.name == 'h2':
                    style = getSampleStyleSheet()['Heading2']
                    story.append(Paragraph(element.get_text(), style))
                elif element.name == 'h3':
                    style = getSampleStyleSheet()['Heading3']
                    story.append(Paragraph(element.get_text(), style))
                elif element.name == 'p':
                    style = getSampleStyleSheet()['Normal']
                    story.append(Paragraph(element.get_text(), style))
                elif element.name == 'table':
                    # Convert HTML table to ReportLab table
                    data = []
                    for row in element.find_all('tr'):
                        row_data = []
                        for cell in row.find_all(['td', 'th']):
                            row_data.append(cell.get_text())
                        data.append(row_data)
                    
                    if data:
                        table = Table(data)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        story.append(table)
                elif element.name == 'div':
                    style = getSampleStyleSheet()['Normal']
                    story.append(Paragraph(element.get_text(), style))
            
            # Build PDF
            doc.build(story)
            logger.info(f"PDF generated successfully using ReportLab: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"ReportLab generation failed: {e}")
            return False
    
    def html_to_pdf_xhtml2pdf(self, html_content: str, output_path: str) -> bool:
        """Generate PDF using xhtml2pdf (good compatibility)"""
        try:

            from xhtml2pdf import pisa

            # Create PDF
            with open(output_path, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(
                    html_content,
                    dest=pdf_file
                )
            
            if not pisa_status.err:
                logger.info(f"PDF generated successfully using xhtml2pdf: {output_path}")
                return True
            else:
                logger.error("xhtml2pdf generation failed with errors")
                return False
                
        except Exception as e:
            logger.error(f"xhtml2pdf generation failed: {e}")
            return False
    
    def html_to_pdf_chrome(self, html_content: str, output_path: str) -> bool:
        """Generate PDF using Chrome Headless (BEST - No shrinking!)"""
        try:
            import shutil
            import subprocess
            import tempfile

            # Find Chrome executable
            chrome_paths = [
                shutil.which('google-chrome'),
                shutil.which('chrome'),
                shutil.which('chromium'),
                shutil.which('chromium-browser'),
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            
            chrome_exe = None
            for path in chrome_paths:
                if path and os.path.exists(path):
                    chrome_exe = path
                    break
            
            if not chrome_exe:
                logger.error("Chrome executable not found")
                return False
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_html = f.name
            
            try:
                # Chrome headless command with PERFECT settings (NO HEADERS/FOOTERS!)
                cmd = [
                    chrome_exe,
                    '--headless',
                    '--disable-gpu',
                    '--no-margins',  # Use CSS margins instead
                    '--disable-smart-shrinking',  # CRITICAL!
                    '--run-all-compositor-stages-before-draw',
                    '--no-pdf-header-footer',  # REMOVE TIMESTAMP AND FILE PATH
                    '--print-to-pdf=' + output_path,
                    temp_html
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and os.path.exists(output_path):
                    logger.info(f"PDF generated successfully using Chrome: {output_path}")
                    return True
                else:
                    logger.error(f"Chrome PDF generation failed: {result.stderr}")
                    return False
                    
            finally:
                # Clean up temp file
                if os.path.exists(temp_html):
                    os.unlink(temp_html)
                    
        except Exception as e:
            logger.error(f"Chrome PDF generation failed: {e}")
            return False
    
    def html_to_pdf_pdfkit(self, html_content: str, output_path: str) -> bool:
        """Generate PDF using pdfkit (basic but reliable)"""
        try:
            import pdfkit

            # Configure options - ROCK SOLID ANTI-SHRINK SETTINGS (NO HEADERS/FOOTERS!)
            options = {
                'page-size': 'A4',
                'orientation': self.orientation,
                'margin-top': f'{self.margin_top}mm',
                'margin-right': f'{self.margin_right}mm',
                'margin-bottom': f'{self.margin_bottom}mm',
                'margin-left': f'{self.margin_left}mm',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None,
                'disable-smart-shrinking': None,  # CRITICAL: Prevents table shrinking
                'zoom': '1.0',  # CRITICAL: No scaling
                'dpi': 96,  # CRITICAL: Standard DPI for perfect rendering
                'image-quality': 100,  # Maximum quality
                'no-header-line': None,  # Remove header line
                'no-footer-line': None  # Remove footer line
            }
            
            # Try to configure wkhtmltopdf path
            try:
                import platform
                if platform.system() == "Windows":
                    wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
                    if os.path.exists(wkhtmltopdf_path):
                        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
                        pdfkit.from_string(html_content, output_path, configuration=config, options=options)
                    else:
                        pdfkit.from_string(html_content, output_path, options=options)
                else:
                    pdfkit.from_string(html_content, output_path, options=options)
            except:
                pdfkit.from_string(html_content, output_path, options=options)
            
            logger.info(f"PDF generated successfully using pdfkit: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"pdfkit generation failed: {e}")
            return False
    
    def generate_pdf(self, html_content: str, output_path: str, engine: Optional[str] = None) -> bool:
        """
        Generate PDF using the specified engine or best available engine
        
        Args:
            html_content: HTML content to convert to PDF
            output_path: Path where PDF should be saved
            engine: Specific engine to use (weasyprint, reportlab, xhtml2pdf, pdfkit)
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Determine which engine to use
        if engine is None:
            if not self.available_engines:
                raise Exception("No PDF generation engines available")
            engine = self.available_engines[0]  # Use the best available engine
        
        # Validate engine
        if engine not in self.available_engines:
            raise Exception(f"PDF engine {engine} not available")
        
        # Generate PDF using selected engine
        if engine == "chrome":
            return self.html_to_pdf_chrome(html_content, output_path)
        elif engine == "pdfkit":
            return self.html_to_pdf_pdfkit(html_content, output_path)
        elif engine == "weasyprint":
            return self.html_to_pdf_weasyprint(html_content, output_path)
        elif engine == "reportlab":
            return self.html_to_pdf_reportlab(html_content, output_path)
        elif engine == "xhtml2pdf":
            return self.html_to_pdf_xhtml2pdf(html_content, output_path)
        else:
            raise Exception(f"Unsupported PDF engine: {engine}")
    
    def generate_with_fallback(self, html_content: str, output_path: str) -> str:
        """
        Generate PDF using the best available engine with fallbacks
        
        Args:
            html_content: HTML content to convert to PDF
            output_path: Path where PDF should be saved
        
        Returns:
            str: Engine used to generate PDF
        """
        # Try engines in order of preference
        for engine in self.available_engines:
            try:
                success = self.generate_pdf(html_content, output_path, engine)
                if success:
                    return engine
            except Exception as e:
                logger.warning(f"Failed to generate PDF with {engine}: {e}")
                continue
        
        raise Exception("Failed to generate PDF with any available engine")


# Example usage
if __name__ == "__main__":
    # Create sample bill data
    sample_content = """
    <table>
        <thead>
            <tr>
                <th>S.No.</th>
                <th>Description</th>
                <th>Unit</th>
                <th>Quantity</th>
                <th>Rate</th>
                <th>Amount</th>
                <th>Remark</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>1</td>
                <td>Excavation in Hard Strata</td>
                <td>Cum</td>
                <td>100.00</td>
                <td>500.00</td>
                <td>50,000.00</td>
                <td>As per specification</td>
            </tr>
            <tr>
                <td>2</td>
                <td>Reinforcement Steel</td>
                <td>MT</td>
                <td>5.00</td>
                <td>60,000.00</td>
                <td>300,000.00</td>
                <td>Fe 500 Grade</td>
            </tr>
        </tbody>
    </table>
    
    <div class="summary-section">
        <div class="summary-row">
            <div class="summary-label">Grand Total:</div>
            <div class="summary-value">₹350,000.00</div>
        </div>
        <div class="summary-row">
            <div class="summary-label">Tender Premium @ 5%:</div>
            <div class="summary-value">₹17,500.00</div>
        </div>
        <div class="summary-row grand-total">
            <div class="summary-label">Payable Amount:</div>
            <div class="summary-value">₹367,500.00</div>
        </div>
    </div>
    """
    
    # Create PDF generator
    pdf_gen = PDFGenerator(orientation='landscape')
    
    # Generate HTML template
    html = pdf_gen.generate_html_template(
        title="INFRASTRUCTURE WORKS BILL",
        subtitle="Government of India - Ministry of Infrastructure",
        content=sample_content,
        footer="This is a computer generated document. No signature required."
    )
    
    # Generate PDF with fallback
    try:
        engine_used = pdf_gen.generate_with_fallback(html, "sample_bill.pdf")
        print(f"PDF generated successfully using {engine_used}")
    except Exception as e:
        print(f"Failed to generate PDF: {e}")