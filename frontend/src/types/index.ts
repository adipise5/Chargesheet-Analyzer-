export type Citation = { document_id: string; page: number; chunk_id: string; label: string }
export type Case = { id: string; case_number: string; police_station: string; language: string; status: string; is_demo: boolean; created_at: string; updated_at: string }
export type Finding = {
  id: string; type: string; title: string; summary: string; classification: string; confidence: number
  supporting_sources: Citation[]; contradicting_sources: Citation[]; entities: string[]; factors: Record<string, number | boolean>
  human_review_required: boolean; verified: boolean
  issue?: string; differences?: { document: string; role: string; value: string }[]; why_important?: string
  recommended_correction?: string; io_action?: string; defense_questions?: string[]; related_document_roles?: string[]
}
export type GraphNode = { id: string; type: string; label: string; aliases: string[]; confidence: number; metadata: Record<string, unknown> }
export type GraphEdge = { id: string; source: string; target: string; relation: string; confidence: number; citations: Citation[]; extraction_method: string; human_verified: boolean }
export type GraphData = { nodes: GraphNode[]; edges: GraphEdge[] }
export type DocumentRecord = { id: string; case_id: string; filename: string; category: string; role: string; page_count: number; status: string }
export type PageRecord = {
  id: string; document_id: string; page_number: number; extraction_method: string; language: string
  original_text: string; normalized_text: string; corrected_text?: string; tesseract_text?: string; vision_candidate_text?: string
  ocr_confidence: number; review_status: string; document_url: string; image_url?: string
}
export type CaseTab = 'Overview' | 'Analysis' | 'Defense' | 'Precedents' | 'Evidence' | 'Timeline' | 'Graph' | 'Documents' | 'Ask Case'
export type Judgment = { id: string; title: string; court: string; judgment_year: string; filename: string; page_count: number }
export type RuntimeHealth = { status: string; mode?: string; read_only?: boolean; models_required?: boolean; llm_model?: string | null; embedding_model?: string | null; ollama: { available: boolean; missing: string[]; disabled?: boolean }; tesseract: { available: boolean; message: string }; neo4j: { available: boolean; mode: string } }

