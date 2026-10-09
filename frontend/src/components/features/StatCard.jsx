export default function StatCard({ label, value, sub, accent = 'var(--wm-green)', bar }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color: accent }}>
        {value}
      </div>
      {typeof bar === 'number' && (
        <div className="stat-bar mt-3">
          <span style={{ width: `${Math.min(Math.max(bar, 0), 100)}%` }} />
        </div>
      )}
      {sub && <div className="muted" style={{ fontSize: 'var(--fs-xs)', marginTop: 6 }}>{sub}</div>}
    </div>
  )
}