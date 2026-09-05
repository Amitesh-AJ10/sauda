import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { DealList } from './DealList'
import type { Deal } from '../types/deal'

function makeDeal(id: string): Deal {
  return {
    id,
    hospital_name: `Hospital ${id}`,
    item_name: 'Syringes',
    qty: 100,
    status: 'negotiating',
    payment_link_url: null,
    invoice_url: null,
    messages: [],
    reply: null,
    guardrail_violations: [],
    audit_trail: [],
  }
}

describe('DealList', () => {
  it('shows an empty state with no deals', () => {
    render(<DealList deals={[]} selectedId={null} onSelect={() => {}} />)
    expect(screen.getByTestId('deal-list-empty')).toBeInTheDocument()
  })

  it('renders one card per deal', () => {
    render(<DealList deals={[makeDeal('a'), makeDeal('b')]} selectedId={null} onSelect={() => {}} />)
    expect(screen.getAllByTestId('deal-card')).toHaveLength(2)
  })

  it('marks unseen deals with an alert and known hospitals with an open-chat link', () => {
    render(
      <DealList
        deals={[makeDeal('a'), makeDeal('b')]}
        selectedId={null}
        onSelect={() => {}}
        unseenIds={new Set(['a'])}
        hospitalIds={new Set(['a'])}
      />,
    )
    const alerts = screen.getAllByTestId('deal-card-alert')
    const links = screen.getAllByTestId('open-hospital-chat')
    expect(alerts).toHaveLength(1)
    expect(links).toHaveLength(1)
  })
})
