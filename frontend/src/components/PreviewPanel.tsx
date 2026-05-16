/**
 * PreviewPanel — shows rendered HTML previews for all 7 document types
 * in sandboxed iframes before committing to PDF generation.
 *
 * Tasks 6.1–6.6: tab bar + parallel fetch, iframe + postMessage edits,
 * numeric validation, per-file selector, confirm/back actions, error UI.
 */
import { useState, useEffect, useCallback } from 'react';
import {
  ArrowLeft,
  FileDown,
  Loader2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { api } from '../lib/api';
import type { BillItemAPI, ExtraItemAPI } from '../lib/api';
import { useBillStore } from '../store/useBillStore';

// ─── Document types ────────────────────────────────────────────────────────────

const DOCUMENT_TYPES = [
  'first_page',
  'deviation_statement',
  'extra_items',
  'note_sheet',
  'certificate_ii',
  'certificate_iii',
  'last_page',
] as const;

type DocumentType = (typeof DOCUMENT_TYPES)[number];

const DOC_LABELS: Record<DocumentType, string> = {
  first_page: 'First Page',
  deviation_statement: 'Deviation',
  extra_items: 'Extra Items',
  note_sheet: 'Note Sheet',
  certificate_ii: 'Cert. II',
  certificate_iii: 'Cert. III',
  last_page: 'Last Page',
};

// ─── Per-tab state ─────────────────────────────────────────────────────────────

type TabStatus = 'loading' | 'loaded' | 'error';

interface TabState {
  status: TabStatus;
  html: string;
  errorMsg: string;
}

// ─── Edit state ────────────────────────────────────────────────────────────────

// previewEdits: fileId → docType → fieldId → value
type PreviewEdits = Record<string, Record<string, Record<string, string>>>;

// Numeric field pattern: item-{rowIdx}-{colIdx} where colIdx >= 2
const NUMERIC_FIELD_RE = /^item-\d+-([2-9]|\d{2,})$/;

function isNumericField(fieldId: string): boolean {
  return NUMERIC_FIELD_RE.test(fieldId);
}

function hasInvalidEdits(
  edits: PreviewEdits,
  fileId: string
): boolean {
  const fileEdits = edits[fileId];
  if (!fileEdits) return false;
  for (const docEdits of Object.values(fileEdits)) {
    for (const [fieldId, value] of Object.entries(docEdits)) {
      if (isNumericField(fieldId) && !isFinite(Number(value))) {
        return true;
      }
    }
  }
  return false;
}

function countEdits(edits: PreviewEdits, fileId: string): number {
  const fileEdits = edits[fileId];
  if (!fileEdits) return 0;
  return Object.values(fileEdits).reduce(
    (sum, docEdits) => sum + Object.keys(docEdits).length,
    0
  );
}

// ─── Component ─────────────────────────────────────────────────────────────────

export default function PreviewPanel() {
  const { header, billItems, parsedData, setViewMode, setCurrentJob } =
    useBillStore();

  // templateVersion: read from store if available, else local state defaulting to 'v1'
  const [templateVersion] = useState<string>('v1');

  // Active tab
  const [activeTab, setActiveTab] = useState<DocumentType>('first_page');

  // Per-tab fetch state
  const [tabs, setTabs] = useState<Record<DocumentType, TabState>>(() => {
    const init = {} as Record<DocumentType, TabState>;
    for (const dt of DOCUMENT_TYPES) {
      init[dt] = { status: 'loading', html: '', errorMsg: '' };
    }
    return init;
  });

  // Preview edits: fileId → docType → fieldId → value
  const [previewEdits, setPreviewEdits] = useState<PreviewEdits>({});

  // Submitting state for confirm action
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  // Current file id (for keying edits)
  const fileId = parsedData?.fileId ?? 'manual';

  // ── Build request payload ──────────────────────────────────────────────────

  const buildTitleData = useCallback((): Record<string, string> => ({
    'Agreement No.': header.agreement_number ?? '',
    'Name of Work': header.work_name ?? '',
    'Name of Contractor or supplier': header.contractor_name ?? '',
    'Cash Book Voucher No.': header.voucher_number ?? '',
    'Serial No. of this bill :': header.serial_number ?? '',
    'Reference to work order or Agreement :': header.work_order_reference ?? '',
    'TENDER PREMIUM %': String(header.tender_premium_percentage ?? 0),
    'ABOVE': header.premium_type === 'above' ? 'ABOVE' : 'BELOW',
    'Date of written order to commence work :': header.commencement_date ?? '',
    'St. date of completion :': header.scheduled_completion_date ?? '',
    'Date of actual completion of work :': header.actual_completion_date ?? '',
    'Date of measurement :': header.measurement_date ?? '',
    'Amount Paid Vide Last Bill': String(header.last_bill_deduction ?? 0),
  }), [header]);

  const buildBillItems = useCallback((): BillItemAPI[] =>
    billItems.map((item) => ({
      itemNo: item.serial_no,
      description: item.description,
      unit: item.unit,
      quantitySince: item.qty_since_last_bill,
      quantityUpto: item.qty_to_date,
      quantity: item.qty_to_date,
      rate: item.rate,
      amount: item.amount_since_previous,
    })), [billItems]);

  const buildExtraItems = useCallback((): ExtraItemAPI[] =>
    (parsedData?.extraItems ?? []).map((ei) => ({
      itemNo: ei.itemNo,
      bsr: ei.bsr,
      description: ei.description,
      quantity: ei.quantity,
      unit: ei.unit,
      rate: ei.rate,
      amount: ei.amount,
      remark: ei.remark,
    })), [parsedData]);

  // ── Fetch a single tab ─────────────────────────────────────────────────────

  const fetchTab = useCallback(
    async (docType: DocumentType) => {
      setTabs((prev) => ({
        ...prev,
        [docType]: { status: 'loading', html: '', errorMsg: '' },
      }));
      try {
        const res = await api.preview({
          document_type: docType,
          fileId,
          titleData: buildTitleData(),
          billItems: buildBillItems(),
          extraItems: buildExtraItems(),
          options: {
            generatePdf: true,
            generateHtml: true,
            templateVersion: templateVersion as 'v1' | 'v2',
            premiumPercent: header.tender_premium_percentage ?? 0,
            premiumType: header.premium_type ?? 'above',
            previousBillAmount: header.last_bill_deduction ?? 0,
          },
        });
        setTabs((prev) => ({
          ...prev,
          [docType]: { status: 'loaded', html: res.html, errorMsg: '' },
        }));
      } catch (err) {
        setTabs((prev) => ({
          ...prev,
          [docType]: {
            status: 'error',
            html: '',
            errorMsg: err instanceof Error ? err.message : 'Preview failed',
          },
        }));
      }
    },
    [fileId, buildTitleData, buildBillItems, buildExtraItems, templateVersion, header]
  );

  // ── On mount: fire all 7 fetches in parallel ───────────────────────────────

  useEffect(() => {
    Promise.allSettled(DOCUMENT_TYPES.map((dt) => fetchTab(dt)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── postMessage listener for inline edits ─────────────────────────────────

  useEffect(() => {
    const handler = (event: MessageEvent) => {
      // Accept messages from any origin (iframes are sandboxed)
      if (
        event.data &&
        typeof event.data === 'object' &&
        typeof event.data.fieldId === 'string' &&
        typeof event.data.value === 'string' &&
        typeof event.data.documentType === 'string'
      ) {
        const { fieldId: fid, value, documentType } = event.data as {
          fieldId: string;
          value: string;
          documentType: string;
        };
        setPreviewEdits((prev) => ({
          ...prev,
          [fileId]: {
            ...(prev[fileId] ?? {}),
            [documentType]: {
              ...((prev[fileId] ?? {})[documentType] ?? {}),
              [fid]: value,
            },
          },
        }));
      }
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, [fileId]);

  // ── Derived state ──────────────────────────────────────────────────────────

  const allFailed = DOCUMENT_TYPES.every((dt) => tabs[dt].status === 'error');
  const hasEdits = countEdits(previewEdits, fileId) > 0;
  const hasInvalid = hasInvalidEdits(previewEdits, fileId);

  // ── Confirm & Generate PDF ─────────────────────────────────────────────────

  const handleConfirm = async () => {
    setSubmitting(true);
    setSubmitError('');
    try {
      const titleData = buildTitleData();
      const apiBillItems = buildBillItems();

      // Apply titleData edits (fieldId not starting with "item-")
      const fileDocEdits = previewEdits[fileId] ?? {};
      for (const docEdits of Object.values(fileDocEdits)) {
        for (const [fid, val] of Object.entries(docEdits)) {
          if (!fid.startsWith('item-')) {
            titleData[fid] = val;
          }
        }
      }

      // TODO: item-row edits are visual-only for now; reverse-mapping
      // item-{rowIdx}-{colIdx} back to BillItemAPI fields is complex.
      // For now, pass original billItems unchanged.

      const job = await api.generate({
        fileId,
        titleData,
        billItems: apiBillItems,
        extraItems: buildExtraItems(),
        options: {
          generatePdf: true,
          generateHtml: true,
          templateVersion: templateVersion as 'v1' | 'v2',
          premiumPercent: header.tender_premium_percentage ?? 0,
          premiumType: header.premium_type ?? 'above',
          previousBillAmount: header.last_bill_deduction ?? 0,
        },
      });
      setCurrentJob(job);
      setViewMode('generating');
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setSubmitting(false);
    }
  };

  // ── Skip preview (all tabs failed) ────────────────────────────────────────

  const handleSkipPreview = async () => {
    setSubmitting(true);
    setSubmitError('');
    try {
      const job = await api.generate({
        fileId,
        titleData: buildTitleData(),
        billItems: buildBillItems(),
        extraItems: buildExtraItems(),
        options: {
          generatePdf: true,
          generateHtml: true,
          templateVersion: templateVersion as 'v1' | 'v2',
          premiumPercent: header.tender_premium_percentage ?? 0,
          premiumType: header.premium_type ?? 'above',
          previousBillAmount: header.last_bill_deduction ?? 0,
        },
      });
      setCurrentJob(job);
      setViewMode('generating');
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setSubmitting(false);
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  const activeTabState = tabs[activeTab];

  return (
    <div className="space-y-4 animate-fade-in max-w-6xl mx-auto">
      {/* Toolbar */}
      <div className="glass rounded-2xl px-5 py-4 flex items-center justify-between">
        <button
          onClick={() => setViewMode('edit')}
          className="btn-ghost py-1.5 flex items-center gap-1.5"
        >
          <ArrowLeft size={15} /> Back to Editor
        </button>

        <div className="flex items-center gap-3">
          {/* Unsaved edits badge */}
          {hasEdits && (
            <span className="flex items-center gap-1.5 text-xs font-medium text-orange-400 bg-orange-500/10 border border-orange-500/20 rounded-full px-3 py-1">
              <span className="w-1.5 h-1.5 rounded-full bg-orange-400 inline-block" />
              Unsaved preview edits
            </span>
          )}

          <button
            onClick={handleConfirm}
            disabled={submitting || hasInvalid}
            className="btn-primary py-1.5 flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? (
              <><Loader2 size={15} className="animate-spin" /> Submitting…</>
            ) : (
              <><FileDown size={15} /> Confirm &amp; Generate PDF</>
            )}
          </button>
        </div>
      </div>

      {/* Submit error */}
      {submitError && (
        <div className="glass rounded-xl p-4 border border-red-500/30 flex items-start gap-2 text-red-400 text-sm">
          <AlertCircle size={16} className="shrink-0 mt-0.5" />
          {submitError}
        </div>
      )}

      {/* Invalid edits warning */}
      {hasInvalid && (
        <div className="glass rounded-xl p-3 border border-red-500/30 flex items-center gap-2 text-red-400 text-sm">
          <AlertCircle size={14} className="shrink-0" />
          Some numeric fields contain invalid values. Fix them before generating.
        </div>
      )}

      {/* File label (task 6.4) */}
      {parsedData?.fileName && (
        <div className="px-1">
          <p className="text-xs text-slate-500 font-medium">
            File: <span className="text-slate-300">{parsedData.fileName}</span>
          </p>
        </div>
      )}

      {/* All-tabs failure: skip preview option (task 6.6) */}
      {allFailed && (
        <div className="glass rounded-2xl p-6 text-center space-y-3 border border-red-500/20">
          <AlertCircle size={32} className="text-red-400 mx-auto" />
          <p className="text-sm text-slate-300">All previews failed to load.</p>
          <button
            onClick={handleSkipPreview}
            disabled={submitting}
            className="btn-primary flex items-center gap-2 mx-auto disabled:opacity-50"
          >
            {submitting ? (
              <><Loader2 size={15} className="animate-spin" /> Submitting…</>
            ) : (
              <><FileDown size={15} /> Skip Preview &amp; Generate PDF</>
            )}
          </button>
        </div>
      )}

      {/* Tab bar + content */}
      {!allFailed && (
        <div className="glass rounded-2xl overflow-hidden">
          {/* Tab bar */}
          <div className="flex border-b border-white/[0.06] overflow-x-auto">
            {DOCUMENT_TYPES.map((dt) => {
              const tabState = tabs[dt];
              const isActive = dt === activeTab;
              return (
                <button
                  key={dt}
                  onClick={() => setActiveTab(dt)}
                  className={`flex items-center gap-1.5 px-4 py-3 text-xs font-medium whitespace-nowrap transition-colors border-b-2 ${
                    isActive
                      ? 'border-accent-500 text-white bg-white/[0.04]'
                      : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/[0.02]'
                  }`}
                >
                  {tabState.status === 'loading' && (
                    <Loader2 size={11} className="animate-spin text-slate-500" />
                  )}
                  {tabState.status === 'error' && (
                    <AlertCircle size={11} className="text-red-400" />
                  )}
                  {DOC_LABELS[dt]}
                </button>
              );
            })}
          </div>

          {/* Tab content */}
          <div className="p-0">
            {activeTabState.status === 'loading' && (
              <div className="flex flex-col items-center justify-center py-24 gap-3 text-slate-500">
                <Loader2 size={28} className="animate-spin" />
                <p className="text-sm">Loading preview…</p>
              </div>
            )}

            {activeTabState.status === 'error' && (
              <div className="flex flex-col items-center justify-center py-24 gap-3">
                <AlertCircle size={28} className="text-red-400" />
                <p className="text-sm text-red-400">{activeTabState.errorMsg}</p>
                <button
                  onClick={() => fetchTab(activeTab)}
                  className="btn-ghost flex items-center gap-1.5 text-sm"
                >
                  <RefreshCw size={14} /> Retry
                </button>
              </div>
            )}

            {activeTabState.status === 'loaded' && (
              <iframe
                srcDoc={activeTabState.html}
                sandbox="allow-scripts allow-same-origin"
                style={{ width: '100%', height: '70vh', border: 'none' }}
                title={`Preview: ${DOC_LABELS[activeTab]}`}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
