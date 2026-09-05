import type { Deal } from '../types/deal'
import { hasActiveLead, paymentIndicatorState } from '../types/deal'
import { useDeliveryEvents } from '../hooks/useDeliveryEvents'
import { DemoControls } from './DemoControls'
import { DialogueBox } from './DialogueBox'
import { DispatchSprite } from './DispatchSprite'
import { GuardrailAlert } from './GuardrailAlert'
import { LeadIndicator } from './LeadIndicator'
import { PaymentIndicator } from './PaymentIndicator'
import { ReceiptFlash } from './ReceiptFlash'
import { TitleCard } from './TitleCard'

interface MapProps {
  deals: Deal[]
}

// Purely decorative scenery — aria-hidden, no semantics to test.
const TREE_POSITIONS = [
  { left: '4%', top: '18%' },
  { left: '9%', top: '62%' },
  { left: '20%', top: '8%' },
  { left: '30%', top: '70%' },
  { left: '70%', top: '10%' },
  { left: '80%', top: '68%' },
  { left: '92%', top: '30%' },
  { left: '95%', top: '75%' },
]

/** The merchant's glanceable view: Hospital ↔ road ↔ Godown (STORY.md §7). */
export function Map({ deals }: MapProps) {
  const leadActive = hasActiveLead(deals)
  const paymentState = paymentIndicatorState(deals)
  const { receiptFlashes, dispatchTrips, guardrailAlerts } = useDeliveryEvents(deals)
  const activeDeal = deals.length > 0 ? deals[deals.length - 1] : null

  return (
    <div className="relative w-full max-w-5xl overflow-hidden rounded-none border-4 border-black bg-emerald-700 p-4 shadow-[8px_8px_0_0_#000]">
      {/* scenery — sits behind everything else (z-0), never competes for layout space */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 z-0">
        {TREE_POSITIONS.map((pos, i) => (
          <img
            key={i}
            src="/assets/sprites/tree.png"
            alt=""
            className="absolute h-10 w-10 select-none opacity-90"
            style={{ ...pos, imageRendering: 'pixelated' }}
          />
        ))}
      </div>

      {/* Everything below is real document flow, not floating boxes — nothing overlaps
          regardless of how tall DemoControls or the dialogue box get. */}
      <div className="relative z-10 flex flex-col gap-6">
        <div className="flex items-start justify-between gap-4">
          <TitleCard />
          <DemoControls />
        </div>

        <div className="flex items-center justify-between gap-4">
          {/* Hospital */}
          <div className="relative flex flex-col items-center gap-2">
            <div className="absolute -top-10 flex h-8 gap-1">
              <LeadIndicator active={leadActive} />
              <PaymentIndicator state={paymentState} />
            </div>
            <div className="rounded-none border-4 border-black bg-white px-6 py-8 text-center shadow-[4px_4px_0_0_#000]">
              <img
                src="/assets/buildings/hospital.png"
                alt="Hospital"
                className="mx-auto h-16 w-16"
                style={{ imageRendering: 'pixelated' }}
              />
              <p className="mt-2 font-pixel text-[9px] text-slate-800">HOSPITAL</p>
            </div>
          </div>

          {/* Road */}
          <div className="relative h-2 flex-1 self-center bg-slate-700">
            <div
              aria-hidden="true"
              className="absolute inset-0 bg-[repeating-linear-gradient(90deg,#fbbf24_0_24px,transparent_24px_48px)]"
            />
            {dispatchTrips.map((trip, index) => (
              <DispatchSprite key={trip.key} laneOffset={-16 - (index % 3) * 20} />
            ))}
          </div>

          {/* Godown / Sauda HQ */}
          <div className="relative flex flex-col items-center gap-2">
            <div className="absolute -top-10 flex h-8 gap-1">
              {receiptFlashes.map((flash) => (
                <ReceiptFlash key={flash.key} />
              ))}
              {guardrailAlerts.map((alert) => (
                <GuardrailAlert key={alert.key} />
              ))}
            </div>
            <div className="rounded-none border-4 border-black bg-amber-100 px-6 py-8 text-center shadow-[4px_4px_0_0_#000]">
              <img
                src="/assets/buildings/godown.png"
                alt="Sauda HQ warehouse"
                className="mx-auto h-16 w-16"
                style={{ imageRendering: 'pixelated' }}
              />
              <p className="mt-2 font-pixel text-[9px] text-slate-800">SAUDA HQ</p>
            </div>
          </div>
        </div>

        <DialogueBox deal={activeDeal} />

        <div className="flex items-center justify-between font-pixel text-[8px] text-emerald-950">
          <span>BUILT FOR A HEALTHIER TOMORROW</span>
          <span>SAUDA v0.1</span>
        </div>
      </div>
    </div>
  )
}
