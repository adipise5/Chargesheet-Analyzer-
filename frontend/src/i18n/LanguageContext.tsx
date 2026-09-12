import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

export type AppLanguage = 'english' | 'gujarati'
type LanguageContextValue = { language: AppLanguage; setLanguage: (language: AppLanguage) => void; toggleLanguage: () => void; t: (english: string) => string }

const translations: Record<string, string> = {
  'FIR / Case ID': 'FIR / કેસ ID', 'Updated': 'છેલ્લે અપડેટ', 'Case workspace': 'કેસ વર્કસ્પેસ',
  'Overview': 'ઝાંખી', 'Analysis': 'વિશ્લેષણ', 'Defense': 'બચાવ પક્ષ', 'Precedents': 'ન્યાયિક પૂર્વનિર્ણયો',
  'Evidence': 'પુરાવા', 'Timeline': 'સમયરેખા', 'Graph': 'ગ્રાફ', 'Documents': 'દસ્તાવેજો', 'Ask Case': 'કેસને પૂછો',
  'Case summary': 'કેસનો સારાંશ', 'Verified workspace synthesis': 'ચકાસાયેલ વર્કસ્પેસ સારાંશ',
  'OCR quality': 'OCR ગુણવત્તા', 'pages': 'પાનાં', 'Native text': 'મૂળ ટેક્સ્ટ', 'Printed OCR': 'પ્રિન્ટેડ OCR',
  'Review required': 'ચકાસણી જરૂરી', 'Open source review': 'સ્ત્રોતની ચકાસણી ખોલો',
  'Key people & material': 'મુખ્ય વ્યક્તિઓ અને સામગ્રી', 'Case entities': 'કેસની એન્ટિટીઝ',
  'Priority review': 'પ્રાથમિક ચકાસણી', 'Source-backed findings': 'સ્ત્રોત આધારિત તારણો',
  'Human review required before relying on this response.': 'આ જવાબ પર આધાર રાખતા પહેલાં માનવ ચકાસણી જરૂરી છે.',
  'This system supports evidence review. It does not determine guilt, innocence, or likely case outcome.': 'આ સિસ્ટમ પુરાવાની ચકાસણીમાં મદદ કરે છે. તે દોષિતતા, નિર્દોષતા અથવા કેસના સંભવિત પરિણામનો નિર્ણય કરતી નથી.',
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<AppLanguage>('english')
  const value = useMemo(() => ({ language, setLanguage, toggleLanguage: () => setLanguage(current => current === 'english' ? 'gujarati' : 'english'), t: (english: string) => language === 'gujarati' ? translations[english] || english : english }), [language])
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export function useLanguage() {
  const value = useContext(LanguageContext)
  if (!value) throw new Error('useLanguage must be used inside LanguageProvider')
  return value
}

export function useTranslatedTexts(texts: Array<string | undefined>) {
  const { language } = useLanguage()
  const stableTexts = texts.filter((text): text is string => Boolean(text))
  const uniqueTexts = [...new Set(stableTexts)]
  const textKey = uniqueTexts.join('\u0000')
  const query = useQuery({
    queryKey: ['translations', language, stableTexts],
    queryFn: async () => {
      // Ollama is a local single-model service. Parallel per-string calls can
      // make it time out or return a malformed partial response, leaving a
      // page half translated. Use small sequential batches and preserve order.
      const translations: string[] = []
      for (let index = 0; index < uniqueTexts.length; index += 6) {
        const batch = uniqueTexts.slice(index, index + 6)
        const response = await api.translate(batch, language)
        if (!response.fallback || batch.length === 1) {
          translations.push(...response.translations)
          continue
        }
        // If one larger prompt is rejected by the local model, retry its
        // items serially so one transient parse/timeout cannot leave a whole
        // section in its original language.
        for (const text of batch) {
          const retry = await api.translate([text], language)
          translations.push(retry.translations[0] || text)
        }
      }
      return { translations }
    },
    enabled: language === 'english' && stableTexts.length > 0,
    staleTime: Infinity,
  })
  const translated = useMemo(() => new Map(textKey ? textKey.split('\u0000').map((text, index) => [text, query.data?.translations[index] || text]) : []), [textKey, query.data?.translations])
  return { translated, translating: language === 'english' && query.isLoading }
}
