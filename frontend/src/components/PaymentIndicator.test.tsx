import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { PaymentIndicator } from './PaymentIndicator'

describe('PaymentIndicator', () => {
  it('renders nothing for "none"', () => {
    render(<PaymentIndicator state="none" />)
    expect(screen.queryByTestId('payment-indicator')).not.toBeInTheDocument()
  })

  it('renders the dollar icon (not green) for "sent"', () => {
    render(<PaymentIndicator state="sent" />)
    const el = screen.getByTestId('payment-indicator')
    expect(el).toBeInTheDocument()
    expect(el).toHaveAttribute('data-state', 'sent')
    expect(el.className).not.toContain('text-emerald-400')
  })

  it('turns green for "confirmed"', () => {
    render(<PaymentIndicator state="confirmed" />)
    const el = screen.getByTestId('payment-indicator')
    expect(el).toBeInTheDocument()
    expect(el).toHaveAttribute('data-state', 'confirmed')
    expect(el.className).toContain('text-emerald-400')
  })
})
