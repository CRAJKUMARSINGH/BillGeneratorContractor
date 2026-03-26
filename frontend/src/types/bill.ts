// Bill domain types — aligned to engine/model/document.py
// Reused from Git4, Supabase fields removed

export interface BillItem {
  id: string;
  serial_no: string;
  description: string;
  unit: string;
  qty_since_last_bill: number;
  qty_to_date: number;
  rate: number;
  amount_to_date: number;       // computed: qty_to_date * rate
  amount_since_previous: number; // computed: qty_since_last_bill * rate
  remarks: string;
  sort_order: number;
}

export interface BillHeader {
  agreement_number: string;
  work_name: string;
  contractor_name: string;
  voucher_number: string;
  bill_date: string;
  serial_number: string;
  work_order_reference: string;
  tender_premium_percentage: number;
  premium_type: 'above' | 'below';
  last_bill_deduction: number;
  commencement_date: string;
  scheduled_completion_date: string;
  actual_completion_date: string;
  measurement_date: string;
}

export interface BillSummary {
  grand_total: number;
  premium_amount: number;
  total_with_premium: number;
  net_payable: number;
}

export function computeItem(item: BillItem): BillItem {
  return {
    ...item,
    amount_since_previous: item.qty_since_last_bill * item.rate,
    amount_to_date: item.qty_to_date * item.rate,
  };
}

export function computeSummary(
  items: BillItem[],
  premiumPct: number,
  premiumType: 'above' | 'below',
  lastBillDeduction: number
): BillSummary {
  const grand_total = items.reduce((s, i) => s + i.amount_since_previous, 0);
  const premium_amount = premiumType === 'above'
    ? grand_total * premiumPct / 100
    : -grand_total * premiumPct / 100;
  const total_with_premium = grand_total + premium_amount;
  const net_payable = total_with_premium - lastBillDeduction;
  return { grand_total, premium_amount, total_with_premium, net_payable };
}

export type ViewMode = 'dashboard' | 'upload' | 'edit' | 'generating' | 'preview';
