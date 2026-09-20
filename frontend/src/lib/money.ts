const SYMBOLS: Record<string, string> = {
  EUR: '€',
  USD: '$',
  BRL: 'R$',
  GBP: '£',
  CHF: 'CHF',
}

export function formatMoney(value: string | number | null | undefined, currency: string): string {
  if (value === null || value === undefined) return '—'
  const amount = typeof value === 'string' ? Number(value) : value
  const symbol = SYMBOLS[currency] ?? currency
  const formatted = amount.toLocaleString('pt-PT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return `${symbol} ${formatted}`
}

export function formatPercent(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A'
  const amount = typeof value === 'string' ? Number(value) : value
  return `${amount.toLocaleString('pt-PT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const [year, month, day] = value.split('-')
  return `${day}/${month}/${year}`
}

export function monthInputValue(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-01`
}
