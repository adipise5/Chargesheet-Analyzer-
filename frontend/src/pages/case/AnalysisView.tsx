import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, ArrowUpRight, CheckCircle2, Link2Off, Scale, SearchCheck } from 'lucide-react'
import { api } from '../../api/client'
import { Badge } from '../../components/Badge'
import { CitationButton } from '../../components/CitationButton'
import { Loading } from '../../components/Loading'
import type { Citation } from '../../types'
import { useLanguage, useTranslatedTexts } from '../../i18n/languageHooks'

const filters = [
  ['all', 'All findings'], ['strong_point', 'Strong points'], ['weak_point', 'Weak points'],
  ['potential_mistake', 'Potential mistakes'], ['contradiction', 'Contradictions'], ['missing_link', 'Missing links'],
]

const icons = { strong_point: CheckCircle2, weak_point: Scale, potential_mistake: SearchCheck, contradiction: AlertTriangle, missing_link: Link2Off }

export function AnalysisView({ caseId, onCitation, onGraph }: { caseId: string; onCitation: (value: Citation) => void; onGraph: () => void }) {
  const [filter, setFilter] = useState('all')
  const query = useQuery({ queryKey: ['findings', caseId], queryFn: () => api.findings(caseId) })
  const { t } = useLanguage()
  const findings = useMemo(() => (query.data || []).filter(item => filter === 'all' || item.type === filter), [query.data, filter])
  const translated = useTranslatedTexts(findings.flatMap(item => [item.title, item.summary, item.why_important || '', item.recommended_correction || '', item.io_action || '', ...(item.differences || []).flatMap(d => [d.role, d.value])]))
  if (query.isLoading) return <Loading />
  return <div className="mx-auto max-w-[1220px]"><div className="flex items-end justify-between"><div><div className="eyebrow">{t('Evidence profile')}</div><h2 className="mt-1.5 text-xl font-semibold">{t('Analysis findings')}</h2><p className="mt-1 text-xs text-slate-500">{t('Interpretive classifications derived from transparent factors—not guilt probabilities.')}</p></div><div className="text-xs text-slate-400">{findings.length} {t('finding')}{findings.length === 1 ? '' : 's'}</div></div>
    <div className="mt-5 flex flex-wrap gap-2">{filters.map(([value, label]) => <button key={value} onClick={() => setFilter(value)} className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${filter === value ? 'border-slate-700 bg-slate-800 text-white' : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'}`}>{t(label)}</button>)}</div>
    <div className="mt-5 space-y-4">{findings.map(finding => { const tr = (value?: string) => value ? translated.translated.get(value) || value : ''; const Icon = icons[finding.type as keyof typeof icons] || SearchCheck; const sources = [...finding.supporting_sources, ...finding.contradicting_sources]; return <article key={finding.id} className="panel overflow-hidden"><div className="grid md:grid-cols-[72px_1fr]"><div className={`grid place-items-start border-b border-slate-100 p-5 md:border-b-0 md:border-r ${finding.type === 'contradiction' ? 'bg-red-50 text-red-700' : finding.type === 'strong_point' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}><Icon size={22} /></div><div className="p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><div className="eyebrow">{t(finding.type.replaceAll('_', ' '))}</div><h3 className="mt-1.5 text-base font-semibold">{tr(finding.title)}</h3></div><Badge value={finding.classification} /></div><p className="mt-3 max-w-4xl text-sm leading-6 text-slate-600">{tr(finding.summary)}</p><div className="mt-4 grid gap-3 border-y border-slate-100 py-3 sm:grid-cols-4"><Factor label={t('Support sources')} value={finding.supporting_sources.length} /><Factor label={t('Conflicting sources')} value={finding.contradicting_sources.length} /><Factor label={t('Confidence')} value={`${Math.round(finding.confidence * 100)}%`} /><Factor label={t('Verification')} value={finding.verified ? t('Source verified') : t('Review required')} /></div>{(finding.why_important || finding.recommended_correction || finding.io_action) && <div className="mt-4 grid gap-3 rounded-lg border border-slate-100 bg-slate-50 p-4 text-xs leading-5 md:grid-cols-3"><div><b>{t('Why important')}</b><p className="mt-1 text-slate-600">{tr(finding.why_important)}</p></div><div><b>{t('Recommended correction')}</b><p className="mt-1 text-slate-600">{tr(finding.recommended_correction)}</p></div><div><b>{t('IO action')}</b><p className="mt-1 text-slate-600">{tr(finding.io_action)}</p></div></div>}{finding.differences && finding.differences.length > 0 && <div className="mt-3 grid gap-2 sm:grid-cols-2">{finding.differences.map(difference => <div key={`${difference.document}-${difference.value}`} className="rounded border border-slate-100 p-2 text-xs"><b>{difference.document}</b><div className="text-slate-500">{tr(difference.role)} · {tr(difference.value)}</div></div>)}</div>}<div className="mt-4 flex flex-wrap items-center gap-2">{sources.map((citation, index) => <CitationButton key={`${citation.chunk_id}-${index}`} citation={citation} onOpen={onCitation} />)}<button onClick={onGraph} className="ml-auto inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-bold text-sky-700 hover:bg-sky-50">{t('Open in graph')} <ArrowUpRight size={13} /></button></div></div></div></article> })}</div>
  </div>
}

function Factor({ label, value }: { label: string; value: string | number }) { return <div><div className="text-[10px] uppercase tracking-wide text-slate-400">{label}</div><div className="mt-1 text-xs font-semibold text-slate-700">{value}</div></div> }

