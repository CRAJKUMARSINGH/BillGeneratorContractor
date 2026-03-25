#!/usr/bin/env python3
"""
Enterprise-Grade HTML Renderer
Production-ready HTML generation with Jinja2 templating, security, and performance optimization.

Author: Senior Python Web Rendering Engineer
Standards: HTML5, Jinja2, Modular Architecture
Security: XSS prevention, content escaping, input validation
Performance: Template caching, batch processing, optimized rendering
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import html
import re

from jinja2 import (
    Environment,
    FileSystemLoader,
    select_autoescape,
    Template,
    TemplateNotFound,
    TemplateSyntaxError
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class DocumentType(Enum):
    """Supported document types."""
    FIRST_PAGE = "first_page"
    LAST_PAGE = "last_page"
    DEVIATION_STATEMENT = "deviation_statement"
    EXTRA_ITEMS = "extra_items"
    NOTE_SHEET = "note_sheet"
    CERTIFICATE_II = "certificate_ii"
    CERTIFICATE_III = "certificate_iii"


class OutputFormat(Enum):
    """Supported output formats."""
    HTML = "html"
    PDF_READY = "pdf_ready"  # HTML optimized for PDF conversion


# Security: Dangerous HTML tags to strip
DANGEROUS_TAGS = [
    'script', 'iframe', 'object', 'embed', 'applet',
    'meta', 'link', 'style', 'base', 'form'
]

# Performance: Template cache size
TEMPLATE_CACHE_SIZE = 50


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class HTMLRenderingError(Exception):
    """Base exception for HTML rendering errors."""
    pass


class TemplateError(HTMLRenderingError):
    """Raised when template operations fail."""
    pass


class ValidationError(HTMLRenderingError):
    """Raised when data validation fails."""
    pass


class SecurityError(HTMLRenderingError):
    """Raised when security checks fail."""
    pass


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class RenderConfig:
    """Configuration for HTML rendering."""
    template_dir: Union[str, Path] = "templates"
    output_dir: Union[str, Path] = "output"
    enable_caching: bool = True
    enable_minification: bool = False
    enable_security_checks: bool = True
    pdf_ready: bool = False
    
    def __post_init__(self):
        """Validate configuration."""
        self.template_dir = Path(self.template_dir)
        self.output_dir = Path(self.output_dir)
        
        if not self.template_dir.exists():
            raise ValueError(f"Template directory not found: {self.template_dir}")


@dataclass
class RenderResult:
    """Result of rendering operation."""
    success: bool
    html_content: Optional[str] = None
    output_path: Optional[Path] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'output_path': str(self.output_path) if self.output_path else None,
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata,
            'html_length': len(self.html_content) if self.html_content else 0
        }


# ============================================================================
# SECURITY UTILITIES
# ============================================================================

class SecurityValidator:
    """Validates and sanitizes HTML content."""
    
    @staticmethod
    def sanitize_html(content: str) -> str:
        """
        Sanitize HTML content to prevent XSS attacks.
        
        Args:
            content: HTML content to sanitize
            
        Returns:
            Sanitized HTML content
        """
        # Escape HTML entities
        content = html.escape(content, quote=True)
        return content
    
    @staticmethod
    def validate_data(data: Dict[str, Any]) -> bool:
        """
        Validate input data structure.
        Only checks for dangerous HTML tags — not % or other numeric chars
        that appear legitimately in bill data.
        """
        if not isinstance(data, dict):
            logger.error(f"Invalid data type: {type(data)}")
            return False

        # Only flag actual dangerous HTML tags, not numeric symbols
        data_str = str(data).lower()
        truly_dangerous = ['<script', '<iframe', '<object', '<embed', '<applet']
        if any(tag in data_str for tag in truly_dangerous):
            logger.warning("Potentially dangerous HTML content detected in data")
            return False

        return True
    
    @staticmethod
    def strip_dangerous_tags(html_content: str) -> str:
        """
        Strip dangerous HTML tags.
        
        Args:
            html_content: HTML content
            
        Returns:
            Cleaned HTML content
        """
        for tag in DANGEROUS_TAGS:
            # Remove opening and closing tags
            pattern = re.compile(f'<{tag}[^>]*>.*?</{tag}>', re.IGNORECASE | re.DOTALL)
            html_content = pattern.sub('', html_content)
            
            # Remove self-closing tags
            pattern = re.compile(f'<{tag}[^>]*/?>', re.IGNORECASE)
            html_content = pattern.sub('', html_content)
        
        return html_content


# ============================================================================
# TEMPLATE MANAGER
# ============================================================================

class TemplateManager:
    """Manages Jinja2 templates with caching and security."""
    
    def __init__(self, config: RenderConfig):
        """
        Initialize template manager.
        
        Args:
            config: Render configuration
        """
        self.config = config
        
        # Initialize Jinja2 environment with security features
        self.env = Environment(
            loader=FileSystemLoader(str(config.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
            cache_size=TEMPLATE_CACHE_SIZE if config.enable_caching else 0
        )
        
        # Add custom filters
        self._register_filters()
        
        logger.info(f"TemplateManager initialized: {config.template_dir}")
    
    def _register_filters(self):
        """Register custom Jinja2 filters."""
        
        def currency_filter(value: float) -> str:
            """Format value as currency."""
            try:
                return f"₹{value:,.2f}"
            except (ValueError, TypeError):
                return "₹0.00"
        
        def number_filter(value: float, decimals: int = 2) -> str:
            """Format value as number."""
            try:
                return f"{value:,.{decimals}f}"
            except (ValueError, TypeError):
                return "0.00"
        
        def percentage_filter(value: float) -> str:
            """Format value as percentage."""
            try:
                return f"{value:.2f}%"
            except (ValueError, TypeError):
                return "0.00%"
        
        def safe_html_filter(value: str) -> str:
            """Escape HTML for safety."""
            return html.escape(str(value), quote=True)
        
        # Register filters
        self.env.filters['currency'] = currency_filter
        self.env.filters['number'] = number_filter
        self.env.filters['percentage'] = percentage_filter
        self.env.filters['safe_html'] = safe_html_filter
    
    def get_template(self, template_name: str) -> Template:
        """
        Get template by name.
        
        Args:
            template_name: Name of template file
            
        Returns:
            Jinja2 Template object
            
        Raises:
            TemplateError: If template not found or invalid
        """
        try:
            # Ensure .html extension
            if not template_name.endswith('.html'):
                template_name = f"{template_name}.html"
            
            template = self.env.get_template(template_name)
            logger.debug(f"Loaded template: {template_name}")
            return template
            
        except TemplateNotFound:
            error_msg = f"Template not found: {template_name}"
            logger.error(error_msg)
            raise TemplateError(error_msg)
        except TemplateSyntaxError as e:
            error_msg = f"Template syntax error in {template_name}: {e}"
            logger.error(error_msg)
            raise TemplateError(error_msg)
    
    def render_template(
        self,
        template_name: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Render template with data.
        
        Args:
            template_name: Name of template
            data: Data dictionary for template
            
        Returns:
            Rendered HTML content
        """
        template = self.get_template(template_name)
        
        try:
            html_content = template.render(**data)
            logger.debug(f"Rendered template: {template_name} ({len(html_content)} chars)")
            return html_content
        except Exception as e:
            error_msg = f"Error rendering template {template_name}: {e}"
            logger.error(error_msg)
            raise TemplateError(error_msg)


