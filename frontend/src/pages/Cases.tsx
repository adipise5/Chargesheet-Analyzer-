import { useMemo, useState } from 'react'
import { ArrowRight, FolderOpen, Search, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import type { Case } from '../types'

export function Cases({ cases, onCase, onNew, onReload }: { cases: Case[]; onCase: (id: string) => void; onNew: () => void; onReload: () => void }) {
  const [search, setSearch] = useState('')
  const [deleting, setDeleting] = useState<string | null>(null)
  
  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (confirm('Are you sure you want to delete this case and all its data? This cannot be undone.')) {
      setDeleting(id)
      try {
        await api.deleteCase(id)
        onReload()
      } catch {
        alert('Failed to delete case')
      } finally {
        setDeleting(null)
      }
    }
  }
  
  const visible = useMemo(() => cases.filter(item => `${item.case_number} ${item.police_station}`.toLowerCase().includes(search.toLowerCase())), [cases, search])
  
  return <main className="min-h-screen bg-canvas px-8 py-8 lg:px-10"><div className="mx-auto max-w-[1320px]"><div className="flex flex-wrap items-end justify-between gap-4"><div><div className="eyebrow">Case register</div><h1 className="mt-2 text-3xl font-semibold tracking-tight text-ink">Cases</h1><p className="mt-2 text-sm text-slate-500">Open an existing investigation workspace or start a new analysis.</p></div><button onClick={onNew} className="rounded-lg bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white">New analysis</button></div><label className="relative mt-7 block max-w-md"><Search className="absolute left-3 top-3 text-slate-400" size={16} /><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Search case ID or police station" className="w-full rounded-lg border border-slate-200 bg-white py-2.5 pl-9 pr-3 text-sm" /></label><section className="panel mt-5 overflow-hidden">{visible.length ? visible.map(item => <div key={item.id} className="group relative flex w-full items-center border-b border-slate-100 last:border-0 hover:bg-slate-50"><button onClick={() => onCase(item.id)} className="grid flex-1 grid-cols-[1fr_220px_120px_26px] items-center gap-4 px-5 py-4 text-left"><div><div className="flex items-center gap-2"><span className="text-sm font-semibold">{item.case_number}</span>{item.is_demo && <span className="chip border-sky-200 bg-sky-50 text-sky-700">Synthetic demo</span>}</div><div className="mt-1 text-xs text-slate-400">{item.language}</div></div><div className="text-xs text-slate-500">{item.police_station}</div><div className="text-xs font-semibold capitalize text-teal-700">{item.status}</div><ArrowRight size={15} className="text-slate-300" /></button><button disabled={deleting === item.id} onClick={(e) => handleDelete(e, item.id)} className="absolute right-12 p-2 text-slate-400 opacity-0 transition hover:text-red-600 group-hover:opacity-100 disabled:opacity-50"><Trash2 size={16} /></button></div>) : <div className="grid min-h-48 place-items-center p-6 text-center"><div><FolderOpen className="mx-auto text-slate-300" /><p className="mt-3 text-sm font-medium">No matching cases</p><p className="mt-1 text-xs text-slate-400">Adjust the search or create a new analysis.</p></div></div>}</section></div></main>
}
