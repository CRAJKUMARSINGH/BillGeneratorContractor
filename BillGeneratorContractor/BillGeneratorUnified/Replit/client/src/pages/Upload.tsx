import React, { useCallback, useState } from "react";
import { useLocation } from "wouter";
import { useDropzone } from "react-dropzone";
import { motion } from "framer-motion";
import { UploadCloud, FileSpreadsheet, Loader2, CheckCircle2 } from "lucide-react";
import { useProcessBill } from "@/hooks/use-bills";
import { clsx } from "clsx";

export default function Upload() {
  const [, setLocation] = useLocation();
  const processMutation = useProcessBill();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    setErrorMsg(null);
    const file = acceptedFiles[0];
    
    processMutation.mutate(file, {
      onSuccess: () => {
        // Allow a brief moment for the success animation to show
        setTimeout(() => setLocation("/viewer"), 800);
      },
      onError: (err) => {
        setErrorMsg(err.message);
      }
    });
  }, [processMutation, setLocation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.ms-excel.sheet.macroEnabled.12': ['.xlsm']
    },
    maxFiles: 1,
    disabled: processMutation.isPending || processMutation.isSuccess
  });

  return (
    <div className="max-w-3xl mx-auto mt-12 px-4">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-12"
      >
        <h1 className="text-4xl md:text-5xl font-display font-extrabold text-foreground mb-4">
          Intelligent Bill Generator
        </h1>
        <p className="text-lg text-muted-foreground">
          Upload your Excel measurements to instantly generate strict PWD-compliant PDF summaries and deviation statements.
        </p>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
      >
        <div 
          {...getRootProps()} 
          className={clsx(
            "relative overflow-hidden group border-2 border-dashed rounded-3xl p-12 text-center transition-all duration-300 ease-out cursor-pointer",
            isDragActive ? "border-primary bg-primary/5" : "border-white/60 bg-white/40 hover:bg-white/60 hover:border-primary/50 glass-panel shadow-xl",
            processMutation.isPending && "pointer-events-none opacity-80",
            processMutation.isSuccess && "border-green-500 bg-green-50"
          )}
        >
          <input {...getInputProps()} />
          
          <div className="flex flex-col items-center justify-center space-y-6 relative z-10">
            {processMutation.isPending ? (
              <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
                <Loader2 className="w-20 h-20 text-primary" />
              </motion.div>
            ) : processMutation.isSuccess ? (
              <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
                <CheckCircle2 className="w-20 h-20 text-green-500" />
              </motion.div>
            ) : (
              <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-primary to-accent flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                <UploadCloud className="w-10 h-10 text-white" />
              </div>
            )}

            <div className="space-y-2">
              <h3 className="text-2xl font-bold font-display text-foreground">
                {processMutation.isPending 
                  ? "Processing Excel Magic..." 
                  : processMutation.isSuccess 
                    ? "Success! Redirecting..." 
                    : isDragActive ? "Drop the file here!" : "Drag & Drop your Excel file"}
              </h3>
              <p className="text-muted-foreground font-medium">
                {!processMutation.isPending && !processMutation.isSuccess && "Supports .xlsx, .xls, .xlsm files"}
              </p>
            </div>

            {!processMutation.isPending && !processMutation.isSuccess && (
              <button className="mt-4 px-8 py-3 bg-white text-primary font-semibold rounded-xl shadow-md border border-white/50 group-hover:shadow-lg group-hover:-translate-y-0.5 transition-all">
                Browse Files
              </button>
            )}
          </div>
        </div>

        {errorMsg && (
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-r-xl text-red-700"
          >
            <p className="font-semibold flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              Upload Failed
            </p>
            <p className="mt-1 ml-7 text-sm">{errorMsg}</p>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
