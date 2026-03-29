import React from "react";
import { useLocation } from "wouter";
import { format } from "date-fns";
import { useBills } from "@/hooks/use-bills";
import { useQueryClient } from "@tanstack/react-query";
import { FileSpreadsheet, ChevronRight, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export default function History() {
  const [, setLocation] = useLocation();
  const queryClient = useQueryClient();
  const { data: bills, isLoading } = useBills();

  const handleOpenBill = (billData: any) => {
    // Load the bill data into the transient state to display in viewer
    queryClient.setQueryData(["current-processed-bill"], billData);
    setLocation("/viewer");
  };

  return (
    <div className="h-full flex flex-col space-y-8">
      <div className="bg-white/70 backdrop-blur-md p-8 rounded-3xl shadow-sm border border-white">
        <h1 className="text-3xl font-display font-bold text-foreground">Saved Bills</h1>
        <p className="text-muted-foreground mt-2">Access and reprint your previously processed documents.</p>
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : !bills || bills.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-12 bg-white/40 rounded-3xl glass-panel">
          <FileSpreadsheet className="w-16 h-16 text-muted-foreground/30 mb-4" />
          <h3 className="text-xl font-bold text-foreground">No Bills Found</h3>
          <p className="text-muted-foreground mt-2">You haven't saved any bills yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {bills.map((bill, index) => (
            <motion.div 
              key={bill.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => handleOpenBill(bill.data)}
              className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-lg hover:border-primary/30 transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                  <FileSpreadsheet className="w-6 h-6 text-primary" />
                </div>
                <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-primary transition-colors" />
              </div>
              <h3 className="text-lg font-bold text-foreground mb-1 line-clamp-1">
                {bill.name}
              </h3>
              <p className="text-sm text-muted-foreground">
                {bill.createdAt ? format(new Date(bill.createdAt), "MMM d, yyyy 'at' h:mm a") : "Unknown date"}
              </p>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
