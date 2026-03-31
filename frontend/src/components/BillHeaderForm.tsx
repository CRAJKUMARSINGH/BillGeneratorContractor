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
    <div className="space-y-6">
      {FIELD_GROUPS.map((group) => (
        <div key={group.title} className="glass-card overflow-hidden">
          <div className="px-6 py-4 bg-gradient-to-r from-primary-400/10 to-transparent border-b border-white/5 flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-[0.2em] flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-gold-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]" />
              {group.title}
            </h3>
            <span className="hindi text-[10px] text-gold-500/50 uppercase tracking-tighter">जानकारी • विवरण</span>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-5 px-6 py-6 font-sans">
            {group.fields.map((f) => {
              const colSpan =
                (f.span as number) === 3 ? 'sm:col-span-2 lg:col-span-3' :
                (f.span as number) === 2 ? 'sm:col-span-2' : '';
              
              const val = header[f.key as keyof typeof header];
              
              return (
                <div key={f.key} className={`${colSpan} group`}>
                  <label className="text-[10px] font-bold text-slate-500 mb-1.5 block uppercase tracking-widest group-focus-within:text-gold-400 transition-colors">
                    {f.label}
                  </label>
                  <div className="relative">
                    {f.type === 'select' ? (
                      <select
                        value={String(val ?? '')}
                        onChange={(e) => patchHeader(f.key as any, e.target.value)}
                        className="input-field w-full group-focus-within:border-gold-500/50"
                      >
                        {(f as any).opts?.map((o: string) => <option key={o} value={o} className="bg-surface-950 capitalize">{o}</option>)}
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
                        className="input-field w-full focus:border-gold-500/50 focus:ring-1 focus:ring-gold-500/20 transition-all"
                        placeholder={f.label}
                      />
                    )}
                    <div className="absolute bottom-0 left-0 h-[2px] w-0 bg-gradient-to-r from-gold-500 to-indigo-500 group-focus-within:w-full transition-all duration-300" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
