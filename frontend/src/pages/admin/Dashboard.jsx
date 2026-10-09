import { useEffect, useState } from 'react'
import { authApi } from '../../lib/api'
import { apiErrorMessage } from '../../lib/api'
import StatCard from '../../components/features/StatCard'
import Spinner from '../../components/ui/Spinner'
import { formatMoney, relativeTime } from '../../lib/format'
import { useToast } from '../../lib/toast'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [audit, setAudit] = useState([])
  const [loading, setLoading] = useState(true)
  const { error } = useToast()

  useEffect(() => {
    authApi
      .get('/api/admin/dashboard/stats')
      .then((res) => {
        setStats(res.data)
        return authApi.get('/api/admin/audit-logs', { params: { limit: 8 } })
      })
      .then((res) => setAudit(res.data.items || []))
      .catch((err) => error(apiErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [error])

  if (loading) return <Spinner center />
  if (!stats) return null

  const users = stats.users || {}
  const listings = stats.listings || {}
  const byRole = users.by_role || {}
  const byCategory = listings.by_category || []
  const byStatus = listings.by_status || {}

  return (
    <div className="stack">
      <h1 style={{ marginTop: 0 }}>Dashboard</h1>

      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))' }}>
        <StatCard label="Users" value={users.total || 0} sub={`${byRole.seller || 0} sellers`} accent="var(--wm-green)" />
        <StatCard label="Listings" value={listings.total || 0} sub={`${byStatus.active || 0} live`} accent="var(--wm-red)" />
        <StatCard label="Active listings" value={byStatus.active || 0} accent="var(--wm-pink)" bar={listings.total ? ((byStatus.active || 0) / listings.total) * 100 : 0} />
        <StatCard label="Orders" value={stats.orders?.total || 0} sub={`${formatMoney(stats.revenue, 'KSh ')} earned`} accent="var(--wm-green)" />
      </div>

      {byCategory.length > 0 && (
        <section className="card card-pad">
          <h2 style={{ marginTop: 0 }}>Listings by category</h2>
          {byCategory.map((c) => (
            <div key={c.slug} className="bar-row">
              <span>{c.emoji || ''} {c.name}</span>
              <div className="stat-bar">
                <span style={{ width: `${listings.total ? (c.count / listings.total) * 100 : 0}%` }} />
              </div>
              <strong>{c.count}</strong>
            </div>
          ))}
        </section>
      )}

      <section className="card">
        <div className="card-pad" style={{ borderBottom: '1px solid var(--wm-border)' }}>
          <h2 style={{ margin: 0 }}>Recent moderation activity</h2>
        </div>
        {audit.length === 0 && <p className="card-pad muted">No activity yet.</p>}
        {audit.map((a) => (
          <div key={a.id} className="card-pad flex-between" style={{ borderBottom: '1px solid var(--wm-border)' }}>
            <div>
              <strong>{a.actor_email || 'Admin'}</strong> · {a.action}{' '}
              {a.target?.listing_id ? `#${a.target.listing_id.slice(-6)}` : a.target?.user_id ? `#${a.target.user_id.slice(-6)}` : ''}
            </div>
            <div className="muted" style={{ fontSize: 'var(--fs-xs)' }}>{relativeTime(a.created_at)}</div>
          </div>
        ))}
      </section>
    </div>
  )
}