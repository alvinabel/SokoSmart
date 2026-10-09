import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { marketApi } from '../lib/api'
import { apiErrorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useToast } from '../lib/toast'
import { relativeTime } from '../lib/format'
import Avatar from '../components/ui/Avatar'
import Spinner from '../components/ui/Spinner'
import RatingStars from '../components/ui/RatingStars'
import { Input, Textarea } from '../components/ui/Inputs'
import Field from '../components/ui/Field'
import Button from '../components/ui/Button'
import ListingCard from '../components/features/ListingCard'

const OWN_KEYS = [
  ['name', 'Full name'],
  ['phone', 'Phone'],
  ['city', 'City'],
  ['bio', 'Bio'],
]

export default function Profile() {
  const { id } = useParams()
  const { user, refreshMe } = useAuth()
  const { success, error } = useToast()
  const isMe = !id || Boolean(user && user.id === id)

  const [profile, setProfile] = useState(null)
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({})
  const [reviews, setReviews] = useState([])
  const [myListings, setMyListings] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const promise = isMe ? marketApi.get('/api/v1/profile/me') : marketApi.get(`/api/v1/profile/${id}`)
    promise
      .then((res) => {
        const data = res.data
        if (isMe) {
          setProfile(data)
        } else {
          const other = data.user || {}
          setProfile({
            id: other.id,
            name: other.name,
            role: other.role,
            phone: other.phone,
            location: other.location,
            rating: other.rating,
            created_at: other.created_at,
            bio: data.bio,
            listings: data.listings,
            listing_count: data.listing_count,
          })
        }
      })
      .catch((err) => error(apiErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [id, isMe, error])

  useEffect(() => {
    if (isMe) {
      marketApi
        .get('/api/v1/listings/mine', { params: { page_size: 12 } })
        .then((res) => setMyListings(res.data.items || []))
        .catch(() => {})
    } else if (id) {
      marketApi
        .get(`/api/v1/reviews/seller/${id}`, { params: { page_size: 12 } })
        .then((res) => setReviews(res.data.items || []))
        .catch(() => {})
    }
  }, [id, isMe])

  const startEdit = () => {
    setForm({
      name: profile.name || '',
      phone: profile.phone || '',
      city: profile.location?.city || '',
      bio: profile.bio || '',
    })
    setEditing(true)
  }

  const setField = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const save = async (e) => {
    e.preventDefault()
    try {
      const { data } = await marketApi.patch('/api/v1/profile/me', {
        name: form.name,
        phone: form.phone,
        bio: form.bio,
        location_city: form.city,
      })
      setProfile((p) => ({ ...p, ...data }))
      setEditing(false)
      success('Profile saved')
      refreshMe?.()
    } catch (err) {
      error(apiErrorMessage(err))
    }
  }

  if (loading) return <Spinner center />
  if (!profile) return <div className="container page">User not found.</div>

  const listings = profile.listings && profile.listings.length ? profile.listings : isMe ? myListings : []

  return (
    <div className="container page">
      <div className="detail-grid">
        <aside className="card card-pad stack">
          <Avatar name={profile.name} size={72} />
          <h2 style={{ marginBottom: 0 }}>{profile.name}</h2>
          <div className="muted">
            {profile.role === 'seller' ? '🌿 Verified producer' : 'Member'} · joined {relativeTime(profile.created_at)}
          </div>
          <RatingStars value={profile.rating?.avg || 0} count={profile.rating?.count || 0} />
          {profile.bio && <p>{profile.bio}</p>}
          {profile.location?.city && <div className="muted">📍 {profile.location.city}</div>}
          {profile.phone && <div className="muted">📞 {profile.phone}</div>}

          {isMe && !editing && (
            <Button variant="outline" block onClick={startEdit}>
              Edit profile
            </Button>
          )}

          {editing && (
            <form onSubmit={save} className="stack">
              <h3>Edit profile</h3>
              {OWN_KEYS.map(([key, label]) => (
                <Field key={key} label={label} htmlFor={`p-${key}`}>
                  {key === 'bio' ? (
                    <Textarea id={`p-${key}`} value={form[key] || ''} onChange={setField(key)} />
                  ) : (
                    <Input id={`p-${key}`} value={form[key] || ''} onChange={setField(key)} />
                  )}
                </Field>
              ))}
              <div className="flex">
                <Button type="submit" variant="primary">
                  Save
                </Button>
                <Button type="button" variant="outline" onClick={() => setEditing(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          )}

          {!isMe && (
            <Button as={Link} to={`/inbox?with=${profile.id}`} variant="secondary" block>
              Message {profile.name.split(' ')[0]}
            </Button>
          )}
        </aside>

        <section className="stack">
          <h2>Listings {listings.length > 0 && `(${listings.length})`}</h2>
          {listings.length === 0 ? (
            <div className="card card-pad muted">No public listings right now.</div>
          ) : (
            <div className="grid grid-cards">
              {listings.map((l) => (
                <ListingCard key={l.id} listing={l} />
              ))}
            </div>
          )}

          {!isMe && (
            <>
              <h2>Ratings &amp; reviews</h2>
              {reviews.length === 0 && <div className="card card-pad muted">No reviews yet.</div>}
              {reviews.map((r) => (
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
            </>
          )}
        </section>
      </div>
    </div>
  )
}