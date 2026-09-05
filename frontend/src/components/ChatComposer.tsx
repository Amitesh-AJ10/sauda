import { useState, type FormEvent } from 'react'

interface ChatComposerProps {
  onSend: (text: string) => Promise<void> | void
  disabled?: boolean
}

/** Text box + send button — typing as the hospital buyer. */
export function ChatComposer({ onSend, disabled = false }: ChatComposerProps) {
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = text.trim()
    if (!trimmed || sending) return
    setSending(true)
    try {
      await onSend(trimmed)
      setText('')
    } finally {
      setSending(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 border-t border-black bg-white p-3">
      <input
        data-testid="chat-input"
        value={text}
        onChange={(event) => setText(event.target.value)}
        disabled={disabled || sending}
        placeholder="Type as the hospital…"
        className="flex-1 rounded-full border border-black px-4 py-2 text-sm disabled:opacity-50"
      />
      <button
        type="submit"
        data-testid="chat-send"
        disabled={disabled || sending || text.trim().length === 0}
        className="rounded-full border border-black bg-black px-4 py-2 text-sm font-bold text-white disabled:opacity-50"
      >
        {sending ? 'Sending…' : 'Send'}
      </button>
    </form>
  )
}
