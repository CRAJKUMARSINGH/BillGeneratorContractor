import type { DocumentStatus, BillStatus } from '../../types/bill';

const STATUS_CONFIG: Record<string, { label: string; cls: string }> = {
  draft:        { label: 'Draft',        cls: 'bg-slate-500/20 text-slate-300' },
  preview:      { label: 'Preview',      cls: 'bg-blue-500/20 text-blue-300' },
  finalized:    { label: 'Finalized',    cls: 'bg-green-500/20 text-green-300' },
  uploaded:     { label: 'Uploaded',     cls: 'bg-yellow-500/20 text-yellow-300' },
  parsed:       { label: 'Parsed',       cls: 'bg-orange-500/20 text-orange-300' },
  input_edited: { label: 'Editing',      cls: 'bg-blue-500/20 text-blue-300' },
  calculated:   { label: 'Calculated',   cls: 'bg-purple-500/20 text-purple-300' },
  final_edited: { label: 'Final Edit',   cls: 'bg-indigo-500/20 text-indigo-300' },
  print_ready:  { label: 'Print Ready',  cls: 'bg-teal-500/20 text-teal-300' },
  exported:     { label: 'Exported',     cls: 'bg-green-500/20 text-green-300' },
};

interface Props {
  status: BillStatus | DocumentStatus | string;
}

export default function StatusBadge({ status }: Props) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, cls: 'bg-slate-500/20 text-slate-300' };
  return (
    <span className={`badge ${cfg.cls}`}>{cfg.label}</span>
  );
}
