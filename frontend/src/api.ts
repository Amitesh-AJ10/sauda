export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export interface Hospital {
  id: string
  name: string
  pin_code: string
}

/** The fixed hospital directory — same 5 counterparties the backend runs the real agent against. */
export async function fetchHospitals(): Promise<Hospital[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/hospitals`)
  if (!response.ok) throw new Error(`Failed to load hospitals (${response.status})`)
  return response.json()
}

export interface ChatMessageResult {
  id: string
  status: string
  reply: string | null
  messages: string[]
  payment_link_url: string | null
  invoice_url: string | null
  guardrail_violations: string[]
  audit_trail: string[]
}

/** Sends one chat turn through the real agent graph for `hospitalId` and returns the updated deal. */
export async function sendChatMessage(hospitalId: string, text: string): Promise<ChatMessageResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/chat/${hospitalId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail ?? `Message failed (${response.status})`)
  }
  return response.json()
}
