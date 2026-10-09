import { Link } from 'react-router-dom'

export default function CategoryChips({ categories = [], value = '', onChange }) {
  const chips = [
    { slug: '', name: 'All', emoji: '🛒' },
    ...(categories.length ? categories : [{ slug: '', name: '…', emoji: '' }]),
  ]

  const render = (chip, active) => (
    <button
      key={chip.slug || `all-${active ? 1 : 0}`}
      className={`category-chip ${value === chip.slug ? 'active' : ''}`}
      onClick={() => onChange(chip.slug)}
    >
      <span aria-hidden="true">{chip.emoji}</span>
      {chip.name}
    </button>
  )

  return (
    <div className="category-chips" role="tablist">
      {onChange ? chips.map((chip) => render(chip, value === chip.slug)) : chips.map((chip) => (
        <Link key={chip.slug} to={`/listings?category=${chip.slug}`} className={`category-chip ${value === chip.slug ? 'active' : ''}`}>
          <span aria-hidden="true">{chip.emoji}</span>
          {chip.name}
        </Link>
      ))}
    </div>
  )
}