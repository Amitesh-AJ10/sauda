import { useEffect, useState } from 'react'
import { sendChatMessage } from '../api'
import { ChatBubble } from '../components/ChatBubble'
import { ChatComposer } from '../components/ChatComposer'
import { HospitalAvatar } from '../components/HospitalAvatar'
import { STATUS_LABEL } from '../lib/status'
import { doodleBackgroundImage, whatsapp } from '../lib/whatsappTheme'
import { useDeals } from '../hooks/useDeals'

interface Turn {
  from: 'hospital' | 'sauda'
  text: string
  time: string
  paymentLinkUrl?: string | null
  invoiceUrl?: string | null
}

interface HospitalChatPageProps {
  hospitalId: string
  hospitalName: string
  onLogout: () => void
}

function nowTime(): string {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

/** What one hospital sees after signing in: only their own thread with Sauda, styled
 * as a desktop WhatsApp window (warm cream canvas, flat colors, no shadows). */
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
    const initial: Turn[] = deal.messages.map((text) => ({ from: 'hospital', text, time: nowTime() }))
    if (deal.reply) {
      initial.push({
        from: 'sauda',
        text: deal.reply,
        time: nowTime(),
        paymentLinkUrl: deal.payment_link_url,
        invoiceUrl: deal.invoice_url,
      })
    }
    setTurns(initial)
    setSeeded(true)
  }, [seeded, deal])

  async function handleSend(text: string) {
    setTurns((prev) => [...prev, { from: 'hospital', text, time: nowTime() }])
    try {
      const result = await sendChatMessage(hospitalId, text)
      const reply = result.reply
      if (reply) {
        setTurns((prev) => [
          ...prev,
          { from: 'sauda', text: reply, time: nowTime(), paymentLinkUrl: result.payment_link_url, invoiceUrl: result.invoice_url },
        ])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Message failed')
    }
  }

  return (
    <div className="mx-auto flex min-h-svh max-w-md flex-col">
      <div
        className="flex items-center justify-between gap-2 border-b px-4 py-3"
        style={{ backgroundColor: whatsapp.paperWhite, borderColor: whatsapp.paleBlueWash }}
      >
        <div className="flex items-center gap-3">
          <HospitalAvatar id={hospitalId} size={40} />
          <div>
            <p className="text-base font-bold" style={{ color: whatsapp.inkBlack }}>
              {hospitalName}
            </p>
            {deal?.status && (
              <p className="text-xs" style={{ color: whatsapp.warmGray }}>
                {STATUS_LABEL[deal.status]}
              </p>
            )}
          </div>
        </div>
        <button
          type="button"
          data-testid="logout-button"
          onClick={onLogout}
          className="text-xs font-bold underline"
          style={{ color: whatsapp.inkBlack }}
        >
          Sign out
        </button>
      </div>

      <div
        data-testid="chat-thread"
        className="flex-1 space-y-2 overflow-y-auto p-4"
        style={{
          backgroundColor: whatsapp.creamCanvas,
          backgroundImage: doodleBackgroundImage,
          backgroundSize: '140px 140px',
        }}
      >
        {turns.length === 0 && (
          <p className="text-center text-sm" style={{ color: whatsapp.warmGray }}>
            Say hello — ask about a product, quantity, or price.
          </p>
        )}
        {turns.map((turn, index) => (
          <ChatBubble
            key={index}
            from={turn.from}
            text={turn.text}
            time={turn.time}
            paymentLinkUrl={turn.paymentLinkUrl}
            invoiceUrl={turn.invoiceUrl}
          />
        ))}
      </div>

      {error && (
        <p className="px-4 py-2 text-sm font-bold text-red-700" style={{ backgroundColor: whatsapp.paperWhite }}>
          {error}
        </p>
      )}
      <ChatComposer onSend={handleSend} />
    </div>
  )
}
