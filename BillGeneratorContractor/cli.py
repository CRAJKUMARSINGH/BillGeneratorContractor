#!/usr/bin/env python3
"""
Enterprise Bill Generation System - CLI Interface
Command-line interface for automation and CI/CD integration.

Usage:
    # Single file processing
    python cli.py process --input file.xlsx --output OUTPUT/

    # Batch processing
    python cli.py batch --input-dir INPUT/ --output-dir OUTPUT/ --workers 4

    # Validation only
    python cli.py validate --input file.xlsx --rules validation_rules.json

Author: Senior CLI Engineer
Standards: Click framework, Type hints, Comprehensive help
"""

import sys
from pathlib import Path
from typing import Optional, List
import json
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import click
except ImportError:
    print("ERROR: Click library not installed. Install with: pip install click")
    sys.exit(1)

from core.processors.excel_processor_enterprise import ExcelProcessor
from core.generators.html_renderer_enterprise import HTMLRenderer, DocumentType
from core.rendering.pdf_renderer_enterprise import (
    PDFRendererFactory, PDFConfig, PageSize, PageOrientation, PDFEngine
)
from core.batch.job_runner_enterprise import BatchJobRunner, BatchConfig, RetryPolicy
from core.validation.error_diagnostics_enterprise import ComprehensiveValidator
from core.logging.structured_logger import get_structured_logger, LogLevel


# Initialize logger
logger = get_structured_logger(
    name="cli",
    level=LogLevel.INFO,
    output_file=Path("logs/cli.log")
)


@click.group()
@click.version_option(version="1.0.0", prog_name="Enterprise Bill Generator")
def cli():
    """
    Enterprise Bill Generation System - CLI Interface
    
    Process Excel files and generate professional documents (HTML, PDF, Word).
    """
    logger.info("cli_started", message="CLI interface initialized")


