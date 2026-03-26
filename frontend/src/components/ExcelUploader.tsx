/**
 * ExcelUploader — sends file to FastAPI /bills/upload.
 * Replaces Git4's client-side xlsx parsing with server-side engine parsing.
 * UI structure preserved from Git4.
 */
import { useRef, useState } from 'react';
import { Upload, FileSpreadsheet, AlertTriangle, CheckCircle, Loader2, X } from 'lucide-react';
import { api } from '../lib/api';
import type { ParsedBillData } from '../lib/api';
import { useBillStore } from '../store/useBillStore';

interface Props {
  onClose: () => void;
  toast: (type: 'success' | 'error' | 'warning', msg: string) => void;
}

export default function ExcelUploader({ onClose, toast }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<ParsedBillData | null>(null);
  const [fileName, setFileName] = useState('');

  const { setParsedData, setBillItems, setHeader, setViewMode } = useBillStore();

  const handleFile = async (file: File) => {
    if (!file.name.match(/\.(xlsx|xls|xlsm)$/i)) {
      toast('error', 'Please upload an Excel file (.xlsx / .xls)');
      return;
    }
    setFileName(file.name);
    setUploading(true);
    try {
      const parsed = await api.uploadExcel(file);
      setResult(parsed);
    } catch (err) {
      toast('error', err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const applyToEditor = () => {
    if (!result) return;

    // Store raw parsed data for part-rate detection
    setParsedData(result);

    // Map API items → store BillItems
    const items = result.billItems.map((api, i) => ({
      id: crypto.randomUUID(),
      serial_no: api.itemNo || String(i + 1),
      description: api.description,
      unit: api.unit,
      qty_since_last_bill: api.quantitySince,
      qty_to_date: api.quantityUpto,
      rate: api.rate,
      amount_to_date: api.quantityUpto * api.rate,
      amount_since_previous: api.quantitySince * api.rate,
      remarks: '',
      sort_order: i,
    }));
    setBillItems(items);

    // Map titleData → header
    const td = result.titleData;
    setHeader({
      agreement_number: td['Agreement No.'] || td['Agreement No'] || '',
      work_name: td['Name of Work'] || td['Name of work'] || '',
      contractor_name: td['Name of Contractor or supplier'] || td['Contractor'] || '',
      voucher_number: td['Cash Book Voucher No.'] || '',
      work_order_reference: td['Reference to work order or Agreement :'] || '',
      tender_premium_percentage: parseFloat(td['TENDER PREMIUM %'] || td['Tender Premium %'] || '0') || 0,
      premium_type: (td['ABOVE'] || td['Above / Below'] || 'above').toLowerCase().includes('below') ? 'below' : 'above',
      last_bill_deduction: parseFloat(td['Amount Paid Vide Last Bill'] || '0') || 0,
      commencement_date: td['Date of written order to commence work :'] || '',
      scheduled_completion_date: td['St. date of completion :'] || '',
      actual_completion_date: td['Date of actual completion of work :'] || '',
      measurement_date: td['Date of measurement :'] || '',
    });

    setViewMode('edit');
    toast('success', `Imported ${items.length} items from "${fileName}"`);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="glass-lg rounded-2xl w-full max-w-lg animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <FileSpreadsheet size={20} className="text-accent-400" />
            <h2 className="font-semibold text-white">Import from Excel</h2>
          </div>
          <button onClick={onClose} className="btn-ghost p-1.5"><X size={18} /></button>
        </div>

        <div className="p-5 space-y-4">
          {/* Drop zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200
              ${dragging ? 'border-accent-500 bg-accent-500/10' : 'border-white/[0.12] hover:border-white/25 hover:bg-white/[0.03]'}`}
          >
            <input ref={fileRef} type="file" accept=".xlsx,.xls,.xlsm" className="hidden"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
            {uploading ? (
              <div className="flex flex-col items-center gap-2">
                <Loader2 size={32} className="text-accent-400 animate-spin" />
                <p className="text-sm text-slate-400">Parsing {fileName} via engine…</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <Upload size={32} className="text-slate-500" />
                <p className="text-sm text-slate-300">Drop Excel file here or click to browse</p>
                <p className="text-xs text-slate-500">.xlsx · .xls · .xlsm</p>
              </div>
            )}
          </div>

          {/* Result */}
          {result && !uploading && (
            <div className="space-y-3 animate-slide-up">
              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: 'Items', value: result.billItems.length },
                  { label: 'Extra Items', value: result.extraItems.length },
                  { label: 'Total (₹)', value: Math.round(result.totalAmount).toLocaleString('en-IN') },
                ].map((s) => (
                  <div key={s.label} className="glass rounded-xl px-3 py-2 text-center">
                    <p className="text-lg font-bold text-white">{s.value}</p>
                    <p className="text-xs text-slate-500">{s.label}</p>
                  </div>
                ))}
              </div>

              {/* Detected header fields */}
              {Object.keys(result.titleData).length > 0 && (
                <div className="glass rounded-xl p-3 space-y-1 max-h-40 overflow-y-auto">
                  <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Detected header</p>
                  {Object.entries(result.titleData).slice(0, 12).map(([k, v]) => v ? (
                    <div key={k} className="flex justify-between text-xs gap-2">
                      <span className="text-slate-500 shrink-0">{k}</span>
                      <span className="text-slate-300 truncate text-right">{v}</span>
                    </div>
                  ) : null)}
                </div>
              )}

              {/* Row preview */}
              {result.billItems.length > 0 && (
                <div className="glass rounded-xl overflow-hidden">
                  <p className="text-xs text-slate-500 uppercase tracking-wide px-3 pt-3 pb-2">
                    Preview (first 3 items)
                  </p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-t border-white/[0.05]">
                          {['#', 'Description', 'Unit', 'Rate'].map((h) => (
                            <th key={h} className="table-header py-1.5">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {result.billItems.slice(0, 3).map((row, i) => (
                          <tr key={i} className="border-t border-white/[0.04]">
                            <td className="table-cell py-1.5">{row.itemNo}</td>
                            <td className="table-cell py-1.5 max-w-[160px] truncate">{row.description}</td>
                            <td className="table-cell py-1.5">{row.unit}</td>
                            <td className="table-cell py-1.5 text-right">₹{row.rate.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 p-5 border-t border-white/[0.06]">
          <button onClick={onClose} className="btn-ghost">Cancel</button>
          {result && result.billItems.length > 0 && (
            <button onClick={applyToEditor} className="btn-primary flex items-center gap-1.5">
              <CheckCircle size={15} /> Apply to Editor
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
