import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  FileSpreadsheet, FileText, Plus, RefreshCw, 
  Image as ImageIcon, Sparkles, Clock, CheckCircle, 
  TrendingUp, Download, ExternalLink, Calendar, Calculator
} from 'lucide-react';
import { useBillStore, blankItem } from '../store/useBillStore';
import { api, BillRecordAPI } from '../lib/api';

interface Props {
  onOpenUploader: () => void;
  onOpenImageUploader: () => void;
  onOpenTemplateGenerator: () => void;
}

function StatCard({ icon, label, labelHi, value, color, delay }: {
  icon: React.ReactNode; label: string; labelHi: string; value: string | number; color: string; delay: number;
}) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="glass-card p-5 flex flex-col gap-3 group relative overflow-hidden"
    >
      <div className={`absolute top-0 right-0 w-24 h-24 ${color} opacity-10 rounded-full -mr-8 -mt-8 blur-2xl group-hover:opacity-20 transition-opacity`} />
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color.replace('bg-', 'bg-opacity-20 ')} bg-opacity-20 border border-white/5`}>
        {icon}
      </div>
      <div>
        <h4 className="text-2xl font-heading font-extrabold text-white tracking-tight">{value}</h4>
        <div className="flex items-center gap-2">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{label}</p>
          <p className="hindi text-[10px] font-bold text-gold-500/60 uppercase tracking-tight">{labelHi}</p>
        </div>
      </div>
    </motion.div>
  );
}

const ServiceCard = ({ onClick, icon, title, titleHi, desc, color, border }: any) => (
  <motion.button
    whileHover={{ y: -5, scale: 1.02 }}
    whileTap={{ scale: 0.98 }}
    onClick={onClick}
    className={`glass-card p-6 text-left group flex flex-col items-center text-center ${border} relative overflow-hidden`}
  >
    <div className={`absolute top-0 right-0 w-32 h-32 ${color} opacity-0 group-hover:opacity-10 rounded-full -mr-12 -mt-12 blur-3xl transition-opacity`} />
    <div className={`w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-5 transition-transform group-hover:scale-110 shadow-lg`}>
      {icon}
    </div>
    <h3 className="text-xl font-heading font-bold text-white mb-1">{title}</h3>
    <h4 className="hindi text-gold-500 font-medium mb-3">{titleHi}</h4>
    <p className="text-xs text-slate-400 leading-relaxed max-w-[180px]">{desc}</p>
    
    <div className="mt-6 flex items-center gap-2 text-gold-400 text-[10px] font-bold uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity">
      <span>Open Tool</span> <ExternalLink size={10} />
    </div>
  </motion.button>
);

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
    <div className="space-y-12 pb-20">
      {/* Dashboard Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-4xl font-heading font-extrabold text-white mb-2">
            Control Center
          </h1>
          <h2 className="hindi text-gold-500 text-xl font-medium tracking-wide">
            नियंत्रण केंद्र • PWD बिल मैनेजमेंट
          </h2>
        </div>
        <div className="flex items-center gap-4 bg-white/5 p-2 rounded-2xl border border-white/5">
          <div className="px-4 py-2 text-center border-r border-white/10">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Server</p>
            <div className="flex items-center gap-1.5 justify-center mt-1">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              <span className="text-xs font-bold text-slate-200 uppercase tracking-tighter">Connected</span>
            </div>
          </div>
          <div className="px-4 py-2 text-center">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Region</p>
            <p className="text-xs font-bold text-slate-200 mt-1 uppercase tracking-tighter">Udaipur, RJ</p>
          </div>
        </div>
      </div>

      {/* Stats Quick View */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={<FileText size={20} className="text-primary-300" />}
          label="Total Jobs" labelHi="कुल कार्य" value={stats.total}
          color="bg-primary-400" delay={0.1}
        />
        <StatCard
          icon={<CheckCircle size={20} className="text-green-300" />}
          label="Successful" labelHi="सफल बिल" value={stats.complete}
          color="bg-green-500" delay={0.2}
        />
        <StatCard
          icon={<Clock size={20} className="text-saffron-300" />}
          label="Processing" labelHi="विचाराधीन" value={stats.pending}
          color="bg-saffron-500" delay={0.3}
        />
        <StatCard
          icon={<TrendingUp size={20} className="text-gold-300" />}
          label="Latest Bill" labelHi="नवीनतम मूल्य" value={`₹${stats.latestValue.toLocaleString()}`}
          color="bg-gold-500" delay={0.4}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        <div className="lg:col-span-2 space-y-12">
          {/* Main Service Grid */}
          <section>
            <div className="flex items-center gap-4 mb-6">
              <div className="w-1.5 h-6 bg-gold-500 rounded-full" />
              <h3 className="text-lg font-bold text-white uppercase tracking-widest">Main Tools • <span className="hindi text-gold-500">मुख्य उपकरण</span></h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <ServiceCard
                onClick={onOpenUploader}
                icon={<FileSpreadsheet size={32} className="text-green-400" />}
                title="Import Excel"
                titleHi="एक्सेल इम्पोर्ट"
                desc="Upload standardized PWD measurement sheets."
                color="bg-green-500"
                border="border-green-500/20 hover:border-green-400/40"
              />
              <ServiceCard
                onClick={onOpenTemplateGenerator}
                icon={<Sparkles size={32} className="text-gold-400" />}
                title="AI Generator"
                titleHi="एआई जनरेटर"
                desc="Create custom templates from plain text prompts."
                color="bg-gold-500"
                border="border-gold-500/20 hover:border-gold-400/40"
              />
              <ServiceCard
                onClick={onOpenImageUploader}
                icon={<ImageIcon size={32} className="text-purple-400" />}
                title="OCR Master"
                titleHi="ओसीआर मास्टर"
                desc="Extract data from handwritten site documents."
                color="bg-purple-500"
                border="border-purple-500/20 hover:border-purple-400/40"
              />
              <ServiceCard
                onClick={createNew}
                icon={<Plus size={32} className="text-primary-400" />}
                title="Manual Entry"
                titleHi="मैन्युअल एंट्री"
                desc="Build a professional bill from absolute zero."
                color="bg-primary-500"
                border="border-primary-500/20 hover:border-primary-400/40"
              />
            </div>
          </section>

          {/* History List */}
          <section>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="w-1.5 h-6 bg-primary-400 rounded-full" />
                <h3 className="text-lg font-bold text-white uppercase tracking-widest">Recent Archive • <span className="hindi text-gold-500">पुरालेख</span></h3>
              </div>
              <button 
                onClick={fetchHistory}
                className="flex items-center gap-2 text-[10px] font-bold text-slate-500 hover:text-white transition-all uppercase tracking-widest bg-white/5 px-3 py-1.5 rounded-lg border border-white/5"
              >
                <RefreshCw size={12} className={loadingHistory ? 'animate-spin' : ''} /> Refresh Sync
              </button>
            </div>

            <div className="glass-card overflow-hidden">
              {loadingHistory ? (
                <div className="py-24 text-center">
                  <RefreshCw className="animate-spin mx-auto text-gold-500 mb-3" size={32} />
                  <p className="text-xs text-slate-500 uppercase tracking-widest">Retrieving Secure Records...</p>
                </div>
              ) : history.length === 0 ? (
                <div className="py-20 text-center opacity-50">
                  <Calculator size={48} className="mx-auto text-slate-600 mb-4" />
                  <p className="text-sm text-slate-400">Your cloud history is currently empty.</p>
                </div>
              ) : (
                <div className="divide-y divide-white/5">
                  {history.slice(0, 8).map((record, i) => (
                    <motion.div 
                      key={record.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="flex items-center justify-between p-5 hover:bg-white/[0.02] transition-all group"
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border border-white/5 ${
                          record.status === 'complete' ? 'bg-green-500/10 text-green-400' :
                          record.status === 'error' ? 'bg-red-500/10 text-red-400' : 'bg-primary-500/10 text-primary-400'
                        }`}>
                          <FileText size={20} />
                        </div>
                        <div>
                          <p className="font-bold text-white group-hover:text-gold-400 transition-colors">
                            {record.work_name?.slice(0, 45) || `Job Reference #${record.job_id.slice(0,8)}`}
                            {(record.work_name?.length || 0) > 45 && '...'}
                          </p>
                          <div className="flex items-center gap-3 mt-1">
                            <span className="flex items-center gap-1 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                              <Calendar size={10} /> {new Date(record.created_at).toLocaleDateString()}
                            </span>
                            <span className="w-1 h-1 rounded-full bg-slate-700" />
                            <span className={`text-[10px] font-extrabold uppercase tracking-widest ${
                              record.status === 'complete' ? 'text-green-500' :
                              record.status === 'error' ? 'text-red-500' : 'text-saffron-500 italic'
                            }`}>
                              {record.message}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {record.status === 'complete' && (
                          <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-all transform translate-x-2 group-hover:translate-x-0">
                            <button 
                              onClick={() => api.downloadFile(record.job_id, 'pdf')}
                              className="p-2 rounded-lg bg-white/5 hover:bg-gold-500 text-slate-400 hover:text-primary-500 transition-all border border-white/10"
                              title="Download PDF Package"
                            >
                              <Download size={16} />
                            </button>
                            <button 
                              className="p-2 rounded-lg bg-white/5 hover:bg-primary-400 text-slate-400 hover:text-white transition-all border border-white/10"
                              title="View Details"
                            >
                              <ExternalLink size={16} />
                            </button>
                          </div>
                        )}
                        <div className={`w-2 h-2 rounded-full shadow-lg ${
                          record.status === 'complete' ? 'bg-green-500 shadow-green-500/40' :
                          record.status === 'error' ? 'bg-red-500 shadow-red-500/40' : 'bg-saffron-500 animate-pulse shadow-saffron-500/40'
                        }`} />
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
            {history.length > 8 && (
              <button className="w-full py-4 text-xs font-bold text-slate-500 hover:text-gold-400 transition-colors uppercase tracking-[0.2em] border-b border-white/5">
                Load Full Cloud Record Archive
              </button>
            )}
          </section>
        </div>

        {/* Info Column */}
        <div className="space-y-12">
          <section className="glass-card p-8 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary-400/10 blur-3xl -mr-16 -mt-16 group-hover:opacity-30 transition-opacity" />
            <h3 className="text-sm font-bold text-white uppercase tracking-[0.2em] mb-6 flex items-center gap-3">
              <Calculator size={16} className="text-gold-500" /> Scrutiny Logic
            </h3>
            <ul className="space-y-4">
              {[
                { name: 'Form 26', hi: 'प्रपत्र २६', desc: 'Running & Final Bill Account' },
                { name: 'Deviation', hi: 'विचलन', desc: 'Automated quantity variation' },
                { name: 'Extra Items', hi: 'अतिरिक्त आइटम', desc: 'BSR Alignment & Non-BSR' },
                { name: 'Note Sheet', hi: 'नोट शीट', desc: 'Departmental logical audit' },
                { name: 'Certificates', hi: 'प्रमाण पत्र', desc: 'Official attestations' }
              ].map((item) => (
                <li key={item.name} className="group/item">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-bold text-white group-hover/item:text-gold-400 transition-colors">{item.name}</span>
                    <span className="hindi text-[10px] text-slate-500">{item.hi}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-tight">{item.desc}</p>
                </li>
              ))}
            </ul>
            <div className="mt-8 p-4 rounded-xl bg-gold-400/5 border border-gold-400/10">
              <p className="text-[10px] font-bold text-gold-400 uppercase tracking-widest mb-1.5 flex items-center gap-2">
                <Sparkles size={12} fill="currentColor" /> Expert Tip
              </p>
              <p className="text-[11px] text-slate-400 leading-relaxed italic">
                "The Note Sheet automatically detects variations between Agreement Qty and Executed Qty."
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
