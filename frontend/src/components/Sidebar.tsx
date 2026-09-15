import { Activity, BarChart3, FilePlus2, FolderKanban, Gauge, Languages, LockKeyhole, Settings, Shield, Sparkles, Trash2 } from 'lucide-react'
import type { Case } from '../types'
import { useLanguage } from '../i18n/languageHooks'

type Props = {
  cases: Case[]
  selectedCaseId?: string
  readOnly?: boolean
  screen: 'dashboard' | 'cases' | 'analytics' | 'new' | 'case'
  onDashboard: () => void
  onCases: () => void
  onAnalytics: () => void
  onNew: () => void
  onCase: (id: string) => void
  onPurge: () => void
}

export function Sidebar({ cases, selectedCaseId, screen, readOnly = false, onDashboard, onCases, onAnalytics, onNew, onCase, onPurge }: Props) {
  const { language, toggleLanguage, t } = useLanguage()
  return (
    <aside className="app-sidebar fixed inset-y-0 left-0 z-20 flex w-[258px] flex-col bg-navy text-slate-100">
      <div className="sidebar-brand border-b border-white/10 px-5 py-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-teal-600 text-white"><Shield size={21} /></div>
            <div className="min-w-0"><div className="text-[11px] font-semibold uppercase tracking-[.13em] text-slate-400">{t('Gujarat Police')}</div><div className="mt-0.5 text-sm font-semibold leading-tight">{t('Chargesheet Intelligence')}</div></div>
          </div>
          <button onClick={toggleLanguage} title={t('Toggle language')} aria-label={t('Toggle language')} className="inline-flex shrink-0 items-center gap-1 rounded-full border border-white/15 bg-white/5 px-2 py-1 text-[10px] font-bold text-slate-300 transition hover:border-teal-300 hover:bg-white/10 hover:text-white"><Languages size={12} />{language === 'english' ? 'ગુજરાતી' : 'English'}</button>
        </div>
      </div>
      <nav className="sidebar-nav space-y-1 px-3 py-4" aria-label="Primary">
        <NavButton active={screen === 'dashboard'} icon={<Gauge size={17} />} label={t('Dashboard')} onClick={onDashboard} />
        <NavButton active={screen === 'cases'} icon={<FolderKanban size={17} />} label={t('Cases')} onClick={onCases} />
        <NavButton active={screen === 'analytics'} icon={<BarChart3 size={17} />} label={t('Analytics')} onClick={onAnalytics} />
        {!readOnly && <NavButton active={screen === 'new'} icon={<FilePlus2 size={17} />} label={t('New Analysis')} onClick={onNew} />}
      </nav>
      <div className="sidebar-recents px-5 pt-3 text-[10px] font-bold uppercase tracking-[.18em] text-slate-500">{t('Recent cases')}</div>
      <div className="sidebar-recents scrollbar-thin mt-2 flex-1 space-y-1 overflow-y-auto px-3">
        {cases.slice(0, 6).map(item => (
          <button key={item.id} onClick={() => onCase(item.id)} className={`w-full rounded-lg px-3 py-2.5 text-left transition ${selectedCaseId === item.id ? 'bg-white/10' : 'hover:bg-white/[.06]'}`}>
            <div className="truncate text-xs font-semibold text-slate-200">{item.case_number}</div>
            <div className="mt-1 flex items-center gap-1.5 text-[10px] text-slate-500">{item.is_demo && <Sparkles size={10} />} {item.police_station}</div>
          </button>
        ))}
      </div>
      <div className="sidebar-footer space-y-1 border-t border-white/10 p-3">
        <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-slate-400"><Activity size={15} /> {t('Audit / System')}</div>
        <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-slate-400"><Settings size={15} /> {t('Settings')}</div>
        {readOnly ? <div className="flex items-start gap-2 rounded-lg border border-sky-800/60 bg-sky-950/45 px-3 py-3 text-[10px] leading-relaxed text-sky-100"><LockKeyhole className="mt-0.5 shrink-0" size={13} />{t('Hosted demo snapshot · read-only')}</div> : <><button onClick={onPurge} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs font-semibold text-red-300 transition hover:bg-red-950/40 hover:text-red-200"><Trash2 size={15} /> {t('Purge sensitive data')}</button><div className="mt-3 flex items-start gap-2 rounded-lg bg-emerald-950/35 px-3 py-3 text-[10px] leading-relaxed text-emerald-100/75"><LockKeyhole className="mt-0.5 shrink-0" size={13} />{t('On-device processing. No case content leaves approved local services.')}</div></>}
      </div>
    </aside>
  )
}

function NavButton({ active, icon, label, onClick }: { active: boolean; icon: React.ReactNode; label: string; onClick: () => void }) {
  return <button onClick={onClick} className={`sidebar-nav-button flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${active ? 'bg-teal-600 text-white shadow-sm' : 'text-slate-300 hover:bg-white/[.06] hover:text-white'}`}>{icon}{label}</button>
}

