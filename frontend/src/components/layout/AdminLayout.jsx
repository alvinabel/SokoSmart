import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../lib/auth'

const LINKS = [
  { to: '/admin', label: '📊 Dashboard', end: true },
  { to: '/admin/users', label: '👥 Users' },
  { to: '/admin/listings', label: '🧾 Listings moderation' },
  { to: '/admin/categories', label: '🏷️ Categories' },
]

export default function AdminLayout() {
  const { user, logout } = useAuth()
  return (
    <div className="container admin-layout" style={{ paddingTop: 'var(--space-6)' }}>
      <aside className="admin-sidebar">
        <div className="card card-pad" style={{ marginBottom: 'var(--space-3)' }}>
          <strong>{user?.name}</strong>
          <div className="muted" style={{ fontSize: 'var(--fs-sm)' }}>{user?.role}</div>
        </div>
        {LINKS.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.end} className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}>
            {link.label}
          </NavLink>
        ))}
        <Link to="/" className="nav-link">
          ← Back to storefront
        </Link>
        <button className="menu-item" onClick={logout}>
          Log out
        </button>
      </aside>
      <section style={{ minWidth: 0 }}>
        <Outlet />
      </section>
    </div>
  )
}