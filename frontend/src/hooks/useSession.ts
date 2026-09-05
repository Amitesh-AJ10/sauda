import { useCallback, useState } from 'react'
import type { Account } from '../lib/accounts'

const STORAGE_KEY = 'sauda_session'

function readStoredUsername(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

/** Who's signed in, backed by localStorage so a refresh doesn't log you out. */
export function useSession(accounts: Account[]) {
  const [username, setUsername] = useState<string | null>(readStoredUsername)

  const login = useCallback((account: Account) => {
    setUsername(account.username)
    try {
      window.localStorage.setItem(STORAGE_KEY, account.username)
    } catch {
      // localStorage unavailable (private mode, etc.) — session just won't survive a refresh.
    }
  }, [])

  const logout = useCallback(() => {
    setUsername(null)
    try {
      window.localStorage.removeItem(STORAGE_KEY)
    } catch {
      // ignore
    }
  }, [])

  const account = username ? accounts.find((candidate) => candidate.username === username) ?? null : null

  return { account, login, logout }
}
