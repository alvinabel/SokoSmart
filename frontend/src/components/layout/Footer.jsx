import { Link } from 'react-router-dom'
import { APP_NAME } from '../../config'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-grid">
          <div>
            <div className="brand" style={{ color: '#fff' }}>
              <span aria-hidden="true">🍉</span> {APP_NAME}
            </div>
            <p style={{ fontSize: 'var(--fs-sm)' }}>
              Buy and sell fresh farm produce directly — farmers to market, no middlemen.
            </p>
          </div>
          <div>
            <strong>Marketplace</strong>
            <p>
              <Link to="/listings">Browse produce</Link>
              <br />
              <Link to="/listings?category=fruits">Fruits</Link> · <Link to="/listings?category=vegetables">Vegetables</Link> ·{' '}
              <Link to="/listings?category=livestock">Livestock</Link>
            </p>
          </div>
          <div>
            <strong>Account</strong>
            <p>
              <Link to="/login">Log in</Link>
              <br />
              <Link to="/register">Create account</Link>
            </p>
          </div>
          <div>
            <strong>PWA</strong>
            <p style={{ fontSize: 'var(--fs-sm)' }}>
              Installable · offline-ready · install from your browser menu and shop on the go.
            </p>
          </div>
        </div>
        <div className="footer-bottom">© {new Date().getFullYear()} {APP_NAME} · Made for farmers &amp; markets 🚜</div>
      </div>
    </footer>
  )
}