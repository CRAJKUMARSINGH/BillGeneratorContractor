/**
 * API client — all calls go to FastAPI backend.
 * Replaces Supabase. No auth yet (Phase 4 scope).
 */

const BASE = import.meta.env.VITE_API_URL ?? '';

export interface AIRow {
  itemNo: string;
  description: string;
  unit: string;
  quantity: number;
  rate: number;
  amount: number;
  remark: string;
  confidence: number;
  aiNote: string;
}

export interface ColumnMapping {
  canonical: string;
  colIndex: number;
  headerText: string;
  confidence: number;
}

export interface AISheetResult {
  sheetName: string;
  headerRowIndex: number;
  columnMappings: ColumnMapping[];
  rows: AIRow[];
  unmappedColumns: string[];
  warnings: string[];
  totalAmount: number;
}

export interface AIParseResult {
  fileId: string;
  fileName: string;
  sheets: AISheetResult[];
  workOrderSheet: AISheetResult | null;
  titleData: Record<string, string>;
  aiSuggestions: string[];
  confidenceOverall: number;
}

export interface CommitRequest {
  fileId: string;
  fileName: string;
  titleData: Record<string, string>;
  rows: AIRow[];
  premiumPercent?: number;
  premiumType?: 'above' | 'below';
}

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

export interface PreviewRequest {
  document_type: string;
  fileId: string;
  titleData: Record<string, string>;
  billItems: BillItemAPI[];
  extraItems: ExtraItemAPI[];
  options: GenerateOptions;
}

export interface PreviewResponse {
  document_type: string;
  html: string;
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

const DEFAULT_TIMEOUT_MS = 8000;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem('token');
  const headers = new Headers(init?.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const controller = new AbortController();
  const timeoutMs = (init as any)?.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      ...init,
      headers,
      signal: controller.signal,
    });
  } catch (err: any) {
    if (err?.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeoutMs}ms: ${path}`);
    }
    throw err;
  } finally {
    window.clearTimeout(timeoutId);
  }

  if (!res.ok) {
    if (res.status === 401) {
      localStorage.removeItem('token');
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

  preview: (req: PreviewRequest): Promise<PreviewResponse> =>
    request<PreviewResponse>('/bills/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
      timeoutMs: 3000,
    } as any),

  downloadUrl: (jobId: string, format: 'zip' | 'pdf' | 'html') =>
    `${BASE}/bills/jobs/${jobId}/download?format=${format}`,

  // AI Excel Assistant
  aiParseExcel: (file: File, useLlm = false): Promise<AIParseResult> => {
    const form = new FormData();
    form.append('file', file);
    return request<AIParseResult>(
      `/ai-excel/parse?use_llm=${useLlm}`,
      { method: 'POST', body: form, timeoutMs: 30000 } as any,
    );
  },

  aiCommit: (req: CommitRequest): Promise<ParsedBillData> =>
    request<ParsedBillData>('/ai-excel/commit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),
};
