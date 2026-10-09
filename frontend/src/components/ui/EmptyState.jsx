export default function EmptyState({ icon = '🧺', title = 'Nothing here yet', message = '', action = null }) {
  return (
    <div className="empty">
      <div className="empty-icon" aria-hidden="true">
        {icon}
      </div>
      <h3>{title}</h3>
      {message && <p className="muted">{message}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}