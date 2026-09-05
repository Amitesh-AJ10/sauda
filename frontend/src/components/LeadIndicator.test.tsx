import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { LeadIndicator } from './LeadIndicator'

describe('LeadIndicator', () => {
  it('renders the exclamation mark when active', () => {
    render(<LeadIndicator active={true} />)
    expect(screen.getByTestId('lead-indicator')).toBeInTheDocument()
  })

  it('renders nothing when inactive', () => {
    render(<LeadIndicator active={false} />)
    expect(screen.queryByTestId('lead-indicator')).not.toBeInTheDocument()
  })
})
