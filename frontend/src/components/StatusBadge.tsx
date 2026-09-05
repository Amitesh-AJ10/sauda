import type { DealStatus } from '../types/deal'
import { STATUS_ACCENT, STATUS_LABEL, isErrorStatus } from '../lib/status'

interface StatusBadgeProps {
  status: DealStatus
}

/** Pill badge naming a deal's current stage, colored per lib/status.ts. */
export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span
      data-testid="status-badge"
      className="inline-flex items-center gap-1.5 rounded-full border border-black px-3 py-1 text-xs font-bold"
      style={{ backgroundColor: STATUS_ACCENT[status] }}
    >
      {isErrorStatus(status) && <span aria-hidden="true">⚠</span>}
      {STATUS_LABEL[status]}
    </span>
  )
}
