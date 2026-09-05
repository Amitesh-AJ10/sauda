import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { HospitalChatPage } from './HospitalChatPage'

const fetchMock = vi.fn()

afterEach(() => {
  vi.restoreAllMocks()
})

describe('HospitalChatPage', () => {
  it('shows only the signed-in hospital — no switcher to any other hospital', async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => [] })
    vi.stubGlobal('fetch', fetchMock)

    render(<HospitalChatPage hospitalId="city-care" hospitalName="City Care Hospital" onLogout={() => {}} />)

    expect(screen.getByText('City Care Hospital')).toBeInTheDocument()
    expect(screen.queryByTestId('hospital-switcher')).not.toBeInTheDocument()
    expect(screen.queryByText('Apollo North')).not.toBeInTheDocument()
  })

  it('calls onLogout when sign out is clicked', async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => [] })
    vi.stubGlobal('fetch', fetchMock)
    const onLogout = vi.fn()

    render(<HospitalChatPage hospitalId="city-care" hospitalName="City Care Hospital" onLogout={onLogout} />)
    screen.getByTestId('logout-button').click()

    expect(onLogout).toHaveBeenCalledOnce()
  })

  it('sends a message through the chat API scoped to this hospital only', async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => [] })
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()

    render(<HospitalChatPage hospitalId="city-care" hospitalName="City Care Hospital" onLogout={() => {}} />)
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())

    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: 'city-care',
        status: 'negotiating',
        reply: 'We can offer 50 units.',
        messages: ['need 50 gloves'],
        payment_link_url: null,
        invoice_url: null,
        guardrail_violations: [],
        audit_trail: [],
      }),
    })

    await user.type(screen.getByTestId('chat-input'), 'need 50 gloves')
    await user.click(screen.getByTestId('chat-send'))

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/chat/city-care/messages'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(await screen.findByText('We can offer 50 units.')).toBeInTheDocument()
  })

  it('does not show a pay-now button once an invoice exists — only view invoice', async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => [] })
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()

    render(<HospitalChatPage hospitalId="city-care" hospitalName="City Care Hospital" onLogout={() => {}} />)
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())

    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: 'city-care',
        status: 'dispatched',
        reply: 'Already paid and dispatched!',
        messages: ['payment done'],
        payment_link_url: 'https://rzp.io/i/stale',
        invoice_url: 'https://rzp.io/i/invfake',
        guardrail_violations: [],
        audit_trail: [],
      }),
    })

    await user.type(screen.getByTestId('chat-input'), 'payment done')
    await user.click(screen.getByTestId('chat-send'))

    await screen.findByText('Already paid and dispatched!')
    expect(screen.queryByTestId('chat-payment-link')).not.toBeInTheDocument()
    expect(screen.getByTestId('chat-invoice-link')).toHaveAttribute('href', 'https://rzp.io/i/invfake')
  })
})
