/**
 * EditableTable — reused from Bill-Contractor-Git4.
 * Supabase removed. Field names aligned to engine BillItem model.
 * Part-rate detection preserved from BillGeneratorUnified.
 */
import { useRef, useEffect, useState } from 'react';
import { Plus, Trash2, AlertTriangle } from 'lucide-react';
import type { BillItem } from '../types/bill';
import { useBillStore } from '../store/useBillStore';

type EditableField = keyof Pick<
  BillItem,
  'serial_no' | 'description' | 'unit' |
  'qty_since_last_bill' | 'qty_to_date' | 'rate' | 'remarks'
>;

const COLUMNS: {
  key: EditableField | 'amount_to_date' | 'amount_since_previous';
  label: string;
  numeric?: boolean;
  computed?: boolean;
  width?: string;
}[] = [
  { key: 'serial_no',             label: 'S.No',           width: 'w-14' },
  { key: 'description',           label: 'Description',    width: 'min-w-[220px]' },
  { key: 'unit',                  label: 'Unit',           width: 'w-20' },
  { key: 'qty_since_last_bill',   label: 'Qty Since Last', numeric: true, width: 'w-28' },
  { key: 'qty_to_date',           label: 'Qty To Date',    numeric: true, width: 'w-28' },
  { key: 'rate',                  label: 'Rate (₹)',       numeric: true, width: 'w-28' },
  { key: 'amount_to_date',        label: 'Amt To Date',    numeric: true, computed: true, width: 'w-32' },
  { key: 'amount_since_previous', label: 'Amt Since Prev', numeric: true, computed: true, width: 'w-32' },
  { key: 'remarks',               label: 'Remarks',        width: 'w-32' },
];

const EDITABLE_FIELDS: EditableField[] = [
  'serial_no', 'description', 'unit',
  'qty_since_last_bill', 'qty_to_date', 'rate', 'remarks',
];

interface CellPos { rowId: string; field: EditableField }

// Part-rate detection: rate reduced vs original (tolerance 0.01)
function isPartRate(item: BillItem, originalRate?: number): boolean {
  if (!originalRate || originalRate <= 0) return false;
  return item.rate < originalRate - 0.01;
}

