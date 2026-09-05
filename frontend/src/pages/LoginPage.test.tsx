import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { LoginPage } from './LoginPage'

describe('LoginPage', () => {
  it('logs in as admin with correct credentials', async () => {
    const onLogin = vi.fn()
    const user = userEvent.setup()
    render(<LoginPage onLogin={onLogin} />)

    await user.type(screen.getByTestId('login-username'), 'admin')
    await user.type(screen.getByTestId('login-password'), 'sauda-admin')
    await user.click(screen.getByTestId('login-submit'))

    expect(onLogin).toHaveBeenCalledWith(expect.objectContaining({ role: 'admin' }))
  })

  it('shows an error on wrong admin credentials', async () => {
    const user = userEvent.setup()
    render(<LoginPage onLogin={vi.fn()} />)

    await user.type(screen.getByTestId('login-username'), 'admin')
    await user.type(screen.getByTestId('login-password'), 'nope')
    await user.click(screen.getByTestId('login-submit'))

    expect(screen.getByTestId('login-error')).toBeInTheDocument()
  })

  it('logs in as a hospital by picking it and entering its password', async () => {
    const onLogin = vi.fn()
    const user = userEvent.setup()
    render(<LoginPage onLogin={onLogin} />)

    await user.click(screen.getByTestId('role-tab-hospital'))
    await user.click(screen.getByTestId('hospital-picker-apollo-north'))
    await user.type(screen.getByTestId('login-password'), 'apollo123')
    await user.click(screen.getByTestId('login-submit'))

    expect(onLogin).toHaveBeenCalledWith(expect.objectContaining({ hospitalId: 'apollo-north' }))
  })

  it('preselects the hospital passed via preselectHospitalId', async () => {
    render(<LoginPage onLogin={vi.fn()} preselectHospitalId="green-valley" />)
    expect(screen.getByTestId('role-tab-hospital')).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByTestId('hospital-picker-green-valley')).toHaveAttribute('aria-pressed', 'true')
  })

  it('does not let a hospital account log in through the admin tab', async () => {
    // findAccount would match the hospital account, but the submitted role must match the tab.
    const user = userEvent.setup()
    render(<LoginPage onLogin={vi.fn()} />)

    await user.type(screen.getByTestId('login-username'), 'citycare')
    await user.type(screen.getByTestId('login-password'), 'citycare123')
    await user.click(screen.getByTestId('login-submit'))

    expect(screen.getByTestId('login-error')).toBeInTheDocument()
  })
})
