import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from engine.rendering.html_renderer_enterprise import EnterpriseHTMLRenderer, DocumentType, RenderConfig
from engine.rendering.pdf_generator import PDFGenerator
from models import BillRecord, DocumentInfo, JobStatus

logger = logging.getLogger(__name__)

class BillService:
    @staticmethod
    def generate_data_hash(data: Dict[str, Any]) -> str:
        """NASA-Grade Data Integrity Hash (SHA-256)"""
        # Canonicalize JSON to ensure consistent hashing
        canonical_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical_data.encode('utf-8')).hexdigest()

    @staticmethod
    async def process_generation(job_id: str, request_data: Dict[str, Any], update_callback):
        """Orchestrate document rendering and storage"""
        options = request_data.get("options", {})
        title_data = request_data.get("titleData", {})
        bill_items = request_data.get("billItems", [])
        
        # 1. Prepare data for template
        template_data = {
            **title_data,
            "items": bill_items,
            "options": options,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # 2. Rendering Config
        config = RenderConfig(
            template_dir="templates",
            output_dir=f"output/{job_id}",
            pdf_ready=True
        )
        renderer = EnterpriseHTMLRenderer(config)
        pdf_gen = PDFGenerator(orientation='landscape')
        
        doc_types = [
            DocumentType.FIRST_PAGE,
            DocumentType.DEVIATION_STATEMENT,
            DocumentType.NOTE_SHEET
        ]
        
        html_paths = []
        for i, dt in enumerate(doc_types):
            progress = 30 + int(30 * (i + 1) / len(doc_types))
            await update_callback(job_id, progress, f"Rendering {dt.value}...")
            
            res = renderer.render(dt, template_data, f"{dt.value}.html")
            if res.success:
                html_paths.append(res.output_path)
                
        # 3. PDF Conversion
        docs = [DocumentInfo(name=p.name, format="html", size=p.stat().st_size) for p in html_paths]
        
        for i, hp in enumerate(html_paths):
            pdf_name = f"{hp.stem}.pdf"
            pdf_path = hp.parent / pdf_name
            
            progress = 70 + int(20 * (i + 1) / len(html_paths))
            await update_callback(job_id, progress, f"Generating PDF for {hp.stem}...")
            
            try:
                content = hp.read_text(encoding='utf-8')
                engine_used = pdf_gen.generate_with_fallback(content, str(pdf_path))
                docs.append(DocumentInfo(name=pdf_name, format="pdf", size=pdf_path.stat().st_size))
                logger.info(f"PDF [{engine_used}] created: {pdf_name}")
            except Exception as e:
                logger.error(f"PDF failed for {hp.name}: {e}")
                
        # 4. Finalize
        # Data hash for integrity
        data_hash = BillService.generate_data_hash(request_data)
        
        return docs, data_hash
