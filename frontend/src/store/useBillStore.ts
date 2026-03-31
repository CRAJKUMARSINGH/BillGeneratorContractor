import { create } from 'zustand';
import type { BillItem, BillHeader, ViewMode } from '../types/bill';
import { computeItem } from '../types/bill';
import type { ParsedBillData, JobStatus } from '../lib/api';

interface BillStore {
  viewMode: ViewMode;
  setViewMode: (m: ViewMode) => void;

  // Parsed upload data (raw from API)
  parsedData: ParsedBillData | null;
  setParsedData: (d: ParsedBillData | null) => void;

  // Editable state
  header: Partial<BillHeader>;
  billItems: BillItem[];
  isDirty: boolean;

  setHeader: (h: Partial<BillHeader>) => void;
  patchHeader: (field: keyof BillHeader, value: unknown) => void;
  setBillItems: (items: BillItem[]) => void;
  updateItem: (id: string, field: keyof BillItem, value: unknown) => void;
  addItem: () => void;
  removeItem: (id: string) => void;

  // Generation job
  currentJob: JobStatus | null;
  setCurrentJob: (j: JobStatus | null) => void;
}

function blankItem(order = 0): BillItem {
  return {
    id: crypto.randomUUID(),
    serial_no: String(order + 1),
    description: '',
    unit: '',
    qty_since_last_bill: 0,
    qty_to_date: 0,
    rate: 0,
    amount_to_date: 0,
    amount_since_previous: 0,
    remarks: '',
    sort_order: order,
  };
}

export const useBillStore = create<BillStore>((set) => ({
  viewMode: 'landing',
  setViewMode: (viewMode) => set({ viewMode }),

  parsedData: null,
  setParsedData: (parsedData) => set({ parsedData }),

  header: {
    tender_premium_percentage: 0,
    premium_type: 'above',
    last_bill_deduction: 0,
  },
  billItems: [blankItem()],
  isDirty: false,

  setHeader: (header) => set({ header, isDirty: true }),
  patchHeader: (field, value) =>
    set((s) => ({ header: { ...s.header, [field]: value }, isDirty: true })),

  setBillItems: (billItems) => set({ billItems, isDirty: true }),

  updateItem: (id, field, value) =>
    set((s) => ({
      isDirty: true,
      billItems: s.billItems.map((item) => {
        if (item.id !== id) return item;
        const numericFields = [
          'qty_since_last_bill', 'qty_to_date', 'rate',
          'amount_to_date', 'amount_since_previous', 'sort_order',
        ];
        const coerced = numericFields.includes(field as string)
          ? parseFloat(String(value)) || 0
          : value;
        return computeItem({ ...item, [field]: coerced });
      }),
    })),

  addItem: () =>
    set((s) => ({
      isDirty: true,
      billItems: [...s.billItems, blankItem(s.billItems.length)],
    })),

  removeItem: (id) =>
    set((s) => ({
      isDirty: true,
      billItems: s.billItems
        .filter((i) => i.id !== id)
        .map((i, idx) => ({ ...i, sort_order: idx })),
    })),

  currentJob: null,
  setCurrentJob: (currentJob) => set({ currentJob }),
}));

export { blankItem };
