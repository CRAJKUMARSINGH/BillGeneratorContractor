import { useState } from 'react';
import {
  Plus, FileSpreadsheet, FileText, TrendingUp,
  Clock, CheckCircle, Trash2, Edit2, Eye,
} from 'lucide-react';
import type { Bill } from '../types/bill';
import { useBillStore, BLANK_BILL } from '../store/useBillStore';
import StatusBadge from './ui/StatusBadge';
import { deleteBill, fetchBillItems } from '../lib/billService';

interface Props {
  bills: Bill[];
  onRefresh: () => void;
  onOpenUploader: () => void;
  toast: (type: 'success' | 'error' | 'info', msg: string) => void;
}

function StatCard({ icon, label, value, sub, color }: {
  icon: React.ReactNode; label: string; value: string | number;
  sub?: string; color: string;
}) {
  return (
    <div className="glass rounded-2xl p-5 flex flex-col gap-3 hover:bg-white/[0.06] transition-colors">
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-xs text-slate-400 mt-0.5">{label}</p>
        {sub && <p className="text-xs text-slate-600 mt-1">{sub}</p>}
      </div>
    </div>
  );
}

export default function Dashboard({ bills, onRefresh, onOpenUploader, toast }: Props) {
  const { setCurrentBill, setBillItems, setViewMode, BLANK_BILL: _b } = {
    ...useBillStore(),
    BLANK_BILL,
  };
  const [deleting, setDeleting] = useState<string | null>(null);

  const stats = {
    total: bills.length,
    draft: bills.filter((b) => b.status === 'draft').length,
    finalized: bills.filter((b) => b.status === 'finalized').length,
    totalValue: bills.reduce((s, b) => s + (b as unknown as Record<string, number>).net_payable || 0, 0),
  };

  const createNew = () => {
    setCurrentBill({ ...BLANK_BILL });
    setBillItems([{
      id: crypto.randomUUID(), bill_id: '', serial_no: '1',
      description: '', unit: '', qty_since_last_bill: 0,
      qty_to_date: 0, rate: 0, amount_to_date: 0,
      amount_since_previous: 0, remarks: '', sort_order: 0,
    }]);
    setViewMode('edit');
  };

  const openBill = async (bill: Bill, mode: 'edit' | 'preview') => {
    try {
      const items = await fetchBillItems(bill.id);
      setCurrentBill(bill);
      setBillItems(items);
      setViewMode(mode);
    } catch {
      toast('error', 'Failed to load bill');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this bill? This cannot be undone.')) return;
    setDeleting(id);
    try {
      await deleteBill(id);
      toast('success', 'Bill deleted');
      onRefresh();
    } catch {
      toast('error', 'Failed to delete bill');
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Bento stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<FileText size={18} className="text-indigo-300" />}
          label="Total Bills" value={stats.total}
          color="bg-indigo-500/20"
        />
        <StatCard
          icon={<Clock size={18} className="text-yellow-300" />}
          label="Drafts" value={stats.draft}
          color="bg-yellow-500/20"
        />
        <StatCard
          icon={<CheckCircle size={18} className="text-green-300" />}
          label="Finalized" value={stats.finalized}
          color="bg-green-500/20"
        />
        <StatCard
          icon={<TrendingUp size={18} className="text-purple-300" />}
          label="This Month" value={bills.filter((b) => {
            const d = new Date(b.created_at);
            const now = new Date();
            return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
          }).length}
          sub="bills created"
          color="bg-purple-500/20"
        />
      </div>

      {/* Action bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-white">Bills</h2>
        <div className="flex gap-2">
          <button onClick={onOpenUploader} className="btn-ghost">
            <FileSpreadsheet size={16} /> Import Excel
          </button>
          <button onClick={createNew} className="btn-primary">
            <Plus size={16} /> New Bill
          </button>
        </div>
      </div>

      {/* Bills table */}
      <div className="glass rounded-2xl overflow-hidden">
        {bills.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="w-16 h-16 rounded-2xl bg-white/[0.04] flex items-center justify-center">
              <FileText size={28} className="text-slate-600" />
            </div>
            <div className="text-center">
              <p className="text-slate-300 font-medium">No bills yet</p>
              <p className="text-slate-600 text-sm mt-1">Create a new bill or import from Excel</p>
            </div>
            <div className="flex gap-2 mt-2">
              <button onClick={onOpenUploader} className="btn-ghost text-sm">
                <FileSpreadsheet size={15} /> Import Excel
              </button>
              <button onClick={createNew} className="btn-primary text-sm">
                <Plus size={15} /> New Bill
              </button>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  {['Voucher No.', 'Contractor', 'Work Name', 'Date', 'Source', 'Status', ''].map((h) => (
                    <th key={h} className="table-header py-3 text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {bills.map((bill, i) => (
                  <tr
                    key={bill.id}
                    className={`border-b border-white/[0.04] transition-colors hover:bg-white/[0.04]
                      ${i % 2 === 0 ? '' : 'bg-white/[0.015]'}`}
                  >
                    <td className="table-cell py-3 font-mono text-xs text-accent-400">
                      {bill.voucher_number || '—'}
                    </td>
                    <td className="table-cell py-3 max-w-[160px] truncate">
                      {bill.contractor_name || '—'}
                    </td>
                    <td className="table-cell py-3 max-w-[200px] truncate text-slate-400">
                      {bill.work_name || '—'}
                    </td>
                    <td className="table-cell py-3 text-slate-400 text-xs whitespace-nowrap">
                      {new Date(bill.bill_date).toLocaleDateString('en-IN')}
                    </td>
                    <td className="table-cell py-3">
                      <span className={`badge text-xs ${
                        bill.source === 'excel' ? 'bg-green-500/15 text-green-400' :
                        bill.source === 'hybrid' ? 'bg-blue-500/15 text-blue-400' :
                        'bg-slate-500/15 text-slate-400'
                      }`}>
                        {bill.source ?? 'manual'}
                      </span>
                    </td>
                    <td className="table-cell py-3">
                      <StatusBadge status={bill.status} />
                    </td>
                    <td className="table-cell py-3">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => openBill(bill, 'edit')}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-accent-400 hover:bg-accent-500/10 transition-colors"
                          title="Edit"
                        >
                          <Edit2 size={14} />
                        </button>
                        <button
                          onClick={() => openBill(bill, 'preview')}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-blue-400 hover:bg-blue-500/10 transition-colors"
                          title="Preview"
                        >
                          <Eye size={14} />
                        </button>
                        <button
                          onClick={() => handleDelete(bill.id)}
                          disabled={deleting === bill.id}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                          title="Delete"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
