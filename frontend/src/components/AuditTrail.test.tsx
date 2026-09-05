import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { AuditTrail } from './AuditTrail'

describe('AuditTrail', () => {
  it('renders nothing with no entries', () => {
    render(<AuditTrail entries={[]} />)
    expect(screen.queryByTestId('audit-trail')).not.toBeInTheDocument()
  })

  it('lists each entry in order', () => {
    render(<AuditTrail entries={['📩 Message received', '🔍 Checked inventory']} />)
    const items = screen.getAllByRole('listitem')
    expect(items.map((item) => item.textContent)).toEqual(['📩 Message received', '🔍 Checked inventory'])
  })
})
