import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../lib/auth'
import { ROLES } from '../../utils/constants'
import Avatar from '../ui/Avatar'
import NotificationBell from '../features/NotificationBell'

export default function Navbar() {
  const { user, isAuthenticated, can, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const [query, setQuery] = useState('')

  const submitSearch = (e) => {
    e.preventDefault()
    navigate(`/listings?q=${encodeURIComponent(query.trim())}`)
    setQuery('')
  }

  return (
    <header className="nav">
      <div className="container">
        <div className="nav-inner">
          <Link to="/" className="brand" aria-label="AgroBasket home">
            <span className="brand-mark" aria-hidden="true">🍉</span>
            <span>AgroBasket</span>
          </Link>

          <form className="nav-search" onSubmit={submitSearch}>
            <input
              className="input"
              placeholder="Search produce, e.g. watermelon, maize, eggs…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search listings"
            />
          </form>

          <nav className="nav-links" aria-label="Primary">
            <Link to="/listings" className="nav-link nav-link--hide-mobile">
              Browse
            </Link>
            {user && (
              <Link to="/orders" className="nav-link nav-link--hide-mobile">
                Orders
              </Link>
            )}
            {can('listing.manage') && (
              <Link to="/sell" className="nav-link nav-link--cta">
                + Sell produce
              </Link>
            )}

            {isAuthenticated ? (
              <>
                <NotificationBell />
                <div className="menu">
                  <button className="btn btn--ghost" onClick={() => setMenuOpen((v) => !v)} aria-label="Account menu">
                    <Avatar name={user.name} size={34} />
                  </button>
                  {menuOpen && (
                    <div className="menu-pop">
                      <div className="menu-item" style={{ cursor: 'default' }}>
                        {user.name} <span className="muted">· {ROLES[user.role] || user.role}</span>
                      </div>
                      <Link className="menu-item" to="/me" onClick={() => setMenuOpen(false)}>
                        My profile
                      </Link>
                      {can('listing.manage') && (
                        <Link className="menu-item" to="/mylistings" onClick={() => setMenuOpen(false)}>
                          My listings
                        </Link>
                      )}
                      <Link className="menu-item" to="/favorites" onClick={() => setMenuOpen(false)}>
                        Favourites
                      </Link>
                      <Link className="menu-item" to="/inbox" onClick={() => setMenuOpen(false)}>
                        Inbox
                      </Link>
                      {can('stats.read') && (
                        <Link className="menu-item" to="/admin" onClick={() => setMenuOpen(false)}>
                          Admin dashboard
                        </Link>
                      )}
                      <button className="menu-item" onClick={async () => { setMenuOpen(false); await logout(); navigate('/') }}>
                        Log out
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <Link to="/login" className="nav-link">
                  Log in
                </Link>
                <Link to="/register" className="nav-link nav-link--cta">
                  Sign up
                </Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  )
}