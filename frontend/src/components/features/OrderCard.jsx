import { Link } from 'react-router-dom'
import Button from '../ui/Button'
import { StatusBadge } from '../ui/Badge'
import { formatMoney, relativeTime } from '../../lib/format'
import { ORDER_STATUS } from '../../utils/constants'

const ACTIONS = {
  selling: {
    placed: [
      { action: 'accept', label: 'Accept', variant: 'secondary' },
      { action: 'reject', label: 'Reject', variant: 'outline' },
    ],
    accepted: [{ action: 'fulfill', label: 'Mark fulfilled', variant: 'secondary' }],
  },
  buying: {
    placed: [{ action: 'cancel', label: 'Cancel', variant: 'outline' }],
    accepted: [{ action: 'cancel', label: 'Cancel', variant: 'outline' }],
    fulfilled: [{ action: 'complete', label: 'Confirm received', variant: 'primary' }],
  },
}

export default function OrderCard({ order, side, onAction, busy }) {
  const actions = ACTIONS[side]?.[order.status] || []
  const counterparty = side === 'selling' ? order.buyer : order.seller
  const listing = order.listing || {}

  return (
    <div className="card card-pad">
      <div className="flex-between wrap">
        <div>
          <div className="flex" style={{ alignItems: 'center', gap: 8 }}>
            <strong>{listing.category_meta?.emoji} {listing.title || 'Listing'}</strong>
            <StatusBadge status={order.status} map={ORDER_STATUS} />
          </div>
          <div className="muted" style={{ fontSize: 'var(--fs-sm)' }}>
            {side === 'selling' ? 'Buyer' : 'Seller'}: {counterparty?.name || '—'} · {relativeTime(order.created_at)}
          </div>
          <div className="muted" style={{ fontSize: 'var(--fs-sm)' }}>
            Qty {order.quantity} × {formatMoney(order.unit_price)} = <strong>{formatMoney(order.total)}</strong>
          </div>
          {order.note && <div className="muted" style={{ fontSize: 'var(--fs-xs)' }}>“{order.note}”</div>}
        </div>
        <div className="flex wrap" style={{ alignItems: 'center' }}>
          {listing.id && (
            <Button as={Link} to={`/listings/${listing.id}`} variant="ghost" size="sm">
              View listing
            </Button>
          )}
          {actions.map((a) => (
            <Button key={a.action} variant={a.variant} size="sm" disabled={busy} onClick={() => onAction(order.id, a.action)}>
              {a.label}
            </Button>
          ))}
        </div>
      </div>
    </div>
  )
}