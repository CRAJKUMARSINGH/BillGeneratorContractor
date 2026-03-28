// ─── Document Workflow States ────────────────────────────────────────────────
export type DocumentStatus =
  | 'uploaded'
  | 'parsed'
  | 'input_edited'
  | 'calculated'
  | 'final_edited'
  | 'print_ready'
  | 'exported';

// Legacy alias kept for DB compatibility
export type BillStatus = 'draft' | 'preview' | 'finalized';

// ─── Core Data Models ─────────────────────────────────────────────────────────
export interface BillItem {
  id: string;
  bill_id: string;
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

export interface Bill {
  id: string;
  user_id: string;
  voucher_number: string;
  bill_date: string;
  contractor_name: string;
  work_name: string;
  serial_number: string;
  previous_bill_number: string;
  previous_bill_date: string | null;
  work_order_reference: string;
  agreement_number: string;
  commencement_date: string | null;
  scheduled_start_date: string | null;
  scheduled_completion_date: string | null;
  actual_completion_date: string | null;
  measurement_date: string | null;
  tender_premium_percentage: number;
  last_bill_deduction: number;
  status: BillStatus;
  workflow_status: DocumentStatus;
  source: 'manual' | 'excel' | 'hybrid';
  created_at: string;
  updated_at: string;
  items?: BillItem[];
}

// ─── Calculation Engine Types ─────────────────────────────────────────────────
export interface BillSummary {
  grand_total: number;
  premium_amount: number;
  total_with_premium: number;
  net_payable: number;
}

export function computeSummary(bill: Partial<Bill>): BillSummary {
  const items = bill.items ?? [];
  const grand_total = items.reduce((s, i) => s + i.amount_since_previous, 0);
  const premium_amount = (grand_total * (bill.tender_premium_percentage ?? 0)) / 100;
  const total_with_premium = grand_total + premium_amount;
  const net_payable = total_with_premium - (bill.last_bill_deduction ?? 0);
  return { grand_total, premium_amount, total_with_premium, net_payable };
}

export function computeItem(item: BillItem): BillItem {
  return {
    ...item,
    amount_since_previous: item.qty_since_last_bill * item.rate,
    amount_to_date: item.qty_to_date * item.rate,
  };
}

// ─── Excel Ingestion Types ────────────────────────────────────────────────────
export interface ParsedExcelRow {
  serial_no: string;
  description: string;
  unit: string;
  qty_since_last_bill: number;
  qty_to_date: number;
  rate: number;
  remarks: string;
}

export interface ExcelParseResult {
  header: Partial<Bill>;
  rows: ParsedExcelRow[];
  confidence: number;        // 0–1
  warnings: string[];
  raw_sheet_names: string[];
}

// ─── UI State ─────────────────────────────────────────────────────────────────
export type ViewMode = 'dashboard' | 'edit' | 'preview' | 'pdf';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
}
