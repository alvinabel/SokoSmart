import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { marketApi } from '../lib/api'
import { apiErrorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useToast } from '../lib/toast'
import { formatMoney, relativeTime } from '../lib/format'
import { LISTING_STATUS } from '../utils/constants'
import Button from '../components/ui/Button'
import { StatusBadge } from '../components/ui/Badge'
import { Input, Textarea } from '../components/ui/Inputs'
import Field from '../components/ui/Field'
import Spinner from '../components/ui/Spinner'
import Modal from '../components/ui/Modal'
import RatingStars from '../components/ui/RatingStars'
import Avatar from '../components/ui/Avatar'
import ListingCard from '../components/features/ListingCard'

export default function ListingDetail() {
  const { id } = useParams()
  const { user, isAuthenticated, can } = useAuth()
  const { success, error } = useToast()
  const navigate = useNavigate()

  const [listing, setListing] = useState(null)
  const [reviews, setReviews] = useState({ items: [], avg: 0 })
  const [related, setRelated] = useState([])
  const [loading, setLoading] = useState(true)
  const [favorite, setFavorite] = useState(false)

  const [bidAmount, setBidAmount] = useState('')
  const [orderQty, setOrderQty] = useState('1')
  const [orderNote, setOrderNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [reportOpen, setReportOpen] = useState(false)
  const [reportReason, setReportReason] = useState('')

  const load = useCallback(async () => {
    try {
      const [detailRes, reviewRes, relatedRes] = await Promise.all([
        marketApi.get(`/api/v1/listings/${id}`),
        marketApi.get(`/api/v1/reviews/listing/${id}`, { params: { page_size: 6 } }).catch(() => null),
        marketApi.get(`/api/v1/listings`, { params: { category: '', page_size: 3, q: '' } }).catch(() => null),
      ])
      setListing(detailRes.data)
      setFavorite(false)
      if (user) {
        try {
          const favs = await marketApi.get('/api/v1/favorites')
          setFavorite(favs.data.items.some((f) => f.listing?.id === id))
        } catch {
          /* guest */
        }
      }
      if (reviewRes) setReviews(reviewRes.data)
      if (relatedRes) setRelated(relatedRes.data.items?.filter((l) => l.id !== id) || [])
    } catch (err) {
      error(apiErrorMessage(err, 'Could not load this listing'))
    } finally {
      setLoading(false)
    }
  }, [id, user, error])

  useEffect(() => {
    setLoading(true)
    load()
  }, [load])

  if (loading) return <Spinner center />

  if (!listing) {
    return (
      <div className="container page">
        <h2>Listing not found</h2>
        <Link to="/listings" className="nav-link">← Back to marketplace</Link>
      </div>
    )
  }

  const isOwner = user?.id === listing.seller?.id
  const meta = listing.category_meta || {}

  const toggleFav = async () => {
    if (!isAuthenticated) return navigate(`/login?next=/listings/${id}`)
    try {
      const { data } = await marketApi.post(`/api/v1/favorites/${id}`)
      setFavorite(data.favorited)
      success(data.favorited ? 'Added to favourites' : 'Removed from favourites')
    } catch (err) {
      error(apiErrorMessage(err))
    }
  }

  const placeBid = async (e) => {
    e.preventDefault()
    if (!Number(bidAmount)) return
    if (!isAuthenticated) return navigate(`/login?next=/listings/${id}`)
    setBusy(true)
    try {
      const { data } = await marketApi.post('/api/v1/bids', { listing_id: id, amount: Number(bidAmount) })
      success(`Bid of ${formatMoney(data.amount)} placed — the seller will review it.`)
      setBidAmount('')
    } catch (err) {
      error(apiErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const placeOrder = async (e) => {
    e.preventDefault()
    if (!isAuthenticated) return navigate(`/login?next=/listings/${id}`)
    setBusy(true)
    try {
      const { data } = await marketApi.post('/api/v1/orders', {
        listing_id: id,
        quantity: Number(orderQty) || 1,
        note: orderNote.trim() || null,
      })
      success(`Order request placed · ${formatMoney(data.total)}`)
      setOrderQty('1')
      setOrderNote('')
    } catch (err) {
      error(apiErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const submitReport = async () => {
    try {
      await marketApi.post(`/api/v1/listings/${id}/report`, { reason: reportReason })
      success('Thanks — our moderation team will look into it.')
      setReportOpen(false)
      setReportReason('')
    } catch (err) {
      error(apiErrorMessage(err))
    }
  }

  const openChat = () => navigate(`/inbox?with=${listing.seller.id}&listing=${id}`)

  const image = listing.images?.[0]

  return (
    <div className="container page">
      <div className="flex-between wrap mb-4">
        <Link to="/listings" className="nav-link">← Back to marketplace</Link>
        <StatusBadge status={listing.status} map={LISTING_STATUS} />
      </div>

      <div className="detail-grid">
        <div className="stack">
          <div className="detail-media">
            {image ? <img src={image} alt={listing.title} /> : <span aria-hidden="true">{meta.emoji || '🥬'}</span>}
          </div>
          <div>
            <h1 style={{ marginBottom: 4 }}>{listing.title}</h1>
            <div className="muted">
              Listed <span>{meta.emoji} {meta.name}</span> · {relativeTime(listing.created_at)} · {listing.views} views
            </div>
            <p>{listing.description || 'No description provided.'}</p>

            {listing.quality && <p><strong>Quality:</strong> {listing.quality}</p>}

            <h3>Reviews</h3>
            {reviews.items.length === 0 && <p className="muted">No reviews yet.</p>}
            {reviews.items.map((r) => (
              <div key={r.id} className="card card-pad mb-3">
                <div className="flex-between">
                  <div className="flex" style={{ alignItems: 'center' }}>
                    <Avatar name={r.author?.name} size={28} />
                    <strong>{r.author?.name}</strong>
                  </div>
                  <RatingStars value={r.rating} />
                </div>
                {r.comment && <p className="muted" style={{ margin: '8px 0 0' }}>{r.comment}</p>}
              </div>
            ))}
          </div>
        </div>

        <aside className="stack">
          <div className="card card-pad">
            <div className="price-lg">{formatMoney(listing.price)} <span style={{ fontSize: '1rem', color: 'var(--wm-text-muted)' }}>/ {listing.unit}</span></div>
            <div className="muted" style={{ fontSize: 'var(--fs-sm)' }}>
              Quantity available: <strong>{listing.quantity}</strong> {listing.unit}(s)
            </div>
            <div className="muted" style={{ fontSize: 'var(--fs-sm)' }}>📍 {listing.location?.city || 'Location on request'}</div>

            <div className="flex mt-4">
              <Button variant="outline" onClick={toggleFav}>{favorite ? '❤️ Favourited' : '🤍 Save'}</Button>
              <Button variant="primary" onClick={openChat} disabled={isOwner || !isAuthenticated}>
                💬 Chat with seller
              </Button>
            </div>

            {!isOwner && (
              <>
                <hr className="rule" />
                <h3>Bid your price</h3>
                <form onSubmit={placeBid} className="flex">
                  <Input type="number" min="0" value={bidAmount} onChange={(e) => setBidAmount(e.target.value)} placeholder="Offer (KSh)" />
                  <Button type="submit" variant="secondary" disabled={busy || !bidAmount} loading={busy}>
                    {isAuthenticated ? 'Bid' : 'Log in to bid'}
                  </Button>
                </form>

                <hr className="rule" />
                <h3>Order now</h3>
                <form onSubmit={placeOrder} className="stack">
                  <Field label={`Quantity (${listing.unit})`} htmlFor="qty">
                    <Input id="qty" type="number" min="1" value={orderQty} onChange={(e) => setOrderQty(e.target.value)} />
                  </Field>
                  <Field label="Note (optional)" htmlFor="note">
                    <Textarea id="note" value={orderNote} onChange={(e) => setOrderNote(e.target.value)} placeholder="Pickup/delivery preferences…" />
                  </Field>
                  <Button type="submit" variant="primary" block loading={busy}>
                    {isAuthenticated ? `Order for ${formatMoney((Number(orderQty) || 1) * listing.price)}` : 'Log in to order'}
                  </Button>
                </form>
              </>
            )}

            {isOwner && <p className="muted" style={{ fontSize: 'var(--fs-sm)' }}>This is your listing — see it under “My listings” to manage.</p>}

            {can('listing.manage') && <Button as={Link} to={`/sell/${id}/edit`} variant="outline" block className="mt-4">Edit listing</Button>}

            <button className="menu-item" onClick={() => setReportOpen(true)} style={{ color: 'var(--wm-danger)' }}>
              🚩 Report this listing
            </button>
          </div>

          <div className="card card-pad">
            <div className="flex" style={{ alignItems: 'center' }}>
              <Avatar name={listing.seller?.name} size={44} />
              <div>
                <Link to={`/u/${listing.seller?.id}`} style={{ fontWeight: 700 }}>
                  {listing.seller?.name}
                </Link>
                <div className="muted" style={{ fontSize: 'var(--fs-sm)' }}>
                  {listing.seller?.role === 'seller' ? 'Verified producer' : 'Member'}
                </div>
              </div>
            </div>
            <RatingStars value={listing.seller?.rating?.avg || 0} count={listing.seller?.rating?.count || 0} />
            <Button className="mt-3" variant="secondary" block onClick={openChat} disabled={isOwner || !isAuthenticated}>
              Contact seller
            </Button>
          </div>
        </aside>
      </div>

      {related.length > 0 && (
        <section className="section mt-4">
          <h2>You might also like</h2>
          <div className="grid grid-cards">
            {related.map((l) => (
              <ListingCard key={l.id} listing={l} />
            ))}
          </div>
        </section>
      )}

      <Modal open={reportOpen} onClose={() => setReportOpen(false)} title="Report listing">
        <Field label="Reason (optional)" htmlFor="report">
          <Textarea id="report" value={reportReason} onChange={(e) => setReportReason(e.target.value)} placeholder="Scam, misleading info, unsafe produce…" />
        </Field>
        <Button variant="danger" block onClick={submitReport}>
          Submit report
        </Button>
      </Modal>
    </div>
  )
}