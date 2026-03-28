import { useMutation, useQuery } from "@tanstack/react-query";

// Types derived from OpenAPI spec
export interface BillData {
  fileId: string;
  fileName: string;
  titleData: Record<string, string>;
  billItems: Array<{
    itemNo: string;
    description: string;
    unit?: string;
    quantitySince?: number;
    quantityUpto?: number;
    quantity?: number;
    rate?: number;
    amount?: number;
  }>;
  extraItems: Array<{
    itemNo?: string;
    bsr?: string;
    description?: string;
    quantity?: number;
    unit?: string;
    rate?: number;
    amount?: number;
    remark?: string;
  }>;
  totalAmount: number;
  hasExtraItems: boolean;
  sheets: string[];
}

export interface GenerateOptions {
  generatePdf?: boolean;
  generateHtml?: boolean;
  generateWord?: boolean;
}

export interface GenerateRequest {
  fileId: string;
  titleData: Record<string, string>;
  billItems: BillData['billItems'];
  extraItems: BillData['extraItems'];
  options?: GenerateOptions;
}

export interface DocumentInfo {
  name: string;
  format: 'html' | 'pdf' | 'word';
  size?: number;
}

export interface JobStatus {
  jobId: string;
  status: 'pending' | 'processing' | 'complete' | 'error';
  progress?: number;
  message?: string;
  documents?: DocumentInfo[];
  error?: string;
}

// Ensure the base path works nicely with Vite's dev server proxy
const API_BASE = '/api';

export function useUploadExcel() {
  return useMutation({
    mutationFn: async (file: File): Promise<BillData> => {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE}/bills/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || error.error || "Failed to upload file");
      }

      return res.json();
    },
  });
}

export function useGenerateBill() {
  return useMutation({
    mutationFn: async (data: GenerateRequest): Promise<JobStatus> => {
      const res = await fetch(`${API_BASE}/bills/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || error.error || "Failed to start generation");
      }

      return res.json();
    },
  });
}

export function useJobStatus(jobId: string | null) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: async (): Promise<JobStatus> => {
      const res = await fetch(`${API_BASE}/bills/jobs/${jobId}`);
      if (!res.ok) throw new Error("Failed to fetch job status");
      return res.json();
    },
    enabled: !!jobId,
    // Poll every 1.5s while the job is pending or processing
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return (status === 'pending' || status === 'processing') ? 1500 : false;
    },
  });
}

export function getDownloadUrl(jobId: string, format: string = 'zip') {
  return `${API_BASE}/bills/jobs/${jobId}/download?format=${format}`;
}
