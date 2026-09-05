export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type DemoTriggerKind = 'whatsapp-lead' | 'guardrail-block' | 'razorpay-payment' | 'ai-buyer-purchase'

export interface DemoTriggerResult {
  triggered: string
  deal_id: string
  status: string
  detail: string
}

/** Fires one of the backend's `/api/v1/demo/*` one-click demo triggers. */
export async function triggerDemo(kind: DemoTriggerKind): Promise<DemoTriggerResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/demo/${kind}`, { method: 'POST' })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail ?? `Demo trigger failed (${response.status})`)
  }
  return response.json()
}
