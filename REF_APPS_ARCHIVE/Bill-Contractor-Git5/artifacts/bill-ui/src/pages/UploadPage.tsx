import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileSpreadsheet, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUploadExcel, type BillData } from "@/hooks/use-bills";
import { useStore } from "@/lib/store";

interface UploadPageProps {
  onSuccess: () => void;
}

export function UploadPage({ onSuccess }: UploadPageProps) {
  const [file, setFile] = useState<File | null>(null);
  const setBillData = useStore((s) => s.setBillData);
  const uploadMutation = useUploadExcel();

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.ms-excel.sheet.macroenabled.12": [".xlsm"],
    },
    maxFiles: 1,
    disabled: uploadMutation.isPending,
  });

  const handleUpload = async () => {
    if (!file) return;
    try {
      const data: BillData = await uploadMutation.mutateAsync(file);
      setBillData(data);
      onSuccess();
    } catch (_) {
      // error shown in UI
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] px-4">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-2xl"
      >
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium mb-4">
            <FileSpreadsheet size={14} />
            Excel Upload Mode
          </div>
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Upload Contractor Bill
          </h1>
          <p className="text-muted-foreground text-base">
            Upload your PWD Excel file (.xlsx / .xlsm) to extract and generate bill documents
          </p>
        </div>

        {/* Drop Zone */}
        <div
          {...getRootProps()}
          className={`
            relative cursor-pointer rounded-2xl border-2 border-dashed p-12 text-center transition-all duration-300
            ${isDragActive
              ? "border-primary bg-primary/10 teal-glow"
              : "border-border/50 bg-card/50 hover:border-primary/50 hover:bg-card"
            }
            ${uploadMutation.isPending ? "opacity-50 cursor-not-allowed" : ""}
          `}
        >
          <input {...getInputProps()} />

          <AnimatePresence mode="wait">
            {file ? (
              <motion.div
                key="file"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center gap-3"
              >
                <div className="w-16 h-16 rounded-2xl bg-primary/15 flex items-center justify-center teal-glow">
                  <FileSpreadsheet size={32} className="text-primary" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">{file.name}</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {(file.size / 1024).toFixed(1)} KB · Ready to upload
                  </p>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center gap-3"
              >
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-colors
                  ${isDragActive ? "bg-primary/20" : "bg-muted/50"}`}>
                  <Upload size={32} className={isDragActive ? "text-primary" : "text-muted-foreground"} />
                </div>
                <div>
                  <p className="font-semibold text-foreground">
                    {isDragActive ? "Drop your Excel file here" : "Drag & drop your Excel file"}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    or <span className="text-primary font-medium">browse to select</span>
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    Supports .xlsx · .xls · .xlsm (max 50 MB)
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Error Message */}
        {uploadMutation.isError && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 flex items-start gap-3 rounded-xl bg-destructive/10 border border-destructive/20 p-4"
          >
            <AlertCircle size={18} className="text-destructive shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-destructive">Upload failed</p>
              <p className="text-xs text-destructive/80 mt-0.5">
                {(uploadMutation.error as Error)?.message || "An unexpected error occurred"}
              </p>
            </div>
          </motion.div>
        )}

        {/* Actions */}
        <div className="mt-6 flex items-center gap-3">
          <Button
            onClick={handleUpload}
            disabled={!file || uploadMutation.isPending}
            size="lg"
            className="flex-1 h-12 text-base font-semibold"
          >
            {uploadMutation.isPending ? (
              <>
                <Loader2 size={18} className="animate-spin mr-2" />
                Processing Excel...
              </>
            ) : (
              <>
                <CheckCircle2 size={18} className="mr-2" />
                Extract Bill Data
              </>
            )}
          </Button>
          {file && !uploadMutation.isPending && (
            <Button
              variant="outline"
              size="lg"
              className="h-12"
              onClick={() => { setFile(null); uploadMutation.reset(); }}
            >
              Clear
            </Button>
          )}
        </div>

        {/* Info Cards */}
        <div className="mt-8 grid grid-cols-3 gap-3">
          {[
            { label: "Bill Quantity", desc: "Main bill items with rates & quantities" },
            { label: "Title Sheet", desc: "Project name, contractor, agreement details" },
            { label: "Extra Items", desc: "Additional work items beyond schedule" },
          ].map((item) => (
            <div key={item.label} className="glass-card rounded-xl p-4">
              <p className="text-xs font-semibold text-primary mb-1">{item.label}</p>
              <p className="text-xs text-muted-foreground">{item.desc}</p>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
