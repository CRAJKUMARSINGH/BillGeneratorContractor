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
      { key: 'contractor_name',   label: 'Contractor Name',   type: 'text',   span: 1 },
      { key: 'work_name',         label: 'Name of Work',      type: 'text',   span: 2 },
      { key: 'agreement_number',  label: 'Agreement Number',  type: 'text',   span: 1 },
      { key: 'work_order_reference', label: 'Work Order Ref', type: 'text',   span: 1 },
    ],
  },
  {
    title: 'Financials & Layout',
    fields: [
      { key: 'tender_premium_percentage', label: 'Tender Premium (%)', type: 'number', span: 1 },
      { key: 'premium_type',              label: 'Premium Type',       type: 'select', opts: ['above', 'below'], span: 1 },
      { key: 'last_bill_deduction',       label: 'Last Bill Deduction (₹)', type: 'number', span: 1 },
    ],
  },
  {
    title: 'Project Dates',
    fields: [
      { key: 'commencement_date',         label: 'Commencement',       type: 'date', span: 1 },
      { key: 'scheduled_completion_date', label: 'Scheduled Completion', type: 'date', span: 1 },
      { key: 'actual_completion_date',    label: 'Actual Completion',  type: 'date', span: 1 },
      { key: 'measurement_date',          label: 'Measurement Date',   type: 'date', span: 1 },
    ],
  },
] as const;

export default function BillHeaderForm() {
  const { header, patchHeader } = useBillStore();

  return (
    <div className="glass rounded-2xl overflow-hidden border border-white/[0.05]">
      {FIELD_GROUPS.map((group) => (
        <div key={group.title} className="border-b border-white/[0.06] last:border-b-0 pb-2">
          <div className="px-5 pt-4 pb-1">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">
              {group.title}
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-5 gap-y-3 px-5 pb-3">
            {group.fields.map((f) => {
              const colSpan =
                f.span === 3 ? 'sm:col-span-2 lg:col-span-3' :
                f.span === 2 ? 'sm:col-span-2' : '';
              
              const val = header[f.key as keyof typeof header];
              
              return (
                <div key={f.key} className={colSpan}>
                  <label className="text-[11px] font-medium text-slate-400 mb-1 block">{f.label}</label>
                  {f.type === 'select' ? (
                    <select
                      value={String(val ?? '')}
                      onChange={(e) => patchHeader(f.key as any, e.target.value)}
                      className="input-field w-full"
                    >
                      {(f as any).opts?.map((o: string) => <option key={o} value={o}>{o}</option>)}
                    </select>
                  ) : (
                    <input
                      type={f.type}
                      step={f.type === 'number' ? '0.01' : undefined}
                      value={String(val ?? '')}
                      onChange={(e) =>
                        patchHeader(
                          f.key as any,
                          f.type === 'number'
                            ? parseFloat(e.target.value) || 0
                            : e.target.value
                        )
                      }
                      className="input-field w-full"
                      placeholder={f.label}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

