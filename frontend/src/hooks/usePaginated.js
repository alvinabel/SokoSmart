import { useCallback, useEffect, useState } from 'react'

/**
 * Fetch a paginated GET endpoint and expose helpers.
 * Usage: usePaginated(fetcher, { pageSize, deps })   OR
 *        usePaginated({ fetcher, pageSize, deps })
 * `fetcher` receives (params) and must return the axios response.
 */
export function usePaginated(fetcherOrOptions, options = {}) {
  const fetcher = typeof fetcherOrOptions === 'function' ? fetcherOrOptions : fetcherOrOptions?.fetcher
  const merged = typeof fetcherOrOptions === 'function' ? options : fetcherOrOptions || {}
  const { pageSize = 12, deps = [] } = merged
  const [items, setItems] = useState([])
  const [meta, setMeta] = useState({ total: 0, page: 1, pages: 1 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)

  const load = useCallback(
    async (nextPage = page) => {
      setLoading(true)
      setError(null)
      try {
        const { data } = await fetcher({ page: nextPage, page_size: pageSize })
        setItems(data.items || [])
        setMeta({ total: data.total || 0, page: data.page || nextPage, pages: data.pages || 1 })
      } catch (err) {
        setError(err)
      } finally {
        setLoading(false)
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [page, pageSize, ...deps],
  )

  useEffect(() => {
    load(page)
  }, [load, page])

  return { items, meta, loading, error, page, setPage, reload: () => load(page) }
}