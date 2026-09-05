import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { DemoControls } from './DemoControls'

const fetchMock = vi.fn()

afterEach(() => {
  vi.restoreAllMocks()
})

describe('DemoControls', () => {
  it('POSTs to the matching demo endpoint on click', async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)

    render(<DemoControls />)
    screen.getByTestId('demo-trigger-whatsapp-lead').click()

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/v1/demo/whatsapp-lead'), expect.objectContaining({ method: 'POST' })))
  })

  it('shows an error message when the trigger fails', async () => {
    fetchMock.mockResolvedValue({ ok: false, status: 500, json: async () => ({ detail: 'boom' }) })
    vi.stubGlobal('fetch', fetchMock)

    render(<DemoControls />)
    screen.getByTestId('demo-trigger-guardrail-block').click()

    expect(await screen.findByTestId('demo-controls-error')).toHaveTextContent('boom')
  })
})
