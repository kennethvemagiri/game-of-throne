export interface Application {
  id: string;
  emailId?: string;
  company?: string;
  role?: string | null;
  status: string;
  suggestedStatus?: string;
  confidence?: string;
  subject?: string;
  snippet?: string;
  receivedAt?: string;
  classifiedAt?: string;
  review?: {
    reviewed?: boolean;
    reviewedAt?: string | null;
  };
}

export interface Stats {
  counts: Record<string, number>;
  needsReview: number;
  total: number;
}

export interface SuggestedJob {
  id: string;
  source: string;
  company: string;
  role: string;
  url: string;
  snippet: string;
  suggestedAt: string;
  status: string;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, options);
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function fetchApplications(params?: { status?: string; needsReview?: boolean }) {
  const search = new URLSearchParams();
  if (params?.status) search.set('status', params.status);
  if (params?.needsReview) search.set('needsReview', 'true');
  const qs = search.toString();
  return request<Application[]>(`/api/applications${qs ? `?${qs}` : ''}`);
}

export function fetchStats() {
  return request<Stats>('/api/stats');
}

export function reviewApplication(id: string, status: string) {
  return request<Application>(`/api/applications/${id}/review`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
}

export function archiveApplication(id: string) {
  return request<Application>(`/api/applications/${id}/archive`, {
    method: 'PATCH',
  });
}

export function fetchSuggestedJobs(status = 'pending') {
  return request<SuggestedJob[]>(`/api/suggested-jobs?status=${status}`);
}

export function rejectSuggestedJob(id: string) {
  return request<SuggestedJob>(`/api/suggested-jobs/${id}/reject`, {
    method: 'PATCH',
  });
}

export function markSuggestedJobViewed(id: string) {
  return request<SuggestedJob>(`/api/suggested-jobs/${id}/viewed`, {
    method: 'PATCH',
  });
}

export interface GmailStatus {
  authenticated: boolean;
  lastFetch: string | null;
}

export interface GmailSyncResult {
  fetched: number;
  classified: number;
  skipped: number;
  errors?: number;
}

export function fetchGmailStatus() {
  return request<GmailStatus>('/api/gmail/status');
}

export function triggerGmailSync() {
  return request<GmailSyncResult>('/api/gmail/fetch', { method: 'POST' });
}
