import { useEffect, useState } from 'react'
import { authApi } from '../../lib/api'
import { apiErrorMessage } from '../../lib/api'
import { Link } from 'react-router-dom'
import Button from '../../components/ui/Button'
import { StatusBadge } from '../../components/ui/Badge'
import { LISTING_STATUS } from '../../utils/constants'
import Pagination from '../../components/ui/Pagination'
import { useToast } from '../../lib/toast'

export default function Moderation() {
  const [items, setItems] = useState([])
  const [pages, setPages] = useState(1)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const { success, error } = useToast()

  const load = () => {
    setLoading(true)
    authApi
      .get('/api/admin/listings', { params: { page, page_size: 15 } })
      .then((res) => {
        setItems(res.data.items || [])
        setPages(res.data.pages || 1)
      })
      .catch((err) => error(apiErrorMessage(err)))
      .finally(() => setLoading(false))
  }

  useEffect(load, [page])

  const moderate = async (id, action) => {
    if (!id) return
    try {
      await authApi.patch(`/api/admin/listings/${id}`, { action })
      success(`Listing ${action}`)
      setSelected(null)
      load()
    } catch (err) {
      error(apiErrorMessage(err))
    }
  }

  return (
    <div className="stack">
      <h1 style={{ marginTop: 0 }}>Listings moderation</h1>
      {loading && <p className="muted">Loading…</p>}

      <table className="table">
        <thead>
          <tr>
            <th>Listing</th>
            <th>Seller</th>
            <th>Price</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((l) => (
            <tr key={l.id}>
              <td>
                <Link to={`/listings/${l.id}`}><strong>{l.title}</strong></Link>
                <div className="muted" style={{ fontSize: 'var(--fs-xs)' }}>{l.category}</div>
              </td>
              <td>{l.seller || '—'}</td>
              <td>{l.price} {l.unit}</td>
              <td><StatusBadge status={l.status} map={LISTING_STATUS} /></td>
              <td>
                <div className="flex wrap">
                  <Button size="sm" variant="ghost" onClick={() => setSelected(l.id)}>
                    Actions
                  </Button>
                  {selected === l.id && (
                    <>
                      <Button size="sm" variant="secondary" onClick={() => moderate(l.id, 'approve')}>Approve</Button>
                      <Button size="sm" variant="danger" onClick={() => moderate(l.id, 'reject')}>Reject</Button>
                      <Button size="sm" variant="outline" onClick={() => moderate(l.id, 'suspend')}>Suspend</Button>
                      <Button size="sm" variant="ghost" onClick={() => moderate(l.id, 'activate')}>Activate</Button>
                    </>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <Pagination page={page} pages={pages} onChange={setPage} />
    </div>
  )
}