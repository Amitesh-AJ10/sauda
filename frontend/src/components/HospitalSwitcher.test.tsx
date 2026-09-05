import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { HospitalSwitcher } from './HospitalSwitcher'

const HOSPITALS = [
  { id: 'city-care', name: 'City Care Hospital', pin_code: '411001' },
  { id: 'apollo-north', name: 'Apollo North', pin_code: '560001' },
]

describe('HospitalSwitcher', () => {
  it('renders one tab per hospital and marks the selected one', () => {
    render(<HospitalSwitcher hospitals={HOSPITALS} selectedId="city-care" onSelect={() => {}} />)
    expect(screen.getByTestId('hospital-tab-city-care')).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByTestId('hospital-tab-apollo-north')).toHaveAttribute('aria-pressed', 'false')
  })

  it('calls onSelect with the clicked hospital id', () => {
    const onSelect = vi.fn()
    render(<HospitalSwitcher hospitals={HOSPITALS} selectedId={null} onSelect={onSelect} />)
    screen.getByTestId('hospital-tab-apollo-north').click()
    expect(onSelect).toHaveBeenCalledWith('apollo-north')
  })
})
