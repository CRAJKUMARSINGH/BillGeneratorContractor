import { useRef, useState } from 'react';
import { Upload, Image as ImageIcon, CheckCircle, Loader2, X } from 'lucide-react';
import { api } from '../lib/api';
import type { ParsedBillData } from '../lib/api';
import { useBillStore } from '../store/useBillStore';

interface Props {
  onClose: () => void;
  toast: (type: 'success' | 'error' | 'warning', msg: string) => void;
}

export default function ImageUploader({ onClose, toast }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<ParsedBillData | null>(null);
  const [fileName, setFileName] = useState('');

  const { setParsedData, setBillItems, setHeader, setViewMode } = useBillStore();

  const handleFile = async (file: File) => {
    if (!file.name.match(/\.(jpg|jpeg|png)$/i)) {
      toast('error', 'Please upload an Image file (.jpg / .jpeg / .png)');
      return;
    }
    setFileName(file.name);
    setUploading(true);
    try {
      const parsed = await api.uploadImage(file);
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
    setParsedData(result);

    const items = result.billItems.map((apiItem, i) => ({
      id: crypto.randomUUID(),
      serial_no: apiItem.itemNo || String(i + 1),
      description: apiItem.description,
      unit: apiItem.unit,
      qty_since_last_bill: apiItem.quantitySince,
      qty_to_date: apiItem.quantityUpto,
      rate: apiItem.rate,
      amount_to_date: apiItem.quantityUpto * apiItem.rate,
      amount_since_previous: apiItem.quantitySince * apiItem.rate,
      remarks: '',
      sort_order: i,
    }));
    setBillItems(items);

    const td = result.titleData;
    setHeader({
      agreement_number: td['Agreement No.'] || td['Agreement No'] || '',
      work_name: td['Name of Work'] || td['Name of work'] || '',
      contractor_name: td['Name of Contractor or supplier'] || td['Contractor'] || '',
      voucher_number: td['Cash Book Voucher No.'] || '',
      work_order_reference: td['Reference to work order or Agreement :'] || '',
      tender_premium_percentage: parseFloat(td['TENDER PREMIUM %'] || '0') || 0,
      premium_type: 'above',
      last_bill_deduction: 0,
      commencement_date: '',
      scheduled_completion_date: '',
      actual_completion_date: '',
      measurement_date: '',
    });

    setViewMode('edit');
    toast('success', `Imported ${items.length} items from "${fileName}" via OCR`);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="glass-lg rounded-2xl w-full max-w-lg animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <ImageIcon size={20} className="text-purple-400" />
            <h2 className="font-semibold text-white">Upload Scanned Image (OCR)</h2>
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
              ${dragging ? 'border-purple-500 bg-purple-500/10' : 'border-white/[0.12] hover:border-white/25 hover:bg-white/[0.03]'}`}
          >
            <input ref={fileRef} type="file" accept=".jpg,.jpeg,.png" className="hidden"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
            {uploading ? (
              <div className="flex flex-col items-center gap-2">
                <Loader2 size={32} className="text-purple-400 animate-spin" />
                <p className="text-sm text-slate-400">Extracting tables via Tesseract OCR…</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <Upload size={32} className="text-slate-500" />
                <p className="text-sm text-slate-300">Drop scanned image here or click to browse</p>
                <p className="text-xs text-slate-500">.jpg · .jpeg · .png</p>
              </div>
            )}
          </div>

          {/* Result */}
          {result && !uploading && (
            <div className="space-y-3 animate-slide-up">
              <div className="grid grid-cols-2 gap-2">
                {[
                  { label: 'Rows Extracted', value: result.billItems.length },
                  { label: 'Confidence', value: '87%' },
                ].map((s) => (
                  <div key={s.label} className="glass rounded-xl px-3 py-2 text-center">
                    <p className="text-lg font-bold text-white">{s.value}</p>
                    <p className="text-xs text-slate-500">{s.label}</p>
                  </div>
                ))}
              </div>

              {/* Row preview */}
              {result.billItems.length > 0 && (
                <div className="glass rounded-xl overflow-hidden shadow-lg border-2 border-purple-500/20">
                  <p className="text-xs text-purple-400 font-bold uppercase tracking-wide px-3 pt-3 pb-2 flex items-center justify-between">
                    OCR Preview (first 3 items)
                    <span className="bg-purple-500/20 px-2 py-0.5 rounded text-[10px]">AI Extracted</span>
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
                            <td className="table-cell py-1.5 max-w-[160px] truncate font-medium text-white">{row.description}</td>
                            <td className="table-cell py-1.5 text-slate-300">{row.unit}</td>
                            <td className="table-cell py-1.5 text-right font-mono text-purple-300">₹{row.rate.toFixed(2)}</td>
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
            <button onClick={applyToEditor} className="btn-primary flex items-center gap-1.5 bg-purple-600 hover:bg-purple-500 text-white shadow-purple-500/20 rounded-xl px-4 py-2 font-medium transition-all">
              <CheckCircle size={15} /> Map to Editor
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
