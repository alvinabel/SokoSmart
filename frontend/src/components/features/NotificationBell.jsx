import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { marketApi } from '../../lib/api'
import { relativeTime } from '../../lib/format'

const LABELS = {
  'order.new': 'New order received',
  'order.accepted': 'Order accepted',
  'order.rejected': 'Order rejected',
  'order.fulfilled': 'Order fulfilled',
  'order.completed': 'Order completed',
  'order.cancelled': 'Order cancelled',
  'bid.new': 'New bid on your listing',
  'bid.accepted': 'Your bid was accepted',
  'bid.declined': 'Your bid was declined',
  'message.new': 'New message',
  'review.new': 'New review received',
  'listing.moderated': 'Listing moderated',
  system: 'Notification',
}

export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState([])
  const [count, setCount] = useState(0)
  const ref = useRef(null)

  const loadCount = async () => {
    try {
      const { data } = await marketApi.get('/api/v1/notifications/unread-count')
      setCount(data.count)
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    loadCount()
    const interval = setInterval(loadCount, 45000)
    return () => clearInterval(interval)
  }, [])

  const toggle = async () => {
    const next = !open
    setOpen(next)
    if (next) {
      try {
        const { data } = await marketApi.get('/api/v1/notifications', { params: { page_size: 12 } })
        setItems(data.items || [])
      } catch {
        /* ignore */
      }
    }
  }

  useEffect(() => {
    const onClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  const markAll = async () => {
    try {
      await marketApi.patch('/api/v1/notifications/read-all')
      setCount(0)
      setItems((list) => list.map((i) => ({ ...i, read: true })))
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="menu" ref={ref}>
      <button className="btn btn--ghost" onClick={toggle} aria-label="Notifications">
        🔔
        {count > 0 && <span className="bell-dot">{count > 9 ? '9+' : count}</span>}
      </button>
      {open && (
        <div className="notif-pop">
          <div className="flex-between" style={{ padding: 'var(--space-3)' }}>
            <strong>Notifications</strong>
            {count > 0 && (
              <button className="btn btn--ghost btn--sm" onClick={markAll}>
                Mark all read
              </button>
            )}
          </div>
          {items.length === 0 && <div className="notif-item muted">You're all caught up 🎉</div>}
          {items.map((n) => {
            const link = n.data?.listing_id ? `/listings/${n.data.listing_id}` : n.data?.order_id ? '/orders' : '#'
            return (
              <Link key={n.id} to={link} className={`notif-item ${n.read ? '' : 'unread'}`} onClick={() => setOpen(false)}>
                <div>{LABELS[n.type] || n.type}</div>
                <div className="muted" style={{ fontSize: 'var(--fs-xs)' }}>
                  {relativeTime(n.created_at)}
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}