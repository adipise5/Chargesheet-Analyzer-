import { FormEvent, useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { AlertTriangle, ArrowUp, Bot, LoaderCircle, MessageCircle, Network, ShieldCheck, User } from 'lucide-react'
import { api } from '../../api/client'
import { CitationButton } from '../../components/CitationButton'
import type { Citation } from '../../types'
import { useLanguage, useTranslatedTexts } from '../../i18n/LanguageContext'

const examples = ['What is this case about?', 'What should I verify before filing this charge sheet?', 'Which claims rely on a single source?', 'Which evidence items are not linked to any claim?']
type Answer = { answer: string; citations: Citation[]; confidence: number; review_required: boolean }
type ChatMessage = { id: number; question: string; response?: Answer; error?: string; pending?: boolean }

function AnswerText({ text }: { text: string }) {
  // Some local-model responses contain a UTF-8 bullet decoded as Windows-1252.
  // Repair that presentation artifact without changing stored source material.
  const cleanText = text.replaceAll('â€¢', '•')
  return <div className="space-y-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">{cleanText.split(/\n{2,}/).map((paragraph, index) => <p key={index}>{paragraph}</p>)}</div>
}

export function AskCaseView({ caseId, onCitation }: { caseId: string; onCitation: (value: Citation) => void }) {
  const { t } = useLanguage()
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [elapsed, setElapsed] = useState(0)
  const query = useMutation({
    mutationFn: ({ value }: { value: string; id: number }) => api.query(caseId, value),
    onSuccess: (response, variables) => setMessages(current => current.map(message => message.id === variables.id ? { ...message, response, pending: false } : message)),
    onError: (reason, variables) => setMessages(current => current.map(message => message.id === variables.id ? { ...message, error: reason instanceof Error ? reason.message : 'The request failed. Please try again.', pending: false } : message)),
  })
  const translatedAnswers = useTranslatedTexts(messages.flatMap(message => message.response ? [message.response.answer] : []))
  useEffect(() => {
    if (!query.isPending) return
    const started = Date.now()
    const timer = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000)
    return () => window.clearInterval(timer)
  }, [query.isPending])
  const submit = (event: FormEvent) => {
    event.preventDefault()
    const value = question.trim()
    if (value.length < 2 || query.isPending) return
    const id = Date.now()
    setMessages(current => [...current, { id, question: value, pending: true }])
    setQuestion('')
    setElapsed(0)
    query.mutate({ value, id })
  }
  return <div className="mx-auto max-w-4xl">
    <div className="eyebrow">{t('GraphRAG investigation')}</div><h2 className="mt-1.5 text-xl font-semibold">{t('Ask this case')}</h2><p className="mt-1 text-xs text-slate-500">{t('Ask questions in plain English. Answers use bounded retrieval and keep source citations attached to each response.')}</p>
    <div className="panel mt-6 overflow-hidden">
      <div className="border-b border-slate-100 bg-gradient-to-r from-sky-50/70 to-white px-5 py-4"><div className="flex items-center gap-2 text-xs font-semibold text-slate-700"><MessageCircle size={16} className="text-teal-700" /> {t('Case conversation')}</div><p className="mt-1 pl-6 text-[11px] text-slate-500">{t('This conversation exists only while this page is open and is not saved.')}</p></div>
      <div className="min-h-[430px] space-y-7 p-5 sm:p-6">
        {messages.length === 0 && <div className="grid min-h-[330px] place-items-center text-center"><div><div className="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-sky-50 text-sky-700"><Network /></div><h3 className="mt-4 text-sm font-semibold">{t('Ask about this case')}</h3><p className="mx-auto mt-2 max-w-md text-xs leading-5 text-slate-400">{t('The whole chargesheet is never sent to the model. Only a conservative, provenance-expanded context is used.')}</p><div className="mx-auto mt-5 flex max-w-xl flex-wrap justify-center gap-2">{examples.map(value => <button key={value} onClick={() => setQuestion(value)} className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[11px] text-slate-600 transition hover:border-sky-300 hover:bg-sky-50">{t(value)}</button>)}</div></div></div>}
        {messages.map(message => <div key={message.id} className="space-y-4"><div className="flex justify-end gap-3"><div className="max-w-[88%] rounded-2xl rounded-tr-md bg-slate-800 px-4 py-3 text-sm leading-6 text-white shadow-sm">{message.question}</div><div className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-full bg-slate-100 text-slate-600"><User size={16} /></div></div><div className="flex items-start gap-3"><div className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-full bg-teal-50 text-teal-700"><Bot size={17} /></div><div className="min-w-0 max-w-[92%] flex-1 rounded-2xl rounded-tl-md border border-slate-200 bg-white px-4 py-4 shadow-sm">{message.pending && <div role="status" className="flex items-center gap-2 text-xs text-slate-500"><LoaderCircle size={15} className="animate-spin text-teal-700" /> {t('Reading case sources and generating an answer locally…')} {elapsed}s</div>}{message.error && <div role="alert" className="text-sm text-red-800"><p className="font-semibold">{t('Could not answer this question')}</p><p className="mt-2 text-xs leading-5">{message.error}</p><p className="mt-2 text-xs text-slate-500">{t('Your question remains above. You can ask it again.')}</p></div>}{message.response && <><div className="mb-3 flex flex-wrap items-center gap-2 text-[10px] text-slate-400"><span className="font-semibold text-slate-600">{t('Case intelligence')}</span><span>·</span><span>{t('Confidence')} {Math.round(message.response.confidence * 100)}%</span><span>·</span><span>{message.response.citations.length} {t(message.response.citations.length === 1 ? 'source' : 'sources')}</span></div><AnswerText text={translatedAnswers.translated.get(message.response.answer) || message.response.answer} />{message.response.review_required && <div className="mt-5 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-800"><AlertTriangle size={15} className="shrink-0" />{t('Human review required before relying on this response.')}</div>}<div className="mt-5 border-t border-slate-100 pt-4"><div className="flex items-center gap-2 text-xs font-semibold text-slate-700"><ShieldCheck size={14} className="text-emerald-700" />{t('Sources')}</div><div className="mt-3 flex flex-wrap gap-2">{message.response.citations.map((citation, index) => <CitationButton key={`${citation.chunk_id}-${index}`} citation={citation} onOpen={onCitation} />)}{message.response.citations.length === 0 && <span className="text-xs text-slate-400">{t('No source passage was returned.')}</span>}</div></div></>}</div></div></div>)}
      </div>
      <form onSubmit={submit} className="flex gap-3 border-t border-slate-200 bg-slate-50 p-4 sm:p-5"><input aria-label={t('Your question')} minLength={2} maxLength={1000} value={question} onChange={event => setQuestion(event.target.value)} placeholder={t('Ask a question about this case…')} className="min-w-0 flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm" /><button type="submit" disabled={question.trim().length < 2 || query.isPending} className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-teal-700 text-white shadow-sm transition hover:bg-teal-800 disabled:opacity-40" aria-label={t('Ask case')}><ArrowUp size={17} /></button></form>
    </div>
  </div>
}
