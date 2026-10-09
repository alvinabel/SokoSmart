import { useEffect, useState } from 'react'
import { authApi } from '../../lib/api'
import { apiErrorMessage } from '../../lib/api'
import Button from '../../components/ui/Button'
import { ROLES } from '../../utils/constants'
import Pagination from '../../components/ui/Pagination'
import { useToast } from '../../lib/toast'

export default function Users() {
  const [items, setItems] = useState([])
  const [meta, setMeta] = useState({ page: 1, pages: 1 })
  const [page, setPage] = useState(1)
  const [q, setQ] = useState('')
  const [loading, setLoading] = useState(true)
  const { success, error } = useToast()

  const load = () => {
    setLoading(true)
    authApi
      .get('/api/admin/users', { params: { page, page_size: 15, q } })
      .then((res) => {
        setItems(res.data.items || [])
        setMeta({ page: res.data.page || 1, pages: res.data.pages || 1 })
      })
      .catch((err) => error(apiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(load, [page, q])

  const act = async (id, action, value) => {
    try {
      const payload = value ? { action, value } : { action }
      await authApi.patch(`/api/admin/users/${id}`, payload)
      success('Done')
      load()
    } catch (err) {
      error(apiErrorMessage(err))
    }
  }

  const isActive = (u) => u.status === 'active'

  return (
    <div className="stack">
      <div className="flex-between wrap">
        <h1 style={{ marginTop: 0 }}>Users</h1>
        <input className="input" placeholder="Search by name or email…" value={q} onChange={(e) => { setQ(e.target.value); setPage(1) }} style={{ maxWidth: 300 }} />
      </div>

      {loading && <p className="muted">Loading…</p>}
      <table className="table">
        <thead>
          <tr>
            <th>User</th>
            <th>Role</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((u) => (
            <tr key={u.id}>
              <td>
                <strong>{u.name}</strong>
                <div className="muted" style={{ fontSize: 'var(--fs-xs)' }}>{u.email}</div>
              </td>
              <td><span className="badge">{ROLES[u.role] || u.role}</span></td>
              <td>{isActive(u) ? 'Active' : 'Suspended'}</td>
              <td>
                <div className="flex wrap">
                  {isActive(u) && u.role !== 'admin' && (
                    <Button size="sm" variant="danger" onClick={() => act(u.id, 'suspend')}>
                      Suspend
                    </Button>
                  )}
                  {isActive(u) && u.role !== 'admin' && (
                    <Button size="sm" variant="outline" onClick={() => act(u.id, 'role', u.role === 'seller' ? 'buyer' : 'seller')}>
                      {u.role === 'seller' ? 'Make buyer' : 'Make seller'}
                    </Button>
                  )}
                  {!isActive(u) && (
                    <Button size="sm" variant="secondary" onClick={() => act(u.id, 'activate')}>
                      Reactivate
                    </Button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <Pagination page={meta.page} pages={meta.pages} onChange={setPage} />
    </div>
  )
}