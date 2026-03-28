import { create } from "zustand";
import type { BillData, GenerateOptions } from "@/hooks/use-bills";

interface AppState {
  billData: BillData | null;
  setBillData: (data: BillData | null) => void;
  updateTitleData: (key: string, value: string) => void;
  updateBillItem: (index: number, field: string, value: any) => void;
  updateExtraItem: (index: number, field: string, value: any) => void;
  
  generateOptions: GenerateOptions;
  setGenerateOptions: (options: Partial<GenerateOptions>) => void;
}

export const useStore = create<AppState>((set) => ({
  billData: null,
  setBillData: (data) => set({ billData: data }),
  
  updateTitleData: (key, value) => set((state) => {
    if (!state.billData) return state;
    return {
      billData: {
        ...state.billData,
        titleData: { ...state.billData.titleData, [key]: value }
      }
    };
  }),
  
  updateBillItem: (index, field, value) => set((state) => {
    if (!state.billData) return state;
    const items = [...state.billData.billItems];
    items[index] = { ...items[index], [field]: value };
    
    // Recalculate amounts if quantity or rate changed
    if (field === 'quantity' || field === 'rate') {
      const q = Number(items[index].quantity || 0);
      const r = Number(items[index].rate || 0);
      items[index].amount = q * r;
    }
    
    // Recalculate total
    const totalAmount = items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0) + 
      state.billData.extraItems.reduce((sum, item) => sum + (Number(item.amount) || 0), 0);
      
    return { billData: { ...state.billData, billItems: items, totalAmount } };
  }),
  
  updateExtraItem: (index, field, value) => set((state) => {
    if (!state.billData) return state;
    const items = [...state.billData.extraItems];
    items[index] = { ...items[index], [field]: value };
    
    // Recalculate amounts if quantity or rate changed
    if (field === 'quantity' || field === 'rate') {
      const q = Number(items[index].quantity || 0);
      const r = Number(items[index].rate || 0);
      items[index].amount = q * r;
    }
    
    // Recalculate total
    const totalAmount = state.billData.billItems.reduce((sum, item) => sum + (Number(item.amount) || 0), 0) + 
      items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0);
      
    return { billData: { ...state.billData, extraItems: items, totalAmount } };
  }),
  
  generateOptions: {
    generatePdf: true,
    generateHtml: true,
    generateWord: false
  },
  setGenerateOptions: (options) => set((state) => ({
    generateOptions: { ...state.generateOptions, ...options }
  }))
}));
