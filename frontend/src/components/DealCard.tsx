import type { Deal } from '../types/deal'
import { StatusBadge } from './StatusBadge'
import { HospitalAvatar } from './HospitalAvatar'

interface DealCardProps {
  deal: Deal
  selected: boolean
  onSelect: () => void
  /** Whether this hospital has an update the merchant hasn't looked at yet. */
  hasAlert?: boolean
  /** True when this id is a real hospital with its own chat page to open. */
  canOpenChat?: boolean
}

/** One row in the deal list — hospital, item, status, click to open the conversation. */
export function DealCard({ deal, selected, onSelect, hasAlert = false, canOpenChat = false }: DealCardProps) {
  const lastMessage = deal.messages[deal.messages.length - 1] ?? 'No messages yet.'

  return (
    <div
      data-testid="deal-card"
      className="relative w-full rounded-[20px] border border-black p-4 text-left transition"
      style={{ backgroundColor: selected ? 'var(--color-lavender)' : 'var(--color-paper)' }}
    >
      {hasAlert && (
        <span
          data-testid="deal-card-alert"
          aria-hidden="true"
          className="absolute top-3 right-3 h-2.5 w-2.5 animate-pulse rounded-full border border-black"
          style={{ backgroundColor: 'var(--color-ember)' }}
        />
      )}
      <button type="button" onClick={onSelect} aria-pressed={selected} className="w-full text-left">
        <div className="flex items-start justify-between gap-2 pr-4">
          <div className="flex min-w-0 items-center gap-3">
            <HospitalAvatar id={deal.id} />
            <div className="min-w-0">
              <p className="truncate font-bold">{deal.hospital_name ?? 'Unknown hospital'}</p>
              <p className="truncate text-sm text-black/70">
                {deal.qty ?? '?'} × {deal.item_name ?? 'item pending'}
              </p>
            </div>
          </div>
          <StatusBadge status={deal.status} />
        </div>
        <p className="mt-2 truncate text-sm text-black/60">{lastMessage}</p>
      </button>
      {canOpenChat && (
        <a
          data-testid="open-hospital-chat"
          href={`/hospital/${deal.id}`}
          target="_blank"
          rel="noreferrer"
          className="mt-2 inline-block text-xs font-bold underline"
        >
          Open hospital's chat ↗
        </a>
      )}
    </div>
  )
}
