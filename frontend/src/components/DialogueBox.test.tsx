import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Deal } from '../types/deal'
import { DialogueBox } from './DialogueBox'

function makeDeal(overrides: Partial<Deal>): Deal {
  return {
    id: '911234567890',
    hospital_name: null,
    item_name: null,
    qty: null,
    status: 'negotiating',
    payment_link_url: null,
    invoice_url: null,
    messages: [],
    reply: null,
    guardrail_violations: [],
    ...overrides,
  }
}

describe('DialogueBox', () => {
  it('shows a placeholder when there is no active deal', () => {
    render(<DialogueBox deal={null} />)
    expect(screen.getByText(/waiting for the first lead/i)).toBeInTheDocument()
  })

  it("shows the deal's last inbound message", () => {
    render(<DialogueBox deal={makeDeal({ messages: ['Need 50 gloves', 'What about the price?'] })} />)
    expect(screen.getByText('What about the price?')).toBeInTheDocument()
  })
})
