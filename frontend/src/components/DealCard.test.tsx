import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { DealCard } from './DealCard'
import type { Deal } from '../types/deal'

const BASE_DEAL: Deal = {
  id: 'deal-1',
  hospital_name: 'City General',
  item_name: 'Nitrile Gloves',
  qty: 500,
  status: 'negotiating',
  payment_link_url: null,
  invoice_url: null,
  messages: ['Need 500 nitrile gloves to Pune, best rate?'],
  reply: null,
  guardrail_violations: [],
}

describe('DealCard', () => {
  it('renders hospital, item, qty, and last message', () => {
    render(<DealCard deal={BASE_DEAL} selected={false} onSelect={() => {}} />)
    expect(screen.getByText('City General')).toBeInTheDocument()
    expect(screen.getByText('500 × Nitrile Gloves')).toBeInTheDocument()
    expect(screen.getByText(/best rate/)).toBeInTheDocument()
  })

  it('falls back to placeholder text for missing fields', () => {
    render(
      <DealCard
        deal={{ ...BASE_DEAL, hospital_name: null, item_name: null, qty: null, messages: [] }}
        selected={false}
        onSelect={() => {}}
      />,
    )
    expect(screen.getByText('Unknown hospital')).toBeInTheDocument()
    expect(screen.getByText('No messages yet.')).toBeInTheDocument()
  })

  it('calls onSelect when clicked and reflects selected state', () => {
    const onSelect = vi.fn()
    render(<DealCard deal={BASE_DEAL} selected={true} onSelect={onSelect} />)
    const card = screen.getByTestId('deal-card')
    expect(card).toHaveAttribute('aria-pressed', 'true')
    card.click()
    expect(onSelect).toHaveBeenCalledOnce()
  })
})
