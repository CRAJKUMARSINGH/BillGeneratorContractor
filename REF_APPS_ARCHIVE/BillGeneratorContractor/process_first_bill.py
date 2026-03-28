#!/usr/bin/env python3
"""
Quick script to process the first bill from INPUT_FILES_LEVEL_02
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.processors.excel_processor_enterprise import ExcelProcessor
from core.generators.document_generator import DocumentGenerator

def process_first_bill(input_file: str, output_dir: str = "OUTPUT"):
    """Process the first bill Excel file."""
    
    print(f"\n{'='*80}")
    print(f"Processing First Bill: {input_file}")
    print(f"{'='*80}\n")
    
    input_path = Path(input_file)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Process Excel
        print("Step 1: Processing Excel file...")
        processor = ExcelProcessor(sanitize_strings=True, validate_schemas=True)
        result = processor.process_file(input_path)
        
        if not result.success:
            print("❌ Excel processing failed:")
            for error in result.errors:
                print(f"   {error}")
            return False
        
        print(f"✅ Excel processed: {result.metadata['sheets_processed']} sheets")
        print(f"   Sheets found: {list(result.data.keys())}")
        
        # Step 2: Generate HTML documents
        print("\nStep 2: Generating HTML documents...")
        doc_gen = DocumentGenerator(result.data)
        html_documents = doc_gen.generate_all_documents()
        
        print(f"✅ Generated {len(html_documents)} HTML documents:")
        for doc_name in html_documents.keys():
            print(f"   - {doc_name}")
        
        # Step 3: Save HTML files
        print("\nStep 3: Saving HTML files...")
        for doc_name, html_content in html_documents.items():
            # Create safe filename
            safe_name = doc_name.replace(' ', '_').replace('/', '_')
            html_file = output_path / f"{input_path.stem}_{safe_name}.html"
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ Saved: {html_file}")
        
        # Step 4: Try to generate PDFs (optional, may fail on Windows)
        print("\nStep 4: Attempting PDF generation...")
        try:
            from core.rendering.pdf_renderer_enterprise import PDFRendererFactory, PDFConfig, PageSize, PageOrientation
            
            # Configure PDF
            pdf_config = PDFConfig(
                page_size=PageSize.A4,
                orientation=PageOrientation.PORTRAIT,
                margin_top="10mm",
                margin_right="10mm",
                margin_bottom="10mm",
                margin_left="10mm"
            )
            
            # Get available PDF renderer
            available_engines = PDFRendererFactory.get_available_engines()
            if not available_engines:
                print("⚠️  No PDF engines available, skipping PDF generation")
            else:
                pdf_renderer = PDFRendererFactory.create_renderer(
                    engine=available_engines[0],
                    config=pdf_config
                )
                
                for doc_name, html_content in html_documents.items():
                    safe_name = doc_name.replace(' ', '_').replace('/', '_')
                    pdf_file = output_path / f"{input_path.stem}_{safe_name}.pdf"
                    
                    pdf_result = pdf_renderer.render_from_html_string(
                        html_content=html_content,
                        output_path=pdf_file
                    )
                    
                    if pdf_result.success:
                        print(f"✅ PDF saved: {pdf_file}")
                    else:
                        print(f"❌ PDF generation failed for {doc_name}")
                        for error in pdf_result.errors:
                            print(f"   {error}")
        except Exception as pdf_error:
            print(f"⚠️  PDF generation skipped due to: {pdf_error}")
            print("   HTML files have been generated successfully.")
        
        print(f"\n{'='*80}")
        print("✅ Processing complete!")
        print(f"   Output directory: {output_path.absolute()}")
        print(f"{'='*80}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Process the first bill file
    input_file = "INPUT_FILES_LEVEL_02/FirstFINALnoExtra.xlsx"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    
    success = process_first_bill(input_file)
    sys.exit(0 if success else 1)
