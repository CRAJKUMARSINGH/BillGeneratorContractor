/**
 * GeneratePanel — calls POST /bills/generate, polls job status,
 * shows progress, provides download links.
 * Output matches engine's 6 statutory documents exactly.
 */
import { useState, useEffect, useRef } from 'react';
import { FileDown, Loader2, CheckCircle, AlertCircle, ArrowLeft } from 'lucide-react';
import { api } from '../lib/api';
import type { JobStatus, BillItemAPI, ExtraItemAPI } from '../lib/api';
import { useBillStore } from '../store/useBillStore';
import { computeSummary } from '../types/bill';

export default function GeneratePanel() {
  const { header, billItems, parsedData, setViewMode, currentJob, setCurrentJob } = useBillStore();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [templateVersion, setTemplateVersion] = useState('v1');
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Stop polling on unmount
  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const summary = computeSummary(
    billItems,
    header.tender_premium_percentage ?? 0,
    header.premium_type ?? 'above',
    header.last_bill_deduction ?? 0
  );

  const startGeneration = async () => {
    setSubmitting(true);
    setError('');
    setCurrentJob(null);

    // Build titleData from header
    const titleData: Record<string, string> = {
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
    };

    // Map store items → API items
    const apiBillItems: BillItemAPI[] = billItems.map((item) => ({
      itemNo: item.serial_no,
      description: item.description,
      unit: item.unit,
      quantitySince: item.qty_since_last_bill,
      quantityUpto: item.qty_to_date,
      quantity: item.qty_to_date,
      rate: item.rate,
      amount: item.amount_since_previous,
    }));

    const apiExtraItems: ExtraItemAPI[] = (parsedData?.extraItems ?? []).map((ei) => ({
      itemNo: ei.itemNo,
      bsr: ei.bsr,
      description: ei.description,
      quantity: ei.quantity,
      unit: ei.unit,
      rate: ei.rate,
      amount: ei.amount,
      remark: ei.remark,
    }));

    try {
      const job = await api.generate({
        fileId: parsedData?.fileId ?? 'manual',
        titleData,
        billItems: apiBillItems,
        extraItems: apiExtraItems,
        options: {
          generatePdf: true,
          generateHtml: true,
          templateVersion: templateVersion,
          premiumPercent: header.tender_premium_percentage ?? 0,
          premiumType: header.premium_type ?? 'above',
          previousBillAmount: header.last_bill_deduction ?? 0,
        },
      });
      setCurrentJob(job);

      // Poll every 1.5s
      pollRef.current = setInterval(async () => {
        try {
          const status = await api.getJob(job.jobId);
          setCurrentJob(status);
          if (status.status === 'complete' || status.status === 'error') {
            if (pollRef.current) clearInterval(pollRef.current);
          }
        } catch { /* ignore transient errors */ }
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setSubmitting(false);
    }
  };

  const job = currentJob;
  const isComplete = job?.status === 'complete';
  const isError = job?.status === 'error';
  const isRunning = job && !isComplete && !isError;

  return (
    <div className="space-y-4 animate-fade-in max-w-2xl mx-auto">
      {/* Toolbar */}
      <div className="glass rounded-2xl px-5 py-4 flex items-center justify-between">
        <button onClick={() => setViewMode('edit')} className="btn-ghost py-1.5 flex items-center gap-1.5">
          <ArrowLeft size={15} /> Back to Editor
        </button>
        <p className="text-sm font-semibold text-white">Generate Documents</p>
      </div>

      {/* Summary */}
      <div className="glass rounded-2xl p-5 space-y-3">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest">Bill Summary</p>
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: 'Grand Total', value: `₹${Math.round(summary.grand_total).toLocaleString('en-IN')}` },
            { label: `Premium (${header.tender_premium_percentage ?? 0}% ${header.premium_type ?? 'above'})`, value: `₹${Math.round(summary.premium_amount).toLocaleString('en-IN')}` },
            { label: 'Total with Premium', value: `₹${Math.round(summary.total_with_premium).toLocaleString('en-IN')}` },
            { label: 'Net Payable', value: `₹${Math.round(summary.net_payable).toLocaleString('en-IN')}`, highlight: true },
          ].map((s) => (
            <div key={s.label} className="glass rounded-xl p-3">
              <p className="text-xs text-slate-500">{s.label}</p>
              <p className={`text-lg font-bold mt-0.5 ${s.highlight ? 'text-green-400' : 'text-white'}`}>{s.value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Template Selection */}
      {!job && (
        <div className="glass rounded-xl p-4 flex flex-col gap-2">
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-widest">Template Version</label>
          <select 
            value={templateVersion}
            onChange={(e) => setTemplateVersion(e.target.value)}
            className="w-full bg-surface-950 border border-white/[0.06] rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-accent-500/50 transition-colors"
          >
            <option value="v1">Standard Template (v1)</option>
            <option value="v2">Modern Template (v2)</option>
            <option value="experimental">Experimental Layout (Legacy)</option>
          </select>
        </div>
      )}

      {/* Generate button */}
      {!job && (
        <button
          onClick={startGeneration}
          disabled={submitting}
          className="btn-primary w-full py-3 text-base flex items-center justify-center gap-2"
        >
          {submitting
            ? <><Loader2 size={18} className="animate-spin" /> Submitting…</>
            : <><FileDown size={18} /> Generate All 6 Documents</>}
        </button>
      )}

      {error && (
        <div className="glass rounded-xl p-4 border border-red-500/30 flex items-start gap-2 text-red-400 text-sm">
          <AlertCircle size={16} className="shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      {/* Progress */}
      {job && (
        <div className="glass rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-white">
              {isComplete ? 'Complete' : isError ? 'Failed' : 'Generating…'}
            </p>
            <span className="text-xs text-slate-400">{Math.round(job.progress)}%</span>
          </div>

          {/* Progress bar */}
          <div className="h-2 bg-white/[0.06] rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isError ? 'bg-red-500' : isComplete ? 'bg-green-500' : 'bg-accent-500'
              }`}
              style={{ width: `${job.progress}%` }}
            />
          </div>

          <p className="text-xs text-slate-400">{job.message}</p>

          {isError && (
            <div className="text-red-400 text-sm flex items-start gap-2">
              <AlertCircle size={14} className="shrink-0 mt-0.5" />
              {job.error}
            </div>
          )}

          {/* Documents list */}
          {isComplete && job.documents.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-slate-500 uppercase tracking-wide">
                Generated ({job.documents.length} files)
              </p>
              {job.documents.map((doc) => (
                <div key={doc.name} className="flex items-center justify-between glass rounded-xl px-3 py-2">
                  <div className="flex items-center gap-2">
                    <CheckCircle size={14} className="text-green-400 shrink-0" />
                    <span className="text-sm text-slate-300">{doc.name}</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      doc.format === 'pdf' ? 'bg-red-500/15 text-red-400' : 'bg-blue-500/15 text-blue-400'
                    }`}>{doc.format.toUpperCase()}</span>
                  </div>
                  <span className="text-xs text-slate-600">{(doc.size / 1024).toFixed(1)} KB</span>
                </div>
              ))}

              <div className="flex gap-2 pt-2">
                <button
                  onClick={() => api.downloadFile(job.jobId, 'zip')}
                  className="btn-primary flex-1 text-center text-sm py-2 flex items-center justify-center gap-1.5"
                >
                  <FileDown size={15} /> Download ZIP
                </button>
                <button
                  onClick={() => api.downloadFile(job.jobId, 'pdf')}
                  className="btn-ghost flex-1 text-center text-sm py-2 flex items-center justify-center gap-1.5"
                >
                  <FileDown size={15} /> PDFs Only
                </button>
              </div>
            </div>
          )}

          {/* Retry */}
          {(isError || isComplete) && (
            <button
              onClick={() => { setCurrentJob(null); }}
              className="btn-ghost w-full text-sm"
            >
              {isError ? 'Retry' : 'Generate Again'}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
