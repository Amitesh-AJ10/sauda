import { useState, type FormEvent } from 'react'
import { whatsapp } from '../lib/whatsappTheme'
import { AttachIcon, MicIcon, SendIcon } from './ChatIcons'

interface ChatComposerProps {
  onSend: (text: string) => Promise<void> | void
  disabled?: boolean
}

/** WhatsApp-style composer: pill input on pale-blue wash, mic/attach glyphs, green send button. */
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
    <form
      onSubmit={handleSubmit}
      className="flex items-center gap-2 border-t px-3 py-2"
      style={{ backgroundColor: whatsapp.paperWhite, borderColor: whatsapp.paleBlueWash }}
    >
      <button type="button" aria-label="Attach" className="shrink-0 p-1" tabIndex={-1}>
        <AttachIcon color={whatsapp.inkBlack} />
      </button>
      <div
        className="flex flex-1 items-center gap-2 px-4 py-2"
        style={{ backgroundColor: whatsapp.paleBlueWash, borderRadius: '50px' }}
      >
        <input
          data-testid="chat-input"
          value={text}
          onChange={(event) => setText(event.target.value)}
          disabled={disabled || sending}
          placeholder="Type as the hospital…"
          className="flex-1 bg-transparent text-sm outline-none disabled:opacity-50"
          style={{ color: whatsapp.inkBlack }}
        />
        <button type="button" aria-label="Voice message" className="shrink-0" tabIndex={-1}>
          <MicIcon color={whatsapp.inkBlack} />
        </button>
      </div>
      <button
        type="submit"
        data-testid="chat-send"
        aria-label="Send"
        disabled={disabled || sending || text.trim().length === 0}
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full disabled:opacity-50"
        style={{ backgroundColor: whatsapp.accentGreen }}
      >
        <SendIcon />
      </button>
    </form>
  )
}
