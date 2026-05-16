import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from engine.rendering.html_renderer_enterprise import EnterpriseHTMLRenderer, DocumentType, RenderConfig
from engine.rendering.pdf_generator import PDFGenerator
from engine.rendering.word_generator import WordGenerator
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
    def prepare_template_data(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Maps unified model data to the structure expected by Jinja2 templates."""
        options = request_data.get("options", {})
        title_data = request_data.get("titleData", {})
        bill_items = request_data.get("billItems", [])
        
        mapped_items = []
        grand_total = 0.0
        work_order_total = 0.0
        overall_excess = 0.0
        overall_saving = 0.0

        for item in bill_items:
            item_dict = item.model_dump() if hasattr(item, "model_dump") else item
            
            # PWD Logic: quantity is usually 'upto date'
            qty_upto = float(item_dict.get("quantity", 0.0) or item_dict.get("quantityUpto", 0.0) or 0.0)
            qty_wo = float(item_dict.get("wo_quantity", 0.0) or 0.0)
            rate = float(item_dict.get("rate", 0.0) or 0.0)
            
            amt_bill = round(qty_upto * rate)
            amt_wo = round(qty_wo * rate)
            
            grand_total += amt_bill
            work_order_total += amt_wo
            
            # Deviation
            excess_qty = max(0, qty_upto - qty_wo)
            saving_qty = max(0, qty_wo - qty_upto)
            excess_amt = round(excess_qty * rate)
            saving_amt = round(saving_qty * rate)
            
            overall_excess += excess_amt
            overall_saving += saving_amt

            mapped_items.append({
                "serial_no": str(item_dict.get("itemNo", "")),
                "description": str(item_dict.get("description", "")),
                "unit": str(item_dict.get("unit", "")),
                "quantity_since_last": str(item_dict.get("quantitySince", qty_upto)), # Fallback for display
                "quantity_upto_date": str(qty_upto),
                "qty_wo": str(qty_wo) if qty_wo > 0 else "",
                "amt_wo": str(amt_wo) if amt_wo > 0 else "",
                "qty_bill": str(qty_upto),
                "amt_bill": str(amt_bill),
                "rate": str(rate),
                "amount": str(amt_bill),
                "amount_previous": str(amt_bill), # For simplified first bill
                "excess_qty": str(excess_qty) if excess_qty > 0 else "",
                "excess_amt": str(excess_amt) if excess_amt > 0 else "",
                "saving_qty": str(saving_qty) if saving_qty > 0 else "",
                "saving_amt": str(saving_amt) if saving_amt > 0 else "",
                "remark": str(item_dict.get("aiNote", ""))
            })

        premium_pct = float(options.get("premiumPercent", 0.0) or 0.0)
        premium_type = options.get("premiumType", "above")
        premium_amount = round(grand_total * premium_pct / 100.0) if premium_type == "above" else round(-grand_total * premium_pct / 100.0)
        payable = grand_total + premium_amount
        last_bill = float(options.get("previousBillAmount", 0.0) or 0.0)
        net_payable = payable - last_bill

        # Premium for deviation summary
        tender_premium_f = round(work_order_total * premium_pct / 100.0) if premium_type == "above" else round(-work_order_total * premium_pct / 100.0)
        tender_premium_h = premium_amount
        grand_total_f = work_order_total + tender_premium_f
        grand_total_h = payable
        
        net_diff = grand_total_h - grand_total_f

        sd_pct = float(options.get("sdPercent", 10.0) or 10.0)
        it_pct = float(options.get("itPercent", 2.0) or 2.0)
        gst_pct = float(options.get("gstPercent", 2.0) or 2.0)
        lc_pct = float(options.get("lcPercent", 1.0) or 1.0)

        sd_amount = round(payable * sd_pct / 100.0)
        it_amount = round(payable * it_pct / 100.0)
        
        # PWD Rule: GST must be an even number
        gst_raw = round(payable * gst_pct / 100.0)
        gst_amount = gst_raw if gst_raw % 2 == 0 else gst_raw + 1
        
        lc_amount = round(payable * lc_pct / 100.0)
        total_deductions = sd_amount + it_amount + gst_amount + lc_amount
        net_payable = payable - last_bill - total_deductions # Simplified

        # Flatten titleData
        flat_header = {
            "agreement_no": title_data.get("Agreement No.", title_data.get("Agreement No", "")),
            "name_of_work": title_data.get("Name of Work", title_data.get("Name of work", "")),
            "name_of_firm": title_data.get("Name of Contractor or supplier", title_data.get("Contractor", "")),
            "date_commencement": title_data.get("Date of written order to commence work :", ""),
            "date_completion": title_data.get("St. date of completion :", ""),
            "actual_completion": title_data.get("Date of actual completion of work :", ""),
            "work_order_amount": float(title_data.get("Work Order Amount Rs.", 0.0) or 0.0),
        }

        return {
            "data": {
                **flat_header,
                "header": [[k, v] for k, v in title_data.items()],
                "items": mapped_items,
                "totals": {
                    "grand_total": grand_total,
                    "premium": {
                        "percent": premium_pct / 100.0,
                        "amount": premium_amount,
                        "type": premium_type
                    },
                    "payable": payable,
                    "last_bill_amount": last_bill,
                    "sd_amount": sd_amount,
                    "it_amount": it_amount,
                    "gst_amount": gst_amount,
                    "lc_amount": lc_amount,
                    "total_deductions": total_deductions,
                    "net_payable": net_payable
                },
                "summary": {
                    "work_order_total": work_order_total,
                    "executed_total": grand_total,
                    "overall_excess": overall_excess,
                    "overall_saving": overall_saving,
                    "premium": {"percent": premium_pct / 100.0},
                    "tender_premium_f": tender_premium_f,
                    "tender_premium_h": tender_premium_h,
                    "grand_total_f": grand_total_f,
                    "grand_total_h": grand_total_h,
                    "net_difference": abs(net_diff),
                    "is_saving": net_diff < 0,
                    "percentage_deviation": (abs(net_diff) / grand_total_f * 100) if grand_total_f != 0 else 0
                },
                "options": options,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    @staticmethod
    async def process_generation(job_id: str, request_data: Dict[str, Any], update_callback):
        """Orchestrate document rendering and storage"""
        # 1. Prepare data for template
        template_data = BillService.prepare_template_data(request_data)
        options = request_data.get("options", {})
        
        # 2. Rendering Config
        base_path = Path(__file__).parent.parent.parent # Root of the project
        config = RenderConfig(
            template_dir=str(base_path / "engine" / "templates" / "v1"),
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
                
        # 3. PDF and Word Conversion
        docs = [DocumentInfo(name=p.name, format="html", size=p.stat().st_size) for p in html_paths]
        word_gen = WordGenerator()
        
        for i, hp in enumerate(html_paths):
            base_name = hp.stem
            progress_base = 70 + int(25 * (i + 1) / len(html_paths))
            
            # --- PDF Generation ---
            pdf_name = f"{base_name}.pdf"
            pdf_path = hp.parent / pdf_name
            await update_callback(job_id, progress_base - 2, f"Generating PDF for {base_name}...")
            try:
                content = hp.read_text(encoding='utf-8')
                engine_used = pdf_gen.generate_with_fallback(content, str(pdf_path))
                docs.append(DocumentInfo(name=pdf_name, format="pdf", size=pdf_path.stat().st_size))
                logger.info(f"PDF [{engine_used}] created: {pdf_name}")
            except Exception as e:
                logger.error(f"PDF failed for {hp.name}: {e}")

            # --- Word (DOCX) Generation ---
            docx_name = f"{base_name}.docx"
            docx_path = hp.parent / docx_name
            await update_callback(job_id, progress_base, f"Generating Word doc for {base_name}...")
            try:
                docx_bytes = word_gen.html_to_docx(content, base_name.replace('_', ' ').upper())
                docx_path.write_bytes(docx_bytes)
                docs.append(DocumentInfo(name=docx_name, format="docx", size=docx_path.stat().st_size))
                logger.info(f"Word doc created: {docx_name}")
            except Exception as e:
                logger.error(f"Word generation failed for {hp.name}: {e}")
                
        # 4. Finalize
        # Data hash for integrity
        data_hash = BillService.generate_data_hash(request_data)
        
        return docs, data_hash
