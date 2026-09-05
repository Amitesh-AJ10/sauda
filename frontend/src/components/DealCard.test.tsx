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
  audit_trail: [],
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
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-pressed', 'true')
    button.click()
    expect(onSelect).toHaveBeenCalledOnce()
  })

  it('shows a pulsing alert dot only when hasAlert is true', () => {
    const { rerender } = render(<DealCard deal={BASE_DEAL} selected={false} onSelect={() => {}} hasAlert={false} />)
    expect(screen.queryByTestId('deal-card-alert')).not.toBeInTheDocument()

    rerender(<DealCard deal={BASE_DEAL} selected={false} onSelect={() => {}} hasAlert={true} />)
    expect(screen.getByTestId('deal-card-alert')).toBeInTheDocument()
  })

  it('shows the open-chat link only when canOpenChat is true', () => {
    const { rerender } = render(<DealCard deal={BASE_DEAL} selected={false} onSelect={() => {}} canOpenChat={false} />)
    expect(screen.queryByTestId('open-hospital-chat')).not.toBeInTheDocument()

    rerender(<DealCard deal={BASE_DEAL} selected={false} onSelect={() => {}} canOpenChat={true} />)
    expect(screen.getByTestId('open-hospital-chat')).toHaveAttribute('href', '/hospital/deal-1')
  })
})
