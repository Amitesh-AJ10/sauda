import { whatsapp } from '../lib/whatsappTheme'

interface ChatBubbleProps {
  from: 'hospital' | 'sauda'
  text: string
  time: string
  paymentLinkUrl?: string | null
  invoiceUrl?: string | null
}

/** One message bubble — outgoing (hospital, green, right) vs incoming (Sauda, white, left). */
export function ChatBubble({ from, text, time, paymentLinkUrl, invoiceUrl }: ChatBubbleProps) {
  const isOutgoing = from === 'hospital'

  return (
    <div className={`flex ${isOutgoing ? 'justify-end' : 'justify-start'}`}>
      <div
        data-testid={`chat-bubble-${from}`}
        className="max-w-[75%] px-3 py-2"
        style={{
          backgroundColor: isOutgoing ? whatsapp.outgoingBubble : whatsapp.incomingBubble,
          color: whatsapp.charcoal,
          // 8px corners, with a 2px "tail" corner — top-left for an
          // incoming bubble, bottom-right for an outgoing one.
          borderRadius: isOutgoing ? '8px 8px 2px 8px' : '2px 8px 8px 8px',
        }}
      >
        <p className="text-sm whitespace-pre-wrap">{text}</p>
        {paymentLinkUrl && (
          <a
            data-testid="chat-payment-link"
            href={paymentLinkUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-block rounded-full px-3 py-1.5 text-xs font-bold"
            style={{ backgroundColor: whatsapp.accentGreen, color: whatsapp.paperWhite }}
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
            className="mt-2 inline-block rounded-full px-3 py-1.5 text-xs font-bold"
            style={{ backgroundColor: whatsapp.paleBlueWash, color: whatsapp.inkBlack }}
          >
            View invoice ↗
          </a>
        )}
        <p className="mt-1 text-right" style={{ fontSize: '11px', color: whatsapp.warmGray }}>
          {time}
        </p>
      </div>
    </div>
  )
}
