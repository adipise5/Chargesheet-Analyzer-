import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './api/client'
import { Sidebar } from './components/Sidebar'
import { Dashboard } from './pages/Dashboard'
import { NewAnalysis } from './pages/NewAnalysis'
import { CaseWorkspace } from './pages/CaseWorkspace'
import { Cases } from './pages/Cases'
import { AnalyticsDashboard } from './pages/AnalyticsDashboard'
import type { Citation } from './types'
import { useLanguage } from './i18n/languageHooks'

export default function App() {
  const { t } = useLanguage()
  const client = useQueryClient()
  const cases = useQuery({ queryKey: ['cases'], queryFn: api.cases })
  const health = useQuery({ queryKey: ['health'], queryFn: api.health })
  const readOnly = !!health.data?.read_only
  const [screen, setScreen] = useState<'dashboard' | 'cases' | 'analytics' | 'new' | 'case'>('dashboard')
  const [caseId, setCaseId] = useState<string>()
  const [citation, setCitation] = useState<Citation>()
  const demo = useMutation({ mutationFn: api.loadDemo, onSuccess: async value => { await client.invalidateQueries({ queryKey: ['cases'] }); setCaseId(value.id); setScreen('case') } })
  const openCase = (id: string) => { setCaseId(id); setCitation(undefined); setScreen('case') }
  const openCitation = (value: Citation) => { setCitation(value) }
  const purge = async () => {
    if (!window.confirm(t('Permanently erase all local cases, uploaded documents, extracted text, graphs, findings, audits, and imported judgments? This cannot be undone.'))) return
    try {
      await api.purgeData()
      await client.invalidateQueries()
      setCaseId(undefined)
      setCitation(undefined)
      setScreen('dashboard')
      window.alert(t('All local sensitive case data has been purged.'))
    } catch (reason) {
      window.alert(reason instanceof Error ? `${t('Purge failed')}: ${reason.message}` : t('Purge failed. The local data was not confirmed as erased.'))
    }
  }
  return (
    <div>
      <Sidebar cases={cases.data || []} selectedCaseId={caseId} screen={screen} readOnly={readOnly} onDashboard={() => setScreen('dashboard')} onCases={() => setScreen('cases')} onAnalytics={() => setScreen('analytics')} onNew={() => setScreen('new')} onCase={openCase} onPurge={purge} />
      <div className="app-content ml-[258px] min-h-screen">
        {screen === 'dashboard' && <Dashboard cases={cases.data || []} readOnly={readOnly} onCase={openCase} onNew={() => setScreen('new')} onDemo={() => demo.mutate()} />}
        {screen === 'cases' && <Cases cases={cases.data || []} readOnly={readOnly} onCase={openCase} onNew={() => setScreen('new')} onReload={() => client.invalidateQueries({ queryKey: ['cases'] })} />}
        {screen === 'analytics' && <AnalyticsDashboard />}
        {screen === 'new' && <NewAnalysis readOnly={readOnly} onCreated={openCase} />}
        {screen === 'case' && caseId && <CaseWorkspace key={caseId} caseId={caseId} readOnly={readOnly} initialCitation={citation} onCitation={openCitation} />}
      </div>
    </div>
  )
}
