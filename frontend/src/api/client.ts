import type { Case, Citation, DocumentRecord, Finding, GraphData, Judgment, PageRecord } from '../types'

const API = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init)
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const detail = payload?.detail
    const message = Array.isArray(detail) ? detail.map((item: { msg?: string }) => item.msg || 'Invalid input').join('; ') : detail?.message || detail || payload?.error?.message
    if (response.status === 404 && path.endsWith('/query')) throw new Error('This case no longer exists. Open an existing case from Cases in the sidebar and ask again.')
    throw new Error(typeof message === 'string' ? message : `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export const api = {
  cases: () => request<Case[]>('/cases'),
  case: (id: string) => request<Case>(`/cases/${id}`),
  deleteCase: (id: string) => request(`/cases/${id}`, { method: 'DELETE' }),
  createCase: (data: { case_number: string; police_station: string; language: string }) => request<Case>('/cases', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }),
  loadDemo: () => request<Case>('/demo', { method: 'POST' }),
  upload: async (caseId: string, file: File, role = 'supporting_record') => { const data = new FormData(); data.append('file', file); data.append('role', role); return request<DocumentRecord>(`/cases/${caseId}/documents`, { method: 'POST', body: data }) },
  process: (caseId: string) => request(`/cases/${caseId}/process`, { method: 'POST' }),
  status: (caseId: string) => request<{ state: string; stage: string; progress: number; counts: Record<string, number | string>; stages: { name: string; state: string }[]; error?: string }>(`/cases/${caseId}/status`),
  overview: (caseId: string) => request<{ case: Case; metrics: Record<string, number>; summary: { english: string; gujarati: string }; key_entities: GraphData['nodes']; priority_findings: Finding[] }>(`/cases/${caseId}/overview`),
  findings: (caseId: string) => request<Finding[]>(`/cases/${caseId}/findings`),
  defense: (caseId: string) => request<Array<{ id: string; type: string; title: string; weakness: string; defense_questions: string[]; relevant_sources: Citation[]; io_action: string; recommended_correction: string; why_important: string; differences: { document: string; role: string; value: string }[]; confidence: number; review_required: boolean }>>(`/cases/${caseId}/defense`),
  judgments: () => request<Judgment[]>('/judgments'),
  uploadJudgment: async (file: File, title: string, court: string, year: string) => { const data = new FormData(); data.append('file', file); data.append('title', title); data.append('court', court); data.append('year', year); return request<Judgment>('/judgments', { method: 'POST', body: data }) },
  precedents: (caseId: string) => request<{ insights: string; citations: { judgment_id: string; page: number; chunk_id: string; label: string }[]; review_required: boolean; matches: { title: string; court: string; year: string; page: number; score: number }[] }>(`/cases/${caseId}/precedents`),
  graph: (caseId: string) => request<GraphData>(`/cases/${caseId}/graph`),
  documents: (caseId: string) => request<DocumentRecord[]>(`/cases/${caseId}/documents`),
  page: (caseId: string, documentId: string, page: number) => request<PageRecord>(`/cases/${caseId}/documents/${documentId}/pages/${page}`),
  evidence: (caseId: string) => request<Array<{ id: string; type: string; label: string; confidence: number; citations: Citation[]; linked_claims: string[]; verification: string }>>(`/cases/${caseId}/evidence`),
  timeline: (caseId: string) => request<Array<{ id: string; date?: string; time?: string; event: string; category: string; location?: string; confidence: number; uncertain: boolean; citation?: Citation }>>(`/cases/${caseId}/timeline`),
  reviews: (caseId: string) => request<PageRecord[]>(`/cases/${caseId}/ocr/review`),
  updateReview: (caseId: string, pageId: string, status: string, corrected_text?: string) => request(`/cases/${caseId}/ocr/review/${pageId}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status, corrected_text }) }),
  query: (caseId: string, question: string) => request<{ answer: string; citations: Citation[]; confidence: number; review_required: boolean }>(`/cases/${caseId}/query`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }) }),
  health: () => request<{ status: string; llm_model: string; embedding_model: string; ollama: { available: boolean; missing: string[] }; tesseract: { available: boolean; message: string }; neo4j: { available: boolean; mode: string } }>('/system/health'),
  purgeData: () => request<{ status: string; removed: Record<string, number> }>('/system/purge', { method: 'DELETE' }),
  translate: (texts: string[], target: 'english' | 'gujarati') => request<{ translations: string[] }>('/system/translate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ texts, target }) }),
  caseByNumber: (caseNumber: string) => request<Case>(`/cases/by-number/${encodeURIComponent(caseNumber)}`).catch(() => null),
  // Analytics endpoints
  analyticsSummary: () => request<Record<string, number>>('/analytics/summary'),
  analyticsCrimeTypes: () => request<Array<{ section: string; count: number }>>('/analytics/crime-types'),
  analyticsTemporal: () => request<Array<{ month: string; cases_registered: number; crime_events: number }>>('/analytics/temporal'),
  analyticsHotspots: () => request<Array<{ station: string; count: number }>>('/analytics/hotspots'),
  analyticsCaseStatus: () => request<Array<{ status: string; count: number }>>('/analytics/case-status'),
  analyticsEvidenceProfile: () => request<Array<{ type: string; count: number }>>('/analytics/evidence-profile'),
  analyticsEntityNetwork: () => request<Array<{ label: string; kind: string; case_count: number }>>('/analytics/entity-network'),
  analyticsFindings: () => request<Array<{ type: string; count: number }>>('/analytics/findings-summary'),
  analyticsDocRoles: () => request<Array<{ role: string; count: number }>>('/analytics/document-roles'),
}
