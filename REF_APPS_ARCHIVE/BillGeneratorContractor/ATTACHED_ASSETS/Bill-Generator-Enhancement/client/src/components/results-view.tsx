import React from "react";
import { format } from "date-fns";
import { motion } from "framer-motion";
import { 
  CheckCircle2, 
  Download, 
  FileSpreadsheet, 
  AlertCircle, 
  FileText,
  Image as ImageIcon
} from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ExtractionJob, ParsedItem } from "@shared/schema";

export function ResultsView({ job, onNew }: { job: ExtractionJob; onNew: () => void }) {
  if (job.status === "error") {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel rounded-3xl p-8 max-w-3xl border-red-100 overflow-hidden relative"
      >
        <div className="absolute top-0 left-0 w-2 h-full bg-destructive" />
        
        <div className="flex items-start gap-5">
          <div className="h-14 w-14 rounded-2xl bg-red-100 flex items-center justify-center shrink-0">
            <AlertCircle className="h-7 w-7 text-destructive" />
          </div>
          <div>
            <h2 className="text-2xl font-display font-bold text-slate-900">Extraction Failed</h2>
            <p className="mt-2 text-slate-600 text-lg">
              We encountered a strict validation error while processing your files. To prevent generating an incorrect bill, processing was halted.
            </p>
            
            <div className="mt-6 p-4 bg-red-50 border border-red-100 rounded-xl text-red-800 font-mono text-sm leading-relaxed">
              {job.errorMessage || "Unknown validation error occurred during OCR matching."}
            </div>
            
            <div className="mt-8 flex gap-4">
              <Button onClick={onNew} size="lg">
                Try Again
              </Button>
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  const items = (job.resultData as ParsedItem[]) || [];
  const totalAmount = items.reduce((sum, item) => sum + item.amount, 0);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <div className="glass-panel rounded-3xl p-8 border-green-100 overflow-hidden relative">
        <div className="absolute top-0 left-0 w-2 h-full bg-success" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <div className="h-14 w-14 rounded-2xl bg-green-100 flex items-center justify-center shrink-0">
              <CheckCircle2 className="h-7 w-7 text-success" />
            </div>
            <div>
              <h2 className="text-2xl font-display font-bold text-slate-900">Extraction Successful</h2>
              <p className="text-slate-500 mt-1">
                Processed {items.length} items on {format(new Date(job.createdAt || new Date()), "MMM d, yyyy 'at' h:mm a")}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Button onClick={onNew} variant="outline">
              Process Another
            </Button>
            {job.excelUrl && (
              <Button asChild className="bg-success hover:bg-success/90 shadow-success/20">
                <a href={job.excelUrl} download>
                  <FileSpreadsheet className="h-5 w-5 mr-2" />
                  Download Excel
                </a>
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/40 border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Extracted Bill of Quantities</h3>
            <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
              <span className="flex items-center gap-1.5"><ImageIcon className="h-4 w-4" /> {job.imageFilename}</span>
              <span className="flex items-center gap-1.5"><FileText className="h-4 w-4" /> {job.qtyFilename}</span>
            </div>
          </div>
          <div className="bg-white px-4 py-2 rounded-xl border border-slate-200 shadow-sm text-right">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Amount</div>
            <div className="text-xl font-mono font-bold text-slate-900">₹{totalAmount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500 font-semibold">
                <th className="p-4 pl-6 w-24">Item Code</th>
                <th className="p-4">Description</th>
                <th className="p-4 w-24">Unit</th>
                <th className="p-4 text-right w-32">Rate (₹)</th>
                <th className="p-4 text-right w-32">Qty</th>
                <th className="p-4 pr-6 text-right w-40">Amount (₹)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                  <td className="p-4 pl-6 font-mono text-sm text-slate-600">{item.code}</td>
                  <td className="p-4 text-sm text-slate-900 font-medium">{item.description}</td>
                  <td className="p-4 text-sm text-slate-500">
                    <span className="bg-slate-100 text-slate-600 px-2.5 py-1 rounded-md text-xs font-medium">
                      {item.unit}
                    </span>
                  </td>
                  <td className="p-4 text-right font-mono text-sm text-slate-700">
                    {item.rate.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="p-4 text-right font-mono text-sm text-primary font-medium">
                    {item.qty.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="p-4 pr-6 text-right font-mono font-semibold text-slate-900">
                    {item.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-500">
                    No items found in this extraction.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
}
