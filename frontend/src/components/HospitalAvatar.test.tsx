import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { HospitalAvatar } from './HospitalAvatar'

describe('HospitalAvatar', () => {
  it('renders one avatar glyph', () => {
    render(<HospitalAvatar id="city-care" />)
    expect(screen.getByTestId('hospital-avatar')).toBeInTheDocument()
  })

  it('gives the same hospital id the same color on repeat renders', () => {
    const { container: a } = render(<HospitalAvatar id="city-care" />)
    const { container: b } = render(<HospitalAvatar id="city-care" />)
    const styleA = a.querySelector('[data-testid="hospital-avatar"]')?.getAttribute('style')
    const styleB = b.querySelector('[data-testid="hospital-avatar"]')?.getAttribute('style')
    expect(styleA).toBe(styleB)
  })
})
