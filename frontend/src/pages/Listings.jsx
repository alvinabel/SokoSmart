import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { marketApi } from '../lib/api'
import { useDebounce } from '../hooks/useDebounce'
import FilterPanel from '../components/features/FilterPanel'
import ListingCard from '../components/features/ListingCard'
import { ListingCardSkeleton } from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import Pagination from '../components/ui/Pagination'
import { FALLBACK_CATEGORIES } from '../utils/constants'

const DEFAULT_FILTERS = { q: '', category: '', min_price: '', max_price: '', city: '', sort: 'newest' }

export default function Listings() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [categories, setCategories] = useState(FALLBACK_CATEGORIES)
  const [items, setItems] = useState([])
  const [meta, setMeta] = useState({ total: 0, page: 1, pages: 1 })
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)

  const [filters, setFilters] = useState(() => ({
    ...DEFAULT_FILTERS,
    q: searchParams.get('q') || '',
    category: searchParams.get('category') || '',
  }))
  const debouncedQ = useDebounce(filters.q, 450)

  useEffect(() => {
    marketApi.get('/api/v1/categories').then((res) => {
      if (res.data.items?.length) setCategories(res.data.items)
    }).catch(() => {})
  }, [])

  const params = useMemo(() => {
    const p = { page, page_size: 12, sort: filters.sort }
    if (debouncedQ.trim()) p.q = debouncedQ.trim()
    if (filters.category) p.category = filters.category
    if (filters.city.trim()) p.city = filters.city.trim()
    if (filters.min_price) p.min_price = filters.min_price
    if (filters.max_price) p.max_price = filters.max_price
    return new URLSearchParams(p).toString()
  }, [page, filters, debouncedQ])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    marketApi
      .get(`/api/v1/listings?${params}`)
      .then((res) => {
        if (cancelled) return
        setItems(res.data.items || [])
        setMeta({ total: res.data.total || 0, page: res.data.page || 1, pages: res.data.pages || 1 })
      })
      .catch(() => {})
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [params])

  const patchFilters = (patch) => {
    const next = { ...filters, ...patch }
    setFilters(next)
    const sp = {}
    if (page !== 1) setPage(1)
    if (next.category) sp.category = next.category
    if (next.q.trim()) sp.q = next.q.trim()
    setSearchParams(sp, { replace: true })
  }

  return (
    <div className="container page">
      <h1 style={{ marginTop: 0 }}>Marketplace</h1>
      <p className="muted">{meta.total.toLocaleString()} produce listings & counting</p>

      <div className="listings-layout">
        <FilterPanel value={filters} categories={categories} onChange={patchFilters} onReset={() => patchFilters(DEFAULT_FILTERS)} />

        <div>
          {loading && (
            <div className="grid grid-cards">
              {Array.from({ length: 6 }).map((_, i) => (
                <ListingCardSkeleton key={i} />
              ))}
            </div>
          )}

          {!loading && items.length === 0 && (
            <EmptyState
              icon="🔍"
              title="No listings match your filters"
              message="Try a different search term, widen the price range, or clear the city filter."
            />
          )}

          {!loading && items.length > 0 && (
            <div className="grid grid-cards">
              {items.map((l) => (
                <ListingCard key={l.id} listing={l} />
              ))}
            </div>
          )}

          <Pagination page={meta.page} pages={meta.pages} onChange={setPage} />
        </div>
      </div>
    </div>
  )
}