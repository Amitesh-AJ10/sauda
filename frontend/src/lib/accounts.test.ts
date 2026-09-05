import { describe, expect, it } from 'vitest'
import { ACCOUNTS, findAccount, hospitalAccounts } from './accounts'

describe('findAccount', () => {
  it('finds the admin account with correct credentials', () => {
    const account = findAccount('admin', 'sauda-admin')
    expect(account?.role).toBe('admin')
  })

  it('finds a hospital account with correct credentials', () => {
    const account = findAccount('citycare', 'citycare123')
    expect(account?.role).toBe('hospital')
    expect(account?.hospitalId).toBe('city-care')
  })

  it('is case-insensitive on username', () => {
    expect(findAccount('CityCare', 'citycare123')?.hospitalId).toBe('city-care')
  })

  it('returns null for a wrong password', () => {
    expect(findAccount('admin', 'wrong')).toBeNull()
  })

  it('returns null for an unknown username', () => {
    expect(findAccount('not-a-real-account', 'whatever')).toBeNull()
  })
})

describe('hospitalAccounts', () => {
  it('excludes the admin account', () => {
    expect(hospitalAccounts().every((account) => account.role === 'hospital')).toBe(true)
    expect(hospitalAccounts().length).toBe(ACCOUNTS.length - 1)
  })
})
