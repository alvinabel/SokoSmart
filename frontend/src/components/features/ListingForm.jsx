import React from 'react'
import { Select, Input, Textarea } from '../ui/Inputs'
import Field from '../ui/Field'
import Button from '../ui/Button'
import { UNITS } from '../../utils/constants'

const EMPTY = {
  title: '',
  description: '',
  category: '',
  price: '',
  unit: 'kg',
  quantity: '',
  quality: '',
  city: '',
  image: '',
  images: [],
}

export default function ListingForm({ initial = {}, categories = [], categoriesLoading = false, onSubmit, submitting = false, submitLabel = 'Publish listing' }) {
  const [form, setForm] = React.useState({ ...EMPTY, ...initial, images: initial.images || [] })
  const [errors, setErrors] = React.useState({})

  const set = (key) => (e) => {
    const value = e.target.value
    setForm((f) => ({ ...f, [key]: value }))
    if (key === 'image' && value) {
      setForm((f) => ({ ...f, images: [...f.images, value.trim()], image: '' }))
    }
  }

  const addImage = () => {
    if (form.image.trim() && !form.images.includes(form.image.trim())) {
      setForm((f) => ({ ...f, images: [...f.images, form.image.trim()], image: '' }))
    }
  }

  const validate = () => {
    const next = {}
    if (!form.title.trim() || form.title.trim().length < 3) next.title = 'A title with 3+ characters is required'
    if (!form.category) next.category = 'Pick a category'
    if (!form.price || Number(form.price) <= 0) next.price = 'Enter a valid price'
    if (!form.quantity || Number(form.quantity) <= 0) next.quantity = 'Enter a valid quantity'
    if (!form.city || form.city.trim().length < 2) next.city = 'Enter a city'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const submit = (e) => {
    e.preventDefault()
    if (!validate()) return
    onSubmit({
      title: form.title.trim(),
      description: form.description.trim(),
      category: form.category,
      price: Number(form.price),
      unit: form.unit,
      quantity: Number(form.quantity),
      quality: form.quality.trim() || null,
      location: { city: form.city.trim() },
      images: form.images,
    })
  }

  return (
    <form onSubmit={submit} className="stack">
      <Field label="Title" htmlFor="title" error={errors.title} hint="Breed/variety + what you're selling">
        <Input id="title" value={form.title} onChange={set('title')} placeholder="E.g. Fresh Watermelon (crate of 10)" />
      </Field>

      <div className="grid grid-2">
        <Field label="Category" htmlFor="category" error={errors.category}>
          <Select id="category" value={form.category} onChange={set('category')} disabled={categoriesLoading}>
            <option value="">Select…</option>
            {(categories.length ? categories : []).map((c) => (
              <option key={c.slug} value={c.slug}>
                {c.emoji} {c.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="City / location" htmlFor="city" error={errors.city}>
          <Input id="city" value={form.city} onChange={set('city')} placeholder="E.g. Kumasi" />
        </Field>
      </div>

      <div className="grid grid-2">
        <Field label="Price" htmlFor="price" error={errors.price}>
          <Input id="price" type="number" step="any" min="0" value={form.price} onChange={set('price')} placeholder="0.00" />
        </Field>
        <Field label="Unit" htmlFor="unit">
          <Select id="unit" value={form.unit} onChange={set('unit')}>
            {UNITS.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
          </Select>
        </Field>
      </div>

      <div className="grid grid-2">
        <Field label="Quantity on hand" htmlFor="quantity" error={errors.quantity}>
          <Input id="quantity" type="number" step="any" min="0" value={form.quantity} onChange={set('quantity')} placeholder="E.g. 40" />
        </Field>
        <Field label="Quality note (optional)" htmlFor="quality">
          <Input id="quality" value={form.quality} onChange={set('quality')} placeholder="Grade A, sun-dried, organic…" />
        </Field>
      </div>

      <Field label="Description" htmlFor="description" hint="Harvest date, packaging, delivery options…">
        <Textarea id="description" value={form.description} onChange={set('description')} />
      </Field>

      <Field label="Photo URL" htmlFor="image" hint="v1 accepts image URLs — swap for upload (S3/Supabase Storage) later">
        <div className="flex">
          <Input id="image" value={form.image} onChange={set('image')} placeholder="https://…/photo.jpg" />
          <Button type="button" variant="outline" onClick={addImage}>
            Add
          </Button>
        </div>
      </Field>

      {form.images.length > 0 && (
        <div className="flex wrap">
          {form.images.map((src, i) => (
            <div key={i} className="flex-between card-pad" style={{ border: '1px solid var(--wm-border)', borderRadius: 8, padding: 6 }}>
              <img src={src} alt="" style={{ width: 48, height: 48, objectFit: 'cover', borderRadius: 6 }} />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setForm((f) => ({ ...f, images: f.images.filter((_, j) => j !== i) }))}
              >
                ✕
              </Button>
            </div>
          ))}
        </div>
      )}

      <div className="flex">
        <Button as="button" type="submit" variant="primary" size="lg" loading={submitting} style={{ flex: 1 }}>
          {submitLabel}
        </Button>
      </div>
    </form>
  )
}