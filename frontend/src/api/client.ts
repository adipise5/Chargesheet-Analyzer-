import type { Case, Citation, DocumentRecord, Finding, GraphData, PageRecord } from '../types'

const API = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init)
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new Error(payload?.detail?.message || payload?.detail || payload?.error?.message || `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export const api = {
  cases: () => request<Case[]>('/cases'),
  case: (id: string) => request<Case>(`/cases/${id}`),
  createCase: (data: { case_number: string; police_station: string; language: string }) => request<Case>('/cases', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }),
  loadDemo: () => request<Case>('/demo', { method: 'POST' }),
  upload: async (caseId: string, file: File) => { const data = new FormData(); data.append('file', file); return request<DocumentRecord>(`/cases/${caseId}/documents`, { method: 'POST', body: data }) },
  process: (caseId: string) => request(`/cases/${caseId}/process`, { method: 'POST' }),
  status: (caseId: string) => request<{ state: string; stage: string; progress: number; counts: Record<string, number | string>; stages: { name: string; state: string }[]; error?: string }>(`/cases/${caseId}/status`),
  overview: (caseId: string) => request<{ case: Case; metrics: Record<string, number>; summary: string; key_entities: GraphData['nodes']; priority_findings: Finding[] }>(`/cases/${caseId}/overview`),
  findings: (caseId: string) => request<Finding[]>(`/cases/${caseId}/findings`),
  graph: (caseId: string) => request<GraphData>(`/cases/${caseId}/graph`),
  documents: (caseId: string) => request<DocumentRecord[]>(`/cases/${caseId}/documents`),
  page: (caseId: string, documentId: string, page: number) => request<PageRecord>(`/cases/${caseId}/documents/${documentId}/pages/${page}`),
  evidence: (caseId: string) => request<Array<{ id: string; type: string; label: string; confidence: number; citations: Citation[]; linked_claims: string[]; verification: string }>>(`/cases/${caseId}/evidence`),
  timeline: (caseId: string) => request<Array<{ id: string; date?: string; time?: string; event: string; category: string; location?: string; confidence: number; uncertain: boolean; citation?: Citation }>>(`/cases/${caseId}/timeline`),
  reviews: (caseId: string) => request<PageRecord[]>(`/cases/${caseId}/ocr/review`),
  updateReview: (caseId: string, pageId: string, status: string, corrected_text?: string) => request(`/cases/${caseId}/ocr/review/${pageId}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status, corrected_text }) }),
  query: (caseId: string, question: string) => request<{ answer: string; citations: Citation[]; confidence: number; review_required: boolean }>(`/cases/${caseId}/query`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }) }),
  health: () => request<{ status: string; llm_model: string; embedding_model: string; ollama: { available: boolean; missing: string[] }; tesseract: { available: boolean; message: string }; neo4j: { available: boolean; mode: string } }>('/system/health'),
}

