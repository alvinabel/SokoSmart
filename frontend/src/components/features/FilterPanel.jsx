import { Select, Input } from '../ui/Inputs'
import Field from '../ui/Field'
import Button from '../ui/Button'

const SORTS = [
  { value: 'newest', label: 'Newest first' },
  { value: 'price_asc', label: 'Price: low → high' },
  { value: 'price_desc', label: 'Price: high → low' },
  { value: 'most_viewed', label: 'Most viewed' },
]

export default function FilterPanel({ value, categories = [], onChange, onReset }) {
  const set = (key) => (e) => onChange({ [key]: e.target.value })

  return (
    <aside className="filter-panel">
      <Field label="Category" htmlFor="f-category">
        <Select id="f-category" value={value.category} onChange={set('category')}>
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c.slug} value={c.slug}>
              {c.emoji} {c.name}
            </option>
          ))}
        </Select>
      </Field>

      <Field label="City" htmlFor="f-city">
        <Input id="f-city" value={value.city} onChange={set('city')} placeholder="E.g. Accra" />
      </Field>

      <div className="flex">
        <Field label="Min price" htmlFor="f-min">
          <Input id="f-min" type="number" min="0" value={value.min_price} onChange={set('min_price')} placeholder="0" />
        </Field>
        <Field label="Max price" htmlFor="f-max">
          <Input id="f-max" type="number" min="0" value={value.max_price} onChange={set('max_price')} placeholder="∞" />
        </Field>
      </div>

      <Field label="Sort by" htmlFor="f-sort">
        <Select id="f-sort" value={value.sort} onChange={set('sort')}>
          {SORTS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </Select>
      </Field>

      {onReset && (
        <Button type="button" variant="outline" onClick={onReset}>
          Reset filters
        </Button>
      )}
    </aside>
  )
}