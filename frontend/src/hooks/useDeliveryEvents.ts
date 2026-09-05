import { useEffect, useRef, useState } from 'react'
import type { Deal } from '../types/deal'

export interface DeliveryEvent {
  key: string
  dealId: string
}

// Framer Motion transition durations for the matching sprites — kept here
// so the auto-cleanup timers below stay in sync with what's on screen.
export const DISPATCH_ANIMATION_SECONDS = 6
export const RECEIPT_FLASH_SECONDS = 1.5
export const GUARDRAIL_ALERT_SECONDS = 1.5

/**
 * Turns deal-list polling into one-shot animation events: a receipt flash
 * the instant a deal's invoice is issued, a driver trip the instant a deal
 * reaches `dispatched`, and a siren the instant a deal's first guardrail
 * violation appears. Each deal fires each event at most once, so sitting
 * in a terminal/flagged state across many more polls doesn't replay it.
 */
export function useDeliveryEvents(deals: Deal[]) {
  const [receiptFlashes, setReceiptFlashes] = useState<DeliveryEvent[]>([])
  const [dispatchTrips, setDispatchTrips] = useState<DeliveryEvent[]>([])
  const [guardrailAlerts, setGuardrailAlerts] = useState<DeliveryEvent[]>([])
  const seenReceipt = useRef(new Set<string>())
  const seenDispatch = useRef(new Set<string>())
  const seenGuardrail = useRef(new Set<string>())

  useEffect(() => {
    for (const deal of deals) {
      if (deal.invoice_url && !seenReceipt.current.has(deal.id)) {
        seenReceipt.current.add(deal.id)
        const key = `${deal.id}-receipt`
        setReceiptFlashes((prev) => [...prev, { key, dealId: deal.id }])
        setTimeout(() => {
          setReceiptFlashes((prev) => prev.filter((event) => event.key !== key))
        }, RECEIPT_FLASH_SECONDS * 1000)
      }

      if (deal.status === 'dispatched' && !seenDispatch.current.has(deal.id)) {
        seenDispatch.current.add(deal.id)
        const key = `${deal.id}-dispatch`
        setDispatchTrips((prev) => [...prev, { key, dealId: deal.id }])
        setTimeout(() => {
          setDispatchTrips((prev) => prev.filter((event) => event.key !== key))
        }, DISPATCH_ANIMATION_SECONDS * 1000)
      }

      if (deal.guardrail_violations.length > 0 && !seenGuardrail.current.has(deal.id)) {
        seenGuardrail.current.add(deal.id)
        const key = `${deal.id}-guardrail`
        setGuardrailAlerts((prev) => [...prev, { key, dealId: deal.id }])
        setTimeout(() => {
          setGuardrailAlerts((prev) => prev.filter((event) => event.key !== key))
        }, GUARDRAIL_ALERT_SECONDS * 1000)
      }
    }
  }, [deals])

  return { receiptFlashes, dispatchTrips, guardrailAlerts }
}
