export function Badge({ tone = 'pale', children }) {
  return <span className={`badge badge--${tone}`}>{children}</span>
}

export function StatusBadge({ status, map }) {
  const entry = map?.[status] || { label: status, tone: 'pale' }
  return <Badge tone={entry.tone}>{entry.label}</Badge>
}

export default Badge