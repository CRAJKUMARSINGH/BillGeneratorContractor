#!/usr/bin/env python3
"""
Generate PDF from HTML using alternative methods for Windows
"""
import sys
from pathlib import Path

def generate_pdf_with_reportlab(html_file: Path, output_pdf: Path):
    """Try to generate PDF using reportlab with xhtml2pdf"""
    try:
        from xhtml2pdf import pisa
        
        print(f"Using xhtml2pdf to generate PDF...")
        
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        with open(output_pdf, 'wb') as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        
        if pisa_status.err:
            print(f"❌ PDF generation had errors")
            return False
        else:
            print(f"✅ PDF generated: {output_pdf}")
            return True
            
    except ImportError:
        print("⚠️  xhtml2pdf not installed. Install with: pip install xhtml2pdf")
        return False
    except Exception as e:
        print(f"❌ Error with xhtml2pdf: {e}")
        return False


def generate_pdf_with_pdfkit(html_file: Path, output_pdf: Path):
    """Try to generate PDF using pdfkit (wkhtmltopdf wrapper)"""
    try:
        import pdfkit
        
        print(f"Using pdfkit/wkhtmltopdf to generate PDF...")
        
        options = {
            'page-size': 'A4',
            'margin-top': '10mm',
            'margin-right': '10mm',
            'margin-bottom': '10mm',
            'margin-left': '10mm',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None
        }
        
        pdfkit.from_file(str(html_file), str(output_pdf), options=options)
        print(f"✅ PDF generated: {output_pdf}")
        return True
        
    except ImportError:
        print("⚠️  pdfkit not installed. Install with: pip install pdfkit")
        print("    Also requires wkhtmltopdf: https://wkhtmltopdf.org/downloads.html")
        return False
    except Exception as e:
        print(f"❌ Error with pdfkit: {e}")
        return False


def generate_pdf_with_playwright(html_file: Path, output_pdf: Path):
    """Try to generate PDF using Playwright (Chromium)"""
    try:
        from playwright.sync_api import sync_playwright
        
        print(f"Using Playwright (Chromium) to generate PDF...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f'file:///{html_file.absolute()}')
            page.pdf(
                path=str(output_pdf),
                format='A4',
                margin={
                    'top': '10mm',
                    'right': '10mm',
                    'bottom': '10mm',
                    'left': '10mm'
                },
                print_background=True
            )
            browser.close()
        
        print(f"✅ PDF generated: {output_pdf}")
        return True
        
    except ImportError:
        print("⚠️  Playwright not installed. Install with: pip install playwright")
        print("    Then run: playwright install chromium")
        return False
    except Exception as e:
        print(f"❌ Error with Playwright: {e}")
        return False


def generate_pdf_with_selenium(html_file: Path, output_pdf: Path):
    """Try to generate PDF using Selenium with Chrome"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import json
        import base64
        
        print(f"Using Selenium (Chrome) to generate PDF...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f'file:///{html_file.absolute()}')
        
        # Use Chrome's print to PDF
        pdf_data = driver.execute_cdp_cmd('Page.printToPDF', {
            'printBackground': True,
            'paperWidth': 8.27,  # A4 width in inches
            'paperHeight': 11.69,  # A4 height in inches
            'marginTop': 0.39,  # 10mm
            'marginBottom': 0.39,
            'marginLeft': 0.39,
            'marginRight': 0.39
        })
        
        with open(output_pdf, 'wb') as f:
            f.write(base64.b64decode(pdf_data['data']))
        
        driver.quit()
        
        print(f"✅ PDF generated: {output_pdf}")
        return True
        
    except ImportError:
        print("⚠️  Selenium not installed. Install with: pip install selenium")
        return False
    except Exception as e:
        print(f"❌ Error with Selenium: {e}")
        return False


def main():
    html_file = Path("OUTPUT/FirstFINALnoExtra_First_Page_Summary.html")
    output_pdf = Path("OUTPUT/FirstFINALnoExtra_First_Page_Summary.pdf")
    
    if len(sys.argv) > 1:
        html_file = Path(sys.argv[1])
        output_pdf = html_file.with_suffix('.pdf')
    
    if not html_file.exists():
        print(f"❌ HTML file not found: {html_file}")
        sys.exit(1)
    
    print(f"\n{'='*80}")
    print(f"Converting HTML to PDF")
    print(f"{'='*80}\n")
    print(f"Input:  {html_file}")
    print(f"Output: {output_pdf}\n")
    
    # Try different methods in order of preference
    methods = [
        ("xhtml2pdf", generate_pdf_with_reportlab),
        ("pdfkit", generate_pdf_with_pdfkit),
        ("Playwright", generate_pdf_with_playwright),
        ("Selenium", generate_pdf_with_selenium)
    ]
    
    for method_name, method_func in methods:
        print(f"\nTrying method: {method_name}")
        print("-" * 40)
        if method_func(html_file, output_pdf):
            print(f"\n{'='*80}")
            print(f"✅ SUCCESS! PDF generated using {method_name}")
            print(f"{'='*80}\n")
            return True
        print()
    
    print(f"\n{'='*80}")
    print("❌ All PDF generation methods failed")
    print(f"{'='*80}\n")
    print("Alternative options:")
    print("1. Open the HTML file in Chrome/Edge and use Print > Save as PDF")
    print("2. Install GTK libraries for WeasyPrint: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows")
    print("3. Install wkhtmltopdf: https://wkhtmltopdf.org/downloads.html")
    print(f"\nHTML file location: {html_file.absolute()}")
    
    return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
