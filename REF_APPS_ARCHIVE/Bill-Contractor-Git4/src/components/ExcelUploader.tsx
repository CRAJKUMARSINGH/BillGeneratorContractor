import { useRef, useState } from 'react';
import { Upload, FileSpreadsheet, AlertTriangle, CheckCircle, Loader2, X } from 'lucide-react';
import { parseExcelFile, parsedRowsToBillItems } from '../lib/excelParser';
import type { ExcelParseResult } from '../types/bill';
import { useBillStore } from '../store/useBillStore';
import { BLANK_BILL } from '../store/useBillStore';

interface Props {
  onClose: () => void;
  toast: (type: 'success' | 'error' | 'warning', msg: string) => void;
}

export default function ExcelUploader({ onClose, toast }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [result, setResult] = useState<ExcelParseResult | null>(null);
  const [fileName, setFileName] = useState('');

  const { setCurrentBill, setBillItems, setViewMode } = useBillStore();

  const handleFile = async (file: File) => {
    if (!file.name.match(/\.(xlsx|xls|xlsm)$/i)) {
      toast('error', 'Please upload an Excel file (.xlsx / .xls)');
      return;
    }
    setFileName(file.name);
    setParsing(true);
    try {
      const parsed = await parseExcelFile(file);
      setResult(parsed);
      if (parsed.confidence < 0.3) {
        toast('warning', 'Low confidence parse — please review all fields carefully');
      }
    } catch (err) {
      toast('error', 'Failed to parse Excel file');
    } finally {
      setParsing(false);
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
    const bill = {
      ...BLANK_BILL,
      ...result.header,
      source: 'excel' as const,
      workflow_status: 'parsed' as const,
    };
    const items = parsedRowsToBillItems(result.rows);
    setCurrentBill(bill);
    setBillItems(items);
    setViewMode('edit');
    toast('success', `Imported ${items.length} items from "${fileName}"`);
    onClose();
  };

  const confidenceColor =
    !result ? '' :
    result.confidence >= 0.7 ? 'text-green-400' :
    result.confidence >= 0.4 ? 'text-yellow-400' : 'text-red-400';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="glass-lg rounded-2xl w-full max-w-lg animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <FileSpreadsheet size={20} className="text-accent-400" />
            <h2 className="font-semibold text-white">Import from Excel</h2>
          </div>
          <button onClick={onClose} className="btn-ghost p-1.5">
            <X size={18} />
          </button>
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
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.xls,.xlsm"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
            {parsing ? (
              <div className="flex flex-col items-center gap-2">
                <Loader2 size={32} className="text-accent-400 animate-spin" />
                <p className="text-sm text-slate-400">Parsing {fileName}…</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <Upload size={32} className="text-slate-500" />
                <p className="text-sm text-slate-300">Drop Excel file here or click to browse</p>
                <p className="text-xs text-slate-500">.xlsx · .xls · .xlsm</p>
              </div>
            )}
          </div>

          {/* Parse result */}
          {result && !parsing && (
            <div className="space-y-3 animate-slide-up">
              {/* Confidence */}
              <div className="flex items-center justify-between glass rounded-xl px-4 py-3">
                <span className="text-sm text-slate-400">Parse confidence</span>
                <span className={`text-sm font-semibold ${confidenceColor}`}>
                  {Math.round(result.confidence * 100)}%
                </span>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: 'Rows found', value: result.rows.length },
                  { label: 'Sheets', value: result.raw_sheet_names.length },
                  { label: 'Header fields', value: Object.keys(result.header).length },
                ].map((s) => (
                  <div key={s.label} className="glass rounded-xl px-3 py-2 text-center">
                    <p className="text-lg font-bold text-white">{s.value}</p>
                    <p className="text-xs text-slate-500">{s.label}</p>
                  </div>
                ))}
              </div>

              {/* Detected header fields */}
              {Object.keys(result.header).length > 0 && (
                <div className="glass rounded-xl p-3 space-y-1">
                  <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Detected header</p>
                  {Object.entries(result.header).map(([k, v]) => v ? (
                    <div key={k} className="flex justify-between text-xs">
                      <span className="text-slate-500">{k.replace(/_/g, ' ')}</span>
                      <span className="text-slate-300 truncate max-w-[60%] text-right">{String(v)}</span>
                    </div>
                  ) : null)}
                </div>
              )}

              {/* Warnings */}
              {result.warnings.length > 0 && (
                <div className="glass rounded-xl p-3 space-y-1 border border-yellow-500/20">
                  {result.warnings.map((w, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-yellow-400">
                      <AlertTriangle size={12} className="shrink-0 mt-0.5" />
                      {w}
                    </div>
                  ))}
                </div>
              )}

              {/* Preview rows */}
              {result.rows.length > 0 && (
                <div className="glass rounded-xl overflow-hidden">
                  <p className="text-xs text-slate-500 uppercase tracking-wide px-3 pt-3 pb-2">
                    Row preview (first 3)
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
                        {result.rows.slice(0, 3).map((row, i) => (
                          <tr key={i} className="border-t border-white/[0.04]">
                            <td className="table-cell py-1.5">{row.serial_no}</td>
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

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-5 border-t border-white/[0.06]">
          <button onClick={onClose} className="btn-ghost">Cancel</button>
          {result && result.rows.length > 0 && (
            <button onClick={applyToEditor} className="btn-primary">
              <CheckCircle size={15} />
              Apply to Editor
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
