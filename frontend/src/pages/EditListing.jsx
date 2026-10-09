import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { marketApi } from '../lib/api'
import { apiErrorMessage } from '../lib/api'
import { useToast } from '../lib/toast'
import { FALLBACK_CATEGORIES, LISTING_STATUS } from '../utils/constants'
import ListingForm from '../components/features/ListingForm'
import Spinner from '../components/ui/Spinner'

export default function EditListing() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { success, error } = useToast()
  const [categories, setCategories] = useState(FALLBACK_CATEGORIES)
  const [listing, setListing] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    Promise.all([
      marketApi.get('/api/v1/categories').catch(() => null),
      marketApi.get(`/api/v1/listings/${id}`).catch((err) => setLoadError(apiErrorMessage(err))),
    ]).then(([catRes, listRes]) => {
      if (catRes?.data?.items?.length) setCategories(catRes.data.items)
      if (listRes?.data) setListing(listRes.data)
      setLoading(false)
    })
  }, [id])

  const onSubmit = async (payload) => {
    try {
      const { data } = await marketApi.patch(`/api/v1/listings/${id}`, payload)
      success('Listing updated')
      navigate(`/listings/${data.id}`)
    } catch (err) {
      error(apiErrorMessage(err))
    }
  }

  if (loading) return <Spinner center />

  return (
    <div className="container page" style={{ maxWidth: 860 }}>
      <h1 style={{ marginTop: 0 }}>Edit listing</h1>
      <div className="mb-3">
        <Link to="/mylistings" className="nav-link">← Back to my listings</Link>
      </div>

      {loadError && <div className="alert alert--danger">{loadError}</div>}

      {listing && (
        <ListingForm
          categories={categories}
          initial={{ ...listing, city: listing.location?.city || '' }}
          onSubmit={onSubmit}
          statuses={LISTING_STATUS}
          submitLabel="Save changes"
        />
      )}
    </div>
  )
}