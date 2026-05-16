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
  sortItems: () => void;
  mergeDuplicates: () => void;

  // Generation job
  currentJob: JobStatus | null;
  setCurrentJob: (j: JobStatus | null) => void;
}

function blankItem(): BillItem {
  return {
    id: crypto.randomUUID(),
    itemNo: '',
    description: '',
    unit: '',
    quantitySince: 0,
    quantityUpto: 0,
    quantity: 0,
    rate: 0,
    amount: 0,
    confidence: 1.0,
    remarks: '',
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
    set((s) => {
      const index = s.billItems.findIndex((item) => item.id === id);
      if (index === -1) return {};

      const item = s.billItems[index];
      const numericFields = [
        'quantitySince', 'quantityUpto', 'quantity', 'rate', 'amount', 'confidence'
      ];
      const coerced = numericFields.includes(field as string)
        ? parseFloat(String(value)) || 0
        : value;

      const updatedItem = computeItem({ ...item, [field]: coerced });
      const newBillItems = [...s.billItems];
      newBillItems[index] = updatedItem;

      return {
        billItems: newBillItems,
        isDirty: true,
      };
    }),

  addItem: () =>
    set((s) => ({
      isDirty: true,
      billItems: [...s.billItems, blankItem()],
    })),

  removeItem: (id) =>
    set((s) => ({
      isDirty: true,
      billItems: s.billItems.filter((i) => i.id !== id),
    })),

  sortItems: () =>
    set((s) => {
      const sorted = [...s.billItems].sort((a, b) => {
        const parseCode = (c: string) => c.split('.').map(p => {
          const m = p.match(/(\d+)([a-z]*)/);
          return m ? [parseInt(m[1]), m[2]] : [p];
        }).flat();
        
        const ak = parseCode(a.itemNo || 'zzzz');
        const bk = parseCode(b.itemNo || 'zzzz');
        
        for (let i = 0; i < Math.max(ak.length, bk.length); i++) {
          if (ak[i] === undefined) return -1;
          if (bk[i] === undefined) return 1;
          if (ak[i] < bk[i]) return -1;
          if (ak[i] > bk[i]) return 1;
        }
        return 0;
      });
      return { billItems: sorted, isDirty: true };
    }),

  mergeDuplicates: () =>
    set((s) => {
      const map: Record<string, BillItem> = {};
      const uniqueItems: BillItem[] = [];
      
      s.billItems.forEach(item => {
        const code = item.itemNo.trim().toLowerCase();
        if (code && map[code]) {
          map[code].quantityUpto += item.quantityUpto;
          map[code].quantitySince += item.quantitySince;
          map[code].amount = map[code].quantityUpto * map[code].rate;
          map[code].aiNote = `Merged duplicate: ${code}`;
        } else {
          const newItem = { ...item };
          if (code) map[code] = newItem;
          uniqueItems.push(newItem);
        }
      });
      
      return { billItems: uniqueItems, isDirty: true };
    }),

  currentJob: null,
  setCurrentJob: (currentJob) => set({ currentJob }),
}));

export { blankItem };
