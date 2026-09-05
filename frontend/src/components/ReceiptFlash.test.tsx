import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ReceiptFlash } from './ReceiptFlash'

describe('ReceiptFlash', () => {
  it('renders the receipt icon', () => {
    render(<ReceiptFlash />)
    expect(screen.getByTestId('receipt-flash')).toBeInTheDocument()
  })
})
