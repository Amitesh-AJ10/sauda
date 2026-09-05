import type { DealStatus } from '../types/deal'

/** Ordered happy-path pipeline shown in the stepper. Terminal error states branch off it. */
export const PIPELINE_STATUSES: DealStatus[] = [
  'extracting_intent',
  'checking_inventory',
  'negotiating',
  'awaiting_payment',
  'paid',
  'issuing_invoice',
  'dispatched',
]

export const ERROR_STATUSES: DealStatus[] = ['out_of_stock', 'declined', 'invoice_failed']

export const STATUS_LABEL: Record<DealStatus, string> = {
  extracting_intent: 'Reading message',
  checking_inventory: 'Checking stock',
  negotiating: 'Negotiating',
  awaiting_payment: 'Awaiting payment',
  paid: 'Paid',
  issuing_invoice: 'Issuing invoice',
  dispatched: 'Dispatched',
  out_of_stock: 'Out of stock',
  declined: 'Declined',
  invoice_failed: 'Invoice failed',
}

/** Pastel accent token per status, drawn from DESIGN.md's sticker palette. */
export const STATUS_ACCENT: Record<DealStatus, string> = {
  extracting_intent: 'var(--color-lavender)',
  checking_inventory: 'var(--color-lavender)',
  negotiating: 'var(--color-electric-blue)',
  awaiting_payment: 'var(--color-sunburst)',
  paid: 'var(--color-mint-pop)',
  issuing_invoice: 'var(--color-mint-pop)',
  dispatched: 'var(--color-mint-pop)',
  out_of_stock: 'var(--color-ember)',
  declined: 'var(--color-ember)',
  invoice_failed: 'var(--color-ember)',
}

export function isErrorStatus(status: DealStatus): boolean {
  return ERROR_STATUSES.includes(status)
}

/** Step index of `status` on the happy-path pipeline, or -1 for a terminal error state. */
export function pipelineIndex(status: DealStatus): number {
  return PIPELINE_STATUSES.indexOf(status)
}
