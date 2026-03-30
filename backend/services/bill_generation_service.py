"""
Bill Generation Service Layer

This module contains the core business logic for bill document generation,
separated from HTTP route handlers to maintain clean architectural boundaries.
"""
import json
import logging
import os
import zipfile
from pathlib import Path
from sqlmodel import Session, select

import redis as _redis_sync

from backend.models import GenerateRequest, BillRecord, DocumentInfo
from backend.database import engine
from ingestion.models import UnifiedDocumentModel, DocumentRow
from engine.calculation.bill_processor import process_unified_bill
from engine.rendering.html_renderer_enterprise import (
    EnterpriseHTMLRenderer, RenderConfig, DocumentType
)
from engine.rendering.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)

# Shared sync pool for progress updates from worker thread
_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_sync_redis_pool = _redis_sync.ConnectionPool.from_url(_REDIS_URL)


def generate_documents(job_id: str, req: GenerateRequest, output_dir: Path):
    """
    Core document generation logic — transforms GenerateRequest into
    UnifiedDocumentModel and runs the unified calculation/rendering pipeline.
    
    This function is CPU-bound and should be run in a thread executor
    when called from async contexts.
    """
    out_dir = output_dir / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    opts = req.options

    def update_db_status(status_str, message_str, amount=None):
        with Session(engine) as session:
            record = session.exec(select(BillRecord).where(BillRecord.job_id == job_id)).first()
            if record:
                record.status = status_str
                record.message = message_str
                if amount is not None:
                    record.total_amount = amount
                session.add(record)
                session.commit()

    try:
        r = _redis_sync.Redis(connection_pool=_sync_redis_pool)

        def update_progress(progress: int, message: str = "") -> None:
            """Atomically update job progress in Redis using full JSON SET."""
            key = f"job:{job_id}"
            try:
                with r.pipeline() as pipe:
                    for _ in range(3):
                        try:
                            pipe.watch(key)
                            raw = pipe.get(key)
                            job_data = json.loads(raw) if raw else {}
                            job_data.update({"progress": progress, "message": message, "status": "processing"})
                            pipe.multi()
                            pipe.set(key, json.dumps(job_data), ex=86400)
                            pipe.execute()
                            return
                        except _redis_sync.WatchError:
                            continue
            except _redis_sync.ConnectionError:
                pass # Silent ignore if Redis is not running
            except Exception as e:
                logger.warning(f"Redis update failed: {e}")

        update_progress(10, "Syncing document model...")
        update_db_status("processing", "Syncing document model...")

        # 1. Map GenerateRequest -> UnifiedDocumentModel
        doc_rows = []
        for item in req.billItems:
            doc_rows.append(DocumentRow(
                serial_no=item.itemNo,
                description=item.description,
                unit=item.unit,
                qty_since_last_bill=item.quantitySince,
                qty_to_date=item.quantityUpto,
                rate=item.rate,
                amount=item.amount
            ))
            
        for ei in req.extraItems:
            doc_rows.append(DocumentRow(
                serial_no=ei.itemNo,
                description=ei.description,
                unit=ei.unit,
                qty_since_last_bill=ei.quantity,
                qty_to_date=ei.quantity,
                rate=ei.rate,
                amount=ei.amount,
                remarks=ei.bsr or ei.remark or "Extra Item"
            ))

        # Inject UI options into metadata for the processor
        # [HIGH-4]: Explicitly map date fields so they appear in all 6 document templates
        metadata = req.titleData.copy()
        metadata['tender_premium_percentage'] = opts.premiumPercent
        metadata['last_bill_deduction'] = opts.previousBillAmount
        metadata['has_extra_items'] = len(req.extraItems) > 0
        # Canonical date field aliases — matched against common Excel header variants
        _DATE_ALIASES = {
            'date_commencement': ['Date of written order to commence work', 'Commencement Date', 'date_commencement'],
            'date_completion':   ['St. Date of Completion', 'Stipulated Date of Completion', 'date_completion'],
            'actual_completion': ['Date of actual completion of work', 'Actual Completion Date', 'actual_completion'],
        }
        for canonical, aliases in _DATE_ALIASES.items():
            if canonical not in metadata or not metadata[canonical]:
                for alias in aliases:
                    if alias in req.titleData and req.titleData[alias]:
                        metadata[canonical] = req.titleData[alias]
                        break

        unified_doc = UnifiedDocumentModel(
            document_id=job_id,
            source_type="ui_edit",
            raw_metadata=metadata,
            rows=doc_rows,
            total_amount=sum(r.amount for r in doc_rows)
        )

        update_progress(30, "Running unified calculation engine...")

        # 2. Run Unified Calculation
        calculated_data = process_unified_bill(unified_doc)
        payable = calculated_data['totals']['payable']
        
        update_db_status("processing", "Calculation complete", payable)

        update_progress(50, "Rendering high-fidelity templates...")

        # 3. Render HTML using v2 templates
        root_dir = Path(__file__).parent.parent.parent
        config = RenderConfig(
            template_dir=root_dir / "engine" / "templates" / "v2",
            output_dir=out_dir,
            enable_security_checks=True,
            pdf_ready=True,
        )
        renderer = EnterpriseHTMLRenderer(config)

        doc_types = [
            DocumentType.FIRST_PAGE,
            DocumentType.NOTE_SHEET,
            DocumentType.DEVIATION_STATEMENT,
            DocumentType.EXTRA_ITEMS,
            DocumentType.CERTIFICATES,
            DocumentType.LAST_PAGE,
        ]

        html_paths = []
        for i, doc_type in enumerate(doc_types):
            # Pass correct sub-data context based on document type
            if doc_type == DocumentType.DEVIATION_STATEMENT:
                template_context = {"data": calculated_data["deviation"], "metadata": calculated_data["metadata"]}
            elif doc_type == DocumentType.EXTRA_ITEMS:
                template_context = {"data": calculated_data["extra_items"], "metadata": calculated_data["metadata"]}
            else:
                template_context = {"data": calculated_data, "metadata": calculated_data["metadata"]}

            result = renderer.render(doc_type, template_context, f"{doc_type.value}.html")
            if result.success:
                html_paths.append(result.output_path)
            update_progress(
                50 + int(20 * (i + 1) / len(doc_types)),
                f"Rendered {doc_type.value} ({i+1}/{len(doc_types)})"
            )

        docs = [DocumentInfo(name=p.name, format="html", size=p.stat().st_size) for p in html_paths]

        # ── Generate PDFs ─────────────────────────────────────────────────────
        if opts.generatePdf and html_paths:
            update_progress(72, "Generating PDFs...")
            pdf_gen = PDFGenerator(orientation="portrait")
            for html_path in html_paths:
                pdf_path = out_dir / (html_path.stem + ".pdf")
                html_content = html_path.read_text(encoding="utf-8")
                try:
                    engine_used = pdf_gen.generate_with_fallback(
                        html_content, str(pdf_path)
                    )
                    docs.append(DocumentInfo(
                        name=pdf_path.name, format="pdf",
                        size=pdf_path.stat().st_size
                    ))
                    logger.info(f"PDF [{engine_used}] → {pdf_path.name}")
                except Exception as e:
                    logger.warning(f"PDF failed for {html_path.name}: {e}")

        # ── ZIP ───────────────────────────────────────────────────────────────
        update_progress(92, "Creating ZIP archive...")
        zip_path = out_dir / "bill_documents.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in out_dir.glob("*"):
                if f.suffix in {".html", ".pdf", ".docx"}:
                    zf.write(f, f.name)

        update_progress(100, "All documents generated successfully")
        # Mark job complete in Redis with final document list
        try:
            with r.pipeline() as pipe:
                for _ in range(3):
                    try:
                        key = f"job:{job_id}"
                        pipe.watch(key)
                        raw = pipe.get(key)
                        job_data = json.loads(raw) if raw else {}
                        job_data.update({
                            "status": "complete",
                            "progress": 100,
                            "message": "Generation complete",
                            "documents": [d.model_dump() for d in docs],
                            "error": None,
                        })
                        pipe.multi()
                        pipe.set(key, json.dumps(job_data), ex=86400)
                        pipe.execute()
                        break
                    except _redis_sync.WatchError:
                        continue
        except _redis_sync.ConnectionError:
            pass
        except Exception as e:
            logger.warning(f"Redis completion update failed: {e}")
        update_db_status("complete", "Generation complete")
        logger.info(f"Job {job_id} completed with {len(docs)} documents")

        return docs

    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        # Best-effort: update Redis job state to error
        try:
            key = f"job:{job_id}"
            raw = r.get(key)
            job_data = json.loads(raw) if raw else {}
            job_data.update({"status": "error", "message": f"Generation failed: {e}", "error": str(e)})
            r.set(key, json.dumps(job_data), ex=86400)
        except Exception:
            pass
        update_db_status("error", f"Generation failed: {e}")
        raise
