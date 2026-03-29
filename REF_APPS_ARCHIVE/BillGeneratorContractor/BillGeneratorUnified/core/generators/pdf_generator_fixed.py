"""
FIXED PDF Generator - 10mm Margins + Landscape Support
Solves: Absurd margins, landscape deviation, table shrinking
"""
import asyncio
import io
import tempfile
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class FixedPDFGenerator:
    """
    Fixed PDF Generator with:
    - Exact 10mm margins on all sides
    - Proper landscape orientation support
    - No table shrinking
    - A4 page size compliance
    """
    
    # A4 dimensions
    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297
    
    # Standard margins (10mm as requested)
    MARGIN_MM = 10
    
    def __init__(self, margin_mm: int = 10):
        """
        Initialize PDF generator
        
        Args:
            margin_mm: Margin size in millimeters (default: 10mm)
        """
        self.margin_mm = margin_mm
        self.dpi = 96  # Standard screen DPI
    
    def add_fixed_css(self, html_content: str, landscape: bool = False) -> str:
        """
        Add CSS for proper margins and no shrinking
        
        Args:
            html_content: Original HTML
            landscape: Use landscape orientation
            
        Returns:
            HTML with fixed CSS
        """
        # Calculate content area (A4 minus margins)
        if landscape:
            content_width_mm = self.A4_HEIGHT_MM - (2 * self.margin_mm)  # 277mm
            content_height_mm = self.A4_WIDTH_MM - (2 * self.margin_mm)  # 190mm
        else:
            content_width_mm = self.A4_WIDTH_MM - (2 * self.margin_mm)  # 190mm
            content_height_mm = self.A4_HEIGHT_MM - (2 * self.margin_mm)  # 277mm
        
        fixed_css = f"""
<style>
    /* CRITICAL: Page setup with exact 10mm margins */
    @page {{
        size: A4 {'landscape' if landscape else 'portrait'};
        margin: {self.margin_mm}mm {self.margin_mm}mm {self.margin_mm}mm {self.margin_mm}mm;
    }}
    
    /* Body setup */
    html, body {{
        margin: 0;
        padding: 0;
        width: 100%;
        height: auto !important;
        min-height: 100%;
        font-family: Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.4;
    }}
    
    /* Content container with exact dimensions */
    body {{
        width: {content_width_mm}mm;
        max-width: {content_width_mm}mm;
        min-height: {content_height_mm}mm;
        margin: 0 auto;
        padding: 0;
        box-sizing: border-box;
    }}
    
    /* CRITICAL: Prevent table shrinking */
    table {{
        width: 100% !important;
        max-width: 100% !important;
        table-layout: fixed !important;
        border-collapse: collapse !important;
        page-break-inside: auto !important;
    }}
    
    /* Table cells */
    th, td {{
        padding: 4px 6px !important;
        border: 1px solid #000 !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        white-space: normal !important;
        vertical-align: top !important;
        box-sizing: border-box !important;
        overflow: visible !important;
    }}
    
    /* Table headers */
    th {{
        background-color: #f0f0f0 !important;
        font-weight: bold !important;
        text-align: center !important;
    }}
    
    /* Prevent page breaks inside table rows */
    tr {{
        page-break-inside: avoid !important;
    }}
    
    /* Headings */
    h1, h2, h3, h4, h5, h6 {{
        margin: 8px 0 !important;
        padding: 0 !important;
        page-break-after: avoid !important;
    }}
    
    h1 {{ font-size: 16pt !important; }}
    h2 {{ font-size: 14pt !important; }}
    h3 {{ font-size: 12pt !important; }}
    
    /* Paragraphs */
    p {{
        margin: 4px 0 !important;
        padding: 0 !important;
    }}
    
    /* Prevent orphans and widows */
    p, li {{
        orphans: 3 !important;
        widows: 3 !important;
    }}
    
    /* Images */
    img {{
        max-width: 100% !important;
        height: auto !important;
        page-break-inside: avoid !important;
    }}
    
    /* CRITICAL: Allow content to flow across pages */
    .container, div {{
        overflow: visible !important;
        height: auto !important;
        max-height: none !important;
    }}
    
    /* Print optimization */
    * {{
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        color-adjust: exact !important;
    }}
    
    /* Disable text rendering optimizations that cause shrinking */
    * {{
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
        text-rendering: geometricPrecision !important;
    }}
</style>
"""
        
        # Insert CSS into HTML
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', f'<head>\n{fixed_css}', 1)
        elif '<html>' in html_content:
            html_content = html_content.replace('<html>', f'<html>\n<head>\n{fixed_css}\n</head>', 1)
        else:
            html_content = f'<!DOCTYPE html>\n<html>\n<head>\n{fixed_css}\n</head>\n<body>\n{html_content}\n</body>\n</html>'
        
        return html_content
    
    def convert_with_reportlab(self, html_content: str, landscape: bool = False) -> bytes:
        """
        Convert HTML to PDF using ReportLab (most reliable, works everywhere)
        
        Args:
            html_content: HTML content
            landscape: Use landscape orientation
            
        Returns:
            PDF bytes
        """
        from reportlab.lib.pagesizes import A4, landscape as rl_landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from bs4 import BeautifulSoup
        import io
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Set page size
        pagesize = rl_landscape(A4) if landscape else A4
        
        # Create PDF with exact 10mm margins
        doc = SimpleDocTemplate(
            buffer,
            pagesize=pagesize,
            leftMargin=self.margin_mm * mm,
            rightMargin=self.margin_mm * mm,
            topMargin=self.margin_mm * mm,
            bottomMargin=self.margin_mm * mm,
            title="Generated Document"
        )
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Build story (content)
        story = []
        styles = getSampleStyleSheet()
        
        # Process HTML elements
        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'table']):
            if element.name in ['h1', 'h2', 'h3']:
                # Headings
                style = styles['Heading1'] if element.name == 'h1' else styles['Heading2']
                story.append(Paragraph(element.get_text(), style))
                story.append(Spacer(1, 6))
            
            elif element.name == 'p':
                # Paragraphs
                story.append(Paragraph(element.get_text(), styles['Normal']))
                story.append(Spacer(1, 4))
            
            elif element.name == 'table':
                # Tables
                table_data = []
                for row in element.find_all('tr'):
                    row_data = []
                    for cell in row.find_all(['th', 'td']):
                        row_data.append(cell.get_text().strip())
                    if row_data:
                        table_data.append(row_data)
                
                if table_data:
                    # Create table
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('WORDWRAP', (0, 0), (-1, -1), True),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def convert_with_weasyprint(self, html_content: str, landscape: bool = False) -> bytes:
        """
        Convert HTML to PDF using WeasyPrint (best HTML/CSS support)
        
        Args:
            html_content: HTML content
            landscape: Use landscape orientation
            
        Returns:
            PDF bytes
        """
        from weasyprint import HTML, CSS
        
        # Add fixed CSS
        html_with_css = self.add_fixed_css(html_content, landscape)
        
        # Convert to PDF
        pdf_bytes = HTML(string=html_with_css).write_pdf()
        
        return pdf_bytes
    
    async def convert_with_playwright_async(self, html_content: str, landscape: bool = False) -> bytes:
        """
        Convert HTML to PDF using Playwright (async)
        
        Args:
            html_content: HTML content
            landscape: Use landscape orientation
            
        Returns:
            PDF bytes
        """
        from playwright.async_api import async_playwright
        
        # Add fixed CSS
        html_with_css = self.add_fixed_css(html_content, landscape)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-smart-shrinking',  # CRITICAL
                ]
            )
            
            page = await browser.new_page()
            
            # Set viewport
            if landscape:
                await page.set_viewport_size({'width': 1123, 'height': 794})  # A4 landscape at 96 DPI
            else:
                await page.set_viewport_size({'width': 794, 'height': 1123})  # A4 portrait at 96 DPI
            
            # Set content
            await page.set_content(html_with_css, wait_until='networkidle')
            await page.wait_for_timeout(500)
            
            # Generate PDF with exact 10mm margins
            pdf_bytes = await page.pdf(
                format='A4',
                landscape=landscape,
                print_background=True,
                margin={
                    'top': f'{self.margin_mm}mm',
                    'right': f'{self.margin_mm}mm',
                    'bottom': f'{self.margin_mm}mm',
                    'left': f'{self.margin_mm}mm'
                },
                prefer_css_page_size=False,  # Use our margin settings
                display_header_footer=False,
                scale=1.0  # No scaling
            )
            
            await browser.close()
            return pdf_bytes
    
    def convert_with_playwright(self, html_content: str, landscape: bool = False) -> bytes:
        """
        Convert HTML to PDF using Playwright (sync wrapper)
        
        Args:
            html_content: HTML content
            landscape: Use landscape orientation
            
        Returns:
            PDF bytes
        """
        return asyncio.run(self.convert_with_playwright_async(html_content, landscape))
    
    def convert_with_chrome(self, html_content: str, landscape: bool = False) -> bytes:
        """
        Convert HTML to PDF using Chrome/Chromium headless
        
        Args:
            html_content: HTML content
            landscape: Use landscape orientation
            
        Returns:
            PDF bytes
        """
        # Add fixed CSS
        html_with_css = self.add_fixed_css(html_content, landscape)
        
        # Create temp files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_with_css)
            html_path = f.name
        
        pdf_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        pdf_path = pdf_file.name
        pdf_file.close()
        
        try:
            # Find Chrome
            chrome_paths = [
                'google-chrome',
                'chrome',
                'chromium',
                'chromium-browser',
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            ]
            
            chrome_cmd = None
            for path in chrome_paths:
                try:
                    result = subprocess.run([path, '--version'], capture_output=True, timeout=5)
                    if result.returncode == 0:
                        chrome_cmd = path
                        break
                except:
                    continue
            
            if not chrome_cmd:
                raise Exception("Chrome/Chromium not found")
            
            # Build command
            cmd = [
                chrome_cmd,
                '--headless',
                '--disable-gpu',
                '--disable-smart-shrinking',  # CRITICAL
                '--no-margins',
                '--run-all-compositor-stages-before-draw',
                f'--print-to-pdf={pdf_path}',
                html_path
            ]
            
            # Execute
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"Chrome failed: {result.stderr}")
            
            # Read PDF
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            
            return pdf_bytes
        
        finally:
            try:
                os.unlink(html_path)
                os.unlink(pdf_path)
            except:
                pass
    
    def auto_convert(self, html_content: str, landscape: bool = False, 
                     doc_name: str = "") -> bytes:
        """
        Auto-select best PDF engine and convert
        
        Priority:
        1. WeasyPrint (best HTML/CSS support)
        2. Playwright (good quality)
        3. Chrome headless (good quality)
        4. ReportLab (always works, basic HTML)
        
        Args:
            html_content: HTML content
            landscape: Use landscape orientation
            doc_name: Document name (for auto-detecting landscape)
            
        Returns:
            PDF bytes
        """
        # Auto-detect landscape for Deviation Statement
        if not landscape and 'deviation' in doc_name.lower():
            landscape = True
            print(f"[INFO] Auto-detected landscape orientation for: {doc_name}")
        
        # Try WeasyPrint first (best HTML/CSS support)
        try:
            print(f"[INFO] Converting with WeasyPrint (landscape={landscape})...")
            return self.convert_with_weasyprint(html_content, landscape)
        except Exception as e:
            print(f"[WARNING] WeasyPrint failed: {e}")
        
        # Try Playwright
        try:
            print(f"[INFO] Converting with Playwright (landscape={landscape})...")
            return self.convert_with_playwright(html_content, landscape)
        except Exception as e:
            print(f"[WARNING] Playwright failed: {e}")
        
        # Try Chrome headless
        try:
            print(f"[INFO] Converting with Chrome (landscape={landscape})...")
            return self.convert_with_chrome(html_content, landscape)
        except Exception as e:
            print(f"[WARNING] Chrome failed: {e}")
        
        # Fallback to ReportLab (always works)
        try:
            print(f"[INFO] Converting with ReportLab (landscape={landscape})...")
            return self.convert_with_reportlab(html_content, landscape)
        except Exception as e:
            print(f"[ERROR] ReportLab failed: {e}")
            raise Exception("All PDF engines failed")
    
    def batch_convert(self, html_documents: Dict[str, str]) -> Dict[str, bytes]:
        """
        Convert multiple HTML documents to PDF
        
        Args:
            html_documents: Dict of {doc_name: html_content}
            
        Returns:
            Dict of {doc_name: pdf_bytes}
        """
        pdf_documents = {}
        
        for doc_name, html_content in html_documents.items():
            try:
                print(f"\n[INFO] Converting: {doc_name}")
                pdf_bytes = self.auto_convert(html_content, doc_name=doc_name)
                pdf_documents[doc_name] = pdf_bytes
                print(f"[OK] {doc_name}: {len(pdf_bytes):,} bytes")
            except Exception as e:
                print(f"[ERROR] Failed to convert {doc_name}: {e}")
        
        return pdf_documents


# Quick test
if __name__ == "__main__":
    generator = FixedPDFGenerator(margin_mm=10)
    
    html = """
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Test Document with 10mm Margins</h1>
        <p>This document should have exactly 10mm margins on all sides.</p>
        <table>
            <tr>
                <th>Column 1</th>
                <th>Column 2</th>
                <th>Column 3</th>
            </tr>
            <tr>
                <td>Data 1</td>
                <td>Data 2</td>
                <td>Data 3</td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Test portrait
    pdf_portrait = generator.auto_convert(html, landscape=False)
    print(f"\nPortrait PDF: {len(pdf_portrait):,} bytes")
    
    # Test landscape
    pdf_landscape = generator.auto_convert(html, landscape=True)
    print(f"Landscape PDF: {len(pdf_landscape):,} bytes")
