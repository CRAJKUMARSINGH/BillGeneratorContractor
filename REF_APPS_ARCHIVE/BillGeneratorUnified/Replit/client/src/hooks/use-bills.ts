import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, buildUrl } from "@shared/routes";
import { type InsertBill, type ProcessedBill, type Bill } from "@shared/schema";

/**
 * Handle File Upload for Bill Processing
 * Posts multipart/form-data to backend, saves result in transient cache
 */
export function useProcessBill() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (file: File): Promise<ProcessedBill> => {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(api.bills.process.path, {
        method: api.bills.process.method,
        body: formData,
        // Browser sets Content-Type to multipart/form-data automatically
        credentials: "include",
      });

      if (!res.ok) {
        let errMsg = "Failed to process bill";
        try {
          const errData = await res.json();
          errMsg = errData.message || errMsg;
        } catch { /* ignore parse error */ }
        throw new Error(errMsg);
      }

      const data = await res.json();
      return api.bills.process.responses[200].parse(data);
    },
    onSuccess: (data) => {
      // Store transient result for the viewer to pick up
      queryClient.setQueryData(["current-processed-bill"], data);
    },
  });
}

/**
 * Save a processed bill into the database for history
 */
export function useSaveBill() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: InsertBill): Promise<Bill> => {
      const res = await fetch(api.bills.save.path, {
        method: api.bills.save.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include",
      });

      if (!res.ok) throw new Error("Failed to save bill");
      
      const json = await res.json();
      return api.bills.save.responses[201].parse(json);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.bills.list.path] });
    },
  });
}

/**
 * List all saved bills
 */
export function useBills() {
  return useQuery({
    queryKey: [api.bills.list.path],
    queryFn: async (): Promise<Bill[]> => {
      const res = await fetch(api.bills.list.path, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch bills");
      const json = await res.json();
      return api.bills.list.responses[200].parse(json);
    },
  });
}

/**
 * Get a specific saved bill by ID
 */
export function useBill(id: number | null) {
  return useQuery({
    queryKey: [api.bills.get.path, id],
    queryFn: async (): Promise<Bill | null> => {
      if (!id) return null;
      const url = buildUrl(api.bills.get.path, { id });
      const res = await fetch(url, { credentials: "include" });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error("Failed to fetch bill");
      const json = await res.json();
      return api.bills.get.responses[200].parse(json);
    },
    enabled: !!id,
  });
}

/**
 * Custom hook to grab the currently processed (but maybe not saved) bill from cache
 */
export function useCurrentProcessedBill() {
  const queryClient = useQueryClient();
  return queryClient.getQueryData<ProcessedBill>(["current-processed-bill"]);
}
