import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ConversationPanel } from './ConversationPanel'
import type { Deal } from '../types/deal'

const DEAL: Deal = {
  id: 'deal-1',
  hospital_name: 'City General',
  item_name: 'Nitrile Gloves',
  qty: 500,
  status: 'awaiting_payment',
  payment_link_url: 'https://rzp.io/pay/abc',
  invoice_url: null,
  messages: ['Need 500 nitrile gloves to Pune, best rate?'],
  reply: 'We can do ₹12,500 for 500 units. Here is your payment link.',
  guardrail_violations: [],
  audit_trail: ['🔍 Checked inventory for \'Nitrile Gloves\'', '✅ Stock confirmed: 500 units available'],
}

describe('ConversationPanel', () => {
  it('shows a prompt when no deal is selected', () => {
    render(<ConversationPanel deal={null} />)
    expect(screen.getByTestId('conversation-panel-empty')).toBeInTheDocument()
  })

  it('renders hospital, messages, reply, and payment link for a selected deal', () => {
    render(<ConversationPanel deal={DEAL} />)
    expect(screen.getByText('City General')).toBeInTheDocument()
    expect(screen.getByText(/best rate/)).toBeInTheDocument()
    expect(screen.getByTestId('deal-reply')).toHaveTextContent('₹12,500')
    expect(screen.getByTestId('payment-link')).toHaveAttribute('href', 'https://rzp.io/pay/abc')
    expect(screen.queryByTestId('invoice-link')).not.toBeInTheDocument()
  })

  it('renders the invoice link once issued', () => {
    render(<ConversationPanel deal={{ ...DEAL, status: 'dispatched', invoice_url: 'https://rzp.io/inv/xyz' }} />)
    expect(screen.getByTestId('invoice-link')).toHaveAttribute('href', 'https://rzp.io/inv/xyz')
  })

  it('shows the guardrail banner when the deal has violations', () => {
    render(<ConversationPanel deal={{ ...DEAL, guardrail_violations: ['Blocked SLA promise'] }} />)
    expect(screen.getByTestId('guardrail-banner')).toBeInTheDocument()
  })

  it('renders the audit trail entries', () => {
    render(<ConversationPanel deal={DEAL} />)
    expect(screen.getByTestId('audit-trail')).toBeInTheDocument()
    expect(screen.getByText(/Stock confirmed: 500 units available/)).toBeInTheDocument()
  })

  it('omits the audit trail card when there are no entries', () => {
    render(<ConversationPanel deal={{ ...DEAL, audit_trail: [] }} />)
    expect(screen.queryByTestId('audit-trail')).not.toBeInTheDocument()
  })
})
