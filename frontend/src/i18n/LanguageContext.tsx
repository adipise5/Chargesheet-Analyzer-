import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

export type AppLanguage = 'english' | 'gujarati'
type LanguageContextValue = { language: AppLanguage; setLanguage: (language: AppLanguage) => void; toggleLanguage: () => void; t: (english: string) => string }

const translations: Record<string, string> = {
  'Dashboard': 'ડેશબોર્ડ', 'Cases': 'કેસો', 'Analytics': 'વિશ્લેષણ', 'New Analysis': 'નવું વિશ્લેષણ', 'Gujarat Police': 'ગુજરાત પોલીસ', 'Chargesheet Intelligence': 'ચાર્જશીટ ઇન્ટેલિજન્સ', 'Recent cases': 'તાજેતરના કેસો', 'Audit / System': 'ઓડિટ / સિસ્ટમ', 'Settings': 'સેટિંગ્સ', 'On-device processing. No case content leaves approved local services.': 'ડિવાઇસ પર પ્રક્રિયા. કોઈ કેસ સામગ્રી મંજૂર સ્થાનિક સેવાઓની બહાર જતી નથી.', 'SYNTHETIC DEMO DATA — NOT A REAL POLICE RECORD': 'સિન્થેટિક ડેમો ડેટા — વાસ્તવિક પોલીસ રેકોર્ડ નથી', 'This case could not be loaded. It may have been removed during a database reset. Open an existing case from Cases in the sidebar.': 'આ કેસ લોડ થઈ શક્યો નથી. કદાચ ડેટાબેઝ રીસેટ દરમિયાન દૂર થયો છે. સાઇડબારમાંથી અસ્તિત્વમાં હોય તેવો કેસ ખોલો.', 'Processing error': 'પ્રક્રિયા ભૂલ', 'ready': 'તૈયાર',
  'Purge sensitive data': 'સંવેદનશીલ ડેટા સાફ કરો',
  'FIR / Case ID': 'FIR / કેસ ID', 'Updated': 'છેલ્લે અપડેટ', 'Case workspace': 'કેસ વર્કસ્પેસ',
  'Overview': 'ઝાંખી', 'Analysis': 'વિશ્લેષણ', 'Defense': 'બચાવ પક્ષ', 'Precedents': 'ન્યાયિક પૂર્વનિર્ણયો',
  'Evidence': 'પુરાવા', 'Timeline': 'સમયરેખા', 'Graph': 'ગ્રાફ', 'Documents': 'દસ્તાવેજો', 'Ask Case': 'કેસને પૂછો',
  'Case summary': 'કેસનો સારાંશ', 'Verified workspace synthesis': 'ચકાસાયેલ વર્કસ્પેસ સારાંશ',
  'OCR quality': 'OCR ગુણવત્તા', 'pages': 'પાનાં', 'Native text': 'મૂળ ટેક્સ્ટ', 'Printed OCR': 'પ્રિન્ટેડ OCR',
  'Review required': 'ચકાસણી જરૂરી', 'Open source review': 'સ્ત્રોતની ચકાસણી ખોલો',
  'Key people & material': 'મુખ્ય વ્યક્તિઓ અને સામગ્રી', 'Case entities': 'કેસની એન્ટિટીઝ',
  'Priority review': 'પ્રાથમિક ચકાસણી', 'Source-backed findings': 'સ્ત્રોત આધારિત તારણો',
  'Human review required before relying on this response.': 'આ જવાબ પર આધાર રાખતા પહેલાં માનવ ચકાસણી જરૂરી છે.',
  'Evidence profile': 'પુરાવા પ્રોફાઇલ', 'Analysis findings': 'વિશ્લેષણ તારણો', 'finding': 'તારણ', 'Interpretive classifications derived from transparent factors—not guilt probabilities.': 'પારદર્શક પરિબળોમાંથી મેળવેલા અર્થઘટનાત્મક વર્ગીકરણ — દોષની સંભાવનાઓ નહીં.', 'All findings': 'બધા તારણો', 'Strong points': 'મજબૂત મુદ્દા', 'Weak points': 'નબળા મુદ્દા', 'Potential mistakes': 'સંભવિત ભૂલો', 'Missing links': 'ગુમ થયેલી કડીઓ', 'strong point': 'મજબૂત મુદ્દો', 'weak point': 'નબળો મુદ્દો', 'potential mistake': 'સંભવિત ભૂલ', 'missing link': 'ગુમ થયેલી કડી', 'Support sources': 'આધાર સ્ત્રોતો', 'Conflicting sources': 'વિરોધી સ્ત્રોતો', 'Source verified': 'સ્ત્રોત ચકાસેલ', 'Why important': 'શા માટે મહત્વનું', 'Recommended correction': 'ભલામણ કરેલો સુધારો', 'IO action': 'IO કાર્યવાહી', 'Open in graph': 'ગ્રાફમાં ખોલો',
  'LIMITED CORROBORATION': 'મર્યાદિત સમર્થન', 'STRONGLY CORROBORATED': 'મજબૂત સમર્થન', 'MODERATELY CORROBORATED': 'મધ્યમ સમર્થન', 'CONFLICTING EVIDENCE': 'વિરોધાભાસી પુરાવા', 'REVIEW REQUIRED': 'ચકાસણી જરૂરી', 'INSUFFICIENT INFORMATION': 'અપૂરતી માહિતી', 'accused': 'આરોપી', 'witnesses': 'સાક્ષીઓ', 'evidence': 'પુરાવા', 'claims': 'દાવાઓ', 'contradictions': 'વિરોધાભાસો', 'review flags': 'ચકાસણી ફ્લેગ્સ',
  'Court-readiness review': 'કોર્ટ તૈયારી ચકાસણી', 'Defense Assistant': 'બચાવ સહાયક', 'Potential challenges are generated from detected gaps and inconsistencies. They are prompts for IO verification, not legal conclusions.': 'શોધાયેલી ખામીઓ અને અસંગતતાઓ પરથી સંભવિત પડકારો બનાવવામાં આવે છે. આ IO ચકાસણી માટેના સૂચનો છે, કાનૂની તારણો નથી.', 'Potential defense weakness': 'બચાવ પક્ષની સંભવિત નબળાઈ', 'Questions the defense may raise': 'બચાવ પક્ષ ઉઠાવી શકે તેવા પ્રશ્નો', 'IO preparation': 'IO તૈયારી', 'Detected document differences': 'શોધાયેલા દસ્તાવેજ તફાવતો', 'Human verification required': 'માનવ ચકાસણી જરૂરી', 'No defense-oriented weaknesses have been generated yet.': 'હજુ બચાવ-કેન્દ્રિત નબળાઈઓ બનાવવામાં આવી નથી.',
  'This system supports evidence review. It does not determine guilt, innocence, or likely case outcome.': 'આ સિસ્ટમ પુરાવાની ચકાસણીમાં મદદ કરે છે. તે દોષિતતા, નિર્દોષતા અથવા કેસના સંભવિત પરિણામનો નિર્ણય કરતી નથી.',
  'Chronology': 'ઘટનાક્રમ', 'Case timeline': 'કેસ સમયરેખા', 'All': 'બધા', 'Incident': 'ઘટના', 'Investigation': 'તપાસ', 'Arrest': 'ધરપકડ', 'Seizure': 'જપ્તી', 'Forensic': 'ફોરેન્સિક', 'Digital': 'ડિજિટલ', 'Date uncertain': 'તારીખ અનિશ્ચિત', 'Uncertain': 'અનિશ્ચિત', 'No timeline events match this category.': 'આ શ્રેણી સાથે મેળ ખાતી સમયરેખાની ઘટનાઓ નથી.',
  'Approved local corpus': 'મંજૂર સ્થાનિક સંગ્રહ', 'Precedent review': 'પૂર્વનિર્ણય ચકાસણી', 'Only judgments imported into this local corpus are searched. Results are research prompts and require legal review.': 'માત્ર આ સ્થાનિક સંગ્રહમાં આયાત કરાયેલા ચુકાદાઓ શોધવામાં આવે છે. પરિણામો સંશોધન સૂચનો છે અને કાનૂની ચકાસણી જરૂરી છે.', 'Judgment title': 'ચુકાદાનું શીર્ષક', 'Court': 'કોર્ટ', 'Year': 'વર્ષ', 'Choose PDF': 'PDF પસંદ કરો', 'Importing…': 'આયાત થઈ રહી છે…', 'Import judgment into local corpus': 'ચુકાદો સ્થાનિક સંગ્રહમાં આયાત કરો', 'Imported judgments': 'આયાત કરાયેલા ચુકાદા', 'Court not specified': 'કોર્ટ દર્શાવેલ નથી', 'Year not specified': 'વર્ષ દર્શાવેલ નથી', 'No judgments imported yet.': 'હજુ કોઈ ચુકાદો આયાત થયો નથી.', 'Case-relevant precedent insights': 'કેસ સંબંધિત પૂર્વનિર્ણય તારણો', 'Human/legal review required.': 'માનવ/કાનૂની ચકાસણી જરૂરી છે.',
  'Material index': 'સામગ્રી સૂચિ', 'Evidence overview': 'પુરાવા ઝાંખી', 'All evidence': 'બધા પુરાવા', 'Physical': 'ભૌતિક', 'Witness': 'સાક્ષી', 'Evidence ID': 'પુરાવા ID', 'Type': 'પ્રકાર', 'Description': 'વર્ણન', 'Linked claims': 'જોડાયેલા દાવા', 'Source': 'સ્ત્રોત', 'No evidence matching this filter.': 'આ ફિલ્ટર સાથે મેળ ખાતો પુરાવો નથી.', 'Unlinked': 'જોડાણ વિનાનું',
  'Source record': 'સ્ત્રોત રેકોર્ડ', 'Document & OCR review': 'દસ્તાવેજ અને OCR ચકાસણી', 'Page': 'પાનું', 'Add case record': 'કેસ રેકોર્ડ ઉમેરો', 'FIR': 'FIR', 'Case diary': 'કેસ ડાયરી', 'Witness statement': 'સાક્ષી નિવેદન', 'Medical report': 'તબીબી અહેવાલ', 'Forensic report': 'ફોરેન્સિક અહેવાલ', 'CCTV / digital record': 'CCTV / ડિજિટલ રેકોર્ડ', 'Seizure memo': 'જપ્તી મેમો', 'Other supporting record': 'અન્ય સહાયક રેકોર્ડ', 'Draft chargesheet': 'ડ્રાફ્ટ ચાર્જશીટ', 'Draft Chargesheet': 'ડ્રાફ્ટ ચાર્જશીટ', 'supporting record': 'સહાયક રેકોર્ડ', 'Adding…': 'ઉમેરાઈ રહ્યું છે…', 'Add and re-analyze': 'ઉમેરીને ફરી વિશ્લેષણ કરો', 'Case documents': 'કેસ દસ્તાવેજો', 'Loading secure local PDF…': 'સુરક્ષિત સ્થાનિક PDF લોડ થઈ રહી છે…', 'extracted Word page': 'કાઢેલું Word પાનું', 'Loading extracted text…': 'કાઢેલું ટેક્સ્ટ લોડ થઈ રહ્યું છે…', 'Loading page provenance…': 'પાનાની પ્રોવેનેન્સ લોડ થઈ રહી છે…', 'Page information': 'પાનાની માહિતી', 'Method': 'પદ્ધતિ', 'Language': 'ભાષા', 'Blocks': 'બ્લોક્સ', 'Provenance linked': 'પ્રોવેનેન્સ જોડાયેલ', 'Extracted text': 'કાઢેલું ટેક્સ્ટ', 'Correct': 'સુધારો', 'Cancel': 'રદ કરો', 'Save correction & rebuild': 'સુધારો સાચવો અને ફરી બનાવો', 'No readable text was extracted.': 'વાંચી શકાય તેવું ટેક્સ્ટ કાઢી શકાયું નથી.', 'Original Tesseract transcript': 'મૂળ Tesseract ટ્રાન્સક્રિપ્ટ', 'Local vision candidate': 'સ્થાનિક વિઝન ઉમેદવાર', 'Original extraction is retained when a human correction is saved.': 'માનવ સુધારો સાચવ્યા પછી મૂળ extraction જાળવી રાખવામાં આવે છે.', 'verified': 'ચકાસેલ', 'REVIEW_REQUIRED': 'ચકાસણી જરૂરી',
  'Claim-centric model': 'દાવા-કેન્દ્રિત મોડેલ', 'Case knowledge graph': 'કેસ જ્ઞાન ગ્રાફ', 'Search nodes': 'નોડ્સ શોધો', 'Contradictions': 'વિરોધાભાસ', 'Fit graph': 'ગ્રાફ ફિટ કરો', 'Reset layout': 'લેઆઉટ રીસેટ કરો', 'Inspect graph context': 'ગ્રાફ સંદર્ભ તપાસો', 'Select a node or edge to inspect confidence, relationships, and exact source provenance.': 'વિશ્વસનીયતા, સંબંધો અને ચોક્કસ સ્ત્રોત પ્રોવેનેન્સ તપાસવા નોડ અથવા એજ પસંદ કરો.', 'Relationship': 'સંબંધ', 'Confidence': 'વિશ્વસનીયતા', 'Supported by': 'આધાર', 'Structural system relationship': 'સિસ્ટમનો માળખાકીય સંબંધ', 'Extraction method': 'કાઢવાની પદ્ધતિ', 'Human verified': 'માનવ ચકાસેલ', 'Yes': 'હા', 'Pending': 'બાકી', 'Aliases': 'ઉપનામો', 'No aliases recorded': 'કોઈ ઉપનામ નોંધાયેલ નથી', 'Source mentions are available from the cited relationships connected to this node.': 'આ નોડ સાથે જોડાયેલા ઉલ્લેખિત સંબંધોમાં સ્ત્રોત ઉલ્લેખ ઉપલબ્ધ છે.',
  'Case': 'કેસ', 'Document': 'દસ્તાવેજ', 'TextChunk': 'ટેક્સ્ટ ભાગ', 'LegalSection': 'કાનૂની કલમ', 'Event': 'ઘટના', 'Accused': 'આરોપી', 'Claim': 'દાવો', 'Location': 'સ્થળ', 'Vehicle': 'વાહન', 'DigitalEvidence': 'ડિજિટલ પુરાવો', 'ForensicEvidence': 'ફોરેન્સિક પુરાવો', 'SUPPORTS': 'આધાર આપે છે', 'CONTRADICTS': 'વિરોધાભાસ કરે છે', 'SOURCE OF': 'નો સ્ત્રોત', 'PART OF': 'નો ભાગ',
  'GraphRAG investigation': 'GraphRAG તપાસ', 'Ask this case': 'આ કેસને પૂછો', 'Ask questions in plain English. Answers use bounded retrieval and keep source citations attached to each response.': 'સાદી અંગ્રેજીમાં પ્રશ્નો પૂછો. જવાબો મર્યાદિત શોધનો ઉપયોગ કરે છે અને દરેક જવાબ સાથે સ્ત્રોતો જોડે છે.', 'Case conversation': 'કેસ વાતચીત', 'This conversation exists only while this page is open and is not saved.': 'આ વાતચીત માત્ર આ પાનું ખુલ્લું હોય ત્યાં સુધી રહે છે અને સાચવવામાં આવતી નથી.', 'Ask about this case': 'આ કેસ વિશે પૂછો', 'The whole chargesheet is never sent to the model. Only a conservative, provenance-expanded context is used.': 'આખું ચાર્જશીટ ક્યારેય મોડેલને મોકલવામાં આવતું નથી. માત્ર સાવચેતીપૂર્વક વિસ્તૃત કરાયેલ પ્રોવેનેન્સ સંદર્ભ વપરાય છે.', 'What is this case about?': 'આ કેસ શેના વિશે છે?', 'What should I verify before filing this charge sheet?': 'આ ચાર્જશીટ ફાઇલ કરતા પહેલાં શું ચકાસવું જોઈએ?', 'Which claims rely on a single source?': 'કયા દાવા એક જ સ્ત્રોત પર આધારિત છે?', 'Which evidence items are not linked to any claim?': 'કયા પુરાવા કોઈ દાવા સાથે જોડાયેલા નથી?', 'Your question': 'તમારો પ્રશ્ન', 'Ask a question about this case…': 'આ કેસ વિશે પ્રશ્ન પૂછો…', 'Ask case': 'કેસને પૂછો', 'Reading case sources and generating an answer locally…': 'કેસના સ્ત્રોતો વાંચીને સ્થાનિક રીતે જવાબ બનાવાઈ રહ્યો છે…', 'Case intelligence': 'કેસ ઇન્ટેલિજન્સ', 'source': 'સ્ત્રોત', 'sources': 'સ્ત્રોતો', 'Could not answer this question': 'આ પ્રશ્નનો જવાબ આપી શકાયો નથી', 'The request failed. Please try again.': 'વિનંતી નિષ્ફળ ગઈ. ફરી પ્રયાસ કરો.', 'Your question remains above. You can ask it again.': 'તમારો પ્રશ્ન ઉપર છે. તમે ફરી પૂછી શકો છો.', 'Sources': 'સ્ત્રોતો', 'No source passage was returned.': 'કોઈ સ્ત્રોત પેસેજ મળ્યો નથી.',
  'No processed documents are available.': 'કોઈ પ્રક્રિયા કરાયેલા દસ્તાવેજો ઉપલબ્ધ નથી.',
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
    enabled: stableTexts.length > 0,
    staleTime: Infinity,
  })
  const translated = useMemo(() => new Map(textKey ? textKey.split('\u0000').map((text, index) => [text, query.data?.translations[index] || text]) : []), [textKey, query.data?.translations])
  return { translated, translating: query.isLoading }
}
