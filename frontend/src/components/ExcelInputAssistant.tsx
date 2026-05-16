/**
 * ExcelInputAssistant — AI-powered flexible Excel input with editable browser table.
 *
 * Flow:
 *   1. User drops any Excel file (haphazard format)
 *   2. Backend AI parser detects columns, extracts rows with confidence scores
 *   3. Rows shown in inline-editable table — Bill Quantity is the key editable field
 *   4. AI notes / warnings shown per row
 *   5. User edits, adds/removes rows, then commits → standard BillEditor pipeline
 */
import { useRef, useState, useCallback } from 'react';
import {
  FileSpreadsheet, X, Loader2, CheckCircle,
  AlertTriangle, Info, Plus, Trash2, Sparkles,
  ChevronDown, ChevronUp, ArrowRight, RefreshCw,
} from 'lucide-react';
import { api } from '../lib/api';
import type { AIParseResult, AIRow, AISheetResult } from '../lib/api';
import { useBillStore } from '../store/useBillStore';

interface Props {
  onClose: () => void;
  toast: (type: 'success' | 'error' | 'warning' | 'info', msg: string) => void;
}

// ── Editable row type (adds local id for React keys) ─────────────────────────
interface EditRow extends AIRow {
  _id: string;
  _dirty: boolean; // user has edited this row
}

function makeId() {
  return Math.random().toString(36).slice(2, 10);
}

function toEditRows(rows: AIRow[]): EditRow[] {
  return rows.map((r) => ({ ...r, _id: makeId(), _dirty: false }));
}

// ── Confidence badge ──────────────────────────────────────────────────────────
function ConfBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 85 ? 'bg-green-500/20 text-green-300 border-green-500/30' :
    pct >= 60 ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30' :
                'bg-red-500/20 text-red-300 border-red-500/30';
  return (
    <span className={`badge border text-[10px] ${color}`}>{pct}%</span>
  );
}

