import { useEffect, useState } from 'react'
import { sendChatMessage } from '../api'
import { ChatBubble } from '../components/ChatBubble'
import { ChatComposer } from '../components/ChatComposer'
import { StatusBadge } from '../components/StatusBadge'
import { HospitalAvatar } from '../components/HospitalAvatar'
import { useDeals } from '../hooks/useDeals'

interface Turn {
  from: 'hospital' | 'sauda'
  text: string
  paymentLinkUrl?: string | null
  invoiceUrl?: string | null
}

interface HospitalChatPageProps {
  hospitalId: string
  hospitalName: string
  onLogout: () => void
}

/** What one hospital sees after signing in: only their own thread with Sauda, nothing else. */
export function HospitalChatPage({ hospitalId, hospitalName, onLogout }: HospitalChatPageProps) {
  const [turns, setTurns] = useState<Turn[]>([])
  const [seeded, setSeeded] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const deals = useDeals()

  const deal = deals.find((candidate) => candidate.id === hospitalId) ?? null

  // Seed this tab's transcript from whatever the backend already knows
  // about this hospital (e.g. messages sent from another tab) the first
  // time deals load — only the latest reply is available, not full
  // turn-by-turn history, since that's all DealState keeps server-side.
  useEffect(() => {
    if (seeded || !deal || deal.messages.length === 0) return
    const initial: Turn[] = deal.messages.map((text) => ({ from: 'hospital', text }))
    if (deal.reply) {
      initial.push({ from: 'sauda', text: deal.reply, paymentLinkUrl: deal.payment_link_url, invoiceUrl: deal.invoice_url })
    }
    setTurns(initial)
    setSeeded(true)
  }, [seeded, deal])

  async function handleSend(text: string) {
    setTurns((prev) => [...prev, { from: 'hospital', text }])
    try {
      const result = await sendChatMessage(hospitalId, text)
      const reply = result.reply
      if (reply) {
        setTurns((prev) => [
          ...prev,
          { from: 'sauda', text: reply, paymentLinkUrl: result.payment_link_url, invoiceUrl: result.invoice_url },
        ])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Message failed')
    }
  }

  return (
    <div className="mx-auto flex min-h-svh max-w-md flex-col border-x border-black bg-white">
      <div className="flex items-center justify-between gap-2 border-b border-black px-4 py-3">
        <div className="flex items-center gap-3">
          <HospitalAvatar id={hospitalId} />
          <p className="font-bold">{hospitalName}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={deal?.status ?? null} />
          <button
            type="button"
            data-testid="logout-button"
            onClick={onLogout}
            className="rounded-full border border-black px-3 py-1 text-xs font-bold"
          >
            Sign out
          </button>
        </div>
      </div>
      <div
        data-testid="chat-thread"
        className="flex-1 space-y-3 overflow-y-auto p-4"
        style={{ backgroundColor: 'var(--color-sky-wash)' }}
      >
        {turns.length === 0 && (
          <p className="text-center text-sm text-black/50">Say hello — ask about a product, quantity, or price.</p>
        )}
        {turns.map((turn, index) => (
          <ChatBubble
            key={index}
            from={turn.from}
            text={turn.text}
            paymentLinkUrl={turn.paymentLinkUrl}
            invoiceUrl={turn.invoiceUrl}
          />
        ))}
      </div>
      {error && <p className="px-4 py-2 text-sm font-bold text-red-700">{error}</p>}
      <ChatComposer onSend={handleSend} />
    </div>
  )
}
