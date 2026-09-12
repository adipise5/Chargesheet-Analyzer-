import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { FileSearch, Filter } from 'lucide-react'
import { api } from '../../api/client'
import { Badge } from '../../components/Badge'
import { CitationButton } from '../../components/CitationButton'
import { Loading } from '../../components/Loading'
import type { Citation } from '../../types'
import { useTranslatedTexts } from '../../i18n/LanguageContext'

export function EvidenceView({ caseId, onCitation }: { caseId: string; onCitation: (value: Citation) => void }) {
  const [filter, setFilter] = useState('all')
  const query = useQuery({ queryKey: ['evidence', caseId], queryFn: () => api.evidence(caseId) })
  const filtered = useMemo(() => (query.data || []).filter(row => filter === 'all' || row.type.toLowerCase().includes(filter)), [query.data, filter])
  const translated = useTranslatedTexts(filtered.flatMap(row => [row.label, row.type, row.verification]))
  if (query.isLoading) return <Loading />
  return <div className="mx-auto max-w-[1320px]"><div className="flex items-end justify-between"><div><div className="eyebrow">Material index</div><h2 className="mt-1.5 text-xl font-semibold">Evidence overview</h2></div><div className="flex items-center gap-2"><Filter size={14} className="text-slate-400" /><select value={filter} onChange={event => setFilter(event.target.value)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs"><option value="all">All evidence</option><option value="digital">Digital</option><option value="physical">Physical</option><option value="forensic">Forensic</option><option value="witness">Witness</option></select></div></div>
    <div className="panel mt-5 overflow-x-auto"><table className="w-full min-w-[900px] text-left"><thead className="border-b border-slate-200 bg-slate-50 text-[10px] uppercase tracking-wider text-slate-500"><tr><th className="px-5 py-3.5">Evidence ID</th><th className="px-4 py-3.5">Type</th><th className="px-4 py-3.5">Description</th><th className="px-4 py-3.5">Linked claims</th><th className="px-4 py-3.5">Source</th><th className="px-4 py-3.5">Verification</th><th className="px-5 py-3.5">Confidence</th></tr></thead><tbody className="divide-y divide-slate-100">{filtered.map(row => <tr key={row.id} className="align-top hover:bg-slate-50/60"><td className="px-5 py-4 text-xs font-mono text-slate-500">{row.id}</td><td className="px-4 py-4 text-xs font-semibold capitalize text-slate-700">{translated.translated.get(row.type) || row.type}</td><td className="max-w-xs px-4 py-4 text-xs leading-5 text-slate-600">{translated.translated.get(row.label) || row.label}</td><td className="px-4 py-4 text-xs text-slate-500">{row.linked_claims.length || <span className="text-amber-700">Unlinked</span>}</td><td className="px-4 py-4">{row.citations[0] ? <CitationButton citation={row.citations[0]} onOpen={onCitation} /> : '—'}</td><td className="px-4 py-4"><Badge value={translated.translated.get(row.verification) || row.verification} /></td><td className="px-5 py-4 text-xs font-semibold">{Math.round(row.confidence * 100)}%</td></tr>)}</tbody></table>{filtered.length === 0 && <div className="grid min-h-48 place-items-center text-center text-xs text-slate-400"><div><FileSearch className="mx-auto mb-2" />No evidence matching this filter.</div></div>}</div>
  </div>
}

