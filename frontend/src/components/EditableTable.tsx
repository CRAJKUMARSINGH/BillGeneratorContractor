/**
 * EditableTable — Unified Version for Mode 1, 2, and 3.
 * Supports confidence-based highlighting for OCR (Mode 3).
 * Real-time calculation and manual editing.
 */
import { useRef, useEffect, useState, memo } from 'react';
import { Plus, Trash2, AlertTriangle, Info, ArrowDownAz, Merge } from 'lucide-react';
import type { BillItem } from '../types/bill';
import { useBillStore } from '../store/useBillStore';

type EditableField = keyof Pick<
  BillItem,
  'description' | 'unit' | 'quantitySince' | 'quantityUpto' | 'rate' | 'remarks' | 'itemNo'
>;

const COLUMNS: {
  key: EditableField | 'amount' | 'confidence';
  label: string;
  numeric?: boolean;
  computed?: boolean;
  width?: string;
}[] = [
  { key: 'itemNo',                label: 'Item No',        width: 'w-20' },
  { key: 'description',           label: 'Description',    width: 'min-w-[320px]' },
  { key: 'unit',                  label: 'Unit',           width: 'w-20' },
  { key: 'quantitySince',         label: 'Qty Since Prev', numeric: true, width: 'w-28' },
  { key: 'quantityUpto',          label: 'Qty To Date',    numeric: true, width: 'w-28' },
  { key: 'rate',                  label: 'Rate (₹)',       numeric: true, width: 'w-28' },
  { key: 'amount',                label: 'Amount',         numeric: true, computed: true, width: 'w-32' },
  { key: 'remarks',               label: 'Remarks',        width: 'w-32' },
];

const EDITABLE_FIELDS: EditableField[] = [
  'itemNo', 'description', 'unit', 'quantitySince', 'quantityUpto', 'rate', 'remarks',
];

interface CellPos { rowId: string; field: EditableField }

const TableRow = memo(({ 
  item, 
  rowIdx, 
  editing, 
  setEditing, 
  updateItem, 
  removeItem, 
  navigate,
  inputRef,
  isDuplicate
}: {
  item: BillItem;
  rowIdx: number;
  editing: CellPos | null;
  setEditing: (pos: CellPos | null) => void;
  updateItem: any;
  removeItem: any;
  navigate: any;
  inputRef: React.RefObject<HTMLInputElement>;
  isDuplicate: boolean;
}) => {
  const isLowConfidence = item.confidence < 0.7;
  
  return (
    <tr
      className={`border-b border-white/[0.04] transition-all duration-200
        ${rowIdx % 2 === 0 ? '' : 'bg-white/[0.015]'}
        hover:bg-white/[0.05]
        ${isLowConfidence ? 'bg-red-500/5' : ''}
        ${isDuplicate ? 'bg-amber-500/5' : ''}`}
    >
      {COLUMNS.map((col) => {
        const isEditing = editing?.rowId === item.id && editing?.field === col.key;
        const val = item[col.key as keyof BillItem];
        const display = typeof val === 'number' ? val.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : String(val ?? '');

        if (col.computed) {
          return (
            <td key={col.key} className="table-cell py-2 text-right text-slate-500 bg-white/[0.02]">
               ₹{display}
            </td>
          );
        }

        return (
          <td
            key={col.key}
            className={`table-cell py-0 ${col.numeric ? 'text-right' : ''}`}
            onClick={() => setEditing({ rowId: item.id, field: col.key as EditableField })}
          >
            {isEditing ? (
              <input
                ref={inputRef}
                type={col.numeric ? 'number' : 'text'}
                step={col.numeric ? '0.01' : undefined}
                defaultValue={val as string | number}
                onBlur={(e) => {
                  updateItem(item.id, col.key as EditableField, e.target.value);
                  setEditing(null);
                }}
                onChange={(e) => updateItem(item.id, col.key as EditableField, e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') setEditing(null);
                  if (e.key === 'Tab') { 
                    e.preventDefault(); 
                    navigate(item.id, col.key as EditableField, e.shiftKey); 
                  }
                  if (e.key === 'Escape') setEditing(null);
                }}
                className="w-full bg-accent-500/10 border border-accent-500/50 rounded px-2 py-1.5
                           text-sm text-white focus:outline-none focus:ring-1 focus:ring-accent-500 text-right"
              />
            ) : (
              <div className={`px-2 py-2 text-sm cursor-text rounded hover:bg-white/[0.04] transition-colors
                ${col.numeric ? 'text-right' : ''}
                ${!display || display === '0.00' ? 'text-slate-600' : 'text-slate-200'}
                ${isLowConfidence && col.key === 'description' ? 'text-red-400' : ''}`}
              >
                {display || '—'}
                {col.key === 'itemNo' && isDuplicate && (
                  <div className="text-[10px] text-amber-400 mt-0.5 flex items-center gap-1">
                    <AlertTriangle size={10} /> Duplicate
                  </div>
                )}
                {col.key === 'description' && item.aiNote && (
                  <div className="text-[10px] text-accent-400 mt-0.5 flex items-center gap-1">
                    <Info size={10} /> {item.aiNote}
                  </div>
                )}
              </div>
            )}
          </td>
        );
      })}

      <td className="table-cell py-2 text-center">
        <button
          onClick={() => removeItem(item.id)}
          className="text-slate-600 hover:text-red-400 transition-colors p-1 rounded"
        >
          <Trash2 size={14} />
        </button>
      </td>
    </tr>
  );
});

