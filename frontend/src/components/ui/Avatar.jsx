import { initials } from '../../lib/format'

export default function Avatar({ name = '', size = 36, tone = 'var(--wm-deep)' }) {
  return (
    <span className="avatar" style={{ width: size, height: size, background: tone, fontSize: size * 0.4 }}>
      {initials(name) || '?'}
    </span>
  )
}