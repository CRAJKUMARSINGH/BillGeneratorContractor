import { useState } from "react";
import { motion } from "framer-motion";
import {
  FileText, Plus, Trash2, ChevronDown, ChevronRight,
  Loader2, Download, CheckCircle2, AlertCircle, RefreshCw
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useStore } from "@/lib/store";
import { useGenerateBill, useJobStatus, getDownloadUrl } from "@/hooks/use-bills";

interface PreviewPageProps {
  onBack: () => void;
}

function formatINR(amount: number): string {
  if (!amount || isNaN(amount)) return "₹ 0.00";
  return "₹ " + amount.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function PreviewPage({ onBack }: PreviewPageProps) {
  const { billData, updateTitleData, updateBillItem, updateExtraItem, generateOptions, setGenerateOptions } = useStore();
  const generateMutation = useGenerateBill();
  const [jobId, setJobId] = useState<string | null>(null);
  const [showExtra, setShowExtra] = useState(true);
  const [showBillItems, setShowBillItems] = useState(true);

  const jobQuery = useJobStatus(jobId);
  const job = jobQuery.data;

  if (!billData) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] text-muted-foreground">
        No bill data loaded. Please upload an Excel file first.
      </div>
    );
  }

  const titleFields = [
    { key: "Name of Work", label: "Name of Work / कार्य का नाम" },
    { key: "Contractor", label: "Contractor / ठेकेदार" },
    { key: "Agreement No", label: "Agreement No." },
    { key: "Budget Head", label: "Budget Head" },
    { key: "Serial No. of this bill :", label: "Bill Serial No." },
    { key: "Amount of Work Order", label: "Work Order Amount" },
    { key: "Date of Start", label: "Date of Start" },
    { key: "Stipulated Date of Completion", label: "Stipulated Completion" },
    { key: "Tender Premium %", label: "Tender Premium %" },
    { key: "Sub-Division", label: "Sub-Division" },
    { key: "Divisional Officer", label: "Divisional Officer" },
  ];

  const handleGenerate = async () => {
    try {
      const result = await generateMutation.mutateAsync({
        fileId: billData.fileId,
        titleData: billData.titleData,
        billItems: billData.billItems,
        extraItems: billData.extraItems,
        options: generateOptions,
      });
      setJobId(result.jobId);
    } catch (_) {}
  };

  const totalAmount = billData.billItems.reduce((s, i) => s + (i.amount || 0), 0);
  const extraTotal = billData.extraItems.reduce((s, i) => s + (i.amount || 0), 0);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <button onClick={onBack} className="hover:text-primary transition-colors">Upload</button>
            <ChevronRight size={14} />
            <span className="text-foreground font-medium">Preview & Edit</span>
          </div>
          <h2 className="text-2xl font-bold text-foreground">Bill Preview & Editor</h2>
          <p className="text-sm text-muted-foreground mt-1">
            {billData.fileName} · {billData.sheets.length} sheets detected
          </p>
        </div>
        <Button onClick={onBack} variant="outline" size="sm">
          <RefreshCw size={14} className="mr-1.5" /> New Upload
        </Button>
      </div>

      {/* Generation Result */}
      {job && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`rounded-xl border p-5 ${
            job.status === "complete"
              ? "bg-primary/10 border-primary/30"
              : job.status === "error"
              ? "bg-destructive/10 border-destructive/30"
              : "bg-card border-border"
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              {job.status === "complete" ? (
                <CheckCircle2 size={18} className="text-primary" />
              ) : job.status === "error" ? (
                <AlertCircle size={18} className="text-destructive" />
              ) : (
                <Loader2 size={18} className="animate-spin text-primary" />
              )}
              <span className="font-medium text-sm">
                {job.status === "complete"
                  ? "Documents Generated Successfully"
                  : job.status === "error"
                  ? `Error: ${job.error}`
                  : `${job.message || "Generating..."} (${Math.round(job.progress || 0)}%)`}
              </span>
            </div>
          </div>

          {/* Progress Bar */}
          {(job.status === "pending" || job.status === "processing") && (
            <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${job.progress || 0}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          )}

          {/* Download Buttons */}
          {job.status === "complete" && jobId && (
            <div className="flex flex-wrap gap-2 mt-3">
              {generateOptions.generatePdf && (
                <a href={getDownloadUrl(jobId, "pdf")} download>
                  <Button size="sm" className="h-8">
                    <Download size={13} className="mr-1.5" /> PDF
                  </Button>
                </a>
              )}
              {generateOptions.generateHtml && (
                <a href={getDownloadUrl(jobId, "html")} download>
                  <Button size="sm" variant="outline" className="h-8">
                    <Download size={13} className="mr-1.5" /> HTML
                  </Button>
                </a>
              )}
              <a href={getDownloadUrl(jobId, "zip")} download>
                <Button size="sm" variant="secondary" className="h-8">
                  <Download size={13} className="mr-1.5" /> All (ZIP)
                </Button>
              </a>
            </div>
          )}
        </motion.div>
      )}

      {/* Bento Grid — Title Data */}
      <div className="glass-card rounded-2xl p-5">
        <h3 className="text-sm font-semibold text-primary mb-4 uppercase tracking-wider">
          Project Details / परियोजना विवरण
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {titleFields.map(({ key, label }) => (
            <div key={key} className="bg-muted/30 rounded-lg p-3 border border-border/30">
              <label className="block text-xs text-muted-foreground mb-1">{label}</label>
              <input
                type="text"
                className="edit-cell text-sm font-medium"
                value={billData.titleData[key] || ""}
                onChange={(e) => updateTitleData(key, e.target.value)}
                placeholder="—"
              />
            </div>
          ))}
          {/* Render any extra keys not in predefined list */}
          {Object.entries(billData.titleData)
            .filter(([k]) => !titleFields.find((f) => f.key === k))
            .map(([key, value]) => (
              <div key={key} className="bg-muted/30 rounded-lg p-3 border border-border/30">
                <label className="block text-xs text-muted-foreground mb-1">{key}</label>
                <input
                  type="text"
                  className="edit-cell text-sm font-medium"
                  value={value || ""}
                  onChange={(e) => updateTitleData(key, e.target.value)}
                  placeholder="—"
                />
              </div>
            ))}
        </div>
      </div>

      {/* Bill Items Table */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <div
          className="flex items-center justify-between p-5 cursor-pointer hover:bg-white/5 transition-colors"
          onClick={() => setShowBillItems((v) => !v)}
        >
          <div className="flex items-center gap-2">
            {showBillItems ? <ChevronDown size={16} className="text-primary" /> : <ChevronRight size={16} className="text-primary" />}
            <h3 className="text-sm font-semibold text-primary uppercase tracking-wider">
              Bill Quantity Items ({billData.billItems.length})
            </h3>
          </div>
          <span className="text-sm font-semibold text-foreground">{formatINR(totalAmount)}</span>
        </div>

        {showBillItems && (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-t border-border/40 bg-muted/30">
                  {["Item No.", "Description", "Unit", "Qty Since", "Qty Upto", "Quantity", "Rate (₹)", "Amount (₹)"].map((h) => (
                    <th key={h} className="px-3 py-2 text-left font-semibold text-muted-foreground whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {billData.billItems.map((item, i) => (
                  <tr
                    key={i}
                    className={`border-t border-border/20 hover:bg-white/5 transition-colors ${
                      item.amount === 0 ? "opacity-50" : ""
                    }`}
                  >
                    <td className="px-3 py-2">
                      <input className="edit-cell w-20 font-mono" value={item.itemNo || ""} onChange={(e) => updateBillItem(i, "itemNo", e.target.value)} />
                    </td>
                    <td className="px-3 py-2">
                      <input className="edit-cell min-w-[200px]" value={item.description || ""} onChange={(e) => updateBillItem(i, "description", e.target.value)} />
                    </td>
                    <td className="px-3 py-2">
                      <input className="edit-cell w-12" value={item.unit || ""} onChange={(e) => updateBillItem(i, "unit", e.target.value)} />
                    </td>
                    <td className="px-3 py-2 text-right">
                      <input className="edit-cell w-20 text-right" type="number" value={item.quantitySince || 0} onChange={(e) => updateBillItem(i, "quantitySince", parseFloat(e.target.value) || 0)} />
                    </td>
                    <td className="px-3 py-2 text-right">
                      <input className="edit-cell w-20 text-right" type="number" value={item.quantityUpto || 0} onChange={(e) => updateBillItem(i, "quantityUpto", parseFloat(e.target.value) || 0)} />
                    </td>
                    <td className="px-3 py-2 text-right">
                      <input className="edit-cell w-20 text-right" type="number" value={item.quantity || 0} onChange={(e) => updateBillItem(i, "quantity", parseFloat(e.target.value) || 0)} />
                    </td>
                    <td className="px-3 py-2 text-right">
                      <input className="edit-cell w-24 text-right" type="number" value={item.rate || 0} onChange={(e) => updateBillItem(i, "rate", parseFloat(e.target.value) || 0)} />
                    </td>
                    <td className="px-3 py-2 text-right font-medium text-foreground">
                      {formatINR(item.amount || 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-primary/30 bg-primary/5">
                  <td colSpan={7} className="px-3 py-3 text-right font-bold text-sm">Bill Total:</td>
                  <td className="px-3 py-3 text-right font-bold text-primary">{formatINR(totalAmount)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>

      {/* Extra Items Table */}
      {billData.hasExtraItems && (
        <div className="glass-card rounded-2xl overflow-hidden">
          <div
            className="flex items-center justify-between p-5 cursor-pointer hover:bg-white/5 transition-colors"
            onClick={() => setShowExtra((v) => !v)}
          >
            <div className="flex items-center gap-2">
              {showExtra ? <ChevronDown size={16} className="text-primary" /> : <ChevronRight size={16} className="text-primary" />}
              <h3 className="text-sm font-semibold text-primary uppercase tracking-wider">
                Extra Items ({billData.extraItems.length})
              </h3>
            </div>
            <span className="text-sm font-semibold text-foreground">{formatINR(extraTotal)}</span>
          </div>

          {showExtra && (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-t border-border/40 bg-muted/30">
                    {["E-No.", "BSR Ref.", "Description", "Qty", "Unit", "Rate (₹)", "Amount (₹)", "Remark"].map((h) => (
                      <th key={h} className="px-3 py-2 text-left font-semibold text-muted-foreground whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {billData.extraItems.map((item, i) => (
                    <tr key={i} className="border-t border-border/20 hover:bg-white/5">
                      <td className="px-3 py-2"><input className="edit-cell w-16 font-mono" value={item.itemNo || ""} onChange={(e) => updateExtraItem(i, "itemNo", e.target.value)} /></td>
                      <td className="px-3 py-2"><input className="edit-cell w-24" value={item.bsr || ""} onChange={(e) => updateExtraItem(i, "bsr", e.target.value)} /></td>
                      <td className="px-3 py-2"><input className="edit-cell min-w-[180px]" value={item.description || ""} onChange={(e) => updateExtraItem(i, "description", e.target.value)} /></td>
                      <td className="px-3 py-2 text-right"><input className="edit-cell w-16 text-right" type="number" value={item.quantity || 0} onChange={(e) => updateExtraItem(i, "quantity", parseFloat(e.target.value) || 0)} /></td>
                      <td className="px-3 py-2"><input className="edit-cell w-12" value={item.unit || ""} onChange={(e) => updateExtraItem(i, "unit", e.target.value)} /></td>
                      <td className="px-3 py-2 text-right"><input className="edit-cell w-24 text-right" type="number" value={item.rate || 0} onChange={(e) => updateExtraItem(i, "rate", parseFloat(e.target.value) || 0)} /></td>
                      <td className="px-3 py-2 text-right font-medium">{formatINR(item.amount || 0)}</td>
                      <td className="px-3 py-2"><input className="edit-cell min-w-[100px]" value={item.remark || ""} onChange={(e) => updateExtraItem(i, "remark", e.target.value)} /></td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-primary/30 bg-primary/5">
                    <td colSpan={6} className="px-3 py-3 text-right font-bold text-sm">Extra Items Total:</td>
                    <td className="px-3 py-3 text-right font-bold text-primary">{formatINR(extraTotal)}</td>
                    <td />
                  </tr>
                </tfoot>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Summary + Generate */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Grand Total Card */}
        <div className="lg:col-span-2 glass-card rounded-2xl p-5 teal-glow">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">Financial Summary</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Bill Total</span>
              <span className="font-medium">{formatINR(totalAmount)}</span>
            </div>
            {billData.hasExtraItems && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Extra Items Total</span>
                <span className="font-medium">{formatINR(extraTotal)}</span>
              </div>
            )}
            <div className="border-t border-border/30 pt-2 flex justify-between text-base">
              <span className="font-bold">Grand Total</span>
              <span className="font-bold text-primary">{formatINR(totalAmount + extraTotal)}</span>
            </div>
          </div>
        </div>

        {/* Generate Options */}
        <div className="glass-card rounded-2xl p-5 flex flex-col gap-4">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Output Formats</h3>
          <div className="space-y-2">
            {[
              { key: "generatePdf" as const, label: "PDF Documents" },
              { key: "generateHtml" as const, label: "HTML Documents" },
              { key: "generateWord" as const, label: "Word Documents" },
            ].map(({ key, label }) => (
              <label key={key} className="flex items-center gap-2.5 cursor-pointer text-sm">
                <input
                  type="checkbox"
                  checked={generateOptions[key]}
                  onChange={(e) => setGenerateOptions({ [key]: e.target.checked })}
                  className="w-4 h-4 rounded accent-primary"
                />
                <span className="text-foreground">{label}</span>
              </label>
            ))}
          </div>
          <Button
            onClick={handleGenerate}
            disabled={generateMutation.isPending || job?.status === "processing" || job?.status === "pending"}
            className="w-full h-11 font-semibold mt-auto"
          >
            {generateMutation.isPending || job?.status === "processing" || job?.status === "pending" ? (
              <><Loader2 size={16} className="animate-spin mr-2" /> Generating...</>
            ) : (
              <><FileText size={16} className="mr-2" /> Generate Bill</>
            )}
          </Button>
          {generateMutation.isError && (
            <p className="text-xs text-destructive">{(generateMutation.error as Error)?.message}</p>
          )}
        </div>
      </div>
    </div>
  );
}
