import React, { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, FileText, Image as ImageIcon, Loader2, Sparkles } from "lucide-react";
import { Layout } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { useProcessJob } from "@/hooks/use-jobs";
import { ResultsView } from "@/components/results-view";
import type { ExtractionJob } from "@shared/schema";

export default function Home() {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [qtyFile, setQtyFile] = useState<File | null>(null);
  const [activeJob, setActiveJob] = useState<ExtractionJob | null>(null);
  
  const imageInputRef = useRef<HTMLInputElement>(null);
  const qtyInputRef = useRef<HTMLInputElement>(null);

  const processMutation = useProcessJob();

  const handleProcess = () => {
    if (!imageFile || !qtyFile) return;
    
    const formData = new FormData();
    formData.append("image", imageFile);
    formData.append("qtyFile", qtyFile);
    
    processMutation.mutate(formData, {
      onSuccess: (job) => {
        setActiveJob(job);
      }
    });
  };

  const handleReset = () => {
    setImageFile(null);
    setQtyFile(null);
    setActiveJob(null);
    processMutation.reset();
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <header className="mb-10">
          <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight">
            Generate Bill
          </h1>
          <p className="text-lg text-slate-500 mt-3 max-w-2xl text-balance">
            Upload the Schedule-G work order image and the quantity text file. 
            Our OCR engine will precisely match and validate row-by-row.
          </p>
        </header>

        <AnimatePresence mode="wait">
          {activeJob ? (
            <ResultsView key="results" job={activeJob} onNew={handleReset} />
          ) : processMutation.isPending ? (
            <motion.div 
              key="loading"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="glass-panel rounded-3xl p-16 flex flex-col items-center justify-center text-center min-h-[400px]"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-primary/20 rounded-full blur-2xl animate-pulse" />
                <div className="h-24 w-24 bg-white rounded-full shadow-2xl flex items-center justify-center relative z-10">
                  <Loader2 className="h-10 w-10 text-primary animate-spin" />
                </div>
              </div>
              <h3 className="text-2xl font-bold mt-8 mb-2">Analyzing Documents</h3>
              <p className="text-slate-500 max-w-md">
                Processing image with row-based OCR & Validation. This ensures strict accuracy so we never produce a wrong bill silently.
              </p>
            </motion.div>
          ) : (
            <motion.div 
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {/* Form Error Banner */}
              {processMutation.isError && (
                <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-r-xl text-red-800 flex items-start gap-3">
                  <Sparkles className="h-5 w-5 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-bold">Processing Failed</h4>
                    <p className="text-sm mt-1">{processMutation.error.message}</p>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Image Upload Card */}
                <div 
                  className={`relative group border-2 border-dashed rounded-3xl p-8 transition-all duration-300 flex flex-col items-center justify-center text-center h-72 cursor-pointer
                    ${imageFile ? 'border-primary bg-primary/5' : 'border-slate-300 bg-white hover:border-primary/50 hover:bg-slate-50'}`}
                  onClick={() => imageInputRef.current?.click()}
                >
                  <input 
                    type="file" 
                    ref={imageInputRef} 
                    className="hidden" 
                    accept="image/*"
                    onChange={(e) => {
                      if (e.target.files && e.target.files.length > 0) {
                        setImageFile(e.target.files[0]);
                      }
                    }}
                  />
                  <div className={`h-16 w-16 rounded-2xl flex items-center justify-center mb-4 transition-colors ${imageFile ? 'bg-primary text-white shadow-lg shadow-primary/30' : 'bg-slate-100 text-slate-500 group-hover:bg-primary/10 group-hover:text-primary'}`}>
                    <ImageIcon className="h-8 w-8" />
                  </div>
                  <h3 className="font-bold text-lg text-slate-900 mb-1">
                    {imageFile ? 'Image Selected' : 'Work Order Image'}
                  </h3>
                  <p className="text-sm text-slate-500 mb-4 max-w-[200px]">
                    {imageFile ? imageFile.name : 'Upload Schedule-G scan or photo (PNG, JPG)'}
                  </p>
                  {imageFile ? (
                    <span className="text-xs font-bold text-primary uppercase tracking-wide bg-primary/10 px-3 py-1 rounded-full">Change File</span>
                  ) : (
                    <Button variant="outline" size="sm" className="pointer-events-none">Browse Files</Button>
                  )}
                </div>

                {/* Qty Upload Card */}
                <div 
                  className={`relative group border-2 border-dashed rounded-3xl p-8 transition-all duration-300 flex flex-col items-center justify-center text-center h-72 cursor-pointer
                    ${qtyFile ? 'border-primary bg-primary/5' : 'border-slate-300 bg-white hover:border-primary/50 hover:bg-slate-50'}`}
                  onClick={() => qtyInputRef.current?.click()}
                >
                  <input 
                    type="file" 
                    ref={qtyInputRef} 
                    className="hidden" 
                    accept=".txt,.csv"
                    onChange={(e) => {
                      if (e.target.files && e.target.files.length > 0) {
                        setQtyFile(e.target.files[0]);
                      }
                    }}
                  />
                  <div className={`h-16 w-16 rounded-2xl flex items-center justify-center mb-4 transition-colors ${qtyFile ? 'bg-primary text-white shadow-lg shadow-primary/30' : 'bg-slate-100 text-slate-500 group-hover:bg-primary/10 group-hover:text-primary'}`}>
                    <FileText className="h-8 w-8" />
                  </div>
                  <h3 className="font-bold text-lg text-slate-900 mb-1">
                    {qtyFile ? 'Quantity File Selected' : 'Quantity List'}
                  </h3>
                  <p className="text-sm text-slate-500 mb-4 max-w-[200px]">
                    {qtyFile ? qtyFile.name : 'Upload the generated qty.txt file'}
                  </p>
                  {qtyFile ? (
                    <span className="text-xs font-bold text-primary uppercase tracking-wide bg-primary/10 px-3 py-1 rounded-full">Change File</span>
                  ) : (
                    <Button variant="outline" size="sm" className="pointer-events-none">Browse Files</Button>
                  )}
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <Button 
                  size="lg" 
                  className="w-full md:w-auto px-12 h-14 text-lg rounded-2xl bg-gradient-to-r from-primary to-indigo-500"
                  disabled={!imageFile || !qtyFile || processMutation.isPending}
                  onClick={handleProcess}
                >
                  <Sparkles className="h-5 w-5 mr-2" />
                  Process & Generate Bill
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </Layout>
  );
}
