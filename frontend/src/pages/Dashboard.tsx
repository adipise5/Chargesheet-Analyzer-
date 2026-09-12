import { useQuery } from '@tanstack/react-query'
import { ArrowRight, BrainCircuit, FilePlus2, FolderOpen, Network, ShieldCheck, Sparkles } from 'lucide-react'
import { api } from '../api/client'
import type { Case } from '../types'

export function Dashboard({ cases, onCase, onNew, onDemo }: { cases: Case[]; onCase: (id: string) => void; onNew: () => void; onDemo: () => void }) {
  const health = useQuery({ queryKey: ['health'], queryFn: api.health })
  const qwenReady = !!health.data?.ollama.available && !health.data.ollama.missing.includes(health.data.llm_model)
  const embeddingReady = !!health.data?.ollama.available && !health.data.ollama.missing.includes(health.data.embedding_model)
  return (
    <main className="min-h-screen bg-canvas px-8 py-8 lg:px-10">
      <div className="mx-auto max-w-[1320px]">
        <header className="flex items-end justify-between gap-5">
          <div><div className="eyebrow">Investigation workspace</div><h1 className="mt-2 text-3xl font-semibold tracking-tight text-ink">Chargesheet intelligence</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Investigate case structure, claims, evidence, contradictions, and source provenance from one secure local workspace.</p></div>
          <button onClick={onNew} className="inline-flex items-center gap-2 rounded-lg bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-teal-800"><FilePlus2 size={16} /> New analysis</button>
        </header>
        <section className="mt-8 grid gap-4 xl:grid-cols-[1.35fr_.65fr]">
          <div className="panel overflow-hidden">
            <div className="border-b border-slate-100 px-6 py-5"><div className="flex items-center justify-between"><div><div className="eyebrow">Safe presentation workspace</div><h2 className="mt-1.5 text-lg font-semibold">Synthetic demonstration case</h2></div><div className="rounded-lg bg-sky-50 p-2.5 text-sky-700"><Sparkles size={19} /></div></div></div>
            <div className="grid gap-4 px-6 py-6 md:grid-cols-3">
              <Feature icon={<BrainCircuit />} title="Evidence profiles" text="Inspect corroboration without guilt scoring." />
              <Feature icon={<Network />} title="Claim-centric graph" text="Trace every edge to its source passage." />
              <Feature icon={<ShieldCheck />} title="Offline by design" text="Only local backend, Ollama, and Neo4j." />
            </div>
            <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50/70 px-6 py-4"><p className="text-xs text-slate-500">Clearly marked fictional names, identifiers, and records.</p><button onClick={onDemo} className="inline-flex items-center gap-2 rounded-lg border border-sky-200 bg-white px-3.5 py-2 text-xs font-bold text-sky-800 hover:bg-sky-50">Load Demo Case <ArrowRight size={14} /></button></div>
          </div>
          <div className="panel p-5">
            <div className="flex items-center gap-2"><div className={`h-2 w-2 rounded-full ${health.data ? 'bg-emerald-500' : 'bg-amber-400'}`} /><h2 className="text-sm font-semibold">Local system readiness</h2></div>
            <div className="mt-5 space-y-3 text-xs">
              <HealthRow label="Backend policy" value="Localhost only" ok />
              <HealthRow label="Local Qwen" value={qwenReady ? health.data!.llm_model : `Missing · ${health.data?.llm_model || 'checking'}`} ok={qwenReady} />
              <HealthRow label="BGE-M3" value={embeddingReady ? health.data!.embedding_model : `Missing · ${health.data?.embedding_model || 'checking'}`} ok={embeddingReady} />
              <HealthRow label="Tesseract guj+eng" value={health.data?.tesseract.message || 'Checking'} ok={!!health.data?.tesseract.available} />
              <HealthRow label="Neo4j projection" value={health.data?.neo4j.mode || 'Checking'} ok={!!health.data?.neo4j.mode} />
            </div>
          </div>
        </section>
        <section className="mt-7">
          <div className="mb-3 flex items-center justify-between"><h2 className="text-sm font-semibold">Recent cases</h2><span className="text-xs text-slate-400">{cases.length} workspace{cases.length === 1 ? '' : 's'}</span></div>
          <div className="panel overflow-hidden">
            {cases.length === 0 ? <div className="grid min-h-48 place-items-center p-6 text-center"><div><FolderOpen className="mx-auto text-slate-300" /><p className="mt-3 text-sm font-medium">No cases yet</p><p className="mt-1 text-xs text-slate-400">Load the safe demo or start a new analysis.</p></div></div> : cases.map(item => <button key={item.id} onClick={() => onCase(item.id)} className="grid w-full grid-cols-[1fr_220px_120px_26px] items-center gap-4 border-b border-slate-100 px-5 py-4 text-left last:border-0 hover:bg-slate-50"><div><div className="flex items-center gap-2"><span className="text-sm font-semibold">{item.case_number}</span>{item.is_demo && <span className="chip border-sky-200 bg-sky-50 text-sky-700">Synthetic demo</span>}</div><div className="mt-1 text-xs text-slate-400">{item.language}</div></div><div className="text-xs text-slate-500">{item.police_station}</div><div className="text-xs font-semibold capitalize text-teal-700">{item.status}</div><ArrowRight size={15} className="text-slate-300" /></button>)}
          </div>
        </section>
      </div>
    </main>
  )
}

function Feature({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) { return <div><div className="text-teal-700 [&>svg]:h-5 [&>svg]:w-5">{icon}</div><h3 className="mt-3 text-sm font-semibold">{title}</h3><p className="mt-1 text-xs leading-5 text-slate-500">{text}</p></div> }
function HealthRow({ label, value, ok }: { label: string; value: string; ok: boolean }) { return <div className="flex items-center justify-between gap-4"><span className="text-slate-500">{label}</span><span className={`max-w-[160px] truncate font-semibold ${ok ? 'text-emerald-700' : 'text-amber-700'}`}>{value}</span></div> }
