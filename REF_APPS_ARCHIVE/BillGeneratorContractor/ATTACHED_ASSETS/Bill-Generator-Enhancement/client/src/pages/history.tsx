import React, { useState } from "react";
import { motion } from "framer-motion";
import { format } from "date-fns";
import { 
  FileText, Image as ImageIcon, Clock, 
  CheckCircle2, AlertCircle, ChevronRight,
  Search, ArrowLeft
} from "lucide-react";
import { Layout } from "@/components/layout";
import { useJobs } from "@/hooks/use-jobs";
import { ResultsView } from "@/components/results-view";
import type { ExtractionJob } from "@shared/schema";

export default function History() {
  const { data: jobs, isLoading } = useJobs();
  const [selectedJob, setSelectedJob] = useState<ExtractionJob | null>(null);

  if (selectedJob) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto">
          <button 
            onClick={() => setSelectedJob(null)}
            className="flex items-center gap-2 text-slate-500 hover:text-slate-900 mb-8 font-medium transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to History
          </button>
          <ResultsView job={selectedJob} onNew={() => setSelectedJob(null)} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-5xl mx-auto">
        <header className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">
              Recent Jobs
            </h1>
            <p className="text-slate-500 mt-2">
              View past extractions, download previous bills, and review validation errors.
            </p>
          </div>
          <div className="relative">
            <Search className="h-5 w-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search history..." 
              className="pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary w-full md:w-64 transition-all"
            />
          </div>
        </header>

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-white rounded-2xl border border-slate-100 shadow-sm animate-pulse" />
            ))}
          </div>
        ) : !jobs || jobs.length === 0 ? (
          <div className="text-center py-20 bg-white border border-dashed border-slate-200 rounded-3xl">
            <Clock className="h-12 w-12 text-slate-300 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-slate-900">No history yet</h3>
            <p className="text-slate-500 mt-2">Generate your first bill to see it here.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {jobs.map((job) => (
              <motion.div
                key={job.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white hover:bg-slate-50 border border-slate-200 rounded-2xl p-4 flex items-center justify-between cursor-pointer transition-all shadow-sm hover:shadow-md"
                onClick={() => setSelectedJob(job)}
              >
                <div className="flex items-center gap-5">
                  <div className={`h-12 w-12 rounded-xl flex items-center justify-center shrink-0 ${
                    job.status === 'success' ? 'bg-success/10' : 'bg-destructive/10'
                  }`}>
                    {job.status === 'success' 
                      ? <CheckCircle2 className="h-6 w-6 text-success" />
                      : <AlertCircle className="h-6 w-6 text-destructive" />
                    }
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900">Job #{job.id}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-md font-semibold ${
                        job.status === 'success' ? 'bg-success/10 text-success' : 'bg-destructive/10 text-destructive'
                      }`}>
                        {job.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4 mt-1 text-sm text-slate-500">
                      <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> {format(new Date(job.createdAt || new Date()), "MMM d, yyyy h:mm a")}</span>
                      <span className="hidden sm:inline text-slate-300">•</span>
                      <span className="flex items-center gap-1 truncate max-w-[150px]"><ImageIcon className="h-3.5 w-3.5" /> {job.imageFilename}</span>
                      <span className="hidden sm:inline text-slate-300">•</span>
                      <span className="flex items-center gap-1 truncate max-w-[150px]"><FileText className="h-3.5 w-3.5" /> {job.qtyFilename}</span>
                    </div>
                  </div>
                </div>
                <div className="pl-4">
                  <div className="h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 group-hover:bg-primary group-hover:text-white transition-colors">
                    <ChevronRight className="h-5 w-5" />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
