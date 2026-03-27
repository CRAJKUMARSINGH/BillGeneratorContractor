import { useRef, useEffect, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
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
  { key: 'serial_no',            label: 'S.No',          width: 'w-14' },
  { key: 'description',          label: 'Description',   width: 'min-w-[200px]' },
  { key: 'unit',                 label: 'Unit',          width: 'w-20' },
  { key: 'qty_since_last_bill',  label: 'Qty Since Last', numeric: true, width: 'w-28' },
  { key: 'qty_to_date',          label: 'Qty To Date',   numeric: true, width: 'w-28' },
  { key: 'rate',                 label: 'Rate (₹)',      numeric: true, width: 'w-28' },
  { key: 'amount_to_date',       label: 'Amt To Date',   numeric: true, computed: true, width: 'w-32' },
  { key: 'amount_since_previous',label: 'Amt Since Prev',numeric: true, computed: true, width: 'w-32' },
  { key: 'remarks',              label: 'Remarks',       width: 'w-32' },
];

const EDITABLE_FIELDS: EditableField[] = [
  'serial_no', 'description', 'unit',
  'qty_since_last_bill', 'qty_to_date', 'rate', 'remarks',
];

interface CellPos { rowId: string; field: EditableField }

export default function EditableTable() {
  const { billItems, updateItem, addItem, removeItem } = useBillStore();
  const [editing, setEditing] = useState<CellPos | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

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
      else { addItem(); setTimeout(() => setEditing({ rowId: billItems[billItems.length - 1]?.id ?? rowId, field: EDITABLE_FIELDS[0] }), 50); }
    }
  };

  const grandTotal = billItems.reduce((s, i) => s + i.amount_since_previous, 0);

  return (
    <div className="glass rounded-2xl overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest">Bill Items</p>
        <button onClick={addItem} className="btn-primary py-1.5 text-xs">
          <Plus size={14} /> Add Row
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
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
              <tr
                key={item.id}
                className={`border-b border-white/[0.04] transition-colors
                  ${rowIdx % 2 === 0 ? '' : 'bg-white/[0.015]'}
                  hover:bg-white/[0.04]`}
              >
                {COLUMNS.map((col) => {
                  const isEditing = editing?.rowId === item.id && editing?.field === col.key;
                  const val = item[col.key as keyof BillItem];
                  const display = typeof val === 'number' ? val.toFixed(2) : String(val ?? '');

                  if (col.computed) {
                    return (
                      <td key={col.key} className={`table-cell py-2 text-right text-slate-500 bg-white/[0.02]`}>
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
                            if (e.key === 'Enter') { setEditing(null); }
                            if (e.key === 'Tab') { e.preventDefault(); navigate(item.id, col.key as EditableField, e.shiftKey); }
                            if (e.key === 'Escape') setEditing(null);
                          }}
                          className="w-full bg-accent-500/10 border border-accent-500/50 rounded px-2 py-1.5
                                     text-sm text-white focus:outline-none focus:ring-1 focus:ring-accent-500
                                     text-right"
                        />
                      ) : (
                        <div className={`px-2 py-2 text-sm cursor-text rounded hover:bg-white/[0.04] transition-colors
                          ${col.numeric ? 'text-right' : ''}
                          ${!display || display === '0.00' ? 'text-slate-600' : 'text-slate-200'}`}
                        >
                          {col.numeric && display !== '0.00' ? display : (display || '—')}
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
            ))}
          </tbody>

          <tfoot>
            <tr className="border-t border-white/[0.10] bg-white/[0.03]">
              <td colSpan={7} className="table-cell py-3 text-right font-semibold text-slate-300">
                Grand Total
              </td>
              <td className="table-cell py-3 text-right font-bold text-white">
                ₹{grandTotal.toFixed(2)}
              </td>
              <td colSpan={2} />
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
