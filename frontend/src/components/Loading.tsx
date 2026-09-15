import { LoaderCircle } from 'lucide-react'
import { useLanguage } from '../i18n/languageHooks'

export function Loading({ label }: { label?: string }) {
  const { t } = useLanguage()
  return <div className="flex min-h-56 items-center justify-center gap-3 text-sm text-slate-500"><LoaderCircle className="animate-spin" size={18} />{label || t('Loading case intelligence…')}</div>
}

