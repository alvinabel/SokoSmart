import { useState } from 'react'
import { marketApi } from '../lib/api'
import { usePaginated } from '../hooks/usePaginated'
import { useToast } from '../lib/toast'
import OrderCard from '../components/features/OrderCard'
import Tabs from '../components/ui/Tabs'
import EmptyState from '../components/ui/EmptyState'
import Pagination from '../components/ui/Pagination'

export default function Orders() {
  const [side, setSide] = useState('selling')
  const { success, error } = useToast()

  const { items, meta, loading, refetch, page, setPage } = usePaginated({
    fetcher: () => marketApi.get(`/api/v1/orders?side=${side}`),
    deps: [side],
  })

  const act = async (orderId, action) => {
    try {
      await marketApi.patch(`/api/v1/orders/${orderId}`, { action })
      success('Order updated')
      refetch()
    } catch (err) {
      error(err.response?.data?.error?.message || 'Update failed')
    }
  }

  return (
    <div className="container page">
      <h1 style={{ marginTop: 0 }}>Orders</h1>
      <p className="muted">Accept or reject buyer requests, and confirm deliveries.</p>

      <Tabs
        active={side}
        onChange={setSide}
        tabs={[
          { value: 'selling', label: 'Selling' },
          { value: 'buying', label: 'Buying' },
        ]}
      />

      {loading && <p className="muted">Loading orders…</p>}

      {!loading && items.length === 0 && (
        <EmptyState
          icon="🧾"
          title="No orders here"
          message={side === 'selling' ? 'Buyers will appear here when they order or bid on your listings.' : "Order something and track it here."}
        />
      )}

      <div className="stack mt-4">
        {items.map((o) => (
          <OrderCard key={o.id} order={o} side={side} onAction={act} />
        ))}
      </div>

      <Pagination page={meta.page} pages={meta.pages} onChange={setPage} />
    </div>
  )
}