export default function EditableTable() {
  const { billItems, parsedData, updateItem, addItem, removeItem, sortItems, mergeDuplicates } = useBillStore();
  const [editing, setEditing] = useState<CellPos | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Duplicate detection
  const duplicateCodes = new Set(
    billItems
      .map(i => i.itemNo.trim().toLowerCase())
      .filter((code, index, array) => code && array.indexOf(code) !== index)
  );

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

  const grandTotal = billItems.reduce((s, i) => s + i.amount, 0);

  return (
    <div className="glass rounded-2xl border border-white/[0.08]">
      {parsedData?.anomaly_warnings && parsedData.anomaly_warnings.length > 0 && (
        <div className="bg-red-500/10 border-b border-red-500/20 px-5 py-3">
          <div className="flex items-center gap-2 text-red-400 mb-1">
            <AlertTriangle size={16} />
            <h3 className="text-sm font-semibold">AI Anomaly Warning: Dirty Scan Detected</h3>
          </div>
          <ul className="list-disc list-inside text-xs text-red-400/80 space-y-1 ml-6">
            {parsedData.anomaly_warnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest">
          Bill Items ({billItems.length})
        </p>
        <div className="flex items-center gap-2">
            <button 
              onClick={sortItems} 
              className="px-3 py-1.5 text-[11px] font-medium text-slate-400 hover:text-white hover:bg-white/10 rounded-lg flex items-center gap-1.5 transition-all"
              title="Sort hierarchically by Item Code"
            >
                <ArrowDownAz size={14} /> Smart Sort
            </button>
            <button 
              onClick={mergeDuplicates} 
              className="px-3 py-1.5 text-[11px] font-medium text-slate-400 hover:text-white hover:bg-white/10 rounded-lg flex items-center gap-1.5 transition-all"
              title="Merge rows with identical Item Codes"
            >
                <Merge size={14} /> Merge Duplicates
            </button>
            <div className="w-px h-4 bg-white/10 mx-1" />
            <button onClick={addItem} className="btn-primary py-1.5 px-4 text-xs flex items-center gap-1.5 shadow-lg shadow-accent-500/10">
                <Plus size={14} /> Add Row
            </button>
        </div>
      </div>

      <div className="overflow-x-auto w-full">
        <table className="w-full min-w-[900px]">
          <thead>
            <tr className="border-b border-white/[0.06]">
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  className={`table-header py-3 ${col.width ?? ''} ${col.numeric ? 'text-right' : 'text-left'} ${col.computed ? 'text-slate-500' : ''}`}
                >
                  {col.label}
                </th>
              ))}
              <th className="table-header py-3 w-10 text-center">×</th>
            </tr>
          </thead>

          <tbody>
            {billItems.map((item, rowIdx) => (
              <TableRow
                key={item.id}
                item={item}
                rowIdx={rowIdx}
                editing={editing}
                setEditing={setEditing}
                updateItem={updateItem}
                removeItem={removeItem}
                navigate={navigate}
                inputRef={inputRef}
                isDuplicate={duplicateCodes.has(item.itemNo.trim().toLowerCase())}
              />
            ))}
          </tbody>

          <tfoot>
            <tr className="border-t border-white/[0.10] bg-white/[0.03]">
              <td colSpan={6} className="table-cell py-3 text-right font-semibold text-slate-300">
                Grand Total
              </td>
              <td className="table-cell py-3 text-right font-bold text-white">
                ₹{grandTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </td>
              <td colSpan={2} />
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
