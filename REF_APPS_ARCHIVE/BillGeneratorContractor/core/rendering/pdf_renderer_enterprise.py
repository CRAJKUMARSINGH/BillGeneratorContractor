"""
Enterprise-Grade PDF Rendering Engine
Isolated PDF generation layer with multiple engine support.

Author: Senior PDF Rendering Engineer
Standards: PDF/A compliance, Print-accurate rendering, Engine abstraction
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import subprocess
import tempfile

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class PDFEngine(Enum):
    """Supported PDF rendering engines."""
    WEASYPRINT = "weasyprint"
    PLAYWRIGHT = "playwright"
    WKHTMLTOPDF = "wkhtmltopdf"


class PageSize(Enum):
    """Standard page sizes."""
    A4 = "A4"
    A4_LANDSCAPE = "A4 landscape"
    LETTER = "Letter"
    LETTER_LANDSCAPE = "Letter landscape"
    LEGAL = "Legal"


class PageOrientation(Enum):
    """Page orientation."""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


# PDF generation defaults
DEFAULT_MARGIN = "10mm"
DEFAULT_DPI = 96
DEFAULT_ENCODING = "utf-8"


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class PDFRenderingError(Exception):
    """Base exception for PDF rendering errors."""
    pass


class EngineNotAvailableError(PDFRenderingError):
    """Raised when PDF engine is not available."""
    pass


class ConversionError(PDFRenderingError):
    """Raised when PDF conversion fails."""
    pass


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PDFConfig:
    """Configuration for PDF rendering."""
    page_size: PageSize = PageSize.A4
    orientation: PageOrientation = PageOrientation.PORTRAIT
    margin_top: str = DEFAULT_MARGIN
    margin_right: str = DEFAULT_MARGIN
    margin_bottom: str = DEFAULT_MARGIN
    margin_left: str = DEFAULT_MARGIN
    dpi: int = DEFAULT_DPI
    enable_forms: bool = False
    enable_javascript: bool = False
    compress: bool = True
    pdf_version: str = "1.7"
    
    def get_margin_css(self) -> str:
        """Generate CSS margin string."""
        return f"{self.margin_top} {self.margin_right} {self.margin_bottom} {self.margin_left}"


@dataclass
class PDFRenderResult:
    """Result of PDF rendering operation."""
    success: bool
    pdf_path: Optional[Path] = None
    pdf_bytes: Optional[bytes] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# PDF RENDERING ENGINES (Abstract Base)
# ============================================================================

class PDFRendererBase(ABC):
    """Abstract base class for PDF rendering engines."""
    
    def __init__(self, config: PDFConfig):
        """
        Initialize PDF renderer.
        
        Args:
            config: PDF configuration
        """
        self.config = config
        logger.info(f"{self.__class__.__name__} initialized")
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if rendering engine is available.
        
        Returns:
            True if engine is available
        """
        pass
    
    @abstractmethod
    def render_from_html_string(
        self,
        html_content: str,
        output_path: Optional[Path] = None
    ) -> PDFRenderResult:
        """
        Render PDF from HTML string.
        
        Args:
            html_content: HTML content as string
            output_path: Optional output file path
            
        Returns:
            PDFRenderResult
        """
        pass
    
    @abstractmethod
    def render_from_html_file(
        self,
        html_path: Path,
        output_path: Optional[Path] = None
    ) -> PDFRenderResult:
        """
        Render PDF from HTML file.
        
        Args:
            html_path: Path to HTML file
            output_path: Optional output file path
            
        Returns:
            PDFRenderResult
        """
        pass


# ============================================================================
# WEASYPRINT ENGINE
# ============================================================================

