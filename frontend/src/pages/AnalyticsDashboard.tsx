import { useQuery } from '@tanstack/react-query'
import {
  BarChart3, TrendingUp, MapPin, Shield, Scale, FileText, Users, Search,
  AlertTriangle, Activity, Eye, Fingerprint, Car, Gavel, Info
} from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts'
import { api } from '../api/client'
import { Loading } from '../components/Loading'

const COLORS = ['#0d9488', '#0ea5e9', '#f59e0b', '#8b5cf6', '#ef4444', '#10b981', '#ec4899', '#6366f1', '#f97316', '#14b8a6']
const FINDING_COLORS: Record<string, string> = {
  strong_point: '#10b981', weak_point: '#f59e0b', contradiction: '#ef4444',
  potential_mistake: '#f97316', missing_link: '#8b5cf6', quality_issue: '#6366f1',
  format_issue: '#ec4899', completeness_gap: '#0ea5e9', custody_issue: '#14b8a6'
}
const STATUS_COLORS: Record<string, string> = {
  created: '#94a3b8', uploaded: '#0ea5e9', processing: '#f59e0b', ready: '#10b981', error: '#ef4444'
}

function formatLabel(s: string) {
  return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

const STAT_ICONS: Record<string, React.ReactNode> = {
  total_cases: <Shield size={18} />, total_documents: <FileText size={18} />,
  total_pages: <Eye size={18} />, total_accused: <Users size={18} />,
  total_witnesses: <Users size={18} />, total_evidence: <Fingerprint size={18} />,
  total_claims: <Scale size={18} />, total_vehicles: <Car size={18} />,
  total_legal_sections: <Gavel size={18} />, total_findings: <AlertTriangle size={18} />,
}

const STAT_LABELS: Record<string, string> = {
  total_cases: 'Cases', total_documents: 'Documents', total_pages: 'Extracted pages',
  total_accused: 'Extracted accused', total_witnesses: 'Extracted witnesses', total_evidence: 'Evidence records',
  total_claims: 'Extracted claims', total_vehicles: 'Extracted vehicles', total_legal_sections: 'Extracted legal sections',
  total_findings: 'Generated findings',
}

const STAT_HELP: Record<string, string> = {
  total_cases: 'Number of non-demo cases currently in the local database.',
  total_documents: 'Uploaded documents linked to non-demo cases.',
  total_pages: 'Pages successfully extracted from those uploaded documents.',
  total_accused: 'People classified by the extractor as accused. Zero may mean extraction missed the person, not that no accused is present.',
  total_witnesses: 'People classified by the extractor as witnesses. This is separate from evidence records labelled as witness material.',
  total_evidence: 'Extracted evidence records across all supported evidence types. These are not necessarily independently verified.',
  total_claims: 'Candidate claims extracted from the documents. They are analysis inputs, not established facts.',
  total_vehicles: 'Vehicle entities explicitly extracted from the documents.',
  total_legal_sections: 'Legal-section entities explicitly extracted. A zero count should prompt source review.',
  total_findings: 'Machine-generated review findings, including possible duplicates or graph-linking gaps.',
}

export function AnalyticsDashboard() {
  const summary = useQuery({ queryKey: ['analytics-summary'], queryFn: api.analyticsSummary })
  const crimeTypes = useQuery({ queryKey: ['analytics-crime-types'], queryFn: api.analyticsCrimeTypes })
  const temporal = useQuery({ queryKey: ['analytics-temporal'], queryFn: api.analyticsTemporal })
  const hotspots = useQuery({ queryKey: ['analytics-hotspots'], queryFn: api.analyticsHotspots })
  const caseStatus = useQuery({ queryKey: ['analytics-case-status'], queryFn: api.analyticsCaseStatus })
  const evidenceProfile = useQuery({ queryKey: ['analytics-evidence'], queryFn: api.analyticsEvidenceProfile })
  const entityNetwork = useQuery({ queryKey: ['analytics-entities'], queryFn: api.analyticsEntityNetwork })
  const findingsSummary = useQuery({ queryKey: ['analytics-findings'], queryFn: api.analyticsFindings })
  const docRoles = useQuery({ queryKey: ['analytics-doc-roles'], queryFn: api.analyticsDocRoles })

  const isLoading = summary.isLoading
  if (isLoading) return <Loading />

  const summaryData = summary.data || {}
  const hasData = (summaryData.total_cases || 0) > 0

  return (
    <main className="min-h-screen bg-canvas px-8 py-8 lg:px-10">
      <div className="mx-auto max-w-[1400px]">
        {/* Hero Header */}
        <header className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-teal-900 px-8 py-10">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(20,184,166,0.15),transparent_60%)]" />
          <div className="relative z-10">
            <div className="flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded-xl bg-teal-500/20 text-teal-400 ring-1 ring-teal-500/30">
                <BarChart3 size={22} />
              </div>
              <div>
                <div className="text-[11px] font-bold uppercase tracking-[0.18em] text-teal-400">Intelligence analytics</div>
                <h1 className="text-2xl font-bold tracking-tight text-white">Crime pattern analysis</h1>
              </div>
            </div>
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-slate-300">
              Aggregate insights across all cases. Identify seasonal crime patterns, geographic hotspots,
              evidence gaps, and repeat entities to support strategic policing decisions.
            </p>
          </div>
        </header>

        {!hasData && (
          <div className="mt-8 grid min-h-[300px] place-items-center rounded-2xl border border-slate-200 bg-white p-12 text-center">
            <div>
              <Search className="mx-auto text-slate-300" size={48} />
              <h2 className="mt-5 text-lg font-semibold text-slate-700">No case data available</h2>
              <p className="mt-2 max-w-md text-sm text-slate-500">
                Upload FIRs, chargesheets, and other police documents via New Analysis.
                Analytics will appear here once cases are processed.
              </p>
            </div>
          </div>
        )}

        {hasData && (
          <>
            {/* Summary Stats */}
            <section className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
              {Object.entries(summaryData).map(([key, value]) => (
                <div key={key} title={STAT_HELP[key]} className="animate-fade-in group relative z-0 overflow-visible rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-300 hover:z-50 hover:-translate-y-0.5 hover:border-teal-200 hover:shadow-md">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-2xl font-bold tracking-tight text-slate-800">{(value as number).toLocaleString()}</div>
                      <div className="mt-1.5 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">{STAT_LABELS[key] || key.replace(/total_/g, '').replace(/_/g, ' ')}<span className="relative normal-case tracking-normal"><Info size={11} className="text-slate-300" /><span className="pointer-events-none absolute left-0 top-full z-[100] mt-2 hidden w-56 rounded-lg bg-slate-900 px-3 py-2 text-left text-[11px] font-normal leading-4 text-white normal-case shadow-xl group-hover:block">{STAT_HELP[key]}</span></span></div>
                    </div>
                    <div className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-teal-50 to-emerald-50 text-teal-600 transition-colors group-hover:from-teal-100 group-hover:to-emerald-100">
                      {STAT_ICONS[key] || <Activity size={18} />}
                    </div>
                  </div>
                </div>
              ))}
            </section>
            <div className="mt-4 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50/70 px-4 py-3 text-xs leading-5 text-amber-900">
              <AlertTriangle size={15} className="mt-0.5 shrink-0" />
              <span><strong>Interpretation note:</strong> These are extraction and database counts, not verified crime statistics. With only {summaryData.total_cases} case{summaryData.total_cases === 1 ? '' : 's'}, seasonality and station comparisons are descriptive only. Zero accused, witness, or legal-section counts should be checked against the source documents.</span>
            </div>

            {/* Row: Seasonality + Hotspots */}
            <div className="mt-6 grid gap-6 xl:grid-cols-[1.4fr_1fr]">
              {/* Crime Seasonality */}
              <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-2.5">
                  <div className="grid h-8 w-8 place-items-center rounded-lg bg-sky-50 text-sky-600"><TrendingUp size={16} /></div>
                  <div>
                    <h2 className="text-sm font-bold text-slate-800">Crime seasonality</h2>
                    <p className="text-[10px] text-slate-400">Case registrations and extracted events by month</p>
                  </div>
                </div>
                {(temporal.data?.length || 0) > 0 ? (
                  <div className="mt-5 h-[280px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={temporal.data}>
                        <defs>
                          <linearGradient id="casesGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#0d9488" stopOpacity={0.3} />
                            <stop offset="100%" stopColor="#0d9488" stopOpacity={0} />
                          </linearGradient>
                          <linearGradient id="eventsGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#0ea5e9" stopOpacity={0.3} />
                            <stop offset="100%" stopColor="#0ea5e9" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="month" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                        <YAxis tick={{ fontSize: 10 }} stroke="#94a3b8" />
                        <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }} />
                        <Legend iconType="circle" wrapperStyle={{ fontSize: 11 }} />
                        <Area type="monotone" dataKey="cases_registered" stroke="#0d9488" fill="url(#casesGrad)" strokeWidth={2} name="Cases registered" />
                        <Area type="monotone" dataKey="crime_events" stroke="#0ea5e9" fill="url(#eventsGrad)" strokeWidth={2} name="Extracted events" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                ) : <EmptyChart message="No temporal data yet" />}
              </section>

              {/* Crime Hotspots */}
              <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-2.5">
                  <div className="grid h-8 w-8 place-items-center rounded-lg bg-rose-50 text-rose-500"><MapPin size={16} /></div>
                  <div>
                    <h2 className="text-sm font-bold text-slate-800">Crime hotspots</h2>
                    <p className="text-[10px] text-slate-400">Cases grouped by police station—not geographic hotspots</p>
                  </div>
                </div>
                {(hotspots.data?.length || 0) > 0 ? (
                  <div className="mt-5 h-[280px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={hotspots.data} layout="vertical" margin={{ left: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis type="number" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                        <YAxis dataKey="station" type="category" width={120} tick={{ fontSize: 10 }} stroke="#94a3b8" />
                        <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }} />
                        <Bar dataKey="count" name="Cases" radius={[0, 6, 6, 0]}>
                          {hotspots.data?.map((_, i) => (
                            <Cell key={i} fill={`hsl(${170 + i * 25}, 70%, ${45 + i * 5}%)`} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : <EmptyChart message="No station data yet" />}
              </section>
            </div>

            {/* Row: IPC Sections + Evidence Profile + Case Pipeline */}
            <div className="mt-6 grid gap-6 lg:grid-cols-3">
              {/* IPC/BNS Sections */}
              <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-2.5">
                  <div className="grid h-8 w-8 place-items-center rounded-lg bg-violet-50 text-violet-600"><Gavel size={16} /></div>
                  <div>
                    <h2 className="text-sm font-bold text-slate-800">Extracted legal sections</h2>
                    <p className="text-[10px] text-slate-400">IPC / BNS frequency</p>
                  </div>
                </div>
                {(crimeTypes.data?.length || 0) > 0 ? (
                  <div className="mt-5 h-[250px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={crimeTypes.data?.slice(0, 8)}
                          dataKey="count"
                          nameKey="section"
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={90}
                          paddingAngle={3}
                          stroke="none"
                        >
                          {crimeTypes.data?.slice(0, 8).map((_, i) => (
                            <Cell key={i} fill={COLORS[i % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }} />
                        <Legend iconType="circle" wrapperStyle={{ fontSize: 10 }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                ) : <EmptyChart message="No legal sections extracted" />}
              </section>

              {/* Evidence Profile */}
              <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-2.5">
                  <div className="grid h-8 w-8 place-items-center rounded-lg bg-amber-50 text-amber-600"><Fingerprint size={16} /></div>
                  <div>
                    <h2 className="text-sm font-bold text-slate-800">Extracted evidence profile</h2>
                    <p className="text-[10px] text-slate-400">Type distribution</p>
                  </div>
                </div>
                {(evidenceProfile.data?.length || 0) > 0 ? (
                  <div className="mt-5 h-[250px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={evidenceProfile.data}>
                        <PolarGrid stroke="#e2e8f0" />
                        <PolarAngleAxis dataKey="type" tick={{ fontSize: 10 }} />
                        <PolarRadiusAxis tick={{ fontSize: 9 }} />
                        <Radar dataKey="count" stroke="#0d9488" fill="#0d9488" fillOpacity={0.25} strokeWidth={2} name="Evidence items" />
                        <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                ) : <EmptyChart message="No evidence data yet" />}
              </section>

              {/* Case Pipeline */}
              <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-2.5">
                  <div className="grid h-8 w-8 place-items-center rounded-lg bg-emerald-50 text-emerald-600"><Activity size={16} /></div>
                  <div>
                    <h2 className="text-sm font-bold text-slate-800">Case pipeline</h2>
                    <p className="text-[10px] text-slate-400">Resolution status</p>
                  </div>
                </div>
                {(caseStatus.data?.length || 0) > 0 ? (
                  <div className="mt-5 space-y-3">
                    {caseStatus.data?.map(item => {
                      const total = caseStatus.data?.reduce((sum, s) => sum + s.count, 0) || 1
                      const pct = Math.round((item.count / total) * 100)
                      return (
                        <div key={item.status}>
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-semibold text-slate-600">{formatLabel(item.status)}</span>
                            <span className="font-bold text-slate-800">{item.count} <span className="font-normal text-slate-400">({pct}%)</span></span>
                          </div>
                          <div className="mt-1.5 h-2.5 overflow-hidden rounded-full bg-slate-100">
                            <div
                              className="h-full rounded-full transition-all duration-700 ease-out"
                              style={{ width: `${pct}%`, backgroundColor: STATUS_COLORS[item.status] || '#94a3b8' }}
                            />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : <EmptyChart message="No case data" />}
              </section>
            </div>

            {/* Row: Findings + Document Roles + Entity Network */}
            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              {/* Finding Types */}
              <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-2.5">
                  <div className="grid h-8 w-8 place-items-center rounded-lg bg-red-50 text-red-500"><AlertTriangle size={16} /></div>
                  <div>
                    <h2 className="text-sm font-bold text-slate-800">Generated findings breakdown</h2>
                    <p className="text-[10px] text-slate-400">Types of issues detected</p>
                  </div>
                </div>
                {(findingsSummary.data?.length || 0) > 0 ? (
                  <div className="mt-5 h-[240px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={findingsSummary.data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="type" tick={{ fontSize: 9 }} stroke="#94a3b8" tickFormatter={formatLabel} />
                        <YAxis tick={{ fontSize: 10 }} stroke="#94a3b8" />
                        <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }} labelFormatter={(label) => formatLabel(String(label))} />
                        <Bar dataKey="count" name="Findings" radius={[6, 6, 0, 0]}>
                          {findingsSummary.data?.map((item, i) => (
                            <Cell key={i} fill={FINDING_COLORS[item.type] || COLORS[i % COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : <EmptyChart message="No findings data yet" />}
              </section>

              {/* Entity Network */}
              <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-2.5">
                  <div className="grid h-8 w-8 place-items-center rounded-lg bg-indigo-50 text-indigo-600"><Users size={16} /></div>
                  <div>
                    <h2 className="text-sm font-bold text-slate-800">Repeated entities</h2>
                    <p className="text-[10px] text-slate-400">Entities appearing in more than one case</p>
                  </div>
                </div>
                {(entityNetwork.data?.length || 0) > 0 ? (
                  <div className="mt-5 max-h-[240px] overflow-y-auto scrollbar-thin">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-slate-100 text-left text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                          <th className="pb-2 pr-3">Entity</th>
                          <th className="pb-2 pr-3">Type</th>
                          <th className="pb-2 text-right">Cases</th>
                        </tr>
                      </thead>
                      <tbody>
                        {entityNetwork.data?.map((item, i) => (
                          <tr key={i} className="border-b border-slate-50 transition-colors hover:bg-slate-50">
                            <td className="py-2.5 pr-3 font-semibold text-slate-700">{item.label}</td>
                            <td className="py-2.5 pr-3">
                              <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold
                                ${item.kind === 'Accused' ? 'bg-red-50 text-red-700' :
                                  item.kind === 'Witness' ? 'bg-blue-50 text-blue-700' :
                                  item.kind === 'Vehicle' ? 'bg-amber-50 text-amber-700' :
                                  'bg-slate-100 text-slate-600'}`}>
                                {item.kind}
                              </span>
                            </td>
                            <td className="py-2.5 text-right font-bold text-teal-700">{item.case_count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : <EmptyChart message="No entities extracted yet" />}
              </section>
            </div>

            {/* Document Role Distribution */}
            {(docRoles.data?.length || 0) > 0 && (
              <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-2.5">
                  <div className="grid h-8 w-8 place-items-center rounded-lg bg-teal-50 text-teal-600"><FileText size={16} /></div>
                  <div>
                    <h2 className="text-sm font-bold text-slate-800">Document types uploaded</h2>
                    <p className="text-[10px] text-slate-400">Distribution of document roles</p>
                  </div>
                </div>
                <div className="mt-5 flex flex-wrap gap-3">
                  {docRoles.data?.map((item, i) => (
                    <div key={i} className="flex items-center gap-3 rounded-xl border border-slate-100 bg-slate-50/50 px-4 py-3 transition-colors hover:border-teal-200 hover:bg-teal-50/30">
                      <div className="text-lg font-bold text-teal-700">{item.count}</div>
                      <div className="text-xs font-semibold text-slate-600">{formatLabel(item.role)}</div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Footer note */}
            <div className="mt-8 rounded-xl border border-amber-100 bg-amber-50/60 p-4 text-xs leading-5 text-amber-800">
              <strong>Offline analytics:</strong> All statistics are computed locally from your uploaded case documents.
              No data leaves this device. Analytics accuracy improves as more cases are processed through the system.
            </div>
          </>
        )}
      </div>
    </main>
  )
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="mt-5 grid min-h-[200px] place-items-center rounded-xl border border-dashed border-slate-200 bg-slate-50/50">
      <div className="text-center">
        <BarChart3 className="mx-auto text-slate-300" size={28} />
        <p className="mt-2 text-xs text-slate-400">{message}</p>
      </div>
    </div>
  )
}
