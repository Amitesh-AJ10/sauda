import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ChatComposer } from './ChatComposer'

describe('ChatComposer', () => {
  it('sends the trimmed text and clears the input', async () => {
    const onSend = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    render(<ChatComposer onSend={onSend} />)

    const input = screen.getByTestId('chat-input')
    await user.type(input, '  Need 50 gloves  ')
    await user.click(screen.getByTestId('chat-send'))

    expect(onSend).toHaveBeenCalledWith('Need 50 gloves')
    expect(input).toHaveValue('')
  })

  it('does not send an empty message', async () => {
    const onSend = vi.fn()
    const user = userEvent.setup()
    render(<ChatComposer onSend={onSend} />)

    await user.click(screen.getByTestId('chat-send'))

    expect(onSend).not.toHaveBeenCalled()
  })

  it('disables input and send when disabled', () => {
    render(<ChatComposer onSend={() => {}} disabled />)
    expect(screen.getByTestId('chat-input')).toBeDisabled()
    expect(screen.getByTestId('chat-send')).toBeDisabled()
  })
})
