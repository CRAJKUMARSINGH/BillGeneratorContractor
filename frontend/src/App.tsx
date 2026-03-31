import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FileText, LogOut, LayoutDashboard, Globe } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useBillStore } from './store/useBillStore';
import { useAuthStore } from './store/useAuthStore';
import Dashboard from './components/Dashboard';
import BillEditor from './components/BillEditor';
import GeneratePanel from './components/GeneratePanel';
import ExcelUploader from './components/ExcelUploader';
import ImageUploader from './components/ImageUploader';
import TemplateGenerator from './components/TemplateGenerator';
import LandingPage from './components/LandingPage';
import Login from './components/Login';

const queryClient = new QueryClient();

function AppInner() {
  const { viewMode, setViewMode } = useBillStore();
  const { token, logout } = useAuthStore();
  const [showUploader, setShowUploader] = useState(false);
  const [showImageUploader, setShowImageUploader] = useState(false);
  const [showTemplateGenerator, setShowTemplateGenerator] = useState(false);
  const [toastMsg, setToastMsg] = useState<{ type: string; msg: string } | null>(null);

  const toast = (type: 'success' | 'error' | 'warning' | 'info', msg: string) => {
    setToastMsg({ type, msg });
    setTimeout(() => setToastMsg(null), 3500);
  };

  return (
    <div className="min-h-screen bg-surface-950 font-sans selection:bg-gold-500/30">
      {/* Premium Navbar */}
      <nav className="glass border-b border-white/[0.06] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div 
            className="flex items-center gap-3 cursor-pointer group"
            onClick={() => setViewMode('landing')}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-400 to-indigo-800 flex items-center justify-center shadow-lg group-hover:shadow-indigo-500/20 transition-all">
              <FileText size={20} className="text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-heading font-bold text-lg text-white tracking-tight">BillForge</span>
                <span className="px-1.5 py-0.5 rounded bg-gold-500/10 border border-gold-500/20 text-[10px] font-bold text-gold-500 uppercase tracking-tighter">v2.1</span>
              </div>
              <p className="text-[10px] text-slate-500 font-medium uppercase tracking-widest leading-none">PWD Contractor Suite</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button className="hidden sm:flex items-center gap-2 px-3 py-1.5 text-xs font-bold text-slate-400 hover:text-gold-400 transition-colors uppercase tracking-widest">
              <Globe size={14} /> Hindi
            </button>
            
            {token ? (
              <div className="flex items-center gap-3">
                <button 
                  onClick={() => setViewMode('dashboard')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all border
                    ${viewMode === 'dashboard' 
                      ? 'bg-primary-400/10 border-primary-400/30 text-primary-300' 
                      : 'text-slate-400 hover:text-white border-transparent hover:bg-white/5'}`}
                >
                  <LayoutDashboard size={14} /> Dashboard
                </button>
                <div className="h-6 w-px bg-white/10 mx-1" />
                <button 
                  onClick={logout}
                  className="p-2.5 text-slate-400 hover:text-red-400 bg-white/5 hover:bg-red-500/10 rounded-xl transition-all border border-transparent hover:border-red-500/20"
                >
                  <LogOut size={18} />
                </button>
              </div>
            ) : (
              <button 
                onClick={() => setViewMode('dashboard')} // Dashboard mode will show Login if no token
                className="btn-primary"
              >
                Login to Portal
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Toast Notification */}
      <AnimatePresence>
        {toastMsg && (
          <motion.div 
            initial={{ opacity: 0, y: -20, x: 20 }}
            animate={{ opacity: 1, y: 0, x: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className={`fixed top-20 right-6 z-[60] px-5 py-3 rounded-2xl text-sm font-semibold shadow-2xl backdrop-blur-xl
              ${toastMsg.type === 'success' ? 'bg-green-500/20 border border-green-500/30 text-green-300' :
                toastMsg.type === 'error'   ? 'bg-red-500/20 border border-red-500/30 text-red-300' :
                toastMsg.type === 'warning' ? 'bg-yellow-500/20 border border-yellow-500/30 text-yellow-300' :
                'bg-primary-500/20 border border-primary-500/30 text-primary-300'}`}
          >
            <div className="flex items-center gap-3">
              <div className={`w-2 h-2 rounded-full animate-pulse
                ${toastMsg.type === 'success' ? 'bg-green-400' : 'bg-red-400'}`} 
              />
              {toastMsg.msg}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Page Content with Transitions */}
      <main>
        <AnimatePresence mode="wait">
          <motion.div
            key={viewMode + (token ? 'auth' : 'noauth')}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className={viewMode === 'landing' ? '' : 'max-w-7xl mx-auto px-6 py-8'}
          >
            {viewMode === 'landing' && <LandingPage />}
            
            {!token && viewMode !== 'landing' && <Login />}
            
            {token && (
              <>
                {viewMode === 'dashboard'   && <Dashboard onOpenUploader={() => setShowUploader(true)} onOpenImageUploader={() => setShowImageUploader(true)} onOpenTemplateGenerator={() => setShowTemplateGenerator(true)} />}
                {viewMode === 'edit'        && <BillEditor />}
                {viewMode === 'generating'  && <GeneratePanel />}
              </>
            )}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Modals */}
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
