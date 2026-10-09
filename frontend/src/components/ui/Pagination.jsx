export default function Pagination({ page = 1, pages = 1, onChange }) {
  if (pages <= 1) return null
  const go = (p) => onChange?.(Math.min(Math.max(p, 1), pages))
  return (
    <nav className="pagination" aria-label="Pagination">
      <button className="btn btn--sm" onClick={() => go(page - 1)} disabled={page <= 1}>
        Prev
      </button>
      <span className="current">
        Page {page} of {pages}
      </span>
      <button className="btn btn--sm" onClick={() => go(page + 1)} disabled={page >= pages}>
        Next
      </button>
    </nav>
  )
}