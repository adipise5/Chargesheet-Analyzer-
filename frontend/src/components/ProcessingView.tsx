import { AlertTriangle, Check, Circle, LoaderCircle } from 'lucide-react'

type Status = { state: string; stage: string; progress: number; counts: Record<string, number | string>; stages: { name: string; state: string }[]; error?: string }

export function ProcessingView({ status }: { status: Status }) {
  const countEntries = [
    ['Total pages', status.counts.total_pages], ['Native pages', status.counts.native_pages], ['OCR pages', status.counts.ocr_pages],
    ['Gujarati pages', status.counts.gujarati_pages], ['English pages', status.counts.english_pages], ['Review pages', status.counts.low_confidence_pages],
    ['Entities', status.counts.entities], ['Evidence', status.counts.evidence],
  ]
  return <main className="min-h-screen bg-canvas px-8 py-8"><div className="mx-auto max-w-5xl"><div className="eyebrow">Case processing</div><div className="mt-2 flex items-center gap-3"><h1 className="text-2xl font-semibold">Building investigation workspace</h1>{status.state === 'running' && <LoaderCircle className="animate-spin text-teal-700" size={20} />}</div><p className="mt-2 text-sm text-slate-500">Each stage runs locally and keeps page-level provenance intact.</p>
    {status.state === 'error' && <div className="mt-6 flex gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"><AlertTriangle className="shrink-0" size={19} /><div><b>Processing stopped</b><p className="mt-1 text-xs leading-5">{status.error}</p></div></div>}
    <div className="mt-7 grid gap-5 lg:grid-cols-[1.35fr_.65fr]">
      <div className="panel p-6"><div className="mb-6"><div className="flex justify-between text-xs font-semibold"><span>{status.stage || 'Queued'}</span><span>{status.progress || 0}%</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-teal-600 transition-all" style={{ width: `${status.progress || 2}%` }} /></div></div><div className="space-y-1">{status.stages?.map(stage => <div key={stage.name} className="flex items-center gap-3 rounded-lg px-2 py-2"><span className={`grid h-5 w-5 place-items-center rounded-full ${stage.state === 'complete' ? 'bg-emerald-100 text-emerald-700' : stage.state === 'active' ? 'bg-sky-100 text-sky-700' : 'text-slate-300'}`}>{stage.state === 'complete' ? <Check size={13} /> : stage.state === 'active' ? <LoaderCircle className="animate-spin" size={13} /> : <Circle size={13} />}</span><span className={`text-xs ${stage.state === 'pending' ? 'text-slate-400' : 'font-medium text-slate-700'}`}>{stage.name}</span></div>)}</div></div>
      <div className="panel p-5"><div className="eyebrow">Live counts</div><div className="mt-4 grid grid-cols-2 gap-3">{countEntries.map(([label, value]) => <div key={String(label)} className="rounded-lg border border-slate-100 bg-slate-50 p-3"><div className="text-xl font-semibold">{value ?? '—'}</div><div className="mt-1 text-[10px] text-slate-500">{label}</div></div>)}</div><p className="mt-5 text-[11px] leading-5 text-slate-400">The source PDF is never modified. Native pages bypass OCR; scanned derivatives are retained under the case’s local UUID path.</p></div>
    </div>
  </div></main>
}

