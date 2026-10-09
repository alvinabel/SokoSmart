import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { apiErrorMessage } from '../lib/api'
import Field from '../components/ui/Field'
import { Input, Select } from '../components/ui/Inputs'
import Button from '../components/ui/Button'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const next = searchParams.get('next') || '/'
  const [form, setForm] = useState({ name: '', email: '', phone: '', city: '', password: '', role: 'buyer' })
  const [busy, setBusy] = useState(false)
  const [formError, setFormError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setFormError('')
    try {
      await register({
        name: form.name,
        email: form.email,
        phone: form.phone || undefined,
        location: { city: form.city || undefined },
        password: form.password,
        role: form.role,
      })
      navigate(next)
    } catch (err) {
      setFormError(apiErrorMessage(err, 'Registration failed'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container page auth-page">
      <div className="card card-pad">
        <h1 style={{ marginTop: 0 }}>Create your account</h1>
        {formError && <div className="alert alert--danger">{formError}</div>}
        <form onSubmit={submit} className="stack">
          <Field label="Full name" htmlFor="name">
            <Input id="name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </Field>
          <Field label="Email" htmlFor="email">
            <Input id="email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </Field>
          <div className="flex">
            <Field label="Phone (optional)" htmlFor="phone">
              <Input id="phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </Field>
            <Field label="City" htmlFor="city">
              <Input id="city" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
            </Field>
          </div>
          <div className="flex">
            <Field label="I am a…" htmlFor="role">
              <Select id="role" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                <option value="buyer">Buyer</option>
                <option value="seller">Farmer / Seller</option>
              </Select>
            </Field>
            <Field label="Password" htmlFor="password">
              <Input id="password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={8} />
            </Field>
          </div>
          <Button type="submit" variant="primary" block loading={busy} disabled={busy}>
            {busy ? 'Creating…' : 'Sign up'}
          </Button>
        </form>
        <p className="muted">
          Already have an account? <Link to={`/login?next=${encodeURIComponent(next)}`}>Log in</Link>
        </p>
      </div>
    </div>
  )
}