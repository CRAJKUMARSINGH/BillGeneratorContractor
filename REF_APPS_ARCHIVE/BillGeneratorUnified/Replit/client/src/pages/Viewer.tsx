import React, { useState } from "react";
import { useLocation } from "wouter";
import { motion, AnimatePresence } from "framer-motion";
import { Printer, Save, FileText, ChevronLeft, AlertCircle } from "lucide-react";
import { useCurrentProcessedBill, useSaveBill } from "@/hooks/use-bills";
import { FirstPageSummary } from "@/components/viewer/FirstPageSummary";
import { DeviationStatement } from "@/components/viewer/DeviationStatement";
import { ExtraItems } from "@/components/viewer/ExtraItems";
import { clsx } from "clsx";

type Tab = "First Page" | "Deviation" | "Extra Items";

export default function Viewer() {
  const [, setLocation] = useLocation();
  const bill = useCurrentProcessedBill();
  const saveMutation = useSaveBill();
  
  const [activeTab, setActiveTab] = useState<Tab>("First Page");

  if (!bill) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <AlertCircle className="w-16 h-16 text-primary opacity-50 mb-4" />
        <h2 className="text-2xl font-bold text-foreground">No Bill Loaded</h2>
        <p className="text-muted-foreground mt-2 mb-6">Please process an Excel file first.</p>
        <button 
          onClick={() => setLocation("/upload")}
          className="px-6 py-3 bg-primary text-primary-foreground rounded-xl font-semibold shadow-lg hover-elevate"
        >
          Go to Upload
        </button>
      </div>
    );
  }

  const handlePrint = () => {
    window.print();
  };

  const handleSave = () => {
    saveMutation.mutate({
      name: bill.titleData.nameOfWork || "Untitled Bill",
      data: bill,
    }, {
      onSuccess: () => alert("Bill saved successfully!"),
    });
  };

  const tabs: Tab[] = ["First Page", "Deviation", "Extra Items"];

  return (
    <div className="h-full flex flex-col space-y-6">
      {/* Header Toolbar - Hidden on Print */}
      <div className="no-print flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white/70 backdrop-blur-md p-4 rounded-2xl shadow-sm border border-white">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Document Viewer</h1>
          <p className="text-muted-foreground text-sm">Review and print your generated sheets</p>
        </div>
        <div className="flex items-center gap-3 w-full md:w-auto">
          <button 
            onClick={handleSave}
            disabled={saveMutation.isPending}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2.5 bg-secondary text-secondary-foreground rounded-xl font-medium hover:bg-secondary/80 transition-colors"
          >
            <Save className="w-4 h-4" />
            {saveMutation.isPending ? "Saving..." : "Save to History"}
          </button>
          <button 
            onClick={handlePrint}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-6 py-2.5 bg-primary text-primary-foreground rounded-xl font-semibold shadow-md shadow-primary/25 hover-elevate active-elevate-2"
          >
            <Printer className="w-4 h-4" />
            Print Active Tab
          </button>
        </div>
      </div>

      {/* Tabs Navigation - Hidden on Print */}
      <div className="no-print flex space-x-2 bg-white/50 backdrop-blur-sm p-1 rounded-xl w-max">
        {tabs.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={clsx(
              "px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 flex items-center gap-2",
              activeTab === tab 
                ? "bg-white text-primary shadow-sm" 
                : "text-muted-foreground hover:text-foreground hover:bg-white/30"
            )}
          >
            <FileText className="w-4 h-4" />
            {tab}
          </button>
        ))}
      </div>

      {/* Render Document Content */}
      <div className="flex-1 rounded-2xl print:m-0">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === "First Page" && <FirstPageSummary bill={bill} />}
            {activeTab === "Deviation" && <DeviationStatement bill={bill} />}
            {activeTab === "Extra Items" && <ExtraItems bill={bill} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
