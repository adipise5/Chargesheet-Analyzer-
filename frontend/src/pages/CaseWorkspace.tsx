import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle2, Clock3, FileStack, Languages, ShieldCheck } from 'lucide-react'
import { api } from '../api/client'
import { Loading } from '../components/Loading'
import { ProcessingView } from '../components/ProcessingView'
import { AnalysisView } from './case/AnalysisView'
import { AskCaseView } from './case/AskCaseView'
import { DocumentsView } from './case/DocumentsView'
import { DefenseView } from './case/DefenseView'
import { PrecedentsView } from './case/PrecedentsView'
import { EvidenceView } from './case/EvidenceView'
import { GraphView } from './case/GraphView'
import { OverviewView } from './case/OverviewView'
import { TimelineView } from './case/TimelineView'
import type { CaseTab, Citation } from '../types'
import { useLanguage } from '../i18n/languageHooks'
import { RecordTypeBadge } from '../components/RecordTypeBadge'

const tabs: CaseTab[] = ['Overview', 'Analysis', 'Defense', 'Precedents', 'Evidence', 'Timeline', 'Graph', 'Documents', 'Ask Case']

export function CaseWorkspace({ caseId, initialCitation, onCitation, readOnly = false }: { caseId: string; initialCitation?: Citation; onCitation: (value: Citation) => void; readOnly?: boolean }) {
  const { language, toggleLanguage, t } = useLanguage()
  const [tab, setTab] = useState<CaseTab>(initialCitation ? 'Documents' : 'Overview')
  const [citation, setCitation] = useState<Citation | undefined>(initialCitation)
  const caseQuery = useQuery({ queryKey: ['case', caseId], queryFn: () => api.case(caseId), refetchInterval: query => query.state.data?.status === 'processing' ? 1000 : false })
  const status = useQuery({ queryKey: ['status', caseId], queryFn: () => api.status(caseId), refetchInterval: query => ['running', 'queued'].includes(query.state.data?.state || '') ? 900 : false })
  useEffect(() => { if (initialCitation) { setCitation(initialCitation); setTab('Documents') } }, [initialCitation])
  const openCitation = (value: Citation) => { setCitation(value); onCitation(value); setTab('Documents') }
  if (caseQuery.isLoading || status.isLoading) return <Loading />
  if (caseQuery.isError || !caseQuery.data) return <div role="alert" className="p-10 text-sm text-red-700">{t('This case could not be loaded. It may have been removed during a database reset. Open an existing case from Cases in the sidebar.')}</div>
  if (status.data && ['running', 'queued'].includes(status.data.state)) return <ProcessingView status={status.data} />
  const item = caseQuery.data
  return (
    <main className="min-h-screen bg-canvas">
      <header className="border-b border-slate-200 bg-white px-8 pt-6">
        {item.record_type === 'public_judgment' ? <div className="mb-4 flex items-center gap-2 rounded-lg border border-violet-200 bg-violet-50 px-3 py-2 text-xs font-bold tracking-wide text-violet-900"><ShieldCheck size={14} /> {t('Incomplete public source set — not a complete chargesheet or live police record.')}</div> : (item.record_type === 'educational_sample' || item.is_demo) && <div className="mb-4 flex items-center gap-2 rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 text-xs font-bold tracking-wide text-sky-800"><ShieldCheck size={14} /> {t('EDUCATIONAL SAMPLE — NOT A REAL POLICE RECORD')}</div>}
        <div className="flex items-start justify-between gap-5"><div><div className="eyebrow">{t(item.record_type === 'public_judgment' ? 'Case record / ID' : 'FIR / Case ID')}</div><div className="flex items-center gap-3"><h1 className="mt-1 text-2xl font-semibold tracking-tight">{item.case_number}</h1><RecordTypeBadge recordType={item.record_type} isDemo={item.is_demo} /><button onClick={toggleLanguage} className="mt-1 inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-bold text-slate-600 shadow-sm transition hover:border-teal-300 hover:text-teal-800" aria-label={t('Toggle language')} title={t('Toggle language')}>{language === 'english' ? 'ગુજરાતી' : 'English'}</button></div><div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-500"><span className="inline-flex items-center gap-1.5"><FileStack size={13} />{item.police_station}</span><span className="inline-flex items-center gap-1.5"><Languages size={13} />{item.language}</span><span className="inline-flex items-center gap-1.5"><Clock3 size={13} />{t('Updated')} {new Date(item.updated_at).toLocaleString()}</span></div></div><div className="flex flex-wrap items-center justify-end gap-2"><div className={`chip mt-2 ${item.status === 'ready' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'}`}>{item.status === 'ready' ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}{t(item.status)}</div>{readOnly && <div className="chip mt-2 border-sky-200 bg-sky-50 text-sky-700">{t('Read-only snapshot')}</div>}</div></div>
        <nav className="mt-6 flex gap-1 overflow-x-auto" aria-label={t('Case workspace')}>{tabs.map(value => <button key={value} onClick={() => setTab(value)} className={`border-b-2 px-4 py-3 text-xs font-semibold transition ${tab === value ? 'border-teal-700 text-teal-800' : 'border-transparent text-slate-500 hover:text-slate-800'}`}>{t(value)}</button>)}</nav>
      </header>
      <div className="px-8 py-7">
        {status.data?.state === 'error' && <div className="mb-5 rounded-lg border border-red-200 bg-red-50 p-4 text-xs text-red-800">{t('Processing error')}: {status.data.error}</div>}
        {tab === 'Overview' && <OverviewView caseId={caseId} status={status.data} onCitation={openCitation} onTab={setTab} />}
        {tab === 'Analysis' && <AnalysisView caseId={caseId} onCitation={openCitation} onGraph={() => setTab('Graph')} />}
        {tab === 'Defense' && <DefenseView caseId={caseId} onCitation={openCitation} />}
        {tab === 'Precedents' && <PrecedentsView caseId={caseId} readOnly={readOnly} />}
        {tab === 'Evidence' && <EvidenceView caseId={caseId} onCitation={openCitation} />}
        {tab === 'Timeline' && <TimelineView caseId={caseId} onCitation={openCitation} />}
        {tab === 'Graph' && <GraphView caseId={caseId} onCitation={openCitation} />}
        {tab === 'Documents' && <DocumentsView caseId={caseId} citation={citation} readOnly={readOnly} />}
        {tab === 'Ask Case' && <AskCaseView caseId={caseId} onCitation={openCitation} readOnly={readOnly} />}
      </div>
    </main>
  )
}