// ── Column mapping panel ──────────────────────────────────────────────────────
function MappingPanel({ sheet }: { sheet: AISheetResult }) {
  const [open, setOpen] = useState(false);
  const CANONICAL_LABELS: Record<string, string> = {
    item_no: 'Item No', description: 'Description', unit: 'Unit',
    quantity: 'Quantity', rate: 'Rate', amount: 'Amount', remark: 'Remark',
  };
  return (
    <div className="glass rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
      >
        <span className="flex items-center gap-2">
          <Sparkles size={13} className="text-accent-400" />
          AI Column Mapping — {sheet.sheetName}
          {sheet.warnings.length > 0 && (
            <span className="badge bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 ml-1">
              {sheet.warnings.length} warning{sheet.warnings.length > 1 ? 's' : ''}
            </span>
          )}
        </span>
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-white/[0.06]">
          {/* Mapped columns */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-3">
            {sheet.columnMappings.map((m) => (
              <div key={m.colIndex} className="glass rounded-lg px-3 py-2 flex items-center justify-between gap-2">
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wide">
                    {CANONICAL_LABELS[m.canonical] ?? m.canonical}
                  </p>
                  <p className="text-xs text-slate-200 truncate max-w-[100px]" title={m.headerText}>
                    "{m.headerText}"
                  </p>
                </div>
                <ConfBadge value={m.confidence} />
              </div>
            ))}
          </div>

          {/* Unmapped */}
          {sheet.unmappedColumns.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              <span className="text-[10px] text-slate-500 self-center">Unmapped:</span>
              {sheet.unmappedColumns.map((c) => (
                <span key={c} className="badge bg-white/5 text-slate-400 border border-white/10 text-[10px]">
                  {c}
                </span>
              ))}
            </div>
          )}

          {/* Warnings */}
          {sheet.warnings.map((w, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-yellow-300 bg-yellow-500/10 rounded-lg px-3 py-2">
              <AlertTriangle size={12} className="mt-0.5 shrink-0" />
              {w}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Inline-editable cell ──────────────────────────────────────────────────────
interface CellProps {
  value: string | number;
  onChange: (v: string) => void;
  type?: 'text' | 'number';
  highlight?: boolean; // Bill Quantity column
  placeholder?: string;
  className?: string;
}

function EditCell({ value, onChange, type = 'text', highlight, placeholder, className = '' }: CellProps) {
  return (
    <input
      type={type}
      value={value === 0 && type === 'number' ? '' : String(value)}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      className={[
        'w-full bg-transparent text-sm outline-none px-1 py-0.5 rounded',
        'focus:bg-white/[0.06] focus:ring-1 focus:ring-accent-500/50',
        highlight
          ? 'text-accent-300 font-semibold placeholder-accent-500/50'
          : 'text-slate-200 placeholder-slate-600',
        className,
      ].join(' ')}
    />
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function ExcelInputAssistant({ onClose, toast }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState('');
  const [parseResult, setParseResult] = useState<AIParseResult | null>(null);
  const [activeSheet, setActiveSheet] = useState<AISheetResult | null>(null);
  const [rows, setRows] = useState<EditRow[]>([]);
  const [committing, setCommitting] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);

  const { setParsedData, setBillItems, setHeader, setViewMode } = useBillStore();

  // ── Upload & parse ──────────────────────────────────────────────────────────
  const handleFile = useCallback(async (file: File) => {
    if (!file.name.match(/\.(xlsx|xls|xlsm)$/i)) {
      toast('error', 'Please upload an Excel file (.xlsx / .xls)');
      return;
    }
    setFileName(file.name);
    setLoading(true);
    setParseResult(null);
    setRows([]);
    try {
      const result = await api.aiParseExcel(file);
      setParseResult(result);
      // Default to Work Order sheet
      const wo = result.workOrderSheet ?? result.sheets[0] ?? null;
      setActiveSheet(wo);
      setRows(wo ? toEditRows(wo.rows) : []);
      if (result.aiSuggestions.length > 0) {
        toast('info', `AI: ${result.aiSuggestions[0]}`);
      }
    } catch (err) {
      toast('error', err instanceof Error ? err.message : 'Parse failed');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  // ── Switch active sheet ─────────────────────────────────────────────────────
  const switchSheet = (sheet: AISheetResult) => {
    setActiveSheet(sheet);
    setRows(toEditRows(sheet.rows));
  };

  // ── Row editing ─────────────────────────────────────────────────────────────
  const updateRow = useCallback((id: string, field: keyof AIRow, raw: string) => {
    setRows((prev) =>
      prev.map((r) => {
        if (r._id !== id) return r;
        const numFields: (keyof AIRow)[] = ['quantity', 'rate', 'amount'];
        const val = numFields.includes(field) ? parseFloat(raw) || 0 : raw;
        const updated = { ...r, [field]: val, _dirty: true };
        // Auto-recalculate amount when qty or rate changes
        if (field === 'quantity' || field === 'rate') {
          updated.amount = Math.round((updated.quantity || 0) * (updated.rate || 0));
        }
        return updated;
      })
    );
  }, []);

  const addRow = () => {
    setRows((prev) => [
      ...prev,
      {
        _id: makeId(), _dirty: true,
        itemNo: '', description: '', unit: '', quantity: 0,
        rate: 0, amount: 0, remark: '', confidence: 1, aiNote: '',
      },
    ]);
  };

  const removeRow = (id: string) => {
    setRows((prev) => prev.filter((r) => r._id !== id));
  };

  const acceptAllAI = () => {
    // Mark all rows as accepted (clear aiNote warnings)
    setRows((prev) => prev.map((r) => ({ ...r, aiNote: '', _dirty: true })));
    toast('success', 'All AI suggestions accepted');
  };

  // ── Commit to pipeline ──────────────────────────────────────────────────────
  const handleCommit = async () => {
    if (!parseResult) return;
    const validRows = rows.filter((r) => r.description.trim() || r.itemNo.trim());
    if (validRows.length === 0) {
      toast('error', 'No rows to commit — add at least one item');
      return;
    }
    setCommitting(true);
    try {
      const committed = await api.aiCommit({
        fileId: parseResult.fileId,
        fileName: parseResult.fileName,
        titleData: parseResult.titleData,
        rows: validRows.map(({ _id, _dirty, ...r }) => r),
      });

      // Push into BillStore — same path as ExcelUploader
      setParsedData(committed);
      const storeItems = committed.billItems.map((item, i) => ({
        id: crypto.randomUUID(),
        serial_no: item.itemNo || String(i + 1),
        description: item.description,
        unit: item.unit,
        qty_since_last_bill: item.quantitySince,
        qty_to_date: item.quantityUpto,
        rate: item.rate,
        amount_to_date: item.quantityUpto * item.rate,
        amount_since_previous: item.quantitySince * item.rate,
        remarks: '',
        sort_order: i,
      }));
      setBillItems(storeItems);

      const td = committed.titleData;
      setHeader({
        agreement_number: td['Agreement No.'] || td['Agreement No'] || '',
        work_name: td['Name of Work ;-'] || td['Name of Work'] || '',
        contractor_name: td['Name of Contractor or supplier :'] || td['Contractor'] || '',
        tender_premium_percentage: parseFloat(td['TENDER PREMIUM %'] || '0') || 0,
        premium_type: (td['ABOVE'] || 'above').toLowerCase().includes('below') ? 'below' : 'above',
        commencement_date: td['Date of written order to commence work :'] || '',
        scheduled_completion_date: td['St. date of completion :'] || '',
        actual_completion_date: td['Date of actual completion of work :'] || '',
        measurement_date: td['Date of measurement :'] || '',
      });

      setViewMode('edit');
      toast('success', `Imported ${storeItems.length} items from "${fileName}"`);
      onClose();
    } catch (err) {
      toast('error', err instanceof Error ? err.message : 'Commit failed');
    } finally {
      setCommitting(false);
    }
  };

  // ── Stats ───────────────────────────────────────────────────────────────────
  const totalAmount = rows.reduce((s, r) => s + (r.amount || 0), 0);
  const aiNoteRows = rows.filter((r) => r.aiNote).length;
  const missingQty = rows.filter((r) => r.rate > 0 && r.quantity === 0).length;

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-surface-950/95 backdrop-blur-sm animate-fade-in">
      {/* ── Header bar ── */}
      <div className="glass border-b border-white/[0.06] px-4 h-14 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent-500/20 border border-accent-500/30 flex items-center justify-center">
            <Sparkles size={15} className="text-accent-400" />
          </div>
          <div>
            <p className="font-semibold text-white text-sm leading-none">AI Excel Assistant</p>
            <p className="text-[10px] text-slate-500 mt-0.5">
              Upload any format — AI detects columns &amp; extracts bill quantities
            </p>
          </div>
        </div>
        <button onClick={onClose} className="btn-ghost p-1.5" aria-label="Close">
          <X size={18} />
        </button>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col max-w-7xl mx-auto w-full px-4 py-4 gap-4">

        {/* ── Upload zone (shown until file parsed) ── */}
        {!parseResult && (
          <div
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
            className={[
              'border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200 flex-1 flex flex-col items-center justify-center',
              dragging ? 'border-accent-500 bg-accent-500/10' : 'border-white/[0.12] hover:border-white/25 hover:bg-white/[0.02]',
            ].join(' ')}
          >
            <input
              ref={fileRef} type="file" accept=".xlsx,.xls,.xlsm" className="hidden"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
            {loading ? (
              <div className="flex flex-col items-center gap-3">
                <Loader2 size={40} className="text-accent-400 animate-spin" />
                <p className="text-slate-300 font-medium">AI parsing {fileName}…</p>
                <p className="text-xs text-slate-500">Detecting columns, extracting items, scoring confidence</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 rounded-2xl bg-accent-500/10 border border-accent-500/20 flex items-center justify-center">
                  <FileSpreadsheet size={32} className="text-accent-400" />
                </div>
                <div>
                  <p className="text-white font-semibold">Drop any Excel file here</p>
                  <p className="text-sm text-slate-400 mt-1">
                    Works with haphazard formats — merged cells, varied column names, multiple sheets
                  </p>
                </div>
                <div className="flex gap-2 mt-2">
                  {['.xlsx', '.xls', '.xlsm'].map((ext) => (
                    <span key={ext} className="badge bg-white/5 text-slate-400 border border-white/10">{ext}</span>
                  ))}
                </div>
                <p className="text-xs text-slate-600 mt-2">
                  AI detects: Item No · Description · Unit · Quantity · Rate · Amount · BSR Ref
                </p>
              </div>
            )}
          </div>
        )}

        {/* ── Post-parse layout ── */}
        {parseResult && (
          <>
            {/* ── Top info bar ── */}
            <div className="flex flex-wrap items-center gap-3 shrink-0">
              {/* File info */}
              <div className="glass rounded-xl px-3 py-2 flex items-center gap-2">
                <FileSpreadsheet size={14} className="text-accent-400" />
                <span className="text-sm text-slate-200 font-medium truncate max-w-[200px]">{parseResult.fileName}</span>
              </div>

              {/* Stats */}
              {[
                { label: 'Rows', value: rows.length, color: 'text-white' },
                { label: 'Total ₹', value: Math.round(totalAmount).toLocaleString('en-IN'), color: 'text-green-300' },
                { label: 'Confidence', value: `${Math.round(parseResult.confidenceOverall * 100)}%`,
                  color: parseResult.confidenceOverall >= 0.8 ? 'text-green-300' : 'text-yellow-300' },
                ...(missingQty > 0 ? [{ label: 'Missing Qty', value: missingQty, color: 'text-red-300' }] : []),
                ...(aiNoteRows > 0 ? [{ label: 'AI Notes', value: aiNoteRows, color: 'text-yellow-300' }] : []),
              ].map((s) => (
                <div key={s.label} className="glass rounded-xl px-3 py-2 text-center min-w-[70px]">
                  <p className={`text-sm font-bold ${s.color}`}>{s.value}</p>
                  <p className="text-[10px] text-slate-500">{s.label}</p>
                </div>
              ))}

              <div className="ml-auto flex items-center gap-2">
                {/* Re-upload */}
                <button
                  onClick={() => { setParseResult(null); setRows([]); fileRef.current?.click(); }}
                  className="btn-ghost text-xs py-1.5 px-3"
                >
                  <RefreshCw size={13} /> Re-upload
                </button>
                {aiNoteRows > 0 && (
                  <button onClick={acceptAllAI} className="btn-ghost text-xs py-1.5 px-3 text-accent-300">
                    <CheckCircle size={13} /> Accept All AI
                  </button>
                )}
              </div>
            </div>

            {/* ── Sheet tabs ── */}
            {parseResult.sheets.length > 1 && (
              <div className="flex gap-1 shrink-0 overflow-x-auto">
                {parseResult.sheets.map((s) => (
                  <button
                    key={s.sheetName}
                    onClick={() => switchSheet(s)}
                    className={[
                      'px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors',
                      activeSheet?.sheetName === s.sheetName
                        ? 'bg-accent-500/20 text-accent-300 border border-accent-500/30'
                        : 'text-slate-400 hover:text-white hover:bg-white/[0.05]',
                    ].join(' ')}
                  >
                    {s.sheetName}
                    <span className="ml-1.5 text-[10px] opacity-60">{s.rows.length}</span>
                  </button>
                ))}
              </div>
            )}

            {/* ── Column mapping panel ── */}
            {activeSheet && <MappingPanel sheet={activeSheet} />}

            {/* ── AI suggestions strip ── */}
            {parseResult.aiSuggestions.length > 0 && showSuggestions && (
              <div className="glass rounded-xl px-4 py-3 flex items-start gap-3 shrink-0">
                <Info size={14} className="text-accent-400 mt-0.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-accent-300 mb-1">AI Suggestions</p>
                  <ul className="space-y-0.5">
                    {parseResult.aiSuggestions.slice(0, 4).map((s, i) => (
                      <li key={i} className="text-xs text-slate-400">{s}</li>
                    ))}
                  </ul>
                </div>
                <button onClick={() => setShowSuggestions(false)} className="text-slate-600 hover:text-slate-400">
                  <X size={13} />
                </button>
              </div>
            )}

            {/* ── Editable table ── */}
            <div className="flex-1 overflow-auto glass rounded-xl min-h-0">
              <table className="w-full text-sm border-collapse" style={{ minWidth: '900px' }}>
                <thead className="sticky top-0 z-10 bg-surface-950">
                  <tr className="border-b border-white/[0.08]">
                    {[
                      { label: 'Item No', w: '80px' },
                      { label: 'Description', w: '280px' },
                      { label: 'Unit', w: '70px' },
                      { label: 'Bill Qty ✏', w: '90px', highlight: true },
                      { label: 'Rate', w: '90px' },
                      { label: 'Amount', w: '100px' },
                      { label: 'BSR / Remark', w: '110px' },
                      { label: 'AI', w: '60px' },
                      { label: '', w: '40px' },
                    ].map((col) => (
                      <th
                        key={col.label}
                        style={{ width: col.w, minWidth: col.w }}
                        className={[
                          'table-header text-left py-2.5 px-3',
                          (col as any).highlight ? 'text-accent-400' : '',
                        ].join(' ')}
                      >
                        {col.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, idx) => {
                    const hasNote = Boolean(row.aiNote);
                    const lowConf = row.confidence < 0.7;
                    const missingBillQty = row.rate > 0 && row.quantity === 0;
                    const rowBg = missingBillQty
                      ? 'bg-red-500/5'
                      : hasNote
                      ? 'bg-yellow-500/5'
                      : idx % 2 === 0
                      ? 'bg-white/[0.01]'
                      : '';

                    return (
                      <tr
                        key={row._id}
                        className={`border-b border-white/[0.04] hover:bg-white/[0.03] transition-colors group ${rowBg}`}
                      >
                        {/* Item No */}
                        <td className="px-3 py-1.5">
                          <EditCell
                            value={row.itemNo}
                            onChange={(v) => updateRow(row._id, 'itemNo', v)}
                            placeholder="1.1"
                          />
                        </td>

                        {/* Description */}
                        <td className="px-3 py-1.5">
                          <EditCell
                            value={row.description}
                            onChange={(v) => updateRow(row._id, 'description', v)}
                            placeholder="Item description…"
                          />
                        </td>

                        {/* Unit */}
                        <td className="px-3 py-1.5">
                          <EditCell
                            value={row.unit}
                            onChange={(v) => updateRow(row._id, 'unit', v)}
                            placeholder="Each"
                          />
                        </td>

                        {/* Bill Quantity — highlighted, most important */}
                        <td className={`px-3 py-1.5 ${missingBillQty ? 'ring-1 ring-inset ring-red-500/40 rounded' : ''}`}>
                          <EditCell
                            value={row.quantity}
                            onChange={(v) => updateRow(row._id, 'quantity', v)}
                            type="number"
                            highlight
                            placeholder="0"
                          />
                        </td>

                        {/* Rate */}
                        <td className="px-3 py-1.5">
                          <EditCell
                            value={row.rate}
                            onChange={(v) => updateRow(row._id, 'rate', v)}
                            type="number"
                            placeholder="0"
                          />
                        </td>

                        {/* Amount (auto-calc, still editable) */}
                        <td className="px-3 py-1.5">
                          <EditCell
                            value={row.amount}
                            onChange={(v) => updateRow(row._id, 'amount', v)}
                            type="number"
                            placeholder="0"
                            className="text-right"
                          />
                        </td>

                        {/* Remark / BSR */}
                        <td className="px-3 py-1.5">
                          <EditCell
                            value={row.remark}
                            onChange={(v) => updateRow(row._id, 'remark', v)}
                            placeholder="BSR ref"
                          />
                        </td>

                        {/* AI note / confidence */}
                        <td className="px-3 py-1.5">
                          <div className="flex flex-col items-center gap-1">
                            {lowConf && <ConfBadge value={row.confidence} />}
                            {hasNote && (
                              <button
                                title={row.aiNote}
                                onClick={() => updateRow(row._id, 'aiNote', '')}
                                className="text-yellow-400 hover:text-yellow-200"
                              >
                                <AlertTriangle size={12} />
                              </button>
                            )}
                          </div>
                        </td>

                        {/* Delete */}
                        <td className="px-2 py-1.5">
                          <button
                            onClick={() => removeRow(row._id)}
                            className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-red-400 transition-all"
                            aria-label="Remove row"
                          >
                            <Trash2 size={13} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {rows.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 text-slate-500">
                  <FileSpreadsheet size={32} className="mb-3 opacity-30" />
                  <p className="text-sm">No rows extracted — check column mapping above</p>
                </div>
              )}
            </div>

            {/* ── Add row + footer actions ── */}
            <div className="flex items-center justify-between shrink-0 pt-1">
              <button onClick={addRow} className="btn-ghost text-xs py-1.5 px-3">
                <Plus size={13} /> Add Row
              </button>

              <div className="flex items-center gap-3">
                {missingQty > 0 && (
                  <span className="text-xs text-red-400 flex items-center gap-1">
                    <AlertTriangle size={12} />
                    {missingQty} row{missingQty > 1 ? 's' : ''} missing Bill Qty
                  </span>
                )}
                <button onClick={onClose} className="btn-ghost">Cancel</button>
                <button
                  onClick={handleCommit}
                  disabled={committing || rows.length === 0}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {committing ? (
                    <><Loader2 size={14} className="animate-spin" /> Committing…</>
                  ) : (
                    <><ArrowRight size={14} /> Send to Bill Editor ({rows.filter(r => r.description || r.itemNo).length} rows)</>
                  )}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
