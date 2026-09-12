import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './api/client'
import { Sidebar } from './components/Sidebar'
import { Dashboard } from './pages/Dashboard'
import { NewAnalysis } from './pages/NewAnalysis'
import { CaseWorkspace } from './pages/CaseWorkspace'
import { Cases } from './pages/Cases'
import type { Citation } from './types'

export default function App() {
  const client = useQueryClient()
  const cases = useQuery({ queryKey: ['cases'], queryFn: api.cases })
  const [screen, setScreen] = useState<'dashboard' | 'cases' | 'new' | 'case'>('dashboard')
  const [caseId, setCaseId] = useState<string>()
  const [citation, setCitation] = useState<Citation>()
  const demo = useMutation({ mutationFn: api.loadDemo, onSuccess: async value => { await client.invalidateQueries({ queryKey: ['cases'] }); setCaseId(value.id); setScreen('case') } })
  const openCase = (id: string) => { setCaseId(id); setCitation(undefined); setScreen('case') }
  const openCitation = (value: Citation) => { setCitation(value) }
  return (
    <div>
      <Sidebar cases={cases.data || []} selectedCaseId={caseId} screen={screen} onDashboard={() => setScreen('dashboard')} onCases={() => setScreen('cases')} onNew={() => setScreen('new')} onCase={openCase} />
      <div className="ml-[258px] min-h-screen">
        {screen === 'dashboard' && <Dashboard cases={cases.data || []} onCase={openCase} onNew={() => setScreen('new')} onDemo={() => demo.mutate()} />}
        {screen === 'cases' && <Cases cases={cases.data || []} onCase={openCase} onNew={() => setScreen('new')} />}
        {screen === 'new' && <NewAnalysis onCreated={openCase} />}
        {screen === 'case' && caseId && <CaseWorkspace key={caseId} caseId={caseId} initialCitation={citation} onCitation={openCitation} />}
      </div>
    </div>
  )
}
