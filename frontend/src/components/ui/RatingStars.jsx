export default function RatingStars({ value = 0, onChange, count }) {
  const interactive = typeof onChange === 'function'
  const stars = [1, 2, 3, 4, 5]
  return (
    <span className={`stars ${interactive ? 'stars--input' : ''}`}>
      {stars.map((n) => (
        <span
          key={n}
          role={interactive ? 'button' : undefined}
          tabIndex={interactive ? 0 : undefined}
          onClick={interactive ? () => onChange(n) : undefined}
          onKeyDown={interactive ? (e) => (e.key === 'Enter' ? onChange(n) : null) : undefined}
          aria-label={interactive ? `Rate ${n}` : undefined}
        >
          {n <= Math.round(value) ? '★' : '☆'}
        </span>
      ))}
      {count != null && <span className="muted" style={{ fontSize: 'var(--fs-sm)', marginLeft: 6 }}>({count})</span>}
    </span>
  )
}