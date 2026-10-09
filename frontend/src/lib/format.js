const moneyFmt = new Intl.NumberFormat('en', { maximumFractionDigits: 0 })

export function formatMoney(value = 0, symbol = 'KSh ') {
  return `${symbol}${moneyFmt.format(Number(value) || 0)}`
}

export function relativeTime(iso) {
  if (!iso) return ''
  const then = new Date(iso)
  const diff = Math.max(0, Date.now() - then.getTime())
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return then.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function initials(name = '') {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('')
}

export function toKes(value) {
  return Number(value || 0).toFixed(0)
}