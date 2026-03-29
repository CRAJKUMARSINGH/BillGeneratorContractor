import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileSpreadsheet, PenLine, HelpCircle, BookOpen,
  ChevronRight, Activity, Menu, X
} from "lucide-react";
import { Toaster } from "@/components/ui/toaster";
import { UploadPage } from "@/pages/UploadPage";
import { PreviewPage } from "@/pages/PreviewPage";
import { useStore } from "@/lib/store";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
    mutations: { retry: 0 },
  },
});

type AppPage = "upload" | "preview" | "manual" | "help";

const navItems: { id: AppPage; icon: typeof FileSpreadsheet; label: string; sub: string }[] = [
  { id: "upload", icon: FileSpreadsheet, label: "Excel Upload", sub: "Upload .xlsx / .xlsm" },
  { id: "manual", icon: PenLine, label: "Manual Entry", sub: "Enter data online" },
  { id: "help", icon: HelpCircle, label: "Help & Guide", sub: "How to use" },
];

function Sidebar({
  currentPage,
  onNavigate,
  open,
  onClose,
}: {
  currentPage: AppPage;
  onNavigate: (p: AppPage) => void;
  open: boolean;
  onClose: () => void;
}) {
  const billData = useStore((s) => s.billData);

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed top-0 left-0 h-full z-30 w-64 glass-sidebar flex flex-col transition-transform duration-300
          ${open ? "translate-x-0" : "-translate-x-full"}
          lg:relative lg:translate-x-0 lg:z-auto
        `}
      >
        {/* Logo / Brand */}
        <div className="p-5 border-b border-sidebar-border">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary/20 border border-primary/30 flex items-center justify-center">
              <BookOpen size={18} className="text-primary" />
            </div>
            <div>
              <p className="font-bold text-sm text-foreground leading-none">Bill Generator</p>
              <p className="text-xs text-muted-foreground mt-0.5">PWD Contractor Bills</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = currentPage === item.id || (item.id === "upload" && currentPage === "preview");
            return (
              <button
                key={item.id}
                onClick={() => { onNavigate(item.id); onClose(); }}
                className={`
                  w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200
                  ${active
                    ? "bg-primary/15 text-primary border border-primary/20"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                  }
                `}
              >
                <Icon size={17} className="shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium leading-none">{item.label}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{item.sub}</p>
                </div>
                {active && <ChevronRight size={14} className="shrink-0 text-primary" />}
              </button>
            );
          })}
        </nav>

        {/* Bill Status */}
        {billData && (
          <div className="p-3 border-t border-sidebar-border">
            <div className="glass rounded-xl p-3">
              <div className="flex items-center gap-2 mb-2">
                <Activity size={13} className="text-primary" />
                <span className="text-xs font-semibold text-primary uppercase tracking-wider">Active Bill</span>
              </div>
              <p className="text-xs font-medium text-foreground truncate">{billData.fileName}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {billData.billItems.length} items · {billData.hasExtraItems ? "With extras" : "No extras"}
              </p>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="p-4 border-t border-sidebar-border">
          <p className="text-xs text-muted-foreground text-center">
            PWD Udaipur · v2.0 · 2026
          </p>
        </div>
      </aside>
    </>
  );
}

function HelpPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h2 className="text-2xl font-bold mb-2">Help & Guide</h2>
      <p className="text-muted-foreground mb-8">How to use the Bill Generator</p>

      <div className="space-y-4">
        {[
          {
            step: "1",
            title: "Prepare your Excel file",
            desc: "Your .xlsx or .xlsm file should have at minimum a Title sheet and a Bill Quantity sheet. Optional: Extra Items sheet for additional works.",
          },
          {
            step: "2",
            title: "Upload the Excel file",
            desc: "Go to Excel Upload, drag and drop or browse to select your file. Click 'Extract Bill Data' to parse the spreadsheet.",
          },
          {
            step: "3",
            title: "Preview and Edit",
            desc: "After extraction, review all fields in the preview screen. You can edit any field inline — click any cell to change its value. Amounts recalculate automatically when you change quantity or rate.",
          },
          {
            step: "4",
            title: "Generate Documents",
            desc: "Select your required output formats (PDF, HTML) and click 'Generate Bill'. The system creates all required bill documents including First Page, Note Sheet, Certificates, Deviation Statement, and Extra Items.",
          },
          {
            step: "5",
            title: "Download",
            desc: "Once generation is complete, download individual PDFs or the complete ZIP archive containing all bill documents.",
          },
        ].map((item) => (
          <div key={item.step} className="glass-card rounded-xl p-5 flex gap-4">
            <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center shrink-0">
              <span className="text-sm font-bold text-primary">{item.step}</span>
            </div>
            <div>
              <h3 className="font-semibold mb-1">{item.title}</h3>
              <p className="text-sm text-muted-foreground">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 glass-card rounded-xl p-5 border-l-4 border-l-primary">
        <h3 className="font-semibold text-primary mb-2">Supported Excel Sheet Names</h3>
        <div className="grid grid-cols-2 gap-x-8 gap-y-1 text-sm text-muted-foreground">
          <div><span className="text-foreground font-medium">Title:</span> Title, TITLE, title, Sheet1</div>
          <div><span className="text-foreground font-medium">Bill:</span> Bill Quantity, Bill, BILL, Data</div>
          <div><span className="text-foreground font-medium">Extra:</span> Extra Items, Extra, EXTRA</div>
        </div>
      </div>
    </div>
  );
}

function ManualEntryPage() {
  return (
    <div className="flex items-center justify-center min-h-[60vh] px-4">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-4">
          <PenLine size={28} className="text-muted-foreground" />
        </div>
        <h2 className="text-xl font-bold mb-2">Manual Entry</h2>
        <p className="text-muted-foreground text-sm">
          Online manual data entry form is coming in the next phase. For now, please use Excel Upload to process your bills.
        </p>
      </div>
    </div>
  );
}

function AppContent() {
  const [page, setPage] = useState<AppPage>("upload");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const billData = useStore((s) => s.billData);

  const navigate = (p: AppPage) => setPage(p);

  const handleUploadSuccess = () => setPage("preview");
  const handleBack = () => setPage("upload");

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar
        currentPage={page}
        onNavigate={navigate}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="h-14 border-b border-border/40 flex items-center gap-3 px-4 shrink-0 bg-card/30 backdrop-blur-sm">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-1.5 rounded-lg hover:bg-muted transition-colors"
          >
            <Menu size={18} />
          </button>
          <div className="flex-1 flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">Bill Generator</span>
            <ChevronRight size={14} className="text-muted-foreground" />
            <span className="font-medium text-foreground capitalize">
              {page === "preview" ? "Preview & Edit" : page === "upload" ? "Excel Upload" : page === "manual" ? "Manual Entry" : "Help"}
            </span>
          </div>
          {billData && page === "upload" && (
            <button
              onClick={() => setPage("preview")}
              className="text-xs text-primary hover:underline font-medium"
            >
              Back to Preview →
            </button>
          )}
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={page}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="min-h-full"
            >
              {page === "upload" && <UploadPage onSuccess={handleUploadSuccess} />}
              {page === "preview" && <PreviewPage onBack={handleBack} />}
              {page === "manual" && <ManualEntryPage />}
              {page === "help" && <HelpPage />}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;
