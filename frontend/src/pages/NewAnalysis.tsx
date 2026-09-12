import { useRef, useState, useCallback, useEffect } from 'react'
import { AlertCircle, CheckCircle2, FileText, FolderPlus, LockKeyhole, UploadCloud, X } from 'lucide-react'
import { api } from '../api/client'
import type { Case } from '../types'

const ACCEPTED_EXTENSIONS = ['.pdf', '.doc', '.docx']
const ACCEPTED_TYPES = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

export function NewAnalysis({ onCreated }: { onCreated: (id: string) => void }) {
  const input = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [caseNumber, setCaseNumber] = useState('')
  const [station, setStation] = useState('')
  const [role, setRole] = useState('draft_chargesheet')
  const [dragging, setDragging] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [existingCase, setExistingCase] = useState<Case | null>(null)
  const [useExisting, setUseExisting] = useState(false)

  // Check for existing case when case number changes
  useEffect(() => {
    const trimmed = caseNumber.trim()
    if (trimmed.length < 2) { setExistingCase(null); setUseExisting(false); return }
    const timeout = setTimeout(async () => {
      const found = await api.caseByNumber(trimmed)
      setExistingCase(found)
      if (found) setUseExisting(true)
    }, 400)
    return () => clearTimeout(timeout)
  }, [caseNumber])

  const select = useCallback((candidate?: File) => {
    setError('')
    if (!candidate) return
    const ext = '.' + candidate.name.split('.').pop()?.toLowerCase()
    if (!ACCEPTED_EXTENSIONS.includes(ext) && !ACCEPTED_TYPES.includes(candidate.type))
      return setError('Accepted formats: PDF, DOC, DOCX')
    if (candidate.size > 250 * 1024 * 1024) return setError('File exceeds the 250 MB limit.')
    setFile(candidate)
  }, [])

  const submit = async () => {
    if (!file || !caseNumber.trim()) return setError('Case ID and a document file are required.')
    setBusy(true); setError('')
    try {
      let targetCaseId: string
      if (useExisting && existingCase) {
        // Upload to existing case
        targetCaseId = existingCase.id
      } else {
        // Create new case
        const created = await api.createCase({ case_number: caseNumber.trim(), police_station: station.trim() || 'Not specified', language: 'Gujarati / English' })
        targetCaseId = created.id
      }
      await api.upload(targetCaseId, file, role)
      await api.process(targetCaseId)
      onCreated(targetCaseId)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Upload failed') } finally { setBusy(false) }
  }
  return (
    <main className="min-h-screen bg-canvas px-8 py-8">
      <div className="mx-auto max-w-4xl"><div className="eyebrow">New analysis</div><h1 className="mt-2 text-3xl font-semibold tracking-tight">Upload case document</h1><p className="mt-2 text-sm text-slate-500">PDF, DOC, or DOCX · Gujarati or English · digital, scanned, or mixed</p>
        <div className="panel mt-7 p-6">
          <div className="grid gap-5 md:grid-cols-3"><label className="text-xs font-semibold text-slate-600">FIR / Case ID<input value={caseNumber} onChange={event => setCaseNumber(event.target.value)} placeholder="e.g. FIR-123/2026" className="mt-2 w-full rounded-lg border border-slate-200 px-3.5 py-2.5 text-sm font-normal" /></label><label className="text-xs font-semibold text-slate-600">Police station<input value={station} onChange={event => setStation(event.target.value)} placeholder="Police station" disabled={useExisting && !!existingCase} className="mt-2 w-full rounded-lg border border-slate-200 px-3.5 py-2.5 text-sm font-normal disabled:bg-slate-50 disabled:text-slate-400" /></label><label className="text-xs font-semibold text-slate-600">Document role<select value={role} onChange={event => setRole(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-normal"><option value="draft_chargesheet">Draft chargesheet</option><option value="fir">FIR</option><option value="case_diary">Case diary</option><option value="witness_statement">Witness statement</option><option value="medical_report">Medical report</option><option value="forensic_report">Forensic report</option><option value="cctv_record">CCTV / digital record</option><option value="seizure_memo">Seizure memo</option><option value="supporting_record">Other supporting record</option></select></label></div>
          {existingCase && (
            <div className="mt-4 flex items-center gap-3 rounded-lg border border-sky-200 bg-sky-50 p-3">
              <FolderPlus size={16} className="shrink-0 text-sky-700" />
              <div className="flex-1 text-xs text-sky-800">
                <strong>Case "{existingCase.case_number}" already exists</strong> at {existingCase.police_station}.
                {useExisting ? ' This document will be added to the existing case.' : ' A new separate case will be created.'}
              </div>
              <button onClick={() => setUseExisting(!useExisting)} className="shrink-0 rounded-lg border border-sky-300 bg-white px-3 py-1.5 text-[11px] font-bold text-sky-700 hover:bg-sky-100">
                {useExisting ? 'Create new instead' : 'Add to existing'}
              </button>
            </div>
          )}
          <div onDragOver={event => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); select(event.dataTransfer.files[0]) }} onClick={() => input.current?.click()} className={`mt-6 grid min-h-64 cursor-pointer place-items-center rounded-xl border-2 border-dashed p-8 text-center transition ${dragging ? 'border-teal-500 bg-teal-50' : file ? 'border-emerald-300 bg-emerald-50/50' : 'border-slate-200 hover:border-sky-300 hover:bg-sky-50/30'}`}>
            <input ref={input} type="file" accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document" className="hidden" onChange={event => select(event.target.files?.[0])} />
            {file ? <div><div className="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-emerald-100 text-emerald-700"><FileText /></div><div className="mt-4 flex items-center justify-center gap-2 text-sm font-semibold"><CheckCircle2 size={16} className="text-emerald-600" />{file.name}<button onClick={event => { event.stopPropagation(); setFile(null) }} aria-label="Remove file" className="rounded p-1 hover:bg-slate-100"><X size={14} /></button></div><p className="mt-1 text-xs text-slate-400">{(file.size / 1024 / 1024).toFixed(1)} MB · ready to validate</p></div> : <div><div className="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-sky-50 text-sky-700"><UploadCloud /></div><h2 className="mt-4 text-sm font-semibold">Drop document here</h2><p className="mt-2 text-xs text-slate-500">PDF, DOC, or DOCX · maximum 250 MB</p></div>}
          </div>
          {error && <div className="mt-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700"><AlertCircle size={15} />{error}</div>}
          <div className="mt-6 flex items-center justify-between gap-5"><div className="flex items-start gap-2 text-xs leading-5 text-slate-500"><LockKeyhole size={15} className="mt-0.5 shrink-0 text-teal-700" /><span>Processing remains on this device. No case content is sent to external services.</span></div><button disabled={busy} onClick={submit} className="min-w-36 rounded-lg bg-teal-700 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{busy ? 'Securing upload…' : 'Start analysis'}</button></div>
        </div>
      </div>
    </main>
  )
}