class WeasyPrintRenderer(PDFRendererBase):
    """WeasyPrint-based PDF renderer (recommended)."""
    
    def __init__(self, config: PDFConfig):
        """Initialize WeasyPrint renderer."""
        super().__init__(config)
        self.font_config = FontConfiguration()
    
    def is_available(self) -> bool:
        """Check if WeasyPrint is available."""
        try:
            import weasyprint
            return True
        except ImportError:
            return False
    
    def render_from_html_string(
        self,
        html_content: str,
        output_path: Optional[Path] = None
    ) -> PDFRenderResult:
        """
        Render PDF from HTML string using WeasyPrint.
        
        Args:
            html_content: HTML content
            output_path: Output PDF path
            
        Returns:
            PDFRenderResult
        """
        result = PDFRenderResult(success=False)
        
        try:
            # Create HTML object
            html = HTML(string=html_content, encoding=DEFAULT_ENCODING)
            
            # Generate custom CSS for page setup
            custom_css = self._generate_page_css()
            css = CSS(string=custom_css, font_config=self.font_config)
            
            # Render PDF
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                html.write_pdf(
                    target=str(output_path),
                    stylesheets=[css],
                    font_config=self.font_config,
                    compress=self.config.compress
                )
                
                result.pdf_path = output_path
                logger.info(f"PDF saved to: {output_path}")
            else:
                # Return as bytes
                pdf_bytes = html.write_pdf(
                    stylesheets=[css],
                    font_config=self.font_config,
                    compress=self.config.compress
                )
                result.pdf_bytes = pdf_bytes
            
            result.success = True
            result.metadata = {
                'engine': 'weasyprint',
                'page_size': self.config.page_size.value,
                'orientation': self.config.orientation.value
            }
            
        except Exception as e:
            error_msg = f"WeasyPrint rendering failed: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        
        return result
    
    def render_from_html_file(
        self,
        html_path: Path,
        output_path: Optional[Path] = None
    ) -> PDFRenderResult:
        """
        Render PDF from HTML file using WeasyPrint.
        
        Args:
            html_path: Path to HTML file
            output_path: Output PDF path
            
        Returns:
            PDFRenderResult
        """
        result = PDFRenderResult(success=False)
        
        try:
            # Validate HTML file
            html_path = Path(html_path)
            if not html_path.exists():
                result.errors.append(f"HTML file not found: {html_path}")
                return result
            
            # Read HTML content
            with open(html_path, 'r', encoding=DEFAULT_ENCODING) as f:
                html_content = f.read()
            
            # Render using string method
            result = self.render_from_html_string(html_content, output_path)
            result.metadata['source_html'] = str(html_path)
            
        except Exception as e:
            error_msg = f"Failed to read HTML file: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        
        return result
    
    def _generate_page_css(self) -> str:
        """
        Generate CSS for page setup.
        
        Returns:
            CSS string
        """
        orientation = "portrait" if self.config.orientation == PageOrientation.PORTRAIT else "landscape"
        
        css = f"""
        @page {{
            size: {self.config.page_size.value} {orientation};
            margin: {self.config.get_margin_css()};
        }}
        
        /* Ensure proper page breaks */
        .page-break {{
            page-break-before: always;
        }}
        
        .no-break {{
            page-break-inside: avoid;
        }}
        
        /* Print-specific styles */
        @media print {{
            body {{
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}
        }}
        """
        
        return css


# ============================================================================
# WKHTMLTOPDF ENGINE (Legacy Support)
# ============================================================================

class WkhtmltopdfRenderer(PDFRendererBase):
    """wkhtmltopdf-based PDF renderer (legacy)."""
    
    def is_available(self) -> bool:
        """Check if wkhtmltopdf is available."""
        try:
            result = subprocess.run(
                ['wkhtmltopdf', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def render_from_html_string(
        self,
        html_content: str,
        output_path: Optional[Path] = None
    ) -> PDFRenderResult:
        """Render PDF from HTML string using wkhtmltopdf."""
        result = PDFRenderResult(success=False)
        
        try:
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.html',
                encoding=DEFAULT_ENCODING,
                delete=False
            ) as tmp_html:
                tmp_html.write(html_content)
                tmp_html_path = Path(tmp_html.name)
            
            # Render from file
            result = self.render_from_html_file(tmp_html_path, output_path)
            
            # Clean up
            tmp_html_path.unlink()
            
        except Exception as e:
            error_msg = f"wkhtmltopdf rendering failed: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        
        return result
    
    def render_from_html_file(
        self,
        html_path: Path,
        output_path: Optional[Path] = None
    ) -> PDFRenderResult:
        """Render PDF from HTML file using wkhtmltopdf."""
        result = PDFRenderResult(success=False)
        
        try:
            # Validate HTML file
            html_path = Path(html_path)
            if not html_path.exists():
                result.errors.append(f"HTML file not found: {html_path}")
                return result
            
            # Prepare output path
            if not output_path:
                output_path = html_path.with_suffix('.pdf')
            else:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build command
            cmd = [
                'wkhtmltopdf',
                '--page-size', self.config.page_size.value,
                '--orientation', self.config.orientation.value,
                '--margin-top', self.config.margin_top,
                '--margin-right', self.config.margin_right,
                '--margin-bottom', self.config.margin_bottom,
                '--margin-left', self.config.margin_left,
                '--dpi', str(self.config.dpi),
                '--enable-local-file-access',
                str(html_path),
                str(output_path)
            ]
            
            # Execute
            proc_result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60
            )
            
            if proc_result.returncode == 0:
                result.success = True
                result.pdf_path = output_path
                result.metadata = {
                    'engine': 'wkhtmltopdf',
                    'page_size': self.config.page_size.value
                }
                logger.info(f"PDF saved to: {output_path}")
            else:
                error_msg = proc_result.stderr.decode('utf-8', errors='ignore')
                result.errors.append(f"wkhtmltopdf error: {error_msg}")
            
        except subprocess.TimeoutExpired:
            result.errors.append("wkhtmltopdf timeout (>60s)")
        except Exception as e:
            error_msg = f"wkhtmltopdf execution failed: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        
        return result