# ============================================================================
# HTML RENDERER
# ============================================================================

class EnterpriseHTMLRenderer:
    """
    Enterprise-grade HTML renderer with Jinja2 templating.
    
    Features:
    - Jinja2 templating with auto-escaping
    - Template caching for performance
    - XSS prevention
    - Input validation
    - Batch processing support
    - PDF-ready HTML generation
    - Structured logging
    """
    
    def __init__(self, config: Optional[RenderConfig] = None):
        """
        Initialize HTML renderer.
        
        Args:
            config: Optional render configuration
        """
        self.config = config or RenderConfig()
        self.template_manager = TemplateManager(self.config)
        self.security_validator = SecurityValidator()
        
        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            f"EnterpriseHTMLRenderer initialized: "
            f"templates={self.config.template_dir}, "
            f"output={self.config.output_dir}"
        )
    
    def render(
        self,
        document_type: Union[DocumentType, str],
        data: Dict[str, Any],
        output_filename: Optional[str] = None
    ) -> RenderResult:
        """
        Render HTML document from template and data.
        
        Args:
            document_type: Type of document to render
            data: Data dictionary for template
            output_filename: Optional output filename
            
        Returns:
            RenderResult with rendered HTML
        """
        result = RenderResult(success=False)
        
        try:
            # Convert to DocumentType if string
            if isinstance(document_type, str):
                try:
                    document_type = DocumentType(document_type)
                except ValueError:
                    result.errors.append(f"Invalid document type: {document_type}")
                    return result
            
            # Validate data
            if self.config.enable_security_checks:
                if not self.security_validator.validate_data(data):
                    result.errors.append("Data validation failed")
                    return result
            
            # Get template name
            template_name = document_type.value
            
            # Render template
            html_content = self.template_manager.render_template(template_name, data)
            
            # Apply security checks
            if self.config.enable_security_checks:
                html_content = self.security_validator.strip_dangerous_tags(html_content)
            
            # Apply PDF-ready optimizations if needed
            if self.config.pdf_ready:
                html_content = self._optimize_for_pdf(html_content)
            
            # Minify if enabled
            if self.config.enable_minification:
                html_content = self._minify_html(html_content)
            
            # Save to file if output filename provided
            if output_filename:
                output_path = self.config.output_dir / output_filename
                self._save_html(html_content, output_path)
                result.output_path = output_path
            
            result.success = True
            result.html_content = html_content
            result.metadata['document_type'] = document_type.value
            result.metadata['html_size'] = len(html_content)
            
            logger.info(
                f"Successfully rendered {document_type.value}: "
                f"{len(html_content)} chars"
            )
            
        except TemplateError as e:
            result.errors.append(str(e))
        except Exception as e:
            error_msg = f"Unexpected error rendering {document_type}: {e}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)
        
        return result
    
    def render_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[RenderResult]:
        """
        Render multiple documents in batch.
        
        Args:
            documents: List of document specifications
                Each dict should contain: 'type', 'data', 'filename'
        
        Returns:
            List of RenderResult objects
        """
        results = []
        
        for i, doc_spec in enumerate(documents):
            try:
                doc_type = doc_spec.get('type')
                data = doc_spec.get('data', {})
                filename = doc_spec.get('filename')
                
                result = self.render(doc_type, data, filename)
                results.append(result)
                
                logger.info(f"Batch render {i+1}/{len(documents)}: {doc_type}")
                
            except Exception as e:
                error_result = RenderResult(success=False)
                error_result.errors.append(f"Batch render error: {e}")
                results.append(error_result)
        
        success_count = sum(1 for r in results if r.success)
        logger.info(f"Batch render complete: {success_count}/{len(documents)} successful")
        
        return results
    
    def _optimize_for_pdf(self, html_content: str) -> str:
        """
        Optimize HTML for PDF conversion.
        Templates already contain precise A4 CSS (190mm widths, Calibri, exact columns).
        We only add print-color-adjust to preserve backgrounds — nothing else.
        """
        pdf_css = """
        <style>
            * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        </style>
        """
        if '</head>' in html_content:
            html_content = html_content.replace('</head>', f'{pdf_css}</head>')
        return html_content
    
    def _minify_html(self, html_content: str) -> str:
        """
        Minify HTML content (basic implementation).
        
        Args:
            html_content: HTML content
            
        Returns:
            Minified HTML content
        """
        # Remove comments
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        
        # Remove extra whitespace
        html_content = re.sub(r'\s+', ' ', html_content)
        html_content = re.sub(r'>\s+<', '><', html_content)
        
        return html_content.strip()
    
    def _save_html(self, html_content: str, output_path: Path):
        """
        Save HTML content to file.
        
        Args:
            html_content: HTML content
            output_path: Output file path
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Saved HTML to: {output_path}")
        except Exception as e:
            error_msg = f"Failed to save HTML to {output_path}: {e}"
            logger.error(error_msg)
            raise HTMLRenderingError(error_msg)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def render_document(
    document_type: Union[DocumentType, str],
    data: Dict[str, Any],
    output_filename: Optional[str] = None,
    **config_kwargs
) -> RenderResult:
    """
    Convenience function to render a single document.
    
    Args:
        document_type: Type of document
        data: Data dictionary
        output_filename: Optional output filename
        **config_kwargs: Additional configuration arguments
        
    Returns:
        RenderResult
    """
    config = RenderConfig(**config_kwargs)
    renderer = EnterpriseHTMLRenderer(config)
    return renderer.render(document_type, data, output_filename)


def render_documents_batch(
    documents: List[Dict[str, Any]],
    **config_kwargs
) -> List[RenderResult]:
    """
    Convenience function to render multiple documents.
    
    Args:
        documents: List of document specifications
        **config_kwargs: Additional configuration arguments
        
    Returns:
        List of RenderResult objects
    """
    config = RenderConfig(**config_kwargs)
    renderer = EnterpriseHTMLRenderer(config)
    return renderer.render_batch(documents)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Render a document
    config = RenderConfig(
        template_dir="templates",
        output_dir="output",
        enable_security_checks=True,
        pdf_ready=True
    )
    
    renderer = EnterpriseHTMLRenderer(config)
    
    # Sample data
    data = {
        'title': 'Sample Bill',
        'project_name': 'Infrastructure Project',
        'total_amount': 1000000.50,
        'items': [
            {'description': 'Item 1', 'quantity': 10, 'rate': 1000, 'amount': 10000},
            {'description': 'Item 2', 'quantity': 20, 'rate': 2000, 'amount': 40000}
        ]
    }
    
    # Render document
    result = renderer.render(
        DocumentType.FIRST_PAGE,
        data,
        'sample_bill.html'
    )
    
    if result.success:
        print(f"✅ Success! Rendered to: {result.output_path}")
        print(f"HTML size: {result.metadata['html_size']} chars")
    else:
        print(f"❌ Failed: {result.errors}")
