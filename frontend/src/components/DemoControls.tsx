import { useState } from 'react'
import { triggerDemo } from '../api'
import type { DemoTriggerKind } from '../api'

const BUTTONS: { kind: DemoTriggerKind; label: string; accent: string }[] = [
  { kind: 'whatsapp-lead', label: 'Trigger WhatsApp lead', accent: 'var(--color-mint-pop)' },
  { kind: 'guardrail-block', label: 'Trigger guardrail block', accent: 'var(--color-electric-blue)' },
  { kind: 'razorpay-payment', label: 'Trigger Razorpay webhook', accent: 'var(--color-sunburst)' },
  { kind: 'ai-buyer-purchase', label: 'AI-buyer purchase', accent: 'var(--color-lavender)' },
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
    <div className="rounded-[20px] border border-black bg-white p-4">
      <p className="mb-3 text-xs font-bold tracking-wide text-black/60 uppercase">Demo controls</p>
      <div className="flex flex-col gap-2">
        {BUTTONS.map((btn) => (
          <button
            key={btn.kind}
            type="button"
            data-testid={`demo-trigger-${btn.kind}`}
            onClick={() => handleClick(btn.kind)}
            disabled={pending !== null}
            className="rounded-full border border-black px-4 py-2 text-left text-sm font-bold disabled:opacity-50"
            style={{ backgroundColor: btn.accent }}
          >
            {pending === btn.kind ? 'Sending…' : btn.label}
          </button>
        ))}
      </div>
      {error && (
        <p data-testid="demo-controls-error" className="mt-3 text-sm font-bold text-red-700">
          {error}
        </p>
      )}
    </div>
  )
}