@cli.command()
@click.option(
    '--input', '-i',
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help='Input Excel file path'
)
@click.option(
    '--output', '-o',
    default='OUTPUT',
    type=click.Path(path_type=Path),
    help='Output directory (default: OUTPUT)'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['html', 'pdf', 'both'], case_sensitive=False),
    default='both',
    help='Output format (default: both)'
)
@click.option(
    '--pdf-engine',
    type=click.Choice(['weasyprint', 'wkhtmltopdf'], case_sensitive=False),
    default='weasyprint',
    help='PDF rendering engine (default: weasyprint)'
)
@click.option(
    '--validate/--no-validate',
    default=True,
    help='Run validation before processing (default: yes)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Verbose output'
)
def process(
    input: Path,
    output: Path,
    format: str,
    pdf_engine: str,
    validate: bool,
    verbose: bool
):
    """
    Process a single Excel file and generate documents.
    
    Example:
        python cli.py process -i input.xlsx -o OUTPUT/ -f both
    """
    start_time = time.time()
    
    click.echo(f"\n{'='*80}")
    click.echo(f"ENTERPRISE BILL GENERATOR - Single File Processing")
    click.echo(f"{'='*80}\n")
    
    click.echo(f"📁 Input file: {input}")
    click.echo(f"📂 Output directory: {output}")
    click.echo(f"📄 Format: {format}")
    click.echo(f"🔧 PDF engine: {pdf_engine}")
    click.echo(f"✅ Validation: {'enabled' if validate else 'disabled'}")
    click.echo()
    
    try:
        # Step 1: Process Excel
        click.echo("Step 1: Processing Excel file...")
        processor = ExcelProcessor(
            sanitize_strings=True,
            validate_schemas=validate
        )
        
        result = processor.process_file(input)
        
        if not result.success:
            click.echo(click.style("❌ Excel processing failed:", fg='red'))
            for error in result.errors:
                click.echo(f"   {error}")
            logger.error("excel_processing_failed", file=str(input), errors=result.errors)
            sys.exit(1)
        
        click.echo(click.style(f"✅ Excel processed: {result.metadata['sheets_processed']} sheets", fg='green'))
        
        # Step 2: Validation (if enabled)
        if validate:
            click.echo("\nStep 2: Running validation...")
            validator = ComprehensiveValidator()
            
            # Validate each sheet
            validation_errors = []
            for sheet_name, df in result.data.items():
                validation_rules = {
                    'required_columns': list(df.columns),
                    'non_null_columns': list(df.columns)
                }
                
                val_result = validator.validate_dataframe(df, validation_rules, sheet_name)
                
                if not val_result.is_valid:
                    validation_errors.extend(val_result.errors)
            
            if validation_errors:
                click.echo(click.style(f"⚠️  Found {len(validation_errors)} validation issues", fg='yellow'))
                if verbose:
                    for error in validation_errors[:5]:  # Show first 5
                        click.echo(f"   {error}")
            else:
                click.echo(click.style("✅ Validation passed", fg='green'))
        
        # Step 3: Generate HTML
        if format in ['html', 'both']:
            click.echo("\nStep 3: Generating HTML...")
            
            # Use DocumentGenerator to prepare proper template data
            from core.generators.document_generator import DocumentGenerator
            
            doc_gen = DocumentGenerator(result.data)
            html_documents = doc_gen.generate_all_documents()
            
            # Get First Page HTML
            html_content = html_documents.get('First Page Summary', '')
            
            if not html_content:
                click.echo(click.style("❌ HTML generation failed: No content generated", fg='red'))
                sys.exit(1)
            
            # Create a result-like object for compatibility
            class HTMLResult:
                def __init__(self, content):
                    self.success = True
                    self.html_content = content
                    self.errors = []
            
            html_result = HTMLResult(html_content)
            
            if html_result.success:
                # Save HTML
                output.mkdir(parents=True, exist_ok=True)
                html_file = output / f"{input.stem}_first_page.html"
                
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_result.html_content)
                
                click.echo(click.style(f"✅ HTML saved: {html_file}", fg='green'))
            else:
                click.echo(click.style("❌ HTML generation failed", fg='red'))
                for error in html_result.errors:
                    click.echo(f"   {error}")
        
        # Step 4: Generate PDF
        if format in ['pdf', 'both'] and html_result.success:
            click.echo("\nStep 4: Generating PDF...")
            
            # Configure PDF
            pdf_config = PDFConfig(
                page_size=PageSize.A4,
                orientation=PageOrientation.PORTRAIT,
                margin_top="10mm",
                margin_right="10mm",
                margin_bottom="10mm",
                margin_left="10mm"
            )
            
            # Get PDF engine
            engine = PDFEngine.WEASYPRINT if pdf_engine == 'weasyprint' else PDFEngine.WKHTMLTOPDF
            
            # Check if engine is available
            available_engines = PDFRendererFactory.get_available_engines()
            if engine not in available_engines:
                click.echo(click.style(f"⚠️  {pdf_engine} not available, using {available_engines[0].value}", fg='yellow'))
                engine = available_engines[0]
            
            # Create renderer
            pdf_renderer = PDFRendererFactory.create_renderer(engine=engine, config=pdf_config)
            
            # Generate PDF
            pdf_file = output / f"{input.stem}_first_page.pdf"
            pdf_result = pdf_renderer.render_from_html_string(
                html_content=html_result.html_content,
                output_path=pdf_file
            )
            
            if pdf_result.success:
                click.echo(click.style(f"✅ PDF saved: {pdf_file}", fg='green'))
            else:
                click.echo(click.style("❌ PDF generation failed", fg='red'))
                for error in pdf_result.errors:
                    click.echo(f"   {error}")
        
        # Summary
        duration = time.time() - start_time
        click.echo(f"\n{'='*80}")
        click.echo(click.style(f"✅ Processing complete in {duration:.2f}s", fg='green', bold=True))
        click.echo(f"{'='*80}\n")
        
        logger.log_performance(
            operation="single_file_processing",
            duration_ms=duration * 1000,
            success=True,
            input_file=str(input),
            output_dir=str(output)
        )
        
    except Exception as e:
        click.echo(click.style(f"\n❌ Error: {e}", fg='red', bold=True))
        if verbose:
            import traceback
            traceback.print_exc()
        
        logger.error("processing_error", message=str(e), input_file=str(input))
        sys.exit(1)


