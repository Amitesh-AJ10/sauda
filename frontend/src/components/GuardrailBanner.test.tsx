import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { GuardrailBanner } from './GuardrailBanner'

describe('GuardrailBanner', () => {
  it('renders nothing when there are no violations', () => {
    render(<GuardrailBanner violations={[]} />)
    expect(screen.queryByTestId('guardrail-banner')).not.toBeInTheDocument()
  })

  it('lists each violation when present', () => {
    render(<GuardrailBanner violations={['Blocked SLA promise', 'Blocked warranty promise']} />)
    expect(screen.getByTestId('guardrail-banner')).toBeInTheDocument()
    expect(screen.getByText('Blocked SLA promise')).toBeInTheDocument()
    expect(screen.getByText('Blocked warranty promise')).toBeInTheDocument()
  })
})
