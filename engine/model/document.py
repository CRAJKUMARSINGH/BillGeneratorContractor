"""
Unified Document Model
Canonical Python dataclasses for the bill domain.
Derived from Git4 TypeScript types (bill.ts) — translated, not redesigned.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class BillItem:
    serial_no: str = ""
    description: str = ""
    unit: str = ""
    quantity_since_last: Any = ""   # blank when rate=0
    quantity_upto_date: Any = ""
    rate: Any = ""
    amount: Any = ""
    amount_previous: Any = ""
    remark: str = ""
    bold: bool = False
    underline: bool = False
    is_divider: bool = False


@dataclass
class ExtraItem:
    serial_no: str = ""
    bsr: str = ""
    description: str = ""
    unit: str = ""
    quantity: Any = ""
    rate: Any = ""
    amount: Any = ""
    remark: str = ""
    is_divider: bool = False


@dataclass
class BillHeader:
    """Key-value pairs from the Title / Work Order sheet header rows."""
    raw: List[List[Any]] = field(default_factory=list)   # first_page.html uses data.header
    agreement_no: str = ""
    name_of_work: str = ""
    name_of_firm: str = ""
    date_commencement: str = ""
    date_completion: str = ""
    actual_completion: str = ""
    work_order_amount: float = 0.0


@dataclass
class BillSummary:
    grand_total: float = 0.0
    premium: dict = field(default_factory=lambda: {"percent": 0.0, "type": "above", "amount": 0.0})
    payable: float = 0.0
    last_bill_amount: float = 0.0
    net_payable: float = 0.0
    extra_items_sum: float = 0.0


@dataclass
class BillDocument:
    """
    Top-level container passed to all Jinja2 templates as `data`.
    Matches the exact variable names used in templates/v1/*.html
    """
    header: List[List[Any]] = field(default_factory=list)   # data.header
    items: List[dict] = field(default_factory=list)          # data["items"]
    totals: dict = field(default_factory=dict)               # data.totals
    # deviation statement
    deviation_items: List[dict] = field(default_factory=list)
    deviation_summary: dict = field(default_factory=dict)
    # extra items
    extra_items: List[dict] = field(default_factory=list)
    # note sheet extras
    agreement_no: str = ""
    name_of_work: str = ""
    name_of_firm: str = ""
    date_commencement: str = ""
    date_completion: str = ""
    actual_completion: str = ""
    work_order_amount: float = 0.0
    extra_item_amount: float = 0.0
    notes: List[str] = field(default_factory=list)

    def to_template_dict(self) -> dict:
        """Return dict that Jinja2 templates receive as `data`."""
        from calculation.bill_processor import number_to_words
        payable = self.totals.get("payable", 0) or 0
        net_payable = self.totals.get("net_payable", payable) or payable
        cheque_amount = int(round(payable - (
            round(payable * 0.10) +
            round(payable * 0.02) +
            (round(payable * 0.02 + 0.5) // 2 * 2) +
            round(payable * 0.01)
        )))
        return {
            "header": self.header,
            "items": self.items,
            "totals": self.totals,
            "deviation_items": self.deviation_items,
            "summary": self.deviation_summary,
            "extra_items": self.extra_items,
            "agreement_no": self.agreement_no,
            "name_of_work": self.name_of_work,
            "name_of_firm": self.name_of_firm,
            "date_commencement": self.date_commencement,
            "date_completion": self.date_completion,
            "actual_completion": self.actual_completion,
            "work_order_amount": self.work_order_amount,
            "extra_item_amount": self.extra_item_amount,
            "notes": self.notes,
            # certificate_iii.html uses these
            "payable_words": number_to_words(int(round(payable))),
            "net_payable_words": number_to_words(int(round(net_payable))),
            "cheque_words": number_to_words(cheque_amount),
            "cheque_amount": cheque_amount,
        }
