import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import cytoscape, { type Core, type EventObject } from 'cytoscape'
import { Filter, Focus, Network, RotateCcw, Search, ShieldCheck, X } from 'lucide-react'
import { api } from '../../api/client'
import { CitationButton } from '../../components/CitationButton'
import { Loading } from '../../components/Loading'
import type { Citation, GraphEdge, GraphNode } from '../../types'

const colors: Record<string, string> = { Accused: '#dc6b4a', Witness: '#4f83cc', Claim: '#9b6acb', DigitalEvidence: '#159a8c', ForensicEvidence: '#159a8c', Evidence: '#159a8c', Event: '#d39534', Location: '#66758a', Vehicle: '#64748b', TextChunk: '#b7c2cd', Document: '#2b5378', Case: '#0b1f33' }

export function GraphView({ caseId, onCitation }: { caseId: string; onCitation: (value: Citation) => void }) {
  const container = useRef<HTMLDivElement>(null)
  const core = useRef<Core | null>(null)
  const query = useQuery({ queryKey: ['graph', caseId], queryFn: () => api.graph(caseId) })
  const [selected, setSelected] = useState<GraphNode | GraphEdge>()
  const [search, setSearch] = useState('')
  const [type, setType] = useState('All')
  const [contradictions, setContradictions] = useState(false)
  const types = useMemo(() => ['All', ...new Set(query.data?.nodes.map(n => n.type) || [])], [query.data])
  useEffect(() => {
    if (!container.current || !query.data) return
    const nodes = query.data.nodes.filter(n => (type === 'All' || n.type === type) && (!search || n.label.toLowerCase().includes(search.toLowerCase())))
    const ids = new Set(nodes.map(n => n.id))
    const edges = query.data.edges.filter(e => ids.has(e.source) && ids.has(e.target) && (!contradictions || e.relation === 'CONTRADICTS'))
    const visibleIds = contradictions ? new Set(edges.flatMap(edge => [edge.source, edge.target])) : ids
    core.current?.destroy()
    core.current = cytoscape({ container: container.current,
      elements: [...nodes.filter(n => visibleIds.has(n.id)).map(n => ({ data: { id: n.id, label: n.label, type: n.type, raw: n } })), ...edges.map(e => ({ data: { id: e.id, source: e.source, target: e.target, label: e.relation.replaceAll('_', ' '), raw: e } }))],
      style: [
        { selector: 'node', style: { 'background-color': ele => colors[String(ele.data('type'))] || '#64748b', label: 'data(label)', color: '#24374a', 'font-size': '9px', 'text-wrap': 'wrap', 'text-max-width': '92px', 'text-valign': 'bottom', 'text-margin-y': 7, width: '30px', height: '30px', 'border-width': '2px', 'border-color': '#fff' } },
        { selector: 'node[type = "Claim"]', style: { shape: 'diamond', width: '34px', height: '34px' } },
        { selector: 'node[type = "Document"], node[type = "TextChunk"]', style: { shape: 'round-rectangle', width: '25px', height: '25px' } },
        { selector: 'edge', style: { width: '1.2px', 'line-color': '#a9b7c5', 'target-arrow-color': '#a9b7c5', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', label: 'data(label)', 'font-size': '7px', color: '#718096', 'text-background-color': '#fff', 'text-background-opacity': .8, 'text-background-padding': '2px' } },
        { selector: 'edge[label = "CONTRADICTS"]', style: { 'line-color': '#dc5964', 'target-arrow-color': '#dc5964', 'line-style': 'dashed' } },
        { selector: ':selected', style: { 'border-color': '#0ea5a0', 'border-width': 4, 'line-color': '#0ea5a0' } },
      ], layout: { name: 'cose', animate: false, randomize: true, nodeRepulsion: () => 8000, idealEdgeLength: () => 90, fit: true, padding: 35 } })
    const select = (event: EventObject) => setSelected(event.target.data('raw') as GraphNode | GraphEdge)
    core.current.on('tap', 'node, edge', select)
    return () => { core.current?.destroy() }
  }, [query.data, search, type, contradictions])
  if (query.isLoading) return <Loading />
  return <div className="mx-auto max-w-[1380px]"><div className="flex flex-wrap items-end justify-between gap-4"><div><div className="eyebrow">Claim-centric model</div><h2 className="mt-1.5 text-xl font-semibold">Case knowledge graph</h2></div><div className="flex flex-wrap gap-2"><label className="relative"><Search className="absolute left-2.5 top-2.5 text-slate-400" size={14} /><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search nodes" className="w-48 rounded-lg border border-slate-200 bg-white py-2 pl-8 pr-3 text-xs" /></label><label className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-xs"><Filter size={13} /><select value={type} onChange={e => setType(e.target.value)} className="bg-transparent py-2 outline-none">{types.map(value => <option key={value}>{value}</option>)}</select></label><button onClick={() => setContradictions(v => !v)} className={`rounded-lg border px-3 py-2 text-xs font-semibold ${contradictions ? 'border-red-300 bg-red-50 text-red-800' : 'border-slate-200 bg-white text-slate-600'}`}>Contradictions</button><button onClick={() => core.current?.fit(undefined, 30)} title="Fit graph" className="rounded-lg border border-slate-200 bg-white p-2 text-slate-500"><Focus size={15} /></button><button onClick={() => core.current?.layout({ name: 'cose', animate: false }).run()} title="Reset layout" className="rounded-lg border border-slate-200 bg-white p-2 text-slate-500"><RotateCcw size={15} /></button></div></div>
    <div className="panel mt-5 grid min-h-[650px] overflow-hidden xl:grid-cols-[1fr_320px]"><div className="relative min-h-[600px] bg-[#f8fafb]"><div ref={container} className="absolute inset-0" /><div className="absolute bottom-4 left-4 flex max-w-lg flex-wrap gap-2 rounded-lg border border-slate-200 bg-white/95 p-2.5 shadow-sm">{Object.entries(colors).filter(([key]) => !['TextChunk', 'Case'].includes(key)).map(([key, color]) => <span key={key} className="flex items-center gap-1.5 text-[9px] font-medium text-slate-500"><i className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />{key}</span>)}</div></div><Inspector selected={selected} onClose={() => setSelected(undefined)} onCitation={onCitation} /></div>
  </div>
}

function Inspector({ selected, onClose, onCitation }: { selected?: GraphNode | GraphEdge; onClose: () => void; onCitation: (value: Citation) => void }) {
  if (!selected) return <aside className="grid place-items-center border-l border-slate-200 bg-white p-6 text-center"><div><Network className="mx-auto text-slate-300" size={28} /><h3 className="mt-3 text-sm font-semibold">Inspect graph context</h3><p className="mt-2 text-xs leading-5 text-slate-400">Select a node or edge to inspect confidence, relationships, and exact source provenance.</p></div></aside>
  const edge = 'source' in selected
  return <aside className="scrollbar-thin overflow-y-auto border-l border-slate-200 bg-white"><div className="flex items-start justify-between border-b border-slate-100 p-5"><div><div className="eyebrow">{edge ? 'Relationship' : selected.type}</div><h3 className="mt-1.5 text-sm font-semibold">{edge ? selected.relation.replaceAll('_', ' ') : selected.label}</h3></div><button onClick={onClose} aria-label="Close inspector" className="rounded p-1 text-slate-400 hover:bg-slate-100"><X size={16} /></button></div><div className="p-5"><div className="flex items-center justify-between text-xs"><span className="text-slate-500">Confidence</span><span className="font-bold">{Math.round(selected.confidence * 100)}%</span></div>{edge ? <><div className="mt-4 grid grid-cols-[1fr_auto_1fr] items-center gap-2 rounded-lg bg-slate-50 p-3 text-[10px]"><span className="truncate">{selected.source}</span><span>→</span><span className="truncate text-right">{selected.target}</span></div><div className="mt-5 eyebrow">Supported by</div><div className="mt-3 flex flex-col items-start gap-2">{selected.citations.map((citation, i) => <CitationButton key={`${citation.chunk_id}-${i}`} citation={citation} onOpen={onCitation} />)}{selected.citations.length === 0 && <span className="text-xs text-slate-400">Structural system relationship</span>}</div><div className="mt-5 border-t border-slate-100 pt-4 text-[11px] text-slate-500"><div className="flex justify-between"><span>Extraction method</span><b>{selected.extraction_method}</b></div><div className="mt-2 flex justify-between"><span>Human verified</span><b className={selected.human_verified ? 'text-emerald-700' : 'text-amber-700'}>{selected.human_verified ? 'Yes' : 'Pending'}</b></div></div></> : <><div className="mt-5 eyebrow">Aliases</div><div className="mt-2 flex flex-wrap gap-2">{selected.aliases.length ? selected.aliases.map(value => <span key={value} className="chip border-slate-200 bg-slate-50 text-slate-600">{value}</span>) : <span className="text-xs text-slate-400">No aliases recorded</span>}</div><div className="mt-5 flex items-center gap-2 rounded-lg border border-emerald-100 bg-emerald-50 p-3 text-[11px] text-emerald-800"><ShieldCheck size={14} />Source mentions are available from the cited relationships connected to this node.</div></>}</div></aside>
}
