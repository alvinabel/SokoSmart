import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { useToast } from '../lib/toast'
import { apiErrorMessage } from '../lib/api'
import Field from '../components/ui/Field'
import { Input } from '../components/ui/Inputs'
import Button from '../components/ui/Button'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const { success, error } = useToast()
  const [searchParams] = useSearchParams()
  const next = searchParams.get('next') || '/'
  const [form, setForm] = useState({ email: '', password: '' })
  const [busy, setBusy] = useState(false)
  const [formError, setFormError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setFormError('')
    try {
      await login(form.email, form.password)
      success('Welcome back!')
      navigate(next)
    } catch (err) {
      setFormError(apiErrorMessage(err, 'Login failed'))
      error(formError)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container page auth-page">
      <div className="card card-pad">
        <h1 style={{ marginTop: 0 }}>Log in</h1>
        {formError && <div className="alert alert--danger">{formError}</div>}
        <form onSubmit={submit} className="stack">
          <Field label="Email" htmlFor="email">
            <Input id="email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </Field>
          <Field label="Password" htmlFor="password">
            <Input id="password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          </Field>
          <Button type="submit" variant="primary" block loading={busy}>
            Log in
          </Button>
        </form>
        <p className="muted">
          New here? <Link to={`/register?next=${encodeURIComponent(next)}`}>Create an account</Link>
        </p>
      </div>
    </div>
  )
}