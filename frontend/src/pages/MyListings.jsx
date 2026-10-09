import { Link } from 'react-router-dom'
import { marketApi } from '../lib/api'
import { usePaginated } from '../hooks/usePaginated'
import ListingCard from '../components/features/ListingCard'
import { ListingCardSkeleton } from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import Pagination from '../components/ui/Pagination'
import Button from '../components/ui/Button'

export default function MyListings() {
  const { items, meta, loading, refetch, page, setPage } = usePaginated({
    fetcher: () => marketApi.get('/api/v1/listings/mine'),
    deps: [],
  })

  const toggleActive = async (listing) => {
    // Owners may only flip between 'active' and 'sold' (moderation handles the rest).
    const next = listing.status === 'active' ? 'sold' : 'active'
    try {
      await marketApi.patch(`/api/v1/listings/${listing.id}`, { status: next })
      refetch()
    } catch {
      /* ignore */
    }
  }

  const remove = async (listing) => {
    if (!window.confirm(`Delete “${listing.title}”? This can't be undone.`)) return
    try {
      await marketApi.delete(`/api/v1/listings/${listing.id}`)
      refetch()
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="container page">
      <div className="flex-between wrap mb-4">
        <div>
          <h1 style={{ margin: 0 }}>My listings</h1>
          <p className="muted">Manage, edit, pause or remove your produce listings.</p>
        </div>
        <Link to="/sell" className="btn btn--primary">+ New listing</Link>
      </div>

      {loading && (
        <div className="grid grid-cards">
          {Array.from({ length: 4 }).map((_, i) => (
            <ListingCardSkeleton key={i} />
          ))}
        </div>
      )}

      {!loading && items.length === 0 && (
        <EmptyState
          icon="🌱"
          title="Nothing listed yet"
          message="List your first batch of produce and reach buyers across your market."
          action={<Link to="/sell" className="btn btn--primary">List produce</Link>}
        />
      )}

      <div className="grid grid-cards">
        {items.map((l) => (
          <div key={l.id} className="card">
            <ListingCard listing={l} />
            <div className="flex" style={{ padding: 'var(--space-3)', borderTop: '1px solid var(--wm-border)' }}>
              <Button as={Link} to={`/sell/${l.id}/edit`} variant="outline" size="sm">
                Edit
              </Button>
              <Button variant="ghost" size="sm" onClick={() => toggleActive(l)}>
                {l.status === 'active' ? 'Mark sold' : 'Reactivate'}
              </Button>
              <Button variant="ghost" size="sm" onClick={() => remove(l)} style={{ color: 'var(--wm-danger)' }}>
                Delete
              </Button>
            </div>
          </div>
        ))}
      </div>

      <Pagination page={meta.page} pages={meta.pages} onChange={setPage} />
    </div>
  )
}