@cli.command()
@click.option(
    '--input-dir', '-i',
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help='Input directory containing Excel files'
)
@click.option(
    '--output-dir', '-o',
    default='OUTPUT/batch',
    type=click.Path(path_type=Path),
    help='Output directory (default: OUTPUT/batch)'
)
@click.option(
    '--workers', '-w',
    default=4,
    type=int,
    help='Number of parallel workers (default: 4)'
)
@click.option(
    '--pattern',
    default='*.xlsx',
    help='File pattern to match (default: *.xlsx)'
)
@click.option(
    '--retry',
    default=3,
    type=int,
    help='Number of retries for failed records (default: 3)'
)
def batch(
    input_dir: Path,
    output_dir: Path,
    workers: int,
    pattern: str,
    retry: int
):
    """
    Process multiple Excel files in batch mode.
    
    Example:
        python cli.py batch -i INPUT/ -o OUTPUT/batch/ -w 4
    """
    start_time = time.time()
    
    click.echo(f"\n{'='*80}")
    click.echo(f"ENTERPRISE BILL GENERATOR - Batch Processing")
    click.echo(f"{'='*80}\n")
    
    # Find all Excel files
    excel_files = list(input_dir.glob(pattern))
    
    if not excel_files:
        click.echo(click.style(f"❌ No files found matching pattern: {pattern}", fg='red'))
        sys.exit(1)
    
    click.echo(f"📁 Input directory: {input_dir}")
    click.echo(f"📂 Output directory: {output_dir}")
    click.echo(f"👷 Workers: {workers}")
    click.echo(f"📄 Files found: {len(excel_files)}")
    click.echo(f"🔄 Retry attempts: {retry}")
    click.echo()
    
    # Create batch records
    records = [
        {'id': f.stem, 'file_path': f}
        for f in excel_files
    ]
    
    # Configure batch processing
    batch_config = BatchConfig(
        max_workers=workers,
        timeout_per_record=300,
        continue_on_error=True,
        retry_policy=RetryPolicy(
            max_retries=retry,
            retry_delay=1.0,
            exponential_backoff=True
        ),
        output_dir=output_dir
    )
    
    # Define processing function
    def process_file(record: dict) -> dict:
        """Process single file."""
        file_path = record['file_path']
        
        # Process Excel
        processor = ExcelProcessor()
        result = processor.process_file(file_path)
        
        if not result.success:
            raise ValueError(f"Excel processing failed: {result.errors}")
        
        return {
            'id': record['id'],
            'sheets_processed': result.metadata['sheets_processed'],
            'status': 'success'
        }
    
    # Run batch job
    try:
        click.echo("Starting batch processing...")
        click.echo()
        
        runner = BatchJobRunner(config=batch_config, job_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        job_result = runner.run_batch(
            records=records,
            process_func=process_file,
            record_id_key='id'
        )
        
        # Display results
        click.echo(f"\n{'='*80}")
        click.echo(click.style("BATCH PROCESSING COMPLETE", fg='green', bold=True))
        click.echo(f"{'='*80}\n")
        
        click.echo(f"Job ID: {job_result.job_id}")
        click.echo(f"Status: {job_result.status.value}")
        click.echo(f"Total records: {job_result.total_records}")
        click.echo(click.style(f"✅ Successful: {job_result.successful_records} ({job_result.get_success_rate():.1f}%)", fg='green'))
        click.echo(click.style(f"❌ Failed: {job_result.failed_records} ({job_result.get_failure_rate():.1f}%)", fg='red'))
        click.echo(f"⏱️  Duration: {job_result.total_duration:.2f}s")
        click.echo()
        
        if job_result.errors_summary:
            click.echo("Error Summary:")
            for error_type, count in job_result.errors_summary.items():
                click.echo(f"  • {error_type}: {count} occurrence(s)")
            click.echo()
        
        click.echo(f"📊 Reports saved to: {output_dir}/logs/")
        click.echo()
        
        logger.log_performance(
            operation="batch_processing",
            duration_ms=job_result.total_duration * 1000,
            success=job_result.status.value == 'success',
            total_records=job_result.total_records,
            successful_records=job_result.successful_records,
            failed_records=job_result.failed_records
        )
        
    except Exception as e:
        click.echo(click.style(f"\n❌ Batch processing error: {e}", fg='red', bold=True))
        logger.error("batch_processing_error", message=str(e))
        sys.exit(1)


@cli.command()
@click.option(
    '--input', '-i',
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help='Input Excel file path'
)
@click.option(
    '--rules',
    type=click.Path(exists=True, path_type=Path),
    help='Validation rules JSON file (optional)'
)
@click.option(
    '--output',
    type=click.Path(path_type=Path),
    help='Output JSON file for validation results (optional)'
)
def validate(input: Path, rules: Optional[Path], output: Optional[Path]):
    """
    Validate Excel file without generating documents.
    
    Example:
        python cli.py validate -i input.xlsx --rules rules.json
    """
    click.echo(f"\n{'='*80}")
    click.echo(f"ENTERPRISE BILL GENERATOR - Validation Only")
    click.echo(f"{'='*80}\n")
    
    click.echo(f"📁 Input file: {input}")
    if rules:
        click.echo(f"📋 Rules file: {rules}")
    click.echo()
    
    try:
        # Process Excel
        click.echo("Processing Excel file...")
        processor = ExcelProcessor()
        result = processor.process_file(input)
        
        if not result.success:
            click.echo(click.style("❌ Excel processing failed", fg='red'))
            for error in result.errors:
                click.echo(f"   {error}")
            sys.exit(1)
        
        click.echo(click.style(f"✅ Excel processed: {result.metadata['sheets_processed']} sheets", fg='green'))
        click.echo()
        
        # Run validation
        click.echo("Running validation...")
        validator = ComprehensiveValidator()
        
        all_errors = []
        all_warnings = []
        
        for sheet_name, df in result.data.items():
            click.echo(f"\nValidating sheet: {sheet_name}")
            
            # Default validation rules
            validation_rules = {
                'required_columns': list(df.columns),
                'non_null_columns': list(df.columns)
            }
            
            # Load custom rules if provided
            if rules:
                with open(rules, 'r') as f:
                    custom_rules = json.load(f)
                    validation_rules.update(custom_rules.get(sheet_name, {}))
            
            val_result = validator.validate_dataframe(df, validation_rules, sheet_name)
            
            if val_result.is_valid:
                click.echo(click.style(f"  ✅ No errors found", fg='green'))
            else:
                click.echo(click.style(f"  ❌ Found {len(val_result.errors)} errors", fg='red'))
                all_errors.extend(val_result.errors)
            
            if val_result.warnings:
                click.echo(click.style(f"  ⚠️  Found {len(val_result.warnings)} warnings", fg='yellow'))
                all_warnings.extend(val_result.warnings)
        
        # Display summary
        click.echo(f"\n{'='*80}")
        click.echo("VALIDATION SUMMARY")
        click.echo(f"{'='*80}\n")
        
        if all_errors:
            click.echo(click.style(f"❌ Total Errors: {len(all_errors)}", fg='red', bold=True))
            click.echo("\nFirst 10 errors:")
            for error in all_errors[:10]:
                click.echo(f"  {error}")
        else:
            click.echo(click.style("✅ No errors found!", fg='green', bold=True))
        
        if all_warnings:
            click.echo(click.style(f"\n⚠️  Total Warnings: {len(all_warnings)}", fg='yellow'))
            click.echo("\nFirst 5 warnings:")
            for warning in all_warnings[:5]:
                click.echo(f"  {warning}")
        
        # Save results if output specified
        if output:
            validation_results = {
                'file': str(input),
                'timestamp': datetime.now().isoformat(),
                'errors': [str(e) for e in all_errors],
                'warnings': [str(w) for w in all_warnings],
                'is_valid': len(all_errors) == 0
            }
            
            output.parent.mkdir(parents=True, exist_ok=True)
            with open(output, 'w') as f:
                json.dump(validation_results, f, indent=2)
            
            click.echo(f"\n💾 Results saved to: {output}")
        
        click.echo()
        
        # Exit with error code if validation failed
        if all_errors:
            sys.exit(1)
        
    except Exception as e:
        click.echo(click.style(f"\n❌ Validation error: {e}", fg='red', bold=True))
        logger.error("validation_error", message=str(e), input_file=str(input))
        sys.exit(1)


def _prepare_template_data(data: dict) -> dict:
    """
    Prepare template data from processed Excel data.
    Note: This is now handled by DocumentGenerator in the process command.
    """
    # This function is kept for backward compatibility
    # but is no longer used in the main flow
    return {
        'title_data': {},
        'items': [],
        'totals': {},
        'deviation_items': [],
        'summary': {}
    }


if __name__ == '__main__':
    cli()
