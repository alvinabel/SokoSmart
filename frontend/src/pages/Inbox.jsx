import { useCallback, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { marketApi } from '../lib/api'
import { apiErrorMessage } from '../lib/api'
import { useToast } from '../lib/toast'
import { relativeTime } from '../lib/format'
import Avatar from '../components/ui/Avatar'
import Spinner from '../components/ui/Spinner'
import ChatWindow from '../components/features/ChatWindow'
import EmptyState from '../components/ui/EmptyState'

export default function Inbox() {
  const { error } = useToast()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeId = searchParams.get('with')
  const listingId = searchParams.get('listing')

  const [conversations, setConversations] = useState([])
  const [users, setUsers] = useState({})
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const timer = useRef(null)

  const loadConversations = useCallback(async () => {
    try {
      const { data } = await marketApi.get('/api/v1/messages')
      const list = data.items || []
      setConversations(list)
      const map = {}
      list.forEach((c) => {
        if (c.with?.id) map[c.with.id] = c.with
      })
      setUsers((prev) => ({ ...prev, ...map }))
    } catch {
      /* ignore */
    }
  }, [])

  useEffect(() => {
    let mounted = true
    loadConversations().finally(() => mounted && setLoading(false))
    return () => {
      mounted = false
    }
  }, [loadConversations])

  const loadThread = useCallback(
    async (otherId) => {
      try {
        const { data } = await marketApi.get(`/api/v1/messages/${otherId}`)
        setMessages(data.items || [])
        if (data.with?.id) setUsers((prev) => ({ ...prev, [data.with.id]: data.with }))
        loadConversations()
      } catch (err) {
        error(apiErrorMessage(err))
      }
    },
    [error, loadConversations],
  )

  useEffect(() => {
    if (!activeId) return
    loadThread(activeId)
    timer.current = setInterval(() => loadThread(activeId), 5000)
    return () => clearInterval(timer.current)
  }, [activeId, loadThread])

  const selectThread = (otherId) => {
    setSearchParams({ with: otherId }, { replace: true })
  }

  const send = async (body) => {
    if (!activeId) return
    setSending(true)
    try {
      await marketApi.post(`/api/v1/messages/${activeId}`, { body, listing_id: listingId || null })
      await loadThread(activeId)
    } catch (err) {
      error(apiErrorMessage(err))
    } finally {
      setSending(false)
    }
  }

  const other = users[activeId]

  return (
    <div className="container page">
      <h1 style={{ marginTop: 0 }}>Inbox</h1>

      <div className="chat-layout">
        <aside className="card">
          <div className="card-pad" style={{ borderBottom: '1px solid var(--wm-border)' }}>
            <strong>Conversations</strong>
          </div>
          {conversations.length === 0 && !loading && (
            <div className="card-pad muted">No conversations yet. Chat with a seller from any listing to start one.</div>
          )}
          {conversations.map((c) => {
            const name = c.with?.name || '…'
            return (
              <button key={c.with?.id} className={`convo ${activeId === c.with?.id ? 'active' : ''}`} onClick={() => selectThread(c.with.id)}>
                <Avatar name={name} size={34} />
                <span className="convo-body">
                  <strong>{name}</strong>
                  <span className="muted">{c.last_message}</span>
                  <span className="muted" style={{ fontSize: 'var(--fs-xs)' }}>{relativeTime(c.last_at)}</span>
                </span>
                {c.unread > 0 && <span className="bell-dot">{c.unread}</span>}
              </button>
            )
          })}
        </aside>

        <section className="card">
          {loading ? (
            <Spinner center />
          ) : activeId && other ? (
            <ChatWindow other={other} messages={messages} onSend={send} sending={sending} onBack={() => setSearchParams({}, { replace: true })} />
          ) : (
            <EmptyState icon="💬" title="Pick a conversation" message="Select a thread on the left to start messaging." />
          )}
        </section>
      </div>
    </div>
  )
}