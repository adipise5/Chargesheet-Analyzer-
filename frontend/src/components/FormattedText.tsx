import type { ReactNode } from 'react'
import { repairDisplayText } from '../lib/text'

function inline(value: string): ReactNode[] {
  const parts = value.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean)
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={index}>{part.slice(2, -2)}</strong>
    if (part.startsWith('`') && part.endsWith('`')) return <code key={index} className="rounded bg-slate-100 px-1 py-0.5 text-[.9em]">{part.slice(1, -1)}</code>
    return <span key={index}>{part}</span>
  })
}

export function FormattedText({ text, className = '' }: { text?: string; className?: string }) {
  if (!text?.trim()) return null
  const lines = repairDisplayText(text).split(/\r?\n/)
  const elements: ReactNode[] = []
  let bullets: { marker: string; text: string }[] = []
  const flushBullets = () => {
    if (!bullets.length) return
    elements.push(<ul key={`list-${elements.length}`} className="my-3 list-disc space-y-2 pl-5">{bullets.map((item, index) => <li key={index}>{inline(item.text)}</li>)}</ul>)
    bullets = []
  }
  lines.forEach((raw, index) => {
    const line = raw.trim()
    if (!line) {
      flushBullets()
      return
    }
    const heading = line.match(/^#{1,3}\s+(.+)$/)
    if (heading) {
      flushBullets()
      elements.push(<h4 key={`heading-${index}`} className="mt-4 text-sm font-semibold text-slate-800">{inline(heading[1])}</h4>)
      return
    }
    const bullet = line.match(/^(?:[-*•]|\d+[.)])\s+(.+)$/)
    if (bullet) {
      bullets.push({ marker: line.slice(0, 1), text: bullet[1] })
      return
    }
    flushBullets()
    elements.push(<p key={`paragraph-${index}`} className="my-3">{inline(line)}</p>)
  })
  flushBullets()
  return <div className={`text-sm leading-7 text-slate-700 ${className}`}>{elements}</div>
}
