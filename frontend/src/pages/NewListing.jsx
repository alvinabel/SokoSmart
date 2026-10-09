import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { marketApi } from '../lib/api'
import { apiErrorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useToast } from '../lib/toast'
import { FALLBACK_CATEGORIES, LISTING_STATUS } from '../utils/constants'
import ListingForm from '../components/features/ListingForm'
import Spinner from '../components/ui/Spinner'
import Field from '../components/ui/Field'
import Button from '../components/ui/Button'

export default function NewListing() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { success, error } = useToast()
  const [categories, setCategories] = useState(FALLBACK_CATEGORIES)
  const [loadingCat, setLoadingCat] = useState(true)
  const [submitError, setSubmitError] = useState('')

  useEffect(() => {
    marketApi
      .get('/api/v1/categories')
      .then((res) => res.data.items?.length && setCategories(res.data.items))
      .catch(() => {})
      .finally(() => setLoadingCat(false))
  }, [])

  const onSubmit = async (payload) => {
    setSubmitError('')
    try {
      const { data } = await marketApi.post('/api/v1/listings', payload)
      success('Listing published!')
      navigate(`/listings/${data.id}`)
    } catch (err) {
      setSubmitError(apiErrorMessage(err, 'Could not publish listing'))
    }
  }

  if (loadingCat) return <Spinner center />

  return (
    <div className="container page" style={{ maxWidth: 860 }}>
      <h1 style={{ marginTop: 0 }}>List your produce</h1>
      <p className="muted">
        Selling as <strong>{user?.name}</strong> · new listings go live immediately. Keep your price firm
        or put “negotiable” to invite bids.
      </p>

      {submitError && <div className="alert alert--danger">{submitError}</div>}

      <ListingForm categories={categories} onSubmit={onSubmit} statuses={LISTING_STATUS} submitLabel="Publish listing" />
    </div>
  )
}