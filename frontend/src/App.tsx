import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FileText, LogOut } from 'lucide-react';
import { useBillStore } from './store/useBillStore';
import { useAuthStore } from './store/useAuthStore';
import Dashboard from './components/Dashboard';
import BillEditor from './components/BillEditor';
import GeneratePanel from './components/GeneratePanel';
import ExcelUploader from './components/ExcelUploader';
import ImageUploader from './components/ImageUploader';
import TemplateGenerator from './components/TemplateGenerator';
import Login from './components/Login';

const queryClient = new QueryClient();

function AppInner() {
  const { viewMode } = useBillStore();
  const { token, logout } = useAuthStore();
  const [showUploader, setShowUploader] = useState(false);
  const [showImageUploader, setShowImageUploader] = useState(false);
  const [showTemplateGenerator, setShowTemplateGenerator] = useState(false);
  const [toastMsg, setToastMsg] = useState<{ type: string; msg: string } | null>(null);

  const toast = (type: 'success' | 'error' | 'warning' | 'info', msg: string) => {
    setToastMsg({ type, msg });
    setTimeout(() => setToastMsg(null), 3500);
  };

  // if (!token) {
  //   return <Login />;
  // }

  return (
    <div className="min-h-screen bg-surface-950">
      {/* Nav */}
      <nav className="glass border-b border-white/[0.06] sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent-500/20 border border-accent-500/30 flex items-center justify-center">
              <FileText size={16} className="text-accent-400" />
            </div>
            <span className="font-bold text-white tracking-tight">BillForge</span>
            <span className="text-xs text-slate-600 ml-1">PWD Contractor Bill Generator</span>
          </div>
          <button 
            onClick={logout}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-300 hover:text-white bg-white/5 hover:bg-white/10 rounded-lg transition-colors border border-white/5"
          >
            <LogOut size={16} /> Logout
          </button>
        </div>
      </nav>

      {/* Toast */}
      {toastMsg && (
        <div className={`fixed top-16 right-4 z-50 px-4 py-3 rounded-xl text-sm font-medium shadow-lg animate-slide-up
          ${toastMsg.type === 'success' ? 'bg-green-500/20 border border-green-500/30 text-green-300' :
            toastMsg.type === 'error'   ? 'bg-red-500/20 border border-red-500/30 text-red-300' :
            toastMsg.type === 'warning' ? 'bg-yellow-500/20 border border-yellow-500/30 text-yellow-300' :
            'bg-blue-500/20 border border-blue-500/30 text-blue-300'}`}
        >
          {toastMsg.msg}
        </div>
      )}

      {/* Main */}
      <main className="max-w-5xl mx-auto px-4 py-6">
        {viewMode === 'dashboard'   && <Dashboard onOpenUploader={() => setShowUploader(true)} onOpenImageUploader={() => setShowImageUploader(true)} onOpenTemplateGenerator={() => setShowTemplateGenerator(true)} />}
        {viewMode === 'edit'        && <BillEditor />}
        {viewMode === 'generating'  && <GeneratePanel />}
      </main>

      {showUploader && (
        <ExcelUploader onClose={() => setShowUploader(false)} toast={toast} />
      )}
      {showImageUploader && (
        <ImageUploader onClose={() => setShowImageUploader(false)} toast={toast} />
      )}
      {showTemplateGenerator && (
        <TemplateGenerator onClose={() => setShowTemplateGenerator(false)} toast={toast} />
      )}
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppInner />
    </QueryClientProvider>
  );
}
