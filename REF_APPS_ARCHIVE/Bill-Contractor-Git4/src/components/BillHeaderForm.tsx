import type { Bill } from '../types/bill';
import { useBillStore } from '../store/useBillStore';

const FIELD_GROUPS = [
  {
    title: 'Identification',
    fields: [
      { key: 'voucher_number',    label: 'Voucher Number',    type: 'text',   span: 1 },
      { key: 'serial_number',     label: 'Serial Number',     type: 'text',   span: 1 },
      { key: 'bill_date',         label: 'Bill Date',         type: 'date',   span: 1 },
    ],
  },
  {
    title: 'Parties & Work',
    fields: [
      { key: 'contractor_name',   label: 'Contractor Name',   type: 'text',   span: 2 },
      { key: 'work_name',         label: 'Name of Work',      type: 'text',   span: 3 },
      { key: 'agreement_number',  label: 'Agreement Number',  type: 'text',   span: 1 },
      { key: 'work_order_reference', label: 'Work Order Ref', type: 'text',   span: 1 },
    ],
  },
  {
    title: 'Previous Bill',
    fields: [
      { key: 'previous_bill_number', label: 'Previous Bill No.', type: 'text', span: 1 },
      { key: 'previous_bill_date',   label: 'Previous Bill Date', type: 'date', span: 1 },
    ],
  },
  {
    title: 'Dates',
    fields: [
      { key: 'commencement_date',         label: 'Commencement',       type: 'date', span: 1 },
      { key: 'scheduled_start_date',      label: 'Scheduled Start',    type: 'date', span: 1 },
      { key: 'scheduled_completion_date', label: 'Scheduled Completion', type: 'date', span: 1 },
      { key: 'actual_completion_date',    label: 'Actual Completion',  type: 'date', span: 1 },
      { key: 'measurement_date',          label: 'Measurement Date',   type: 'date', span: 1 },
    ],
  },
  {
    title: 'Financials',
    fields: [
      { key: 'tender_premium_percentage', label: 'Tender Premium (%)', type: 'number', span: 1 },
      { key: 'last_bill_deduction',       label: 'Last Bill Deduction (₹)', type: 'number', span: 1 },
    ],
  },
] as const;

export default function BillHeaderForm() {
  const { currentBill, patchBill } = useBillStore();

  return (
    <div className="glass rounded-2xl overflow-hidden">
      {FIELD_GROUPS.map((group) => (
        <div key={group.title} className="border-b border-white/[0.06] last:border-b-0">
          <div className="px-5 pt-4 pb-1">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest">
              {group.title}
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 px-5 pb-5">
            {group.fields.map((f) => {
              const colSpan =
                f.span === 3 ? 'sm:col-span-2 lg:col-span-3' :
                f.span === 2 ? 'sm:col-span-2' : '';
              const val = (currentBill as Record<string, unknown>)[f.key];
              return (
                <div key={f.key} className={colSpan}>
                  <label className="label">{f.label}</label>
                  <input
                    type={f.type}
                    step={f.type === 'number' ? '0.01' : undefined}
                    value={val === null || val === undefined ? '' : String(val)}
                    onChange={(e) =>
                      patchBill(
                        f.key as keyof Bill,
                        f.type === 'number'
                          ? parseFloat(e.target.value) || 0
                          : e.target.value || null
                      )
                    }
                    className="input-field"
                  />
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
