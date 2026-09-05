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
    ...overrides,
  }
}

describe('Map', () => {
  it('renders the Hospital/Godown layout without crashing given a mocked deals list', () => {
    render(<Map deals={[makeDeal({})]} />)
    expect(screen.getByText('Hospital')).toBeInTheDocument()
    expect(screen.getByText('Godown')).toBeInTheDocument()
  })

  it('renders with no deals at all', () => {
    render(<Map deals={[]} />)
    expect(screen.getByText('Hospital')).toBeInTheDocument()
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
})
