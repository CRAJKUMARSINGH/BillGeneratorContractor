"""
Batch ZIP Integration for BillGeneratorUnified
Utility to integrate batch processing results with enhanced ZIP download capabilities
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from core.utils.optimized_zip_processor import OptimizedZipProcessor, OptimizedZipConfig
from core.utils.download_manager import EnhancedDownloadManager, FileType, DownloadCategory
from core.ui.enhanced_download_center import integrate_with_batch_processor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BatchZipIntegration:
    """Integrates batch processing results with enhanced ZIP download capabilities"""
    
    def __init__(self, download_manager: EnhancedDownloadManager):
        self.download_manager = download_manager
        self.logger = logging.getLogger(__name__)
        
    def process_batch_results(self, batch_results: List[Dict[str, Any]], 
                            output_base_dir: str = "output",
                            create_zip_archives: bool = True,
                            add_to_download_manager: bool = True) -> Dict[str, Any]:
        """
        Process batch results and integrate with download manager
        
        Args:
            batch_results: List of results from batch processor
            output_base_dir: Base directory for output files
            create_zip_archives: Whether to create ZIP archives for each result
            add_to_download_manager: Whether to add files to download manager
            
        Returns:
            Dictionary with processing statistics and created ZIP files
        """
        stats = {
            'total_results': len(batch_results),
            'successful_results': 0,
            'failed_results': 0,
            'total_files_added': 0,
            'zip_archives_created': 0,
            'errors': []
        }
        
        # Process each result
        for idx, result in enumerate(batch_results):
            try:
                if result.get('status') == 'success':
                    self._process_successful_result(
                        result, output_base_dir, create_zip_archives, add_to_download_manager
                    )
                    stats['successful_results'] += 1
                else:
                    stats['failed_results'] += 1
                    stats['errors'].append({
                        'filename': result.get('filename', 'unknown'),
                        'error': result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                stats['failed_results'] += 1
                stats['errors'].append({
                    'filename': result.get('filename', 'unknown'),
                    'error': str(e)
                })
                self.logger.error(f"Error processing result {idx}: {e}")
                
        return stats
        
    def _process_successful_result(self, result: Dict[str, Any], output_base_dir: str,
                                 create_zip_archives: bool, add_to_download_manager: bool):
        """Process a successful batch result"""
        filename = result.get('filename', 'unknown')
        output_folder = result.get('output_folder', '')
        
        # Add files to download manager if requested
        if add_to_download_manager:
            self._add_files_to_download_manager(result, filename)
            
        # Create ZIP archive if requested
        if create_zip_archives:
            self._create_result_zip_archive(result, output_folder, filename)
            
    def _add_files_to_download_manager(self, result: Dict[str, Any], filename: str):
        """Add files from result to download manager"""
        try:
            # Add HTML files
            html_files = result.get('html_files', [])
            for html_file in html_files:
                html_path = Path(result.get('output_folder', '')) / 'html' / f"{html_file}.html"
                if html_path.exists():
                    try:
                        content = html_path.read_text(encoding='utf-8')
                        self.download_manager.add_html_document(
                            f"{filename}_{html_file}.html",
                            content,
                            f"HTML document for {filename}"
                        )
                    except Exception as e:
                        self.logger.warning(f"Could not read HTML file {html_path}: {e}")
                        
            # Add PDF files
            pdf_files = result.get('pdf_files', [])
            for pdf_file in pdf_files:
                pdf_path = Path(result.get('output_folder', '')) / 'pdf' / pdf_file
                if pdf_path.exists():
                    try:
                        content = pdf_path.read_bytes()
                        self.download_manager.add_pdf_document(
                            f"{filename}_{pdf_file}",
                            content,
                            f"PDF document for {filename}"
                        )
                    except Exception as e:
                        self.logger.warning(f"Could not read PDF file {pdf_path}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error adding files to download manager for {filename}: {e}")
            
    def _create_result_zip_archive(self, result: Dict[str, Any], output_folder: str, filename: str):
        """Create a ZIP archive for a single result"""
        try:
            # Configure ZIP processor
            config = OptimizedZipConfig(
                compression_level=6,
                streaming_threshold_mb=5,
                memory_limit_mb=256,
                enable_caching=True
            )
            
            # Create ZIP processor
            with OptimizedZipProcessor(config) as processor:
                # Add HTML files
                html_dir = Path(output_folder) / 'html'
                if html_dir.exists():
                    for html_file in html_dir.glob("*.html"):
                        processor.add_file_from_path(html_file, f"html/{html_file.name}")
                        
                # Add PDF files
                pdf_dir = Path(output_folder) / 'pdf'
                if pdf_dir.exists():
                    for pdf_file in pdf_dir.glob("*.pdf"):
                        processor.add_file_from_path(pdf_file, f"pdf/{pdf_file.name}")
                        
                # Create ZIP
                if processor.processed_files:  # Only create ZIP if there are files
                    zip_buffer, metrics = processor.create_zip()
                    
                    # Save ZIP file
                    zip_filename = f"{filename}_documents.zip"
                    zip_path = Path(output_folder) / zip_filename
                    
                    with open(zip_path, 'wb') as f:
                        f.write(zip_buffer.getvalue())
                        
                    # Add ZIP to download manager
                    self.download_manager.add_item(
                        zip_filename,
                        zip_buffer.getvalue(),
                        FileType.ZIP,
                        f"ZIP archive for {filename}",
                        DownloadCategory.GENERAL
                    )
                    
                    self.logger.info(f"Created ZIP archive: {zip_path}")
                    
        except Exception as e:
            self.logger.error(f"Error creating ZIP archive for {filename}: {e}")
            
    def create_combined_zip_archive(self, batch_results: List[Dict[str, Any]], 
                                  archive_name: str | None = None) -> str:
        """
        Create a combined ZIP archive containing all files from all batch results
        
        Args:
            batch_results: List of results from batch processor
            archive_name: Name for the combined archive
            
        Returns:
            Path to the created ZIP file
        """
        if not archive_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_name = f"combined_documents_{timestamp}.zip"
        else:
            archive_name = str(archive_name)
            
        # Configure ZIP processor
        config = OptimizedZipConfig(
            compression_level=6,
            streaming_threshold_mb=10,
            memory_limit_mb=512,
            enable_caching=True
        )
        
        # Create ZIP processor
        with OptimizedZipProcessor(config) as processor:
            # Process each result
            for result in batch_results:
                if result.get('status') == 'success':
                    output_folder = result.get('output_folder', '')
                    filename = result.get('filename', 'unknown')
                    
                    # Add HTML files
                    html_dir = Path(output_folder) / 'html'
                    if html_dir.exists():
                        for html_file in html_dir.glob("*.html"):
                            # Use filename as folder to organize files
                            clean_filename = Path(filename).stem
                            processor.add_file_from_path(
                                html_file, 
                                f"{clean_filename}/html/{html_file.name}"
                            )
                            
                    # Add PDF files
                    pdf_dir = Path(output_folder) / 'pdf'
                    if pdf_dir.exists():
                        for pdf_file in pdf_dir.glob("*.pdf"):
                            # Use filename as folder to organize files
                            clean_filename = Path(filename).stem
                            processor.add_file_from_path(
                                pdf_file, 
                                f"{clean_filename}/pdf/{pdf_file.name}"
                            )
                            
            # Create ZIP if there are files
            if processor.processed_files:
                zip_buffer, metrics = processor.create_zip()
                
                # Save ZIP file
                output_path = Path("output") / archive_name
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    f.write(zip_buffer.getvalue())
                    
                # Add to download manager
                self.download_manager.add_item(
                    archive_name,
                    zip_buffer.getvalue(),
                    FileType.ZIP,
                    "Combined ZIP archive of all batch results",
                    DownloadCategory.GENERAL
                )
                
                self.logger.info(f"Created combined ZIP archive: {output_path}")
                return str(output_path)
            else:
                self.logger.warning("No files to include in combined ZIP archive")
                return ""
                
    def cleanup_batch_output(self, batch_results: List[Dict[str, Any]], 
                           keep_zip_only: bool = True):
        """
        Clean up batch output directories
        
        Args:
            batch_results: List of results from batch processor
            keep_zip_only: Whether to keep only ZIP files and remove individual documents
        """
        for result in batch_results:
            if result.get('status') == 'success':
                output_folder = Path(result.get('output_folder', ''))
                
                if keep_zip_only and output_folder.exists():
                    # Remove individual HTML and PDF directories, keep ZIP files
                    html_dir = output_folder / 'html'
                    if html_dir.exists():
                        for file in html_dir.glob("*"):
                            file.unlink()
                        html_dir.rmdir()
                        
                    pdf_dir = output_folder / 'pdf'
                    if pdf_dir.exists():
                        for file in pdf_dir.glob("*"):
                            file.unlink()
                        pdf_dir.rmdir()
                        
                    self.logger.info(f"Cleaned up individual files in {output_folder}")


# Utility functions for easy integration
def integrate_batch_results_with_download_manager(batch_results: List[Dict[str, Any]], 
                                               download_manager: EnhancedDownloadManager,
                                               create_individual_zips: bool = True,
                                               create_combined_zip: bool = True) -> Dict[str, Any]:
    """
    Easy integration function for batch results
    
    Args:
        batch_results: List of results from batch processor
        download_manager: Download manager to integrate with
        create_individual_zips: Whether to create ZIP archives for each result
        create_combined_zip: Whether to create a combined ZIP archive
        
    Returns:
        Processing statistics
    """
    integrator = BatchZipIntegration(download_manager)
    
    # Process individual results
    stats = integrator.process_batch_results(
        batch_results,
        create_zip_archives=create_individual_zips,
        add_to_download_manager=True
    )
    
    # Create combined ZIP if requested
    if create_combined_zip and batch_results:
        try:
            combined_zip_path = integrator.create_combined_zip_archive(batch_results)
            if combined_zip_path:
                stats['combined_zip_created'] = combined_zip_path
        except Exception as e:
            stats['errors'].append({
                'operation': 'combined_zip_creation',
                'error': str(e)
            })
            logger.error(f"Error creating combined ZIP: {e}")
            
    return stats


def setup_batch_download_integration(batch_results: List[Dict[str, Any]]) -> EnhancedDownloadManager:
    """
    Set up complete download integration for batch results
    
    Args:
        batch_results: List of results from batch processor
        
    Returns:
        Configured download manager with all batch results
    """
    # Create download manager
    download_manager = EnhancedDownloadManager()
    
    # Integrate results
    stats = integrate_batch_results_with_download_manager(
        batch_results, 
        download_manager,
        create_individual_zips=True,
        create_combined_zip=True
    )
    
    logger.info(f"Batch download integration completed: {stats}")
    
    return download_manager