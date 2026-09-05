import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { useSession } from './useSession'
import { ACCOUNTS } from '../lib/accounts'

afterEach(() => {
  window.localStorage.clear()
})

describe('useSession', () => {
  it('starts logged out with no stored session', () => {
    const { result } = renderHook(() => useSession(ACCOUNTS))
    expect(result.current.account).toBeNull()
  })

  it('logs in and persists to localStorage', () => {
    const { result } = renderHook(() => useSession(ACCOUNTS))
    const admin = ACCOUNTS.find((a) => a.role === 'admin')!

    act(() => result.current.login(admin))

    expect(result.current.account?.username).toBe('admin')
    expect(window.localStorage.getItem('sauda_session')).toBe('admin')
  })

  it('restores the session from localStorage on mount', () => {
    window.localStorage.setItem('sauda_session', 'citycare')
    const { result } = renderHook(() => useSession(ACCOUNTS))
    expect(result.current.account?.hospitalId).toBe('city-care')
  })

  it('logs out and clears localStorage', () => {
    const { result } = renderHook(() => useSession(ACCOUNTS))
    const admin = ACCOUNTS.find((a) => a.role === 'admin')!
    act(() => result.current.login(admin))

    act(() => result.current.logout())

    expect(result.current.account).toBeNull()
    expect(window.localStorage.getItem('sauda_session')).toBeNull()
  })
})
