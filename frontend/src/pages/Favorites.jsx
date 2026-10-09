import { marketApi } from '../lib/api'
import { usePaginated } from '../hooks/usePaginated'
import ListingCard from '../components/features/ListingCard'
import { ListingCardSkeleton } from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import Pagination from '../components/ui/Pagination'
import { Link } from 'react-router-dom'

export default function Favorites() {
  const { items, meta, loading, page, setPage } = usePaginated({
    fetcher: () => marketApi.get('/api/v1/favorites'),
    deps: [],
  })

  return (
    <div className="container page">
      <h1 style={{ marginTop: 0 }}>Favourites</h1>
      <p className="muted">Produce you've saved for later.</p>

      {loading && (
        <div className="grid grid-cards">
          {Array.from({ length: 4 }).map((_, i) => (
            <ListingCardSkeleton key={i} />
          ))}
        </div>
      )}

      {!loading && items.length === 0 && (
        <EmptyState
          icon="🤍"
          title="Nothing saved yet"
          message='Tap the heart on any listing to build your wishlist.'
          action={<Link to="/listings" className="btn btn--primary">Browse listings</Link>}
        />
      )}

      <div className="grid grid-cards">
        {items.map((f) => (
          <ListingCard key={f.listing?.id || f.id} listing={f.listing || f} />
        ))}
      </div>

      <Pagination page={meta.page} pages={meta.pages} onChange={setPage} />
    </div>
  )
}