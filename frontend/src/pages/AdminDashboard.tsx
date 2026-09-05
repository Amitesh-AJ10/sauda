import { useEffect, useRef, useState } from 'react'
import { Header } from '../components/Header'
import { DealList } from '../components/DealList'
import { ConversationPanel } from '../components/ConversationPanel'
import { useDeals } from '../hooks/useDeals'
import { fetchHospitals } from '../api'

/** The merchant's view: every hospital tile, click one to see its live chat + audit trail. */
export function AdminDashboard() {
  const deals = useDeals()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [hospitalIds, setHospitalIds] = useState<Set<string>>(new Set())
  const [unseenIds, setUnseenIds] = useState<Set<string>>(new Set())
  const lastMessageCount = useRef<Record<string, number>>({})

  useEffect(() => {
    fetchHospitals()
      .then((list) => setHospitalIds(new Set(list.map((hospital) => hospital.id))))
      .catch(() => {
        // Dashboard still works without the chat-open links if this fails.
      })
  }, [])

  // Flag any hospital whose message count grew since we last looked, unless
  // it's the one currently open.
  useEffect(() => {
    setUnseenIds((prev) => {
      let next = prev
      for (const deal of deals) {
        const seenCount = lastMessageCount.current[deal.id] ?? 0
        if (deal.messages.length > seenCount && deal.id !== selectedId) {
          if (next === prev) next = new Set(prev)
          next.add(deal.id)
        }
        lastMessageCount.current[deal.id] = deal.messages.length
      }
      return next
    })
  }, [deals, selectedId])

  function handleSelect(id: string) {
    setSelectedId(id)
    setUnseenIds((prev) => {
      if (!prev.has(id)) return prev
      const next = new Set(prev)
      next.delete(id)
      return next
    })
  }

  // Default to whichever hospital has an actual lead in progress, else the first tile.
  const defaultId = deals.find((deal) => deal.status !== null)?.id ?? deals[0]?.id ?? null
  const effectiveSelectedId = selectedId && deals.some((deal) => deal.id === selectedId) ? selectedId : defaultId
  const selectedDeal = deals.find((deal) => deal.id === effectiveSelectedId) ?? null

  return (
    <div className="min-h-svh">
      <Header />
      <main className="mx-auto grid max-w-6xl gap-6 p-6 lg:grid-cols-[minmax(0,320px)_1fr]">
        <aside className="flex flex-col gap-4">
          <DealList
            deals={deals}
            selectedId={effectiveSelectedId}
            onSelect={handleSelect}
            unseenIds={unseenIds}
            hospitalIds={hospitalIds}
          />
        </aside>
        <section>
          <ConversationPanel deal={selectedDeal} />
        </section>
      </main>
    </div>
  )
}
