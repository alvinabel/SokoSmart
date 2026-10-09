import { Link } from 'react-router-dom'
import { useAuth } from '../../lib/auth'
import { useToast } from '../../lib/toast'
import { marketApi } from '../../lib/api'
import { formatMoney, relativeTime } from '../../lib/format'
import { LISTING_STATUS } from '../../utils/constants'
import { StatusBadge } from '../ui/Badge'
import { useState } from 'react'

export default function ListingCard({ listing, onToggleFavorite }) {
  const { user } = useAuth()
  const { success } = useToast()
  const [favorite, setFavorite] = useState(false)

  const toggle = async (e) => {
    e.preventDefault()
    if (!user) return
    try {
      const { data } = await marketApi.post(`/api/v1/favorites/${listing.id}`)
      setFavorite(data.favorited)
      if (onToggleFavorite) onToggleFavorite(listing.id, data.favorited)
      success(data.favorited ? 'Saved to favourites ❤️' : 'Removed from favourites')
    } catch {
      /* toast handled elsewhere */
    }
  }

  const image = listing.images?.[0]
  const meta = listing.category_meta || {}
  const status = LISTING_STATUS[listing.status] || { label: listing.status, tone: 'pale' }

  return (
    <Link to={`/listings/${listing.id}`} className="listing-card">
      <div className="listing-media">
        {image ? <img src={image} alt={listing.title} loading="lazy" /> : <span aria-hidden="true">{meta.emoji || '🥬'}</span>}
      </div>
      {user && user.id !== listing.seller?.id && (
        <button className={`listing-fav ${favorite ? 'active' : ''}`} onClick={toggle} aria-label="Toggle favourite">
          {favorite ? '❤️' : '🤍'}
        </button>
      )}
      <div className="listing-body">
        <span className="listing-price">
          {formatMoney(listing.price)} / {listing.unit}
        </span>
        <span className="listing-title">{listing.title}</span>
        <span className="listing-meta">
          <span>📍 {listing.location?.city || 'Unknown area'}</span>
          <span>·</span>
          <span>{relativeTime(listing.created_at)}</span>
        </span>
        <span className="flex-between">
          {listing.quantity != null && <span className="muted" style={{ fontSize: 'var(--fs-xs)' }}>Qty {listing.quantity}</span>}
          <StatusBadge status={listing.status} map={LISTING_STATUS} />
        </span>
      </div>
    </Link>
  )
}