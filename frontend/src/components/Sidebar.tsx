import { Activity, BarChart3, FilePlus2, FolderKanban, Gauge, LockKeyhole, Settings, Shield, Sparkles, Trash2 } from 'lucide-react'
import type { Case } from '../types'

type Props = {
  cases: Case[]
  selectedCaseId?: string
  screen: 'dashboard' | 'cases' | 'analytics' | 'new' | 'case'
  onDashboard: () => void
  onCases: () => void
  onAnalytics: () => void
  onNew: () => void
  onCase: (id: string) => void
  onPurge: () => void
}

export function Sidebar({ cases, selectedCaseId, screen, onDashboard, onCases, onAnalytics, onNew, onCase, onPurge }: Props) {
  return (
    <aside className="fixed inset-y-0 left-0 z-20 flex w-[258px] flex-col bg-navy text-slate-100">
      <div className="border-b border-white/10 px-5 py-5">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-lg bg-teal-600 text-white"><Shield size={21} /></div>
          <div><div className="text-[11px] font-semibold uppercase tracking-[.13em] text-slate-400">Gujarat Police</div><div className="mt-0.5 text-sm font-semibold leading-tight">Chargesheet Intelligence</div></div>
        </div>
      </div>
      <nav className="space-y-1 px-3 py-4" aria-label="Primary">
        <NavButton active={screen === 'dashboard'} icon={<Gauge size={17} />} label="Dashboard" onClick={onDashboard} />
        <NavButton active={screen === 'cases'} icon={<FolderKanban size={17} />} label="Cases" onClick={onCases} />
        <NavButton active={screen === 'analytics'} icon={<BarChart3 size={17} />} label="Analytics" onClick={onAnalytics} />
        <NavButton active={screen === 'new'} icon={<FilePlus2 size={17} />} label="New Analysis" onClick={onNew} />
      </nav>
      <div className="px-5 pt-3 text-[10px] font-bold uppercase tracking-[.18em] text-slate-500">Recent cases</div>
      <div className="scrollbar-thin mt-2 flex-1 space-y-1 overflow-y-auto px-3">
        {cases.slice(0, 6).map(item => (
          <button key={item.id} onClick={() => onCase(item.id)} className={`w-full rounded-lg px-3 py-2.5 text-left transition ${selectedCaseId === item.id ? 'bg-white/10' : 'hover:bg-white/[.06]'}`}>
            <div className="truncate text-xs font-semibold text-slate-200">{item.case_number}</div>
            <div className="mt-1 flex items-center gap-1.5 text-[10px] text-slate-500">{item.is_demo && <Sparkles size={10} />} {item.police_station}</div>
          </button>
        ))}
      </div>
      <div className="space-y-1 border-t border-white/10 p-3">
        <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-slate-400"><Activity size={15} /> Audit / System</div>
        <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-slate-400"><Settings size={15} /> Settings</div>
        <button onClick={onPurge} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs font-semibold text-red-300 transition hover:bg-red-950/40 hover:text-red-200"><Trash2 size={15} /> Purge sensitive data</button>
        <div className="mt-3 flex items-start gap-2 rounded-lg bg-emerald-950/35 px-3 py-3 text-[10px] leading-relaxed text-emerald-100/75"><LockKeyhole className="mt-0.5 shrink-0" size={13} />On-device processing. No case content leaves approved local services.</div>
      </div>
    </aside>
  )
}

function NavButton({ active, icon, label, onClick }: { active: boolean; icon: React.ReactNode; label: string; onClick: () => void }) {
  return <button onClick={onClick} className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${active ? 'bg-teal-600 text-white shadow-sm' : 'text-slate-300 hover:bg-white/[.06] hover:text-white'}`}>{icon}{label}</button>
}

