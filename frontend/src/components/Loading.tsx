import { LoaderCircle } from 'lucide-react'

export function Loading({ label = 'Loading case intelligence…' }: { label?: string }) {
  return <div className="flex min-h-56 items-center justify-center gap-3 text-sm text-slate-500"><LoaderCircle className="animate-spin" size={18} />{label}</div>
}

