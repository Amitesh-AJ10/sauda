import type { Deal } from '../types/deal'
import { DealCard } from './DealCard'

interface DealListProps {
  deals: Deal[]
  selectedId: string | null
  onSelect: (id: string) => void
  /** Ids with an update the merchant hasn't looked at yet. */
  unseenIds?: Set<string>
  /** Ids that have their own hospital chat page (the hardcoded directory). */
  hospitalIds?: Set<string>
}

/** Sidebar list of every in-flight/closed deal, most recent first. */
export function DealList({ deals, selectedId, onSelect, unseenIds, hospitalIds }: DealListProps) {
  if (deals.length === 0) {
    return (
      <p data-testid="deal-list-empty" className="rounded-[20px] border border-black bg-white p-4 text-sm text-black/60">
        No leads yet. Waiting for the first message…
      </p>
    )
  }

  return (
    <div data-testid="deal-list" className="flex flex-col gap-3">
      {deals.map((deal) => (
        <DealCard
          key={deal.id}
          deal={deal}
          selected={deal.id === selectedId}
          onSelect={() => onSelect(deal.id)}
          hasAlert={unseenIds?.has(deal.id) ?? false}
          canOpenChat={hospitalIds?.has(deal.id) ?? false}
        />
      ))}
    </div>
  )
}
