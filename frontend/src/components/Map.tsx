import type { Deal } from '../types/deal'
import { hasActiveLead, paymentIndicatorState } from '../types/deal'
import { DispatchSprite } from './DispatchSprite'
import { LeadIndicator } from './LeadIndicator'
import { PaymentIndicator } from './PaymentIndicator'
import { ReceiptFlash } from './ReceiptFlash'
import { useDeliveryEvents } from '../hooks/useDeliveryEvents'

interface MapProps {
  deals: Deal[]
}

/** The merchant's glanceable view: Hospital ↔ road ↔ Godown (STORY.md §7). */
export function Map({ deals }: MapProps) {
  const leadActive = hasActiveLead(deals)
  const paymentState = paymentIndicatorState(deals)
  const { receiptFlashes, dispatchTrips } = useDeliveryEvents(deals)

  return (
    <div className="relative flex w-full max-w-3xl items-center justify-between gap-4 rounded-lg border border-slate-700 bg-slate-900 p-8">
      <div className="relative flex flex-col items-center gap-2">
        <div className="absolute -top-8 h-8">
          <LeadIndicator active={leadActive} />
        </div>
        <span className="text-6xl" aria-hidden="true">
          🏥
        </span>
        <span className="text-sm text-slate-400">Hospital</span>
      </div>

      <div className="relative h-1 flex-1 rounded bg-slate-700">
        <div className="absolute -top-8 left-1/2 h-8 -translate-x-1/2">
          <PaymentIndicator state={paymentState} />
        </div>
        {dispatchTrips.map((trip, index) => (
          <DispatchSprite key={trip.key} laneOffset={-16 - (index % 3) * 20} />
        ))}
      </div>

      <div className="relative flex flex-col items-center gap-2">
        <div className="absolute -top-10 flex h-8 gap-1">
          {receiptFlashes.map((flash) => (
            <ReceiptFlash key={flash.key} />
          ))}
        </div>
        <span className="text-6xl" aria-hidden="true">
          🏭
        </span>
        <span className="text-sm text-slate-400">Godown</span>
      </div>
    </div>
  )
}
