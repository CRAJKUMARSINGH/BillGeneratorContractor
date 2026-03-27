import { create } from 'zustand';
import type { Bill, BillItem, ViewMode } from '../types/bill';
import { computeItem } from '../types/bill';

interface BillStore {
  // View
  viewMode: ViewMode;
  setViewMode: (m: ViewMode) => void;

  // Current bill being edited
  currentBill: Partial<Bill>;
  billItems: BillItem[];
  isDirty: boolean;

  setCurrentBill: (bill: Partial<Bill>) => void;
  patchBill: (field: keyof Bill, value: unknown) => void;
  setBillItems: (items: BillItem[]) => void;
  updateItem: (id: string, field: keyof BillItem, value: unknown) => void;
  addItem: () => void;
  removeItem: (id: string) => void;
  reorderItems: (items: BillItem[]) => void;
  resetDirty: () => void;

  // Upload state
  uploadProgress: number | null;
  setUploadProgress: (p: number | null) => void;
}

const BLANK_BILL: Partial<Bill> = {
  voucher_number: '',
  bill_date: new Date().toISOString().split('T')[0],
  contractor_name: '',
  work_name: '',
  serial_number: '',
  previous_bill_number: '',
  previous_bill_date: null,
  work_order_reference: '',
  agreement_number: '',
  commencement_date: null,
  scheduled_start_date: null,
  scheduled_completion_date: null,
  actual_completion_date: null,
  measurement_date: null,
  tender_premium_percentage: 0,
  last_bill_deduction: 0,
  status: 'draft',
  workflow_status: 'input_edited',
  source: 'manual',
};

function blankItem(billId = '', order = 0): BillItem {
  return {
    id: crypto.randomUUID(),
    bill_id: billId,
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

export const useBillStore = create<BillStore>((set, get) => ({
  viewMode: 'dashboard',
  setViewMode: (viewMode) => set({ viewMode }),

  currentBill: { ...BLANK_BILL },
  billItems: [blankItem()],
  isDirty: false,

  setCurrentBill: (bill) =>
    set({ currentBill: bill, isDirty: false }),

  patchBill: (field, value) =>
    set((s) => ({ currentBill: { ...s.currentBill, [field]: value }, isDirty: true })),

  setBillItems: (billItems) =>
    set({ billItems, isDirty: true }),

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
      billItems: [
        ...s.billItems,
        blankItem(s.currentBill.id, s.billItems.length),
      ],
    })),

  removeItem: (id) =>
    set((s) => ({
      isDirty: true,
      billItems: s.billItems
        .filter((i) => i.id !== id)
        .map((i, idx) => ({ ...i, sort_order: idx })),
    })),

  reorderItems: (billItems) => set({ billItems, isDirty: true }),

  resetDirty: () => set({ isDirty: false }),

  uploadProgress: null,
  setUploadProgress: (uploadProgress) => set({ uploadProgress }),
}));

export { BLANK_BILL, blankItem };
