export type Citation = { document_id: string; page: number; chunk_id: string; label: string }
export type Case = { id: string; case_number: string; police_station: string; language: string; status: string; is_demo: boolean; created_at: string; updated_at: string }
export type Finding = {
  id: string; type: string; title: string; summary: string; classification: string; confidence: number
  supporting_sources: Citation[]; contradicting_sources: Citation[]; entities: string[]; factors: Record<string, number | boolean>
  human_review_required: boolean; verified: boolean
}
export type GraphNode = { id: string; type: string; label: string; aliases: string[]; confidence: number; metadata: Record<string, unknown> }
export type GraphEdge = { id: string; source: string; target: string; relation: string; confidence: number; citations: Citation[]; extraction_method: string; human_verified: boolean }
export type GraphData = { nodes: GraphNode[]; edges: GraphEdge[] }
export type DocumentRecord = { id: string; case_id: string; filename: string; category: string; page_count: number; status: string }
export type PageRecord = {
  id: string; document_id: string; page_number: number; extraction_method: string; language: string
  original_text: string; normalized_text: string; corrected_text?: string; tesseract_text?: string; vision_candidate_text?: string
  ocr_confidence: number; review_status: string; document_url: string; image_url?: string
}
export type CaseTab = 'Overview' | 'Analysis' | 'Evidence' | 'Timeline' | 'Graph' | 'Documents' | 'Ask Case'

