import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StatusStepper } from './StatusStepper'

describe('StatusStepper', () => {
  it('marks the current step active and later steps inactive', () => {
    render(<StatusStepper status="negotiating" />)
    expect(screen.getByTestId('stepper-step-negotiating')).toHaveAttribute('data-active', 'true')
    expect(screen.getByTestId('stepper-step-awaiting_payment')).toHaveAttribute('data-active', 'false')
  })

  it('marks earlier steps done (inactive but not dimmed to the same degree as the label implies)', () => {
    render(<StatusStepper status="paid" />)
    expect(screen.getByTestId('stepper-step-negotiating')).toHaveAttribute('data-active', 'false')
    expect(screen.getByTestId('stepper-step-paid')).toHaveAttribute('data-active', 'true')
  })

  it('collapses to a single flagged step for terminal error statuses', () => {
    render(<StatusStepper status="out_of_stock" />)
    expect(screen.queryByTestId('stepper-step-negotiating')).not.toBeInTheDocument()
    expect(screen.getByText('Out of stock')).toBeInTheDocument()
  })
})