export default function EditableTable() {
  const { billItems, parsedData, updateItem, addItem, removeItem } = useBillStore();
  const [editing, setEditing] = useState<CellPos | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Build original rate map from parsed data for part-rate detection
  const originalRates = new Map<string, number>();
  if (parsedData) {
    parsedData.billItems.forEach((apiItem, i) => {
      const item = billItems[i];
      if (item) originalRates.set(item.id, apiItem.rate);
    });
  }

  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  const navigate = (rowId: string, field: EditableField, shift: boolean) => {
    const fi = EDITABLE_FIELDS.indexOf(field);
    const ri = billItems.findIndex((i) => i.id === rowId);
    if (shift) {
      if (fi > 0) setEditing({ rowId, field: EDITABLE_FIELDS[fi - 1] });
      else if (ri > 0) setEditing({ rowId: billItems[ri - 1].id, field: EDITABLE_FIELDS[EDITABLE_FIELDS.length - 1] });
    } else {
      if (fi < EDITABLE_FIELDS.length - 1) setEditing({ rowId, field: EDITABLE_FIELDS[fi + 1] });
      else if (ri < billItems.length - 1) setEditing({ rowId: billItems[ri + 1].id, field: EDITABLE_FIELDS[0] });
      else { addItem(); }
    }
  };

  const grandTotal = billItems.reduce((s, i) => s + i.amount_since_previous, 0);

  return (
    <div className="glass-card overflow-hidden">
      {parsedData?.anomaly_warnings && parsedData.anomaly_warnings.length > 0 && (
        <div className="bg-red-500/10 border-b border-red-500/20 px-6 py-4">
          <div className="flex items-center gap-4 text-red-400 mb-2">
            <div className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center">
              <AlertTriangle size={18} />
            </div>
            <div>
              <h3 className="text-sm font-bold uppercase tracking-widest leading-none">AI Anomaly Warning</h3>
              <p className="hindi text-[10px] text-red-500/60 mt-1 uppercase tracking-tighter">दस्तावेज़ में विसंगति पाई गई</p>
            </div>
          </div>
          <ul className="list-disc list-inside text-[11px] text-red-400/80 space-y-1 ml-12">
            {parsedData.anomaly_warnings.map((warning, idx) => (
              <li key={idx} className="font-medium">{warning}</li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-gradient-to-r from-primary-400/10 to-transparent">
        <div>
          <p className="text-xs font-bold text-white uppercase tracking-[0.2em]">
            Bill Items ({billItems.length})
          </p>
          <p className="hindi text-[10px] text-gold-500 font-medium uppercase tracking-tighter">बिल मदों की सूची</p>
        </div>
        <button 
          onClick={addItem} 
          className="px-4 py-2 rounded-xl bg-primary-400/20 border border-primary-400/30 text-primary-300 hover:bg-primary-400 hover:text-white transition-all text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 group"
        >
          <Plus size={14} className="group-hover:scale-125 transition-transform" /> Add New Row
        </button>
      </div>

      <div className="overflow-x-auto selection:bg-gold-500/30">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-indigo-500/20 bg-indigo-500/5">
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest ${col.numeric ? 'text-right' : ''} ${col.computed ? 'opacity-50' : ''}`}
                >
                  <div className="flex flex-col">
                    <span>{col.label}</span>
                    {col.computed && <span className="text-[8px] text-indigo-400 tracking-tighter">Computed</span>}
                  </div>
                </th>
              ))}
              <th className="px-4 py-4 w-12 text-center opacity-30 text-[10px]">Actions</th>
            </tr>
          </thead>

          <tbody>
            {billItems.map((item, rowIdx) => {
              const partRate = isPartRate(item, originalRates.get(item.id));
              return (
                <tr
                  key={item.id}
                  className={`group transition-all duration-200 border-b border-white/[0.03]
                    ${rowIdx % 2 === 0 ? '' : 'bg-white/[0.01]'}
                    hover:bg-primary-400/[0.04]
                    ${partRate ? 'bg-yellow-500/[0.03]' : ''}`}
                >
                  {COLUMNS.map((col) => {
                    const isEditing = editing?.rowId === item.id && editing?.field === col.key;
                    const val = item[col.key as keyof BillItem];
                    const display = typeof val === 'number' ? val.toFixed(2) : String(val ?? '');

                    if (col.computed) {
                      return (
                        <td key={col.key} className="px-4 py-4 text-right font-mono text-sm text-indigo-400/80 bg-indigo-500/[0.01]">
                          <span className="text-xs mr-0.5">₹</span>{display}
                        </td>
                      );
                    }

                    const isRateCol = col.key === 'rate';
                    const isEmpty = !display || display === '0.00' || display === '0';

                    return (
                      <td
                        key={col.key}
                        className={`px-4 py-4 relative group/cell ${col.numeric ? 'text-right' : ''}`}
                        onClick={() => setEditing({ rowId: item.id, field: col.key as EditableField })}
                      >
                        {isEditing ? (
                          <div className="absolute inset-x-1 inset-y-1 z-10 flex items-center">
                            <input
                              ref={inputRef}
                              type={col.numeric ? 'number' : 'text'}
                              step={col.numeric ? '0.01' : undefined}
                              defaultValue={val as string | number}
                              onBlur={(e) => {
                                updateItem(item.id, col.key as EditableField, e.target.value);
                                setEditing(null);
                              }}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') setEditing(null);
                                if (e.key === 'Tab') { e.preventDefault(); navigate(item.id, col.key as EditableField, e.shiftKey); }
                                if (e.key === 'Escape') setEditing(null);
                              }}
                              className="w-full h-full bg-surface-950 border border-gold-500/50 rounded-lg px-2 py-1
                                         text-sm text-white focus:outline-none focus:ring-2 focus:ring-gold-500/30 
                                         shadow-[0_0_15px_rgba(245,158,11,0.1)] transition-all"
                            />
                          </div>
                        ) : (
                          <div className={`text-sm transition-colors relative
                            ${col.numeric ? 'font-mono text-right' : 'font-sans'}
                            ${isEmpty ? 'text-slate-600' : 'text-slate-200'}
                            ${isRateCol && partRate ? 'text-gold-400 font-bold' : ''}
                            group-hover/cell:text-gold-400 cursor-text py-1`}
                          >
                            {col.numeric && display !== '0.00' ? display : (display || '—')}
                            {isRateCol && partRate && (
                              <div className="absolute -top-3 right-0 text-[8px] font-bold text-gold-500 uppercase tracking-tighter opacity-70">
                                Part Rate
                              </div>
                            )}
                          </div>
                        )}
                      </td>
                    );
                  })}

                  <td className="px-4 py-4 text-center">
                    <button
                      onClick={() => removeItem(item.id)}
                      className="p-2 rounded-xl bg-red-500/5 text-red-500/30 hover:bg-red-500 hover:text-white transition-all opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>

          <tfoot>
            <tr className="bg-gradient-to-r from-primary-500/20 to-indigo-500/20">
              <td colSpan={7} className="px-6 py-8 text-right">
                <div className="inline-flex flex-col items-end">
                   <div className="flex items-center gap-3 mb-1">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Measurement Total</span>
                      <span className="hindi text-[10px] text-gold-500/50 tracking-tighter">कुल माप मूल्य</span>
                   </div>
                   <div className="text-3xl font-heading font-extrabold text-white tracking-tight flex items-center gap-2">
                     <span className="text-lg font-bold text-slate-400">₹</span>
                     {grandTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                   </div>
                </div>
              </td>
              <td colSpan={2} />
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
