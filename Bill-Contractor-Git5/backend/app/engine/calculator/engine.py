"""
Auto Calculation Engine
Reactive recalculation of all financial totals from the UnifiedDocument.
Deterministic ordering — no side effects.
"""
from __future__ import annotations
import math
from app.engine.models import UnifiedDocument


def _safe(v: float) -> float:
    return 0.0 if (math.isnan(v) or math.isinf(v)) else v


def calculate(doc: UnifiedDocument) -> dict:
    """
    Build the complete financial summary dict from a UnifiedDocument.
    Pure function — does not mutate doc.
    Returns the template_data dict consumed by the renderer.
    """
    title = dict(doc.titleData)

    bill_total = _safe(sum(i.amount for i in doc.billItems))
    extra_total = _safe(sum(i.amount for i in doc.extraItems))

    # Tender premium
    tender_premium_pct = 0.0
    above_below = "Above"
    try:
        tp_raw = title.get("Tender Premium %", title.get("Tender Premium", "0"))
        tender_premium_pct = float(str(tp_raw).replace("%", "").strip() or 0)
        above_below = str(title.get("Above / Below", title.get("Premium Type", "Above"))).strip()
    except Exception:
        pass

    premium_amount = _safe(bill_total * tender_premium_pct / 100)
    payable = bill_total - premium_amount if above_below.lower() == "below" else bill_total + premium_amount
    total_bill_amount = _safe(payable + extra_total)

    # Standard Rajasthan PWD deductions
    sd_amount = round(total_bill_amount * 0.10, 2)
    it_amount = round(total_bill_amount * 0.02, 2)
    gst_amount = round(total_bill_amount * 0.02)
    if int(gst_amount) % 2 != 0:
        gst_amount += 1
    lc_amount = round(total_bill_amount * 0.01, 2)
    total_deductions = sd_amount + it_amount + gst_amount + lc_amount

    # Last bill / work order
    try:
        last_bill_amount = float(str(title.get("Amount Paid Vide Last Bill", "0")).replace(",", "").strip() or 0)
    except Exception:
        last_bill_amount = 0.0

    try:
        work_order_amount = float(str(title.get("WORK ORDER AMOUNT RS.", "0")).replace(",", "").strip() or 0)
    except Exception:
        work_order_amount = 0.0

    net_payable = _safe(total_bill_amount - last_bill_amount)
    net_difference = work_order_amount - total_bill_amount

    totals = {
        "work_order_amount": work_order_amount,
        "last_bill_amount": last_bill_amount,
        "bill_total": bill_total,
        "payable": payable,
        "extra_items_sum": extra_total,
        "total_bill_amount": total_bill_amount,
        "sd_amount": sd_amount,
        "it_amount": it_amount,
        "gst_amount": gst_amount,
        "lc_amount": lc_amount,
        "total_deductions": total_deductions,
        "net_payable": net_payable,
        "grand_total": total_bill_amount,
        "premium": {
            "percent": tender_premium_pct / 100,
            "amount": premium_amount,
            "above_below": above_below,
        },
    }

    summary = {
        "work_order_total": work_order_amount,
        "executed_total": total_bill_amount,
        "net_difference": abs(net_difference),
        "is_saving": net_difference >= 0,
        "overall_saving": max(0.0, net_difference),
        "overall_excess": max(0.0, -net_difference),
        "percentage_deviation": (net_difference / work_order_amount * 100) if work_order_amount else 0,
        "premium": totals["premium"],
        "grand_total_f": total_bill_amount,
        "grand_total_h": 0.0,
        "grand_total_j": 0.0,
        "grand_total_l": 0.0,
        "tender_premium_f": premium_amount,
        "tender_premium_h": 0.0,
        "tender_premium_j": 0.0,
        "tender_premium_l": 0.0,
        **totals,
    }

    def _enrich(d: dict) -> dict:
        d["quantity_since_last"] = d.get("quantitySince", 0) or 0
        d["quantity_upto_date"] = d.get("quantityUpto", 0) or d.get("quantity", 0) or 0
        d["serial_no"] = d.get("itemNo", "")
        d["bold"] = False
        d["underline"] = False
        d["amount_previous"] = 0.0
        d.setdefault("remark", "")
        return d

    from datetime import datetime
    from app.engine.calculator.words import number_to_words

    return {
        "title_data": title,
        "bill_items": [_enrich(i.model_dump()) for i in doc.billItems],
        "extra_items": [_enrich(i.model_dump()) for i in doc.extraItems],
        "items": [_enrich(i.model_dump()) for i in doc.billItems],
        "totals": totals,
        "summary": summary,
        "bill_total": bill_total,
        "extra_total": extra_total,
        "tender_premium_pct": tender_premium_pct,
        "tender_amount": premium_amount,
        "above_below": above_below,
        "grand_total": total_bill_amount,
        "net_payable": net_payable,
        "grand_total_words": number_to_words(int(total_bill_amount)),
        "net_payable_words": number_to_words(int(net_payable)),
        "generated_at": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "has_extra_items": len(doc.extraItems) > 0,
    }
