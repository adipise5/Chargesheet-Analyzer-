import { FileText } from 'lucide-react'
import type { Citation } from '../types'

export function CitationButton({ citation, onOpen }: { citation: Citation; onOpen: (citation: Citation) => void }) {
  return (
    <button onClick={() => onOpen(citation)} className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-left text-xs font-medium text-slate-700 transition hover:border-sky-300 hover:text-sky-800">
      <FileText size={13} /> {citation.label} <span className="text-slate-400">p.{citation.page}</span>
    </button>
  )
}

