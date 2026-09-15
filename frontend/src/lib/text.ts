/** Repair common UTF-8/Windows-1252 display artifacts without changing data. */
export function repairDisplayText(value: string): string {
  return value
    .replaceAll('â€¢', '•')
    .replaceAll('â€“', '–')
    .replaceAll('â€”', '—')
    .replaceAll('â€™', '’')
    .replaceAll('â€œ', '“')
    .replaceAll('â€�', '”')
    .replaceAll('Â', '')
}
