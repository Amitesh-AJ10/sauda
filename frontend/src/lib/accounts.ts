/** Hardcoded login directory — no real auth (per design), just a gate so
 * a hospital tab only ever sees its own chat, and the merchant dashboard
 * needs its own sign-in separate from any hospital. */

export interface Account {
  role: 'admin' | 'hospital'
  /** For a hospital account, matches its id in the backend's hospital directory. */
  hospitalId: string | null
  username: string
  password: string
  label: string
}

export const ACCOUNTS: Account[] = [
  { role: 'admin', hospitalId: null, username: 'admin', password: 'sauda-admin', label: 'Merchant admin' },
  { role: 'hospital', hospitalId: 'city-care', username: 'citycare', password: 'citycare123', label: 'City Care Hospital' },
  { role: 'hospital', hospitalId: 'apollo-north', username: 'apollonorth', password: 'apollo123', label: 'Apollo North' },
  {
    role: 'hospital',
    hospitalId: 'sunrise-multispecialty',
    username: 'sunrise',
    password: 'sunrise123',
    label: 'Sunrise Multispecialty',
  },
  { role: 'hospital', hospitalId: 'st-marys', username: 'stmarys', password: 'stmarys123', label: "St. Mary's Medical Center" },
  { role: 'hospital', hospitalId: 'green-valley', username: 'greenvalley', password: 'green123', label: 'Green Valley Clinic' },
]

export function findAccount(username: string, password: string): Account | null {
  const normalized = username.trim().toLowerCase()
  return ACCOUNTS.find((account) => account.username === normalized && account.password === password) ?? null
}

export function hospitalAccounts(): Account[] {
  return ACCOUNTS.filter((account) => account.role === 'hospital')
}
