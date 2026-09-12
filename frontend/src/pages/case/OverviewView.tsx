import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, ArrowRight, Eye, FileText, Network, Scale, ScanText, Users } from 'lucide-react'
import { api } from '../../api/client'
import { Badge } from '../../components/Badge'
import { CitationButton } from '../../components/CitationButton'
import { Loading } from '../../components/Loading'
import type { CaseTab, Citation } from '../../types'
import { useLanguage } from '../../i18n/LanguageContext'

const metricIcons = [FileText, Scale, Users, ScanText, Network, AlertTriangle, Eye]

export function OverviewView({ caseId, status, onCitation, onTab }: { caseId: string; status?: { counts: Record<string, number | string> }; onCitation: (value: Citation) => void; onTab: (value: CaseTab) => void }) {
  const { language, t } = useLanguage()
  const query = useQuery({ queryKey: ['overview', caseId], queryFn: () => api.overview(caseId) })
  if (!query.data) return <Loading />
  const data = query.data
  return <div className="mx-auto max-w-[1320px]">
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">{Object.entries(data.metrics).map(([label, value], index) => { const Icon = metricIcons[index] || FileText; return <div key={label} className="panel p-4"><div className="flex items-center justify-between"><div className="text-2xl font-semibold tracking-tight">{value}</div><Icon size={16} className="text-slate-400" /></div><div className="mt-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">{label.replaceAll('_', ' ')}</div></div> })}</div>
    <div className="mt-5 grid gap-5 xl:grid-cols-[1.25fr_.75fr]">
      <section className="panel p-6"><div className="flex items-center justify-between"><div><div className="eyebrow">{t('Verified workspace synthesis')}</div><h2 className="mt-1.5 text-lg font-semibold">{t('Case summary')}</h2></div><Scale size={20} className="text-teal-700" /></div><p className="mt-5 whitespace-pre-wrap text-sm leading-7 text-slate-600">{data.summary[language]}</p><div className="mt-5 rounded-lg border border-amber-100 bg-amber-50/60 p-3 text-xs leading-5 text-amber-800">{t('This system supports evidence review. It does not determine guilt, innocence, or likely case outcome.')}</div></section>
      <section className="panel p-6"><div className="flex items-center justify-between"><div><div className="eyebrow">OCR quality</div><h2 className="mt-1.5 text-lg font-semibold">{status?.counts.total_pages ?? data.metrics.pages} pages</h2></div><ScanText size={19} className="text-sky-700" /></div><div className="mt-5 space-y-3"><Quality label="Native text" value={Number(status?.counts.native_pages || (data.metrics.pages ?? 0))} total={data.metrics.pages} color="bg-emerald-500" /><Quality label="Printed OCR" value={Number(status?.counts.ocr_pages || 0)} total={data.metrics.pages} color="bg-sky-500" /><Quality label="Review required" value={Number(status?.counts.low_confidence_pages || 0)} total={data.metrics.pages} color="bg-amber-500" /></div><button onClick={() => onTab('Documents')} className="mt-5 inline-flex items-center gap-2 text-xs font-bold text-sky-700">Open source review <ArrowRight size={13} /></button></section>
    </div>
    <div className="mt-5 grid gap-5 lg:grid-cols-2">
      <section className="panel p-6"><div className="eyebrow">Key people & material</div><h2 className="mt-1.5 text-lg font-semibold">Case entities</h2><div className="mt-4 grid gap-2 sm:grid-cols-2">{data.key_entities.map(node => <button key={node.id} onClick={() => onTab('Graph')} className="flex items-center gap-3 rounded-lg border border-slate-100 px-3 py-3 text-left hover:border-sky-200 hover:bg-sky-50/40"><span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-100 text-xs font-bold text-slate-600">{node.type.slice(0, 2).toUpperCase()}</span><span className="min-w-0"><span className="block truncate text-xs font-semibold">{node.label}</span><span className="mt-0.5 block text-[10px] text-slate-400">{node.type} · {Math.round(node.confidence * 100)}%</span></span></button>)}</div></section>
      <section className="panel p-6"><div className="eyebrow">Priority review</div><h2 className="mt-1.5 text-lg font-semibold">Source-backed findings</h2><div className="mt-4 space-y-3">{data.priority_findings.map(finding => <div key={finding.id} className="rounded-lg border border-slate-100 p-3"><div className="flex items-start justify-between gap-3"><div className="text-xs font-semibold">{finding.title}</div><Badge value={finding.classification} /></div><p className="mt-2 line-clamp-2 text-[11px] leading-5 text-slate-500">{finding.summary}</p><div className="mt-2 flex flex-wrap gap-2">{[...finding.supporting_sources, ...finding.contradicting_sources].slice(0, 1).map(citation => <CitationButton key={citation.chunk_id} citation={citation} onOpen={onCitation} />)}</div></div>)}</div></section>
    </div>
  </div>
}

function Quality({ label, value, total, color }: { label: string; value: number; total: number; color: string }) { const width = total ? Math.max(1, Math.round(value / total * 100)) : 0; return <div><div className="flex justify-between text-xs"><span className="text-slate-500">{label}</span><span className="font-semibold">{value}</span></div><div className="mt-1.5 h-1.5 rounded-full bg-slate-100"><div className={`h-full rounded-full ${color}`} style={{ width: `${width}%` }} /></div></div> }

