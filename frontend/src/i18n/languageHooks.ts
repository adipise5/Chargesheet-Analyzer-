import { createContext, useContext, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

export type AppLanguage = 'english' | 'gujarati'
type LanguageContextValue = { language: AppLanguage; setLanguage: (language: AppLanguage) => void; toggleLanguage: () => void; t: (english: string) => string }

export const LanguageContext = createContext<LanguageContextValue | null>(null)

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
        if (!response.fallback || ('cache_only' in response && response.cache_only) || batch.length === 1) {
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
    enabled: stableTexts.length > 0,
    staleTime: Infinity,
  })
  const translated = useMemo(() => new Map(textKey ? textKey.split('\u0000').map((text, index) => [text, query.data?.translations[index] || text]) : []), [textKey, query.data?.translations])
  return { translated, translating: query.isLoading }
}
