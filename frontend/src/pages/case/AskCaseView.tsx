import { FormEvent, useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { AlertTriangle, ArrowUp, Bot, Network, ShieldCheck } from 'lucide-react'
import { api } from '../../api/client'
import { CitationButton } from '../../components/CitationButton'
import type { Citation } from '../../types'

const examples = ['What is this case about?', 'What should I verify before filing this charge sheet?', 'Which claims rely on a single source?', 'Which evidence items are not linked to any claim?']

export function AskCaseView({ caseId, onCitation }: { caseId: string; onCitation: (value: Citation) => void }) {
  const [question, setQuestion] = useState('')
  const query = useMutation({ mutationFn: (value: string) => api.query(caseId, value) })
  const [elapsed, setElapsed] = useState(0)
  useEffect(() => {
    if (!query.isPending) return
    const started = Date.now()
    const timer = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000)
    return () => window.clearInterval(timer)
  }, [query.isPending])
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (question.trim().length >= 2 && !query.isPending) {
      setElapsed(0)
      query.mutate(question.trim())
    }
  }
  return <div className="mx-auto max-w-4xl"><div className="eyebrow">GraphRAG investigation</div><h2 className="mt-1.5 text-xl font-semibold">Ask this case</h2><p className="mt-1 text-xs text-slate-500">Answers use bounded graph, semantic, and lexical retrieval. Every supported factual statement must retain a source.</p>
    <div className="panel mt-6 overflow-hidden"><div className="min-h-[430px] p-6">{!query.data && !query.isPending && !query.isError && <div className="grid min-h-[350px] place-items-center text-center"><div><div className="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-sky-50 text-sky-700"><Network /></div><h3 className="mt-4 text-sm font-semibold">Ask about evidence relationships</h3><p className="mx-auto mt-2 max-w-md text-xs leading-5 text-slate-400">The whole chargesheet is never sent to the model. Only a conservative, provenance-expanded context is used.</p><div className="mx-auto mt-5 flex max-w-xl flex-wrap justify-center gap-2">{examples.map(value => <button key={value} onClick={() => setQuestion(value)} className="rounded-full border border-slate-200 px-3 py-1.5 text-[11px] text-slate-600 hover:border-sky-300 hover:bg-sky-50">{value}</button>)}</div></div></div>}{query.isError && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800"><p className="font-semibold">Could not answer this question</p><p className="mt-2">{query.error instanceof Error ? query.error.message : 'The request failed. Please try again.'}</p><p className="mt-2">Your question is still below. You can edit it and submit again.</p></div>}{query.isPending && <div className="grid min-h-[350px] place-items-center"><div className="text-center"><Bot className="mx-auto animate-pulse text-teal-700" /><p role="status" className="mt-3 text-xs text-slate-500">Reading case sources and generating an answer locally… {elapsed}s</p><p className="mt-2 text-xs text-slate-400">The local model may take a minute to respond.</p></div></div>}{query.data && !query.isPending && !query.isError && <article><div className="flex items-center gap-2"><div className="grid h-8 w-8 place-items-center rounded-lg bg-teal-50 text-teal-700"><Bot size={17} /></div><div><div className="text-xs font-semibold">Case intelligence response</div><div className="mt-0.5 text-[10px] text-slate-400">Confidence {Math.round(query.data.confidence * 100)}% · {query.data.citations.length} sources</div></div></div><div className="mt-5 whitespace-pre-wrap text-sm leading-7 text-slate-700">{query.data.answer}</div>{query.data.review_required && <div className="mt-5 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800"><AlertTriangle size={15} />Human review required before relying on this response.</div>}<div className="mt-6 border-t border-slate-100 pt-4"><div className="flex items-center gap-2 text-xs font-semibold"><ShieldCheck size={14} className="text-emerald-700" />Sources</div><div className="mt-3 flex flex-wrap gap-2">{query.data.citations.map((citation, index) => <CitationButton key={`${citation.chunk_id}-${index}`} citation={citation} onOpen={onCitation} />)}</div></div></article>}</div><form onSubmit={submit} className="flex gap-3 border-t border-slate-200 bg-slate-50 p-4"><input aria-label="Your question" minLength={2} maxLength={1000} value={question} onChange={event => setQuestion(event.target.value)} placeholder="Ask an evidence-oriented question…" className="flex-1 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm" /><button type="submit" disabled={question.trim().length < 2 || query.isPending} className="grid h-10 w-10 place-items-center rounded-lg bg-teal-700 text-white disabled:opacity-40" aria-label="Ask case"><ArrowUp size={17} /></button></form></div>
  </div>
}

