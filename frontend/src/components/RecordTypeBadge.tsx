import type { Case } from '../types'
import { useLanguage } from '../i18n/languageHooks'

export function RecordTypeBadge({ recordType, isDemo = false }: { recordType: Case['record_type']; isDemo?: boolean }) {
  const { t } = useLanguage()
  if (recordType === 'public_judgment') {
    return <span className="chip border-violet-200 bg-violet-50 text-violet-800">{t('Public judgment example')}</span>
  }
  if (recordType === 'educational_sample') {
    return <span className="chip border-sky-200 bg-sky-50 text-sky-800">{t('Educational sample')}</span>
  }
  if (isDemo) {
    return <span className="chip border-sky-200 bg-sky-50 text-slate-700">{t('Synthetic demo')}</span>
  }
  return null
}
