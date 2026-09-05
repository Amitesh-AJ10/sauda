import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { DemoControls } from './DemoControls'

describe('DemoControls', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders all four demo trigger buttons', () => {
    render(<DemoControls />)
    expect(screen.getByTestId('demo-trigger-whatsapp-lead')).toBeInTheDocument()
    expect(screen.getByTestId('demo-trigger-guardrail-block')).toBeInTheDocument()
    expect(screen.getByTestId('demo-trigger-razorpay-payment')).toBeInTheDocument()
    expect(screen.getByTestId('demo-trigger-ai-buyer-purchase')).toBeInTheDocument()
  })

  it('POSTs to the matching backend endpoint when a button is clicked', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ triggered: 'whatsapp_lead', deal_id: 'x', status: 'negotiating', detail: '' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<DemoControls />)
    fireEvent.click(screen.getByTestId('demo-trigger-whatsapp-lead'))

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(fetchMock.mock.calls[0][0]).toContain('/api/v1/demo/whatsapp-lead')
  })

  it('shows an error message if the trigger fails', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'No deal is currently awaiting payment' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<DemoControls />)
    fireEvent.click(screen.getByTestId('demo-trigger-razorpay-payment'))

    await waitFor(() =>
      expect(screen.getByTestId('demo-controls-error')).toHaveTextContent('No deal is currently awaiting payment'),
    )
  })
})
