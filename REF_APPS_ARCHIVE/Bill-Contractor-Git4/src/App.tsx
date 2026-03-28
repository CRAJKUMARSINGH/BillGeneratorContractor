import { useState, useEffect, Suspense } from 'react';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { FileText, LogOut, Loader2 } from 'lucide-react';
import { supabase } from './lib/supabase';
import { fetchBills } from './lib/billService';
import { useBillStore } from './store/useBillStore';
import { useToast } from './hooks/useToast';
import { ToastContainer } from './components/ui/Toast';
import AuthModal from './components/AuthModal';
import Dashboard from './components/Dashboard';
import BillEditor from './components/BillEditor';
import BillPreview from './components/BillPreview';
import ExcelUploader from './components/ExcelUploader';

// ─── Query client ─────────────────────────────────────────────────────────────
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
});

// ─── Inner app (needs QueryClient context) ────────────────────────────────────
function AppInner() {
  const [user, setUser] = useState<{ id: string; email: string } | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [showUploader, setShowUploader] = useState(false);
  const { toasts, toast, dismiss } = useToast();
  const { viewMode } = useBillStore();

  // Auth
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      const u = session?.user;
      setUser(u ? { id: u.id, email: u.email ?? '' } : null);
      setAuthLoading(false);
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, session) => {
      const u = session?.user;
      setUser(u ? { id: u.id, email: u.email ?? '' } : null);
    });
    return () => subscription.unsubscribe();
  }, []);

  // Bills query
  const { data: bills = [], refetch } = useQuery({
    queryKey: ['bills', user?.id],
    queryFn: fetchBills,
    enabled: !!user,
  });

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    queryClient.clear();
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-surface-950 flex items-center justify-center">
        <Loader2 size={32} className="text-accent-400 animate-spin" />
      </div>
    );
  }

  if (!user) {
    return (
      <>
        <AuthModal
          onSuccess={() => {
            supabase.auth.getSession().then(({ data: { session } }) => {
              const u = session?.user;
              setUser(u ? { id: u.id, email: u.email ?? '' } : null);
            });
          }}
          toast={toast}
        />
        <ToastContainer toasts={toasts} onDismiss={dismiss} />
      </>
    );
  }

  return (
    <div className="min-h-screen bg-surface-950 bg-mesh-dark">
      {/* Nav */}
      <nav className="glass border-b border-white/[0.06] sticky top-0 z-40 no-print">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent-500/20 border border-accent-500/30 flex items-center justify-center">
              <FileText size={16} className="text-accent-400" />
            </div>
            <span className="font-bold text-white tracking-tight">BillForge</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500 hidden sm:block">{user.email}</span>
            <button onClick={handleSignOut} className="btn-ghost py-1.5 text-xs">
              <LogOut size={14} /> Sign Out
            </button>
          </div>
        </div>
      </nav>

      {/* Main */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {viewMode === 'dashboard' && (
          <Dashboard
            bills={bills}
            onRefresh={() => refetch()}
            onOpenUploader={() => setShowUploader(true)}
            toast={toast}
          />
        )}
        {viewMode === 'edit' && (
          <BillEditor
            userId={user.id}
            onSaved={() => refetch()}
            toast={toast}
          />
        )}
        {viewMode === 'preview' && (
          <Suspense fallback={
            <div className="flex items-center justify-center py-20">
              <Loader2 size={28} className="text-accent-400 animate-spin" />
            </div>
          }>
            <BillPreview />
          </Suspense>
        )}
      </main>

      {/* Excel uploader modal */}
      {showUploader && (
        <ExcelUploader
          onClose={() => setShowUploader(false)}
          toast={toast}
        />
      )}

      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </div>
  );
}

// ─── Root with providers ──────────────────────────────────────────────────────
export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppInner />
    </QueryClientProvider>
  );
}
