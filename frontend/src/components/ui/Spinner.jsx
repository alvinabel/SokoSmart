export default function Spinner({ size = 'md', center = false }) {
  const spinner = <span className={`spinner ${size === 'lg' ? 'spinner--lg' : ''}`} aria-label="loading" />
  return center ? <div className="center-stage">{spinner}</div> : spinner
}