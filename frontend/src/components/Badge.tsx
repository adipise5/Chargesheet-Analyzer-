import { AlertTriangle, CheckCircle2, CircleDashed, ShieldCheck } from 'lucide-react'
import { useLanguage } from '../i18n/LanguageContext'

const palettes: Record<string, string> = {
  STRONGLY_CORROBORATED: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  MODERATELY_CORROBORATED: 'border-teal-200 bg-teal-50 text-teal-800',
  LIMITED_CORROBORATION: 'border-amber-200 bg-amber-50 text-amber-800',
  CONFLICTING_EVIDENCE: 'border-red-200 bg-red-50 text-red-800',
  REVIEW_REQUIRED: 'border-amber-200 bg-amber-50 text-amber-800',
  INSUFFICIENT_INFORMATION: 'border-slate-200 bg-slate-50 text-slate-700',
}

export function Badge({ value }: { value: string }) {
  const { t } = useLanguage()
  const Icon = value === 'STRONGLY_CORROBORATED' ? ShieldCheck : value === 'CONFLICTING_EVIDENCE' ? AlertTriangle : value === 'verified' ? CheckCircle2 : CircleDashed
  return <span className={`chip ${palettes[value] || 'border-slate-200 bg-slate-50 text-slate-700'}`}><Icon size={12} />{t(value.replaceAll('_', ' '))}</span>
}

