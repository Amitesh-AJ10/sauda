import { useState } from 'react'
import { Header } from './components/Header'
import { DealList } from './components/DealList'
import { ConversationPanel } from './components/ConversationPanel'
import { DemoControls } from './components/DemoControls'
import { useDeals } from './hooks/useDeals'

function App() {
  const deals = useDeals()
  const [selectedId, setSelectedId] = useState<string | null>(null)

  // Default to the most recently added deal until the merchant picks one explicitly.
  const effectiveSelectedId = selectedId && deals.some((deal) => deal.id === selectedId)
    ? selectedId
    : deals[deals.length - 1]?.id ?? null

  const selectedDeal = deals.find((deal) => deal.id === effectiveSelectedId) ?? null

  return (
    <div className="min-h-svh">
      <Header />
      <main className="mx-auto grid max-w-6xl gap-6 p-6 lg:grid-cols-[minmax(0,320px)_1fr]">
        <aside className="flex flex-col gap-4">
          <DealList deals={deals} selectedId={effectiveSelectedId} onSelect={setSelectedId} />
          <DemoControls />
        </aside>
        <section>
          <ConversationPanel deal={selectedDeal} />
        </section>
      </main>
    </div>
  )
}

export default App
