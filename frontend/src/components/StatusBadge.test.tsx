import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StatusBadge } from './StatusBadge'
import { STATUS_LABEL } from '../lib/status'
import type { DealStatus } from '../types/deal'

describe('StatusBadge', () => {
  it.each(Object.keys(STATUS_LABEL) as DealStatus[])('renders the label for %s', (status) => {
    render(<StatusBadge status={status} />)
    expect(screen.getByTestId('status-badge')).toHaveTextContent(STATUS_LABEL[status])
  })

  it('shows a warning glyph for error statuses', () => {
    render(<StatusBadge status="declined" />)
    expect(screen.getByTestId('status-badge')).toHaveTextContent('⚠')
  })

  it('omits the warning glyph for in-progress statuses', () => {
    render(<StatusBadge status="negotiating" />)
    expect(screen.getByTestId('status-badge')).not.toHaveTextContent('⚠')
  })
})