# ============================================================================
# PDF RENDERER FACTORY
# ============================================================================

class PDFRendererFactory:
    """Factory for creating PDF renderers."""
    
    @staticmethod
    def create_renderer(
        engine: PDFEngine = PDFEngine.WEASYPRINT,
        config: Optional[PDFConfig] = None
    ) -> PDFRendererBase:
        """
        Create PDF renderer instance.
        
        Args:
            engine: PDF engine to use
            config: PDF configuration
            
        Returns:
            PDFRendererBase instance
            
        Raises:
            EngineNotAvailableError: If engine is not available
        """
        if config is None:
            config = PDFConfig()
        
        # Create renderer based on engine
        if engine == PDFEngine.WEASYPRINT:
            renderer = WeasyPrintRenderer(config)
        elif engine == PDFEngine.WKHTMLTOPDF:
            renderer = WkhtmltopdfRenderer(config)
        else:
            raise ValueError(f"Unsupported PDF engine: {engine}")
        
        # Check availability
        if not renderer.is_available():
            raise EngineNotAvailableError(
                f"PDF engine not available: {engine.value}. "
                f"Please install the required dependencies."
            )
        
        return renderer
    
    @staticmethod
    def get_available_engines() -> List[PDFEngine]:
        """
        Get list of available PDF engines.
        
        Returns:
            List of available engines
        """
        available = []
        
        for engine in PDFEngine:
            try:
                config = PDFConfig()
                if engine == PDFEngine.WEASYPRINT:
                    renderer = WeasyPrintRenderer(config)
                elif engine == PDFEngine.WKHTMLTOPDF:
                    renderer = WkhtmltopdfRenderer(config)
                else:
                    continue
                
                if renderer.is_available():
                    available.append(engine)
            except Exception:
                pass
        
        return available


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def render_pdf(
    html_content: str,
    output_path: Path,
    engine: PDFEngine = PDFEngine.WEASYPRINT,
    config: Optional[PDFConfig] = None
) -> PDFRenderResult:
    """
    Convenience function to render PDF from HTML.
    
    Args:
        html_content: HTML content string
        output_path: Output PDF path
        engine: PDF engine to use
        config: PDF configuration
        
    Returns:
        PDFRenderResult
    """
    renderer = PDFRendererFactory.create_renderer(engine, config)
    return renderer.render_from_html_string(html_content, output_path)


def render_pdf_from_file(
    html_path: Path,
    output_path: Path,
    engine: PDFEngine = PDFEngine.WEASYPRINT,
    config: Optional[PDFConfig] = None
) -> PDFRenderResult:
    """
    Convenience function to render PDF from HTML file.
    
    Args:
        html_path: Path to HTML file
        output_path: Output PDF path
        engine: PDF engine to use
        config: PDF configuration
        
    Returns:
        PDFRenderResult
    """
    renderer = PDFRendererFactory.create_renderer(engine, config)
    return renderer.render_from_html_file(html_path, output_path)
