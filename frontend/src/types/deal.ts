// Mirrors backend/app/agent/state.py::DealStatus
export type DealStatus =
  | 'extracting_intent'
  | 'checking_inventory'
  | 'negotiating'
  | 'awaiting_payment'
  | 'paid'
  | 'issuing_invoice'
  | 'dispatched'
  | 'out_of_stock'
  | 'declined'
  | 'invoice_failed'

export interface Deal {
  id: string
  hospital_name: string | null
  item_name: string | null
  qty: number | null
  /** null means this hospital hasn't sent a first message yet. */
  status: DealStatus | null
  payment_link_url: string | null
  invoice_url: string | null
  messages: string[]
  reply: string | null
  guardrail_violations: string[]
  audit_trail: string[]
}

const LEAD_STATUSES: DealStatus[] = ['extracting_intent', 'checking_inventory', 'negotiating']
const PAYMENT_SENT_STATUSES: DealStatus[] = ['awaiting_payment']
const PAYMENT_CONFIRMED_STATUSES: DealStatus[] = ['paid', 'issuing_invoice', 'dispatched']

/** Any deal still being negotiated shows the exclamation mark over the Hospital. */
export function hasActiveLead(deals: Deal[]): boolean {
  return deals.some((deal) => deal.status !== null && LEAD_STATUSES.includes(deal.status))
}

export type PaymentIndicatorState = 'none' | 'sent' | 'confirmed'

/** Payment confirmed takes priority over "link sent" when both exist across deals. */
export function paymentIndicatorState(deals: Deal[]): PaymentIndicatorState {
  if (deals.some((deal) => deal.status !== null && PAYMENT_CONFIRMED_STATUSES.includes(deal.status))) return 'confirmed'
  if (deals.some((deal) => deal.status !== null && PAYMENT_SENT_STATUSES.includes(deal.status))) return 'sent'
  return 'none'
}
