import { useEffect, useState } from 'react'
import { fetchHospitals, sendChatMessage, type Hospital } from '../api'
import { HospitalSwitcher } from '../components/HospitalSwitcher'
import { ChatBubble } from '../components/ChatBubble'
import { ChatComposer } from '../components/ChatComposer'
import { StatusBadge } from '../components/StatusBadge'
import { useDeals } from '../hooks/useDeals'

interface Turn {
  from: 'hospital' | 'sauda'
  text: string
  paymentLinkUrl?: string | null
  invoiceUrl?: string | null
}

interface HospitalChatPageProps {
  initialHospitalId: string | null
}

/** What one hospital sees: their own WhatsApp-style thread with Sauda, nothing else. */
export function HospitalChatPage({ initialHospitalId }: HospitalChatPageProps) {
  const [hospitals, setHospitals] = useState<Hospital[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(initialHospitalId)
  const [turnsByHospital, setTurnsByHospital] = useState<Record<string, Turn[]>>({})
  const [error, setError] = useState<string | null>(null)
  const deals = useDeals()

  useEffect(() => {
    fetchHospitals()
      .then((list) => {
        setHospitals(list)
        setSelectedId((current) => current ?? list[0]?.id ?? null)
      })
      .catch(() => setError('Could not load the hospital directory.'))
  }, [])

  const deal = deals.find((candidate) => candidate.id === selectedId) ?? null

  // Seed this tab's transcript from whatever the backend already knows about
  // this hospital (e.g. messages sent from another tab) the first time we
  // open it — only the latest reply is available, not full turn-by-turn
  // history, since that's all DealState keeps server-side.
  useEffect(() => {
    if (!selectedId || turnsByHospital[selectedId] || !deal || deal.messages.length === 0) return
    const seeded: Turn[] = deal.messages.map((text) => ({ from: 'hospital', text }))
    if (deal.reply) {
      seeded.push({
        from: 'sauda',
        text: deal.reply,
        paymentLinkUrl: deal.payment_link_url,
        invoiceUrl: deal.invoice_url,
      })
    }
    setTurnsByHospital((prev) => ({ ...prev, [selectedId]: seeded }))
  }, [selectedId, deal, turnsByHospital])

  const turns = selectedId ? turnsByHospital[selectedId] ?? [] : []

  async function handleSend(text: string) {
    if (!selectedId) return
    const hospitalId = selectedId
    setTurnsByHospital((prev) => ({
      ...prev,
      [hospitalId]: [...(prev[hospitalId] ?? []), { from: 'hospital', text }],
    }))
    try {
      const result = await sendChatMessage(hospitalId, text)
      setTurnsByHospital((prev) => ({
        ...prev,
        [hospitalId]: [
          ...(prev[hospitalId] ?? []),
          ...(result.reply
            ? [
                {
                  from: 'sauda' as const,
                  text: result.reply,
                  paymentLinkUrl: result.payment_link_url,
                  invoiceUrl: result.invoice_url,
                },
              ]
            : []),
        ],
      }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Message failed')
    }
  }

  return (
    <div className="mx-auto flex min-h-svh max-w-md flex-col border-x border-black bg-white">
      <HospitalSwitcher hospitals={hospitals} selectedId={selectedId} onSelect={setSelectedId} />
      {selectedId && (
        <div className="flex items-center justify-between border-b border-black px-4 py-2">
          <p className="font-bold">{hospitals.find((h) => h.id === selectedId)?.name}</p>
          <StatusBadge status={deal?.status ?? null} />
        </div>
      )}
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
      <ChatComposer onSend={handleSend} disabled={!selectedId} />
    </div>
  )
}
