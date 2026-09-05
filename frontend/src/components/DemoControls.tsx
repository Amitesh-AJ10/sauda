import { useState } from 'react'
import { triggerDemo } from '../api'
import type { DemoTriggerKind } from '../api'

const BUTTONS: { kind: DemoTriggerKind; label: string; className: string }[] = [
  { kind: 'whatsapp-lead', label: 'Trigger WhatsApp Lead', className: 'bg-emerald-500 hover:bg-emerald-400' },
  { kind: 'guardrail-block', label: 'Trigger Guardrail Block', className: 'bg-sky-500 hover:bg-sky-400' },
  { kind: 'razorpay-payment', label: 'Trigger Razorpay Webhook', className: 'bg-amber-400 hover:bg-amber-300' },
  { kind: 'ai-buyer-purchase', label: 'AI-Buyer Purchase', className: 'bg-rose-500 hover:bg-rose-400' },
]

/** One-click backend triggers so a demo recording never needs a terminal alongside the browser. */
export function DemoControls() {
  const [pending, setPending] = useState<DemoTriggerKind | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleClick(kind: DemoTriggerKind) {
    setPending(kind)
    setError(null)
    try {
      await triggerDemo(kind)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Trigger failed')
    } finally {
      setPending(null)
    }
  }

  return (
    <div className="w-60 rounded border-4 border-black bg-white p-2 font-pixel text-black shadow-[4px_4px_0_0_rgba(0,0,0,0.5)]">
      <p className="mb-2 text-center text-[9px]">DEMO CONTROLS</p>
      <div className="flex flex-col gap-1.5">
        {BUTTONS.map((btn) => (
          <button
            key={btn.kind}
            type="button"
            data-testid={`demo-trigger-${btn.kind}`}
            onClick={() => handleClick(btn.kind)}
            disabled={pending !== null}
            className={`rounded border-2 border-black px-2 py-1.5 text-left text-[8px] leading-tight text-white transition disabled:opacity-50 ${btn.className}`}
          >
            {pending === btn.kind ? 'SENDING…' : btn.label.toUpperCase()}
          </button>
        ))}
      </div>
      {error && (
        <p data-testid="demo-controls-error" className="mt-2 text-[8px] text-red-600">
          {error}
        </p>
      )}
    </div>
  )
}
