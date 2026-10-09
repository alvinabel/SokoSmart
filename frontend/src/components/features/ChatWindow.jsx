import { useAuth } from '../../lib/auth'
import Avatar from '../ui/Avatar'

export default function ChatWindow({ other, messages = [], onSend, sending, onBack }) {
  const { user } = useAuth()

  const submit = (e) => {
    e.preventDefault()
    const input = e.currentTarget.elements.body
    const body = input.value.trim()
    if (!body) return
    onSend(body)
    input.value = ''
  }

  return (
    <div className="chat-window">
      <div className="flex-between" style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--wm-border)' }}>
        <div className="flex" style={{ alignItems: 'center' }}>
          {onBack && (
            <button className="btn btn--ghost btn--sm" onClick={onBack} aria-label="Back">
              ←
            </button>
          )}
          <Avatar name={other?.name} size={32} />
          <strong>{other?.name || 'Conversation'}</strong>
        </div>
      </div>

      <div className="chat-scroll">
        {messages.length === 0 && <p className="muted">No messages yet. Say hello 👋</p>}
        {messages.map((m) => (
          <div key={m.id} className={`bubble ${m.sender === user?.id ? 'bubble--me' : 'bubble--them'}`}>
            {m.body}
          </div>
        ))}
      </div>

      <form className="chat-input" onSubmit={submit}>
        <input className="input" name="body" placeholder="Write a message…" autoComplete="off" />
        <button className="btn btn--primary" type="submit" disabled={sending}>
          Send
        </button>
      </form>
    </div>
  )
}