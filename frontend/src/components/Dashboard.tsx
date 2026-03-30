import { useEffect, useState } from 'react';
import { 
  FileSpreadsheet, FileText, Plus, RefreshCw, 
  Image as ImageIcon, Sparkles, Clock, CheckCircle, TrendingUp 
} from 'lucide-react';
import { useBillStore, blankItem } from '../store/useBillStore';
import { api, BillRecordAPI } from '../lib/api';

interface Props {
  onOpenUploader: () => void;
  onOpenImageUploader: () => void;
  onOpenTemplateGenerator: () => void;
}

function StatCard({ icon, label, value, color }: {
  icon: React.ReactNode; label: string; value: string | number; color: string;
}) {
  return (
    <div className="glass rounded-2xl p-4 flex flex-col gap-2 hover:bg-white/[0.06] transition-all group border border-white/[0.03]">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${color} mb-1 group-hover:scale-110 transition-transform`}>
        {icon}
      </div>
      <div>
        <p className="text-xl font-bold text-white tracking-tight">{value}</p>
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">{label}</p>
      </div>
    </div>
  );
}

export default function Dashboard({ onOpenUploader, onOpenImageUploader, onOpenTemplateGenerator }: Props) {
  const { setViewMode, setBillItems, setHeader, setParsedData } = useBillStore();
  const [history, setHistory] = useState<BillRecordAPI[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  const createNew = () => {
    setParsedData(null);
    setHeader({ tender_premium_percentage: 0, premium_type: 'above', last_bill_deduction: 0 });
    setBillItems([blankItem(0)]);
    setViewMode('edit');
  };

  const fetchHistory = () => {
    setLoadingHistory(true);
    api.getHistory()
      .then(setHistory)
      .catch(console.error)
      .finally(() => setLoadingHistory(false));
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const stats = {
    total: history.length,
    complete: history.filter(h => h.status === 'complete').length,
    pending: history.filter(h => h.status === 'pending' || h.status === 'processing').length,
    latestValue: history.length > 0 && history[0].total_amount ? history[0].total_amount : 0
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto pt-8">
      {/* Bento Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<FileText size={16} className="text-accent-300" />}
          label="Total Jobs" value={stats.total}
          color="bg-accent-500/20"
        />
        <StatCard
          icon={<CheckCircle size={16} className="text-green-300" />}
          label="Succeeded" value={stats.complete}
          color="bg-green-500/20"
        />
        <StatCard
          icon={<Clock size={16} className="text-yellow-300" />}
          label="In Progress" value={stats.pending}
          color="bg-yellow-500/20"
        />
        <StatCard
          icon={<TrendingUp size={16} className="text-purple-300" />}
          label="Last Amount" value={`₹${stats.latestValue.toLocaleString()}`}
          color="bg-purple-500/20"
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Actions */}
        <div className="lg:col-span-2 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <button
              onClick={onOpenUploader}
              className="glass rounded-2xl p-6 text-left hover:bg-white/[0.06] transition-all group border border-white/[0.05]"
            >
              <FileSpreadsheet size={24} className="text-green-400 mb-4 group-hover:scale-110 transition-transform" />
              <p className="font-bold text-white mb-1">Import Excel</p>
              <p className="text-xs text-slate-500">Auto-parse statuatory PWD Excel formats</p>
            </button>

            <button
              onClick={onOpenImageUploader}
              className="glass rounded-2xl p-6 text-left hover:bg-white/[0.06] transition-all group border border-purple-500/20 hover:border-purple-500/40"
            >
              <ImageIcon size={24} className="text-purple-400 mb-4 group-hover:scale-110 transition-transform" />
              <p className="font-bold text-white mb-1">OCR Upload</p>
              <p className="text-xs text-purple-200/60">Harvest data from handwritten images</p>
            </button>

            <button
              onClick={createNew}
              className="glass rounded-2xl p-6 text-left hover:bg-white/[0.06] transition-all group border border-white/[0.05]"
            >
              <Plus size={24} className="text-accent-400 mb-4 group-hover:scale-110 transition-transform" />
              <p className="font-bold text-white mb-1">Manual Entry</p>
              <p className="text-xs text-slate-500">Create a blank bill and edit from scratch</p>
            </button>

            <button
              onClick={onOpenTemplateGenerator}
              className="glass rounded-2xl p-6 text-left hover:bg-white/[0.06] transition-all group border border-yellow-500/20 hover:border-yellow-500/40"
            >
              <Sparkles size={24} className="text-yellow-400 mb-4 group-hover:scale-110 transition-transform" />
              <p className="font-bold text-white mb-1">AI Template Gen</p>
              <p className="text-xs text-yellow-200/60">Generate layout schemas via LLM</p>
            </button>
          </div>

          {/* History */}
          <div className="glass rounded-2xl p-6 space-y-4 border border-white/[0.05]">
            <div className="flex justify-between items-end">
               <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Recent Activity</p>
               <button 
                 className="text-xs flex items-center gap-1 text-slate-500 hover:text-white transition-colors" 
                 onClick={fetchHistory}
               >
                 <RefreshCw size={12} className={loadingHistory ? 'animate-spin' : ''} /> Refresh
               </button>
            </div>
            
            {loadingHistory ? (
              <div className="py-20 text-center"><Loader2 className="animate-spin mx-auto text-accent-500" /></div>
            ) : history.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-10 bg-white/[0.01] rounded-xl border border-dashed border-white/[0.05]">No activity detected.</p>
            ) : (
              <div className="divide-y divide-white/[0.03]">
                {history.slice(0, 5).map(record => (
                  <div key={record.id} className="flex items-center justify-between py-4 group">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${
                        record.status === 'complete' ? 'bg-green-500' :
                        record.status === 'error' ? 'bg-red-500' : 'bg-yellow-500 animate-pulse'
                      }`} />
                      <div>
                        <p className="text-sm font-semibold text-slate-200">
                          {record.work_name || `Job ${record.job_id.slice(0,8)}`}
                        </p>
                        <p className="text-[10px] text-slate-500 mt-0.5">
                          {new Date(record.created_at).toLocaleDateString()} • {record.message}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {record.status === 'complete' && (
                        <button 
                          onClick={() => api.downloadFile(record.job_id, 'pdf')}
                          className="text-[10px] font-bold text-accent-400 hover:text-white px-2 py-1 rounded bg-accent-500/10 hover:bg-accent-500 transition-all border border-accent-500/20"
                        >
                          PDF
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Mini Info / Metadata */}
        <div className="space-y-6">
          <div className="glass rounded-2xl p-6 space-y-4 border border-white/[0.05]">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Output Package</p>
            <ul className="space-y-3">
              {[
                { name: 'First Page', desc: 'Bill Account Form 26' },
                { name: 'Deviation', desc: 'Schedules and Changes' },
                { name: 'Extra Items', desc: 'Non-BSR approvals' },
                { name: 'Note Sheet', desc: 'Departmental Scrutiny' },
                { name: 'Certificates', desc: 'Phase II & III signatures' }
              ].map((item) => (
                <li key={item.name} className="flex flex-col">
                  <span className="text-xs font-semibold text-white">{item.name}</span>
                  <span className="text-[10px] text-slate-500">{item.desc}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="glass rounded-2xl p-6 bg-accent-500/5 border border-accent-500/10">
            <p className="text-xs font-bold text-accent-400 mb-2">Pro Tip</p>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Use Excel import for bulk measurements. The AI will automatically detect part-rates and deviation schedules based on original work order values.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}

const Loader2 = ({ className }: { className?: string }) => (
  <RefreshCw className={`${className} animate-spin`} />
);
