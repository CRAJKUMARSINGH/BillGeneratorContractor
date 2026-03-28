"""Jinja2 HTML renderer — uses templates from app/engine/renderer/templates/"""
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)

_TEMPLATE_MAP = {
    "first_page.html": "01_first_page.html",
    "note_sheet_new.html": "02_note_sheet.html",
    "certificate_ii.html": "03_certificate_ii.html",
    "certificate_iii.html": "04_certificate_iii.html",
}
_EXTRA_TEMPLATES = {
    "extra_items.html": "05_extra_items.html",
    "deviation_statement.html": "06_deviation.html",
}


def render_html(data: dict, out_dir: Path) -> list[Path]:
    """Render all Jinja2 templates and write to out_dir. Returns list of written files."""
    tmpl_dir = settings.template_dir
    if not tmpl_dir.exists():
        logger.error(f"Template dir not found: {tmpl_dir}")
        return []

    env = Environment(
        loader=FileSystemLoader(str(tmpl_dir)),
        autoescape=select_autoescape(["html"]),
    )

    template_map = dict(_TEMPLATE_MAP)
    if data.get("has_extra_items"):
        template_map.update(_EXTRA_TEMPLATES)

    rendered: list[Path] = []
    for tmpl_name, out_name in template_map.items():
        if not (tmpl_dir / tmpl_name).exists():
            logger.warning(f"Template missing: {tmpl_name}, skipping")
            continue
        try:
            html = env.get_template(tmpl_name).render(data=data)
            out_file = out_dir / out_name
            out_file.write_text(html, encoding="utf-8")
            rendered.append(out_file)
        except Exception as e:
            logger.warning(f"Failed to render {tmpl_name}: {e}")

    return rendered
