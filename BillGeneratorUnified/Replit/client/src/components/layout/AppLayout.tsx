import React from "react";
import { Link, useLocation } from "wouter";
import { motion } from "framer-motion";
import { 
  FileSpreadsheet, 
  History, 
  Settings, 
  LayoutDashboard,
  LogOut,
  Menu
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const [location] = useLocation();
  const [sidebarOpen, setSidebarOpen] = React.useState(true);

  const navItems = [
    { label: "Dashboard", icon: LayoutDashboard, path: "/" },
    { label: "Upload Excel", icon: FileSpreadsheet, path: "/upload" },
    { label: "Saved Bills", icon: History, path: "/history" },
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-transparent">
      {/* Sidebar - Hidden in Print */}
      <motion.aside 
        initial={{ width: 260 }}
        animate={{ width: sidebarOpen ? 260 : 80 }}
        className="no-print hidden md:flex flex-col glass-panel shadow-xl z-20 transition-all duration-300 border-r border-white/40"
      >
        <div className="p-6 flex items-center gap-3">
          <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white shadow-lg">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
          {sidebarOpen && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="overflow-hidden whitespace-nowrap">
              <h2 className="font-display font-bold text-lg leading-tight text-foreground">BillGenerator</h2>
              <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Unified Pro</p>
            </motion.div>
          )}
        </div>

        <div className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = location === item.path || (item.path !== "/" && location.startsWith(item.path));
            return (
              <Link key={item.path} href={item.path} className="block">
                <div
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group cursor-pointer",
                    isActive 
                      ? "bg-white shadow-md shadow-primary/5 text-primary font-semibold border border-white/60" 
                      : "text-foreground/70 hover:bg-white/50 hover:text-foreground"
                  )}
                >
                  <item.icon className={cn("w-5 h-5 transition-colors", isActive ? "text-primary" : "text-foreground/50 group-hover:text-foreground/80")} />
                  {sidebarOpen && <span>{item.label}</span>}
                </div>
              </Link>
            );
          })}
        </div>

        <div className="p-4 border-t border-white/40">
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="w-full flex items-center justify-center p-3 rounded-xl hover:bg-white/50 text-foreground/50 transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
        <div className="flex-1 overflow-auto p-4 md:p-8 print:p-0 print:overflow-visible">
          <div className="max-w-7xl mx-auto print:max-w-none print:mx-0">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
