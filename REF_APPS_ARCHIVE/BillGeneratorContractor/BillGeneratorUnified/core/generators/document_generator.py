"""
Document Generator - Main entry point for document generation
"""
from typing import Dict, Any
from core.generators.html_generator import HTMLGenerator
from core.generators.pdf_generator_fixed import FixedPDFGenerator
from core.generators.doc_generator import DOCGenerator

class DocumentGenerator:
    """Main document generator that coordinates specialized generators"""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.html_generator = HTMLGenerator(data)
        self.pdf_generator = FixedPDFGenerator(margin_mm=10)
        self.doc_generator = DOCGenerator(data)
    
    def generate_all_documents(self) -> Dict[str, str]:
        """
        Generate all required documents using HTML generator
        
        Returns:
            Dictionary containing all generated documents in HTML format
        """
        return self.html_generator.generate_all_documents()
    
    def generate_doc_documents(self) -> Dict[str, bytes]:
        """
        Generate all required documents in DOC format
        
        Returns:
            Dictionary containing all generated documents in DOC format (bytes)
        """
        return self.doc_generator.generate_doc_documents()
    
    def create_pdf_documents(self, documents: Dict[str, str]) -> Dict[str, bytes]:
        """
        Convert HTML documents to PDF format
        
        Args:
            documents: Dictionary of HTML documents
            
        Returns:
            Dictionary of PDF documents as bytes
        """
        return self.pdf_generator.create_pdf_documents(documents)
    
    def batch_convert(self, html_documents: Dict[str, str], 
                     output_dir: str = "output_pdfs",
                     enable_fallback: bool = True) -> Dict[str, str]:
        """
        Batch convert HTML documents to PDFs
        
        Args:
            html_documents: Dictionary mapping document names to HTML content
            output_dir: Directory to save PDFs
            enable_fallback: Enable fallback to xhtml2pdf if Playwright fails
            
        Returns:
            Dictionary mapping document names to PDF file paths
        """
        return self.pdf_generator.batch_convert(html_documents, output_dir, enable_fallback)
