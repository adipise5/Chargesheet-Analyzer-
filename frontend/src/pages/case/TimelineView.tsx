import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, CalendarClock, MapPin } from 'lucide-react'
import { api } from '../../api/client'
import { CitationButton } from '../../components/CitationButton'
import { Loading } from '../../components/Loading'
import type { Citation } from '../../types'

export function TimelineView({ caseId, onCitation }: { caseId: string; onCitation: (value: Citation) => void }) {
  const query = useQuery({ queryKey: ['timeline', caseId], queryFn: () => api.timeline(caseId) })
  if (query.isLoading) return <Loading />
  return <div className="mx-auto max-w-4xl"><div className="eyebrow">Chronology</div><h2 className="mt-1.5 text-xl font-semibold">Case timeline</h2><div className="mt-6 flex gap-2 overflow-x-auto">{['All', 'Incident', 'Investigation', 'Arrest', 'Seizure', 'Forensic', 'Digital'].map((item, index) => <button key={item} className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${index === 0 ? 'border-slate-700 bg-slate-800 text-white' : 'border-slate-200 bg-white text-slate-500'}`}>{item}</button>)}</div>
    <div className="relative mt-7 ml-3 border-l border-slate-200 pl-7">{query.data?.map(event => <article key={event.id} className="panel relative mb-4 p-5 before:absolute before:-left-[35px] before:top-6 before:h-3 before:w-3 before:rounded-full before:border-2 before:border-white before:bg-teal-600 before:ring-1 before:ring-teal-200"><div className="flex flex-wrap items-start justify-between gap-3"><div><div className="flex items-center gap-2 text-xs font-bold text-teal-800"><CalendarClock size={14} />{event.date || 'Date uncertain'} {event.time && `· ${event.time}`}{event.uncertain && <span className="chip border-amber-200 bg-amber-50 text-amber-800"><AlertTriangle size={11} /> Uncertain</span>}</div><h3 className="mt-2 text-sm font-semibold">{event.event}</h3>{event.location && <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-500"><MapPin size={13} />{event.location}</div>}</div><div className="text-xs font-semibold text-slate-500">{Math.round(event.confidence * 100)}%</div></div>{event.citation && <div className="mt-4"><CitationButton citation={event.citation} onOpen={onCitation} /></div>}</article>)}</div>
  </div>
}

