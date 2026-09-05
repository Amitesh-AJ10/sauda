import type { DealStatus } from '../types/deal'
import { PIPELINE_STATUSES, STATUS_LABEL, isErrorStatus } from '../lib/status'

interface StatusStepperProps {
  status: DealStatus | null
}

/** Horizontal step tracker for the happy-path pipeline; collapses to a single flagged step on error. */
export function StatusStepper({ status }: StatusStepperProps) {
  if (status === null) {
    return (
      <p data-testid="status-stepper" className="text-sm text-black/50">
        Waiting for the first message…
      </p>
    )
  }

  if (isErrorStatus(status)) {
    return (
      <div data-testid="status-stepper" className="flex items-center gap-2 text-sm font-bold text-black">
        <span
          className="flex h-6 w-6 items-center justify-center rounded-full border border-black text-xs"
          style={{ backgroundColor: 'var(--color-ember)' }}
        >
          ⚠
        </span>
        {STATUS_LABEL[status]}
      </div>
    )
  }

  const currentIndex = PIPELINE_STATUSES.indexOf(status)

  return (
    <ol data-testid="status-stepper" className="flex flex-wrap items-center gap-x-1 gap-y-2">
      {PIPELINE_STATUSES.map((step, index) => {
        const done = index < currentIndex
        const active = index === currentIndex
        return (
          <li key={step} className="flex items-center gap-1">
            <span
              data-testid={`stepper-step-${step}`}
              data-active={active}
              className="flex items-center gap-1.5 rounded-full border border-black px-2.5 py-1 text-[11px] font-bold whitespace-nowrap"
              style={{
                backgroundColor: done || active ? 'var(--color-mint-pop)' : 'var(--color-paper)',
                opacity: done || active ? 1 : 0.5,
              }}
            >
              {STATUS_LABEL[step]}
            </span>
            {index < PIPELINE_STATUSES.length - 1 && (
              <span aria-hidden="true" className="text-black/40">
                →
              </span>
            )}
          </li>
        )
      })}
    </ol>
  )
}
