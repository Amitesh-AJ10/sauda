import type { Deal } from '../types/deal'
import { StatusStepper } from './StatusStepper'
import { GuardrailBanner } from './GuardrailBanner'
import { AuditTrail } from './AuditTrail'

interface ConversationPanelProps {
  deal: Deal | null
}

/** Detail view for the selected deal: pipeline progress, audit trail, message log, payment/invoice links. */
export function ConversationPanel({ deal }: ConversationPanelProps) {
  if (!deal) {
    return (
      <div
        data-testid="conversation-panel-empty"
        className="flex h-full min-h-64 items-center justify-center rounded-[20px] border border-black bg-white p-8 text-center text-black/50"
      >
        Select a hospital to see the conversation and its progress.
      </div>
    )
  }

  return (
    <div data-testid="conversation-panel" className="flex flex-col gap-4">
      <div className="rounded-[20px] border border-black bg-white p-4">
        <h2 className="font-display text-3xl leading-none">{deal.hospital_name ?? 'Unknown hospital'}</h2>
        <p className="mt-1 text-black/70">
          {deal.qty ?? '?'} × {deal.item_name ?? 'item pending'}
        </p>
        <div className="mt-4">
          <StatusStepper status={deal.status} />
        </div>
      </div>

      <GuardrailBanner violations={deal.guardrail_violations} />

      <AuditTrail entries={deal.audit_trail} />

      <div className="rounded-[20px] border border-black bg-white p-4">
        <p className="font-bold">Conversation</p>
        <ol data-testid="message-log" className="mt-2 flex flex-col gap-2">
          {deal.messages.length === 0 && <li className="text-sm text-black/50">No messages yet.</li>}
          {deal.messages.map((message, index) => (
            <li
              key={index}
              className="rounded-[16px] border border-black px-3 py-2 text-sm"
              style={{ backgroundColor: 'var(--color-sky-wash)' }}
            >
              {message}
            </li>
          ))}
        </ol>
        {deal.reply && (
          <p data-testid="deal-reply" className="mt-3 rounded-[16px] border border-black bg-white px-3 py-2 text-sm">
            <span className="font-bold">Sauda: </span>
            {deal.reply}
          </p>
        )}
      </div>

      {(deal.payment_link_url || deal.invoice_url) && (
        <div className="flex flex-wrap gap-3">
          {deal.payment_link_url && (
            <a
              data-testid="payment-link"
              href={deal.payment_link_url}
              target="_blank"
              rel="noreferrer"
              className="rounded-full border border-black bg-black px-4 py-2 text-sm font-bold text-white"
            >
              View payment link ↗
            </a>
          )}
          {deal.invoice_url && (
            <a
              data-testid="invoice-link"
              href={deal.invoice_url}
              target="_blank"
              rel="noreferrer"
              className="rounded-full border border-black bg-white px-4 py-2 text-sm font-bold"
            >
              View invoice ↗
            </a>
          )}
        </div>
      )}
    </div>
  )
}
