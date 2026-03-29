"""WeasyPrint PDF renderer"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def render_pdf(html_files: list[Path], out_dir: Path) -> list[Path]:
    """Convert HTML files to PDF. Returns list of generated PDF paths."""
    pdfs: list[Path] = []
    try:
        from weasyprint import HTML
    except ImportError:
        logger.warning("WeasyPrint not installed — skipping PDF generation")
        return pdfs

    for html_file in html_files:
        pdf_path = out_dir / (html_file.stem + ".pdf")
        try:
            HTML(filename=str(html_file)).write_pdf(str(pdf_path))
            pdfs.append(pdf_path)
            logger.info(f"PDF: {pdf_path.name}")
        except Exception as e:
            logger.warning(f"PDF failed for {html_file.name}: {e}")

    return pdfs
