import { useEffect, useState } from 'react'
import { marketApi } from '../../lib/api'
import { apiErrorMessage } from '../../lib/api'
import Button from '../../components/ui/Button'
import { Input } from '../../components/ui/Inputs'
import Field from '../../components/ui/Field'
import { useToast } from '../../lib/toast'

const GLYPHS = ['🌾', '🌽', '🥕', '🥬', '🍅', '🥔', '🧅', '🍌', '🥭', '🍊', '🐂', '🐔', '🐟', '🥚', '🍯', '🌰']

const toSlug = (value) =>
  value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')

export default function Categories() {
  const [items, setItems] = useState([])
  const [name, setName] = useState('')
  const [emoji, setEmoji] = useState('🌾')
  const [editingId, setEditingId] = useState(null)
  const { success, error } = useToast()

  const load = () =>
    marketApi
      .get('/api/v1/categories')
      .then((res) => setItems(res.data.items || []))
      .catch((err) => error(apiErrorMessage(err)))

  useEffect(() => {
    load()
  }, [])

  const submit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    try {
      if (editingId) {
        await marketApi.patch(`/api/v1/categories/${editingId}`, { name: name.trim(), emoji })
        success('Category updated')
      } else {
        await marketApi.post('/api/v1/categories', { slug: toSlug(name), name: name.trim(), emoji })
        success('Category created')
      }
      setName('')
      setEmoji('🌾')
      setEditingId(null)
      load()
    } catch (err) {
      error(apiErrorMessage(err))
    }
  }

  const remove = async (slug) => {
    if (!window.confirm('Delete this category? Listings inside it will keep their current label.')) return
    try {
      await marketApi.delete(`/api/v1/categories/${slug}`)
      success('Category deleted')
      load()
    } catch (err) {
      error(apiErrorMessage(err))
    }
  }

  return (
    <div className="stack">
      <h1 style={{ marginTop: 0 }}>Categories</h1>

      <form onSubmit={submit} className="card card-pad flex wrap" style={{ gap: 'var(--space-3)' }}>
        <Field label={editingId ? 'Rename category' : 'New category'} htmlFor="cat-name">
          <Input id="cat-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Dairy & eggs" />
        </Field>
        <Field label="Icon" htmlFor="cat-emoji">
          <select id="cat-emoji" className="select" value={emoji} onChange={(e) => setEmoji(e.target.value)}>
            {GLYPHS.map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        </Field>
        <Button type="submit" variant="primary" style={{ alignSelf: 'flex-end' }}>
          {editingId ? 'Save' : 'Add'}
        </Button>
        {editingId && (
          <Button type="button" variant="ghost" style={{ alignSelf: 'flex-end' }} onClick={() => { setEditingId(null); setName(''); setEmoji('🌾') }}>
            Cancel
          </Button>
        )}
      </form>

      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))' }}>
        {items.map((c) => (
          <div key={c.id} className="card card-pad">
            <div className="flex-between">
              <div className="flex" style={{ alignItems: 'center' }}>
                <span style={{ fontSize: '1.6rem' }}>{c.emoji}</span>
                <strong>{c.name}</strong>
              </div>
              <div className="flex">
                <Button size="sm" variant="ghost" onClick={() => { setEditingId(c.slug); setName(c.name); setEmoji(c.emoji || '🌾') }}>
                  Edit
                </Button>
                <Button size="sm" variant="ghost" onClick={() => remove(c.slug)} style={{ color: 'var(--wm-danger)' }}>
                  Delete
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}