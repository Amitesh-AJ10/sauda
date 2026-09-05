import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Deal } from '../types/deal'
import { Map } from './Map'

function makeDeal(overrides: Partial<Deal>): Deal {
  return {
    id: '911234567890',
    hospital_name: 'City Care',
    item_name: 'Nitrile Gloves',
    qty: 50,
    status: 'negotiating',
    payment_link_url: null,
    invoice_url: null,
    messages: [],
    reply: null,
    guardrail_violations: [],
    ...overrides,
  }
}

describe('Map', () => {
  it('renders the Hospital/Godown layout without crashing given a mocked deals list', () => {
    render(<Map deals={[makeDeal({})]} />)
    expect(screen.getByText('HOSPITAL')).toBeInTheDocument()
    expect(screen.getByText('SAUDA HQ')).toBeInTheDocument()
  })

  it('renders with no deals at all', () => {
    render(<Map deals={[]} />)
    expect(screen.getByText('HOSPITAL')).toBeInTheDocument()
    expect(screen.queryByTestId('lead-indicator')).not.toBeInTheDocument()
    expect(screen.queryByTestId('payment-indicator')).not.toBeInTheDocument()
  })

  it('shows the lead indicator for a deal still under negotiation', () => {
    render(<Map deals={[makeDeal({ status: 'negotiating' })]} />)
    expect(screen.getByTestId('lead-indicator')).toBeInTheDocument()
  })

  it('shows the payment indicator (unconfirmed) once a payment link is sent', () => {
    render(<Map deals={[makeDeal({ status: 'awaiting_payment', payment_link_url: 'https://rzp.io/i/fake' })]} />)
    const el = screen.getByTestId('payment-indicator')
    expect(el).toHaveAttribute('data-state', 'sent')
  })

  it('shows the payment indicator confirmed (green) once paid', () => {
    render(<Map deals={[makeDeal({ status: 'paid' })]} />)
    const el = screen.getByTestId('payment-indicator')
    expect(el).toHaveAttribute('data-state', 'confirmed')
  })

  it('does not show a dispatch sprite before a deal is dispatched', () => {
    render(<Map deals={[makeDeal({ status: 'issuing_invoice' })]} />)
    expect(screen.queryByTestId('dispatch-sprite')).not.toBeInTheDocument()
  })

  it('shows a dispatch sprite once a deal is dispatched', () => {
    render(<Map deals={[makeDeal({ status: 'dispatched' })]} />)
    expect(screen.getByTestId('dispatch-sprite')).toBeInTheDocument()
  })

  it('shows a receipt flash once a deal has an invoice url', () => {
    render(<Map deals={[makeDeal({ status: 'issuing_invoice', invoice_url: 'https://rzp.io/invoice/fake' })]} />)
    expect(screen.getByTestId('receipt-flash')).toBeInTheDocument()
  })

  it('does not re-trigger the dispatch trip on repeated polls of the same dispatched deal', () => {
    const deal = makeDeal({ status: 'dispatched' })
    const { rerender } = render(<Map deals={[deal]} />)
    expect(screen.getAllByTestId('dispatch-sprite')).toHaveLength(1)

    // Simulate the next poll returning the same still-dispatched deal.
    rerender(<Map deals={[{ ...deal }]} />)
    expect(screen.getAllByTestId('dispatch-sprite')).toHaveLength(1)
  })

  it('shows a guardrail alert once a deal has a guardrail violation', () => {
    render(<Map deals={[makeDeal({ guardrail_violations: ['\\bguarantee[sd]?\\b'] })]} />)
    expect(screen.getByTestId('guardrail-alert')).toBeInTheDocument()
  })

  it('shows the dialogue box with the most recent deal\'s last message', () => {
    render(
      <Map
        deals={[
          makeDeal({ id: 'a', messages: ['first buyer message'] }),
          makeDeal({ id: 'b', messages: ['Need 500 masks, best price?'] }),
        ]}
      />,
    )
    expect(screen.getByTestId('dialogue-box')).toHaveTextContent('Need 500 masks, best price?')
  })

  it('renders the demo controls panel', () => {
    render(<Map deals={[]} />)
    expect(screen.getByTestId('demo-trigger-whatsapp-lead')).toBeInTheDocument()
    expect(screen.getByTestId('demo-trigger-guardrail-block')).toBeInTheDocument()
    expect(screen.getByTestId('demo-trigger-razorpay-payment')).toBeInTheDocument()
    expect(screen.getByTestId('demo-trigger-ai-buyer-purchase')).toBeInTheDocument()
  })
})
