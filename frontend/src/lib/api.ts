/**
 * api.ts — Authenticated FastAPI client for BillForge.
 * Auth: Bearer JWT token injected automatically from localStorage.
 * Download: Use downloadFile() — NOT downloadUrl() — to preserve auth header.
 */

const BASE = import.meta.env.VITE_API_URL ?? '';

export interface BillItemAPI {
  itemNo: string;
  description: string;
  unit: string;
  quantitySince: number;
  quantityUpto: number;
  quantity: number;
  rate: number;
  amount: number;
}

export interface ExtraItemAPI {
  itemNo: string;
  bsr: string;
  description: string;
  quantity: number;
  unit: string;
  rate: number;
  amount: number;
  remark: string;
}

export interface ParsedBillData {
  fileId: string;
  fileName: string;
  titleData: Record<string, string>;
  billItems: BillItemAPI[];
  extraItems: ExtraItemAPI[];
  totalAmount: number;
  hasExtraItems: boolean;
  sheets: string[];
  anomaly_warnings?: string[];
}

export interface GenerateOptions {
  generatePdf: boolean;
  generateHtml: boolean;
  templateVersion: 'v1' | 'v2';
  premiumPercent: number;
  premiumType: 'above' | 'below';
  previousBillAmount: number;
}

export interface GenerateRequest {
  fileId: string;
  titleData: Record<string, string>;
  billItems: BillItemAPI[];
  extraItems: ExtraItemAPI[];
  options: GenerateOptions;
}

export interface DocumentInfo {
  name: string;
  format: string;
  size: number;
}

export interface JobStatus {
  jobId: string;
  status: 'pending' | 'processing' | 'complete' | 'error';
  progress: number;
  message: string;
  documents: DocumentInfo[];
  error?: string;
}

export interface BillRecordAPI {
  id: number;
  job_id: string;
  user_id: number;
  status: string;
  message: string;
  total_amount: number;
  created_at: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem('token');
  const headers = new Headers(init?.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers
  });

  if (!res.ok) {
    if (res.status === 401) {
      localStorage.removeItem('token');
      window.location.reload();
    }
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; engine: string }>('/healthz'),

  uploadExcel: (file: File): Promise<ParsedBillData> => {
    const form = new FormData();
    form.append('file', file);
    return request<ParsedBillData>('/bills/upload', { method: 'POST', body: form });
  },

  uploadImage: (file: File): Promise<ParsedBillData> => {
    const form = new FormData();
    form.append('file', file);
    return request<ParsedBillData>('/bills/upload-image', { method: 'POST', body: form });
  },

  generateTemplate: (prompt: string): Promise<any> =>
    request<any>('/bills/generate-template', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    }),

  generate: (req: GenerateRequest): Promise<JobStatus> =>
    request<JobStatus>('/bills/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),

  getJob: (jobId: string): Promise<JobStatus> =>
    request<JobStatus>(`/bills/jobs/${jobId}`),

  getHistory: (): Promise<BillRecordAPI[]> => 
    request<BillRecordAPI[]>('/bills/history'),

  downloadFile: async (jobId: string, format: 'zip' | 'pdf' | 'html') => {
    const token = localStorage.getItem('token');
    const headers = new Headers();
    if (token) headers.set('Authorization', `Bearer ${token}`);

    const res = await fetch(`${BASE}/bills/jobs/${jobId}/download?format=${format}`, { headers });
    if (!res.ok) {
        if (res.status === 401) {
            localStorage.removeItem('token');
            window.location.reload();
        }
        throw new Error(`Download failed: ${res.statusText}`);
    }

    const contentDisposition = res.headers.get('Content-Disposition');
    let filename = `bill_${jobId.slice(0, 8)}.${format}`;
    if (contentDisposition && contentDisposition.includes('filename="')) {
      filename = contentDisposition.split('filename="')[1].split('"')[0];
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
  },
};
