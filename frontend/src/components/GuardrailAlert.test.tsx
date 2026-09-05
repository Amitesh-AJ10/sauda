import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { GuardrailAlert } from './GuardrailAlert'

describe('GuardrailAlert', () => {
  it('renders the siren icon', () => {
    render(<GuardrailAlert />)
    expect(screen.getByTestId('guardrail-alert')).toBeInTheDocument()
  })
})
