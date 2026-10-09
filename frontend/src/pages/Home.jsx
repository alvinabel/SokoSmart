import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { marketApi } from '../lib/api'
import { APP_NAME } from '../config'
import CategoryChips from '../components/features/CategoryChips'
import ListingCard from '../components/features/ListingCard'
import { ListingCardSkeleton } from '../components/ui/Skeleton'
import { FALLBACK_CATEGORIES } from '../utils/constants'

const HIGHLIGHTS = [
  { emoji: '🚜', title: 'Farm-gate prices', body: 'Buy straight from producers, skip the middlemen.' },
  { emoji: '📦', title: 'Bulk & retail', body: 'From a single crate to tonnes — negotiate bids and orders.' },
  { emoji: '💬', title: 'Talk to the farmer', body: 'Chat before you buy. Confirm freshness and delivery.' },
  { emoji: '📱', title: 'Works offline', body: 'Installable PWA — browse listings even on low signal.' },
]

export default function Home() {
  const [categories, setCategories] = useState(FALLBACK_CATEGORIES)
  const [recent, setRecent] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    Promise.all([
      marketApi.get('/api/v1/categories').catch(() => null),
      marketApi.get('/api/v1/listings', { params: { page_size: 8 } }).catch(() => null),
    ]).then(([catRes, listRes]) => {
      if (!mounted) return
      if (catRes?.data?.items?.length) setCategories(catRes.data.items)
      setRecent(listRes?.data?.items || [])
      setLoading(false)
    })
    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="container page">
      <section className="hero mb-4">
        <div className="flex-between wrap">
          <div>
            <h1>Fresh produce, straight from the farm.</h1>
            <p style={{ fontSize: '1.1rem', maxWidth: 520 }}>
              {APP_NAME} connects farmers to buyers for crops, livestock, dairy and more — with
              bidding, chat and trusted ratings.
            </p>
            <div className="flex mt-4 wrap">
              <Link to="/listings" className="btn btn--secondary btn--lg">
                Browse produce
              </Link>
              <Link to="/sell" className="btn btn--lg" style={{ background: '#fff', color: 'var(--wm-red)' }}>
                Sell farm produce
              </Link>
            </div>
          </div>
          <div className="hero-emoji" aria-hidden="true">
            🍉🌽🥕
          </div>
        </div>
      </section>

      <section className="section">
        <div className="flex-between mb-3">
          <h2 style={{ margin: 0 }}>Shop by category</h2>
        </div>
        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))' }}>
          {categories.map((c) => (
            <Link key={c.slug} to={`/listings?category=${c.slug}`} className="card card-pad" style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2.2rem' }} aria-hidden="true">
                {c.emoji}
              </div>
              <div style={{ fontWeight: 700, marginTop: 8 }}>{c.name}</div>
            </Link>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="flex-between mb-3">
          <h2 style={{ margin: 0 }}>Freshly listed</h2>
          <Link to="/listings" className="nav-link">
            See all →
          </Link>
        </div>
        <div className="grid grid-cards">
          {loading
            ? Array.from({ length: 8 }).map((_, i) => <ListingCardSkeleton key={i} />)
            : recent.map((l) => <ListingCard key={l.id} listing={l} />)}
        </div>
        {!loading && recent.length === 0 && (
          <div className="empty">
            <div className="empty-icon" aria-hidden="true">🌱</div>
            <h3>No listings yet</h3>
            <p className="muted">Be the first farmer to list produce on {APP_NAME}.</p>
            <div className="flex-center mt-4">
              <Link to="/sell" className="btn btn--primary">
                List your produce
              </Link>
            </div>
          </div>
        )}
      </section>

      <section>
        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
          {HIGHLIGHTS.map((h) => (
            <div key={h.title} className="card card-pad">
              <div style={{ fontSize: '2rem' }} aria-hidden="true">
                {h.emoji}
              </div>
              <h3 style={{ margin: '8px 0 4px' }}>{h.title}</h3>
              <p className="muted" style={{ margin: 0 }}>
                {h.body}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}