import React from "react";
import { Link, useLocation } from "wouter";
import { Receipt, ListTree, History, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

export function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();

  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row overflow-hidden">
      {/* Sidebar */}
      <aside className="w-full md:w-72 bg-white border-r border-slate-200 flex flex-col z-10 shrink-0">
        <div className="h-20 flex items-center px-6 border-b border-slate-100">
          <div className="flex items-center gap-3 text-primary font-display font-bold text-xl">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary to-indigo-400 flex items-center justify-center text-white shadow-lg shadow-primary/20">
              <Receipt className="h-5 w-5" />
            </div>
            BillGen <span className="text-slate-400 font-medium">Pro</span>
          </div>
        </div>

        <div className="p-4 flex-1 flex flex-col gap-2">
          <p className="px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 mt-4">
            Workspace
          </p>
          <Link href="/" className="block">
            <span
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all duration-200",
                location === "/"
                  ? "bg-primary/10 text-primary"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              <Plus className="h-5 w-5" />
              New Extraction
            </span>
          </Link>
          <Link href="/history" className="block">
            <span
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all duration-200",
                location === "/history"
                  ? "bg-primary/10 text-primary"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              <History className="h-5 w-5" />
              Recent Jobs
            </span>
          </Link>
        </div>
        
        <div className="p-6 border-t border-slate-100 bg-slate-50">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-slate-200 border-2 border-white shadow-sm flex items-center justify-center font-bold text-slate-600">
              CT
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-bold text-slate-900">Contractor Tool</span>
              <span className="text-xs text-slate-500">v2.1.0 Enterprise</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 relative h-screen overflow-y-auto">
        {/* Subtle background decoration */}
        <div className="absolute top-0 left-0 w-full h-[500px] bg-gradient-to-b from-indigo-50/50 to-transparent pointer-events-none -z-10" />
        <div className="p-4 md:p-8 lg:p-12 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
