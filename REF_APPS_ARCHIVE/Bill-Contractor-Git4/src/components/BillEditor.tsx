import { useState } from 'react';
import { ArrowLeft, Save, Eye, Loader2, AlertCircle } from 'lucide-react';
import { useBillStore } from '../store/useBillStore';
import { upsertBill } from '../lib/billService';
import BillHeaderForm from './BillHeaderForm';
import EditableTable from './EditableTable';
import StatusBadge from './ui/StatusBadge';

interface Props {
  userId: string;
  onSaved: () => void;
  toast: (type: 'success' | 'error', msg: string) => void;
}

export default function BillEditor({ userId, onSaved, toast }: Props) {
  const { currentBill, billItems, setViewMode, setCurrentBill, isDirty, resetDirty } = useBillStore();
  const [saving, setSaving] = useState(false);

  const save = async (andPreview = false) => {
    setSaving(true);
    try {
      const saved = await upsertBill(currentBill, billItems, userId);
      setCurrentBill(saved);
      resetDirty();
      toast('success', 'Bill saved');
      onSaved();
      if (andPreview) setViewMode('preview');
    } catch (err) {
      toast('error', err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Toolbar */}
      <div className="glass rounded-2xl px-5 py-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button onClick={() => setViewMode('dashboard')} className="btn-ghost py-1.5">
            <ArrowLeft size={15} /> Dashboard
          </button>
          {isDirty && (
            <div className="flex items-center gap-1.5 text-xs text-yellow-400">
              <AlertCircle size={13} />
              Unsaved changes
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <StatusBadge status={currentBill.status ?? 'draft'} />
          <button
            onClick={() => save(false)}
            disabled={saving}
            className="btn-ghost"
          >
            {saving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
            Save
          </button>
          <button
            onClick={() => save(true)}
            disabled={saving}
            className="btn-primary"
          >
            {saving ? <Loader2 size={15} className="animate-spin" /> : <Eye size={15} />}
            Save & Preview
          </button>
        </div>
      </div>

      <BillHeaderForm />
      <EditableTable />
    </div>
  );
}
