interface ChatBubbleProps {
  from: 'hospital' | 'sauda'
  text: string
  paymentLinkUrl?: string | null
  invoiceUrl?: string | null
}

/** One message bubble in the hospital-facing chat — right side is the hospital, left is Sauda. */
export function ChatBubble({ from, text, paymentLinkUrl, invoiceUrl }: ChatBubbleProps) {
  const isHospital = from === 'hospital'

  return (
    <div className={`flex ${isHospital ? 'justify-end' : 'justify-start'}`}>
      <div
        data-testid={`chat-bubble-${from}`}
        className="max-w-[80%] rounded-[16px] border border-black px-3 py-2 text-sm"
        style={{ backgroundColor: isHospital ? 'var(--color-electric-blue)' : 'var(--color-paper)' }}
      >
        <p>{text}</p>
        {paymentLinkUrl && (
          <a
            data-testid="chat-payment-link"
            href={paymentLinkUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-block rounded-full border border-black bg-black px-3 py-1 text-xs font-bold text-white"
          >
            Pay now ↗
          </a>
        )}
        {invoiceUrl && (
          <a
            data-testid="chat-invoice-link"
            href={invoiceUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-block rounded-full border border-black bg-white px-3 py-1 text-xs font-bold"
          >
            View invoice ↗
          </a>
        )}
      </div>
    </div>
  )
}
