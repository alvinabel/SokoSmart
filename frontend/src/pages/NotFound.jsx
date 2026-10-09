import { Link } from 'react-router-dom'
import Button from '../components/ui/Button'

export default function NotFound() {
  return (
    <div className="container page">
      <div className="empty">
        <div className="empty-icon" aria-hidden="true">🍂</div>
        <h1 style={{ fontSize: '3rem', marginBottom: 0 }}>404</h1>
        <h3>This patch is empty</h3>
        <p className="muted">The page you're looking for doesn't exist or was moved.</p>
        <div className="flex-center mt-4">
          <Button as={Link} to="/" variant="primary">
            Back to marketplace
          </Button>
        </div>
      </div>
    </div>
  )
}