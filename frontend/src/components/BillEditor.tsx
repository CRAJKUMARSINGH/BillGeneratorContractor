import { ArrowLeft, FileDown, AlertCircle } from 'lucide-react';
import { useBillStore } from '../store/useBillStore';
import BillHeaderForm from './BillHeaderForm';
import EditableTable from './EditableTable';

export default function BillEditor() {
  const { setViewMode, isDirty } = useBillStore();

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Toolbar */}
      <div className="glass rounded-2xl px-5 py-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button onClick={() => setViewMode('dashboard')} className="btn-ghost py-1.5 flex items-center gap-1.5">
            <ArrowLeft size={15} /> Dashboard
          </button>
          {isDirty && (
            <div className="flex items-center gap-1.5 text-xs text-yellow-400">
              <AlertCircle size={13} /> Unsaved changes
            </div>
          )}
        </div>
        <button
          onClick={() => setViewMode('generating')}
          className="btn-primary flex items-center gap-1.5"
        >
          <FileDown size={15} /> Generate Documents
        </button>
      </div>

      <BillHeaderForm />
      <EditableTable />
    </div>
  );
}
