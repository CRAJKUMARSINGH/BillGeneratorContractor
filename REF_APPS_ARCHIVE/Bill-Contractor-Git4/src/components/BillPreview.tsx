import { Suspense, lazy } from 'react';
import { Download, Edit2, Loader2, Printer } from 'lucide-react';
import type { Bill } from '../types/bill';
import { computeSummary } from '../types/bill';
import { useBillStore } from '../store/useBillStore';

// Lazy-load PDF renderer to keep initial bundle small
const PDFDownloadLink = lazy(() =>
  import('@react-pdf/renderer').then((m) => ({ default: m.PDFDownloadLink }))
);
const BillPDFDocument = lazy(() => import('./BillPDFDocument'));

function fmt(d: string | null) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}
function money(n: number) {
  return `₹${n.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
}

interface MetaRowProps { label: string; value: string; full?: boolean }
function MetaRow({ label, value, full }: MetaRowProps) {
  return (
    <div className={`flex gap-2 ${full ? 'col-span-2' : ''}`}>
      <span className="text-slate-500 text-xs w-40 shrink-0">{label}</span>
      <span className="text-slate-200 text-xs">{value}</span>
    </div>
  );
}

export default function BillPreview() {
  const { currentBill, billItems, setViewMode } = useBillStore();
  const bill = { ...currentBill, items: billItems } as Bill;
  const { grand_total, premium_amount, total_with_premium, net_payable } = computeSummary(bill);

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Toolbar */}
      <div className="glass rounded-2xl px-5 py-4 flex items-center justify-between no-print">
        <h2 className="font-semibold text-white">Bill Preview</h2>
        <div className="flex items-center gap-2">
          <button onClick={() => setViewMode('edit')} className="btn-ghost">
            <Edit2 size={15} /> Edit
          </button>
          <button onClick={() => window.print()} className="btn-ghost">
            <Printer size={15} /> Print
          </button>
          <Suspense fallback={
            <button className="btn-primary opacity-60" disabled>
              <Loader2 size={15} className="animate-spin" /> Preparing PDF…
            </button>
          }>
            <PDFDownloadLink
              document={<BillPDFDocument bill={bill} />}
              fileName={`bill-${bill.voucher_number || bill.id || 'draft'}.pdf`}
            >
              {({ loading }) => (
                <button className="btn-primary" disabled={loading}>
                  {loading
                    ? <><Loader2 size={15} className="animate-spin" /> Generating…</>
                    : <><Download size={15} /> Download PDF</>
                  }
                </button>
              )}
            </PDFDownloadLink>
          </Suspense>
        </div>
      </div>

      {/* Print area */}
      <div className="bg-white text-gray-900 rounded-2xl p-10 print-area shadow-glass-lg" id="bill-content">
        <div className="max-w-[900px] mx-auto">
          {/* Title */}
          <div className="text-center border-b-2 border-indigo-600 pb-4 mb-6">
            <h1 className="text-2xl font-bold tracking-wide text-indigo-700">CONTRACTOR RUNNING ACCOUNT BILL</h1>
            <p className="text-xs text-gray-500 mt-1">Running Account Bill</p>
          </div>

          {/* Meta */}
          <div className="grid grid-cols-2 gap-x-8 gap-y-2 mb-6 text-sm border border-gray-200 rounded-lg p-4 bg-gray-50">
            <MetaRow label="Voucher Number"    value={bill.voucher_number || '—'} />
            <MetaRow label="Bill Date"         value={fmt(bill.bill_date)} />
            <MetaRow label="Serial Number"     value={bill.serial_number || '—'} />
            <MetaRow label="Agreement Number"  value={bill.agreement_number || '—'} />
            <MetaRow label="Contractor Name"   value={bill.contractor_name || '—'} full />
            <MetaRow label="Name of Work"      value={bill.work_name || '—'} full />
            <MetaRow label="Work Order Ref"    value={bill.work_order_reference || '—'} />
            <MetaRow label="Previous Bill No." value={bill.previous_bill_number || '—'} />
            <MetaRow label="Previous Bill Date"value={fmt(bill.previous_bill_date)} />
            <MetaRow label="Commencement Date" value={fmt(bill.commencement_date)} />
            <MetaRow label="Measurement Date"  value={fmt(bill.measurement_date)} />
          </div>

          {/* Items table */}
          <div className="overflow-x-auto mb-6">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr className="bg-indigo-600 text-white">
                  {['S.No','Description of Work','Unit','Qty Since Last','Qty To Date','Rate','Amt To Date','Amt Since Prev','Remarks'].map((h) => (
                    <th key={h} className="border border-indigo-500 px-2 py-2 text-left font-semibold">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {billItems.map((item, i) => (
                  <tr key={item.id} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="border border-gray-300 px-2 py-1.5 text-center">{item.serial_no || i + 1}</td>
                    <td className="border border-gray-300 px-2 py-1.5">{item.description}</td>
                    <td className="border border-gray-300 px-2 py-1.5 text-center">{item.unit}</td>
                    <td className="border border-gray-300 px-2 py-1.5 text-right">{item.qty_since_last_bill.toFixed(2)}</td>
                    <td className="border border-gray-300 px-2 py-1.5 text-right">{item.qty_to_date.toFixed(2)}</td>
                    <td className="border border-gray-300 px-2 py-1.5 text-right">{money(item.rate)}</td>
                    <td className="border border-gray-300 px-2 py-1.5 text-right">{money(item.amount_to_date)}</td>
                    <td className="border border-gray-300 px-2 py-1.5 text-right font-medium">{money(item.amount_since_previous)}</td>
                    <td className="border border-gray-300 px-2 py-1.5">{item.remarks}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Summary */}
          <div className="flex justify-end mb-8">
            <div className="w-72 border border-gray-200 rounded-lg overflow-hidden text-sm">
              <div className="flex justify-between px-4 py-2 border-b border-gray-200">
                <span className="text-gray-600">Grand Total</span>
                <span className="font-semibold">{money(grand_total)}</span>
              </div>
              {bill.tender_premium_percentage > 0 && (
                <>
                  <div className="flex justify-between px-4 py-2 border-b border-gray-200">
                    <span className="text-gray-600">Tender Premium ({bill.tender_premium_percentage}%)</span>
                    <span>{money(premium_amount)}</span>
                  </div>
                  <div className="flex justify-between px-4 py-2 border-b border-gray-200">
                    <span className="text-gray-600">Total with Premium</span>
                    <span className="font-semibold">{money(total_with_premium)}</span>
                  </div>
                </>
              )}
              {bill.last_bill_deduction > 0 && (
                <div className="flex justify-between px-4 py-2 border-b border-gray-200">
                  <span className="text-gray-600">Less: Previous Bill</span>
                  <span>({money(bill.last_bill_deduction)})</span>
                </div>
              )}
              <div className="flex justify-between px-4 py-3 bg-indigo-600 text-white">
                <span className="font-bold">Net Payable Amount</span>
                <span className="font-bold text-base">{money(net_payable)}</span>
              </div>
            </div>
          </div>

          {/* Signatures */}
          <div className="grid grid-cols-3 gap-8 mt-12 pt-6 border-t border-gray-300 text-xs text-center text-gray-600">
            {['Prepared By', 'Checked By', 'Approved By'].map((label) => (
              <div key={label}>
                <div className="border-t border-gray-800 pt-2 mt-10">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
