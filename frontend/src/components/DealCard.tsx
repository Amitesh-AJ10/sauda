import type { Deal } from '../types/deal'
import { StatusBadge } from './StatusBadge'

interface DealCardProps {
  deal: Deal
  selected: boolean
  onSelect: () => void
}

/** One row in the deal list — hospital, item, status, click to open the conversation. */
export function DealCard({ deal, selected, onSelect }: DealCardProps) {
  const lastMessage = deal.messages[deal.messages.length - 1] ?? 'No messages yet.'

  return (
    <button
      type="button"
      data-testid="deal-card"
      onClick={onSelect}
      aria-pressed={selected}
      className="w-full rounded-[20px] border border-black bg-white p-4 text-left transition"
      style={{ backgroundColor: selected ? 'var(--color-lavender)' : 'var(--color-paper)' }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-bold">{deal.hospital_name ?? 'Unknown hospital'}</p>
          <p className="truncate text-sm text-black/70">
            {deal.qty ?? '?'} × {deal.item_name ?? 'item pending'}
          </p>
        </div>
        <StatusBadge status={deal.status} />
      </div>
      <p className="mt-2 truncate text-sm text-black/60">{lastMessage}</p>
    </button>
  )
}
