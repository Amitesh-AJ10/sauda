import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ChatBubble } from './ChatBubble'

describe('ChatBubble', () => {
  it('renders a hospital bubble', () => {
    render(<ChatBubble from="hospital" text="Need 50 gloves" />)
    expect(screen.getByTestId('chat-bubble-hospital')).toHaveTextContent('Need 50 gloves')
  })

  it('renders a sauda bubble with a payment link', () => {
    render(<ChatBubble from="sauda" text="Please pay" paymentLinkUrl="https://rzp.io/pay/abc" />)
    expect(screen.getByTestId('chat-bubble-sauda')).toHaveTextContent('Please pay')
    expect(screen.getByTestId('chat-payment-link')).toHaveAttribute('href', 'https://rzp.io/pay/abc')
    expect(screen.queryByTestId('chat-invoice-link')).not.toBeInTheDocument()
  })

  it('renders an invoice link when present', () => {
    render(<ChatBubble from="sauda" text="Paid!" invoiceUrl="https://rzp.io/inv/xyz" />)
    expect(screen.getByTestId('chat-invoice-link')).toHaveAttribute('href', 'https://rzp.io/inv/xyz')
  })
})
