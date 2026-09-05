import { useState, type FormEvent } from 'react'
import { ACCOUNTS, findAccount, hospitalAccounts, type Account } from '../lib/accounts'
import { HospitalAvatar } from '../components/HospitalAvatar'

interface LoginPageProps {
  onLogin: (account: Account) => void
  /** Prefills the hospital tab when arriving via /hospital/<id>. */
  preselectHospitalId?: string | null
}

/** Two sign-in modes: the merchant admin, or one of the fixed hospital accounts. */
export function LoginPage({ onLogin, preselectHospitalId = null }: LoginPageProps) {
  const [role, setRole] = useState<'admin' | 'hospital'>(preselectHospitalId ? 'hospital' : 'admin')
  const [selectedHospitalId, setSelectedHospitalId] = useState<string | null>(
    preselectHospitalId ?? hospitalAccounts()[0]?.hospitalId ?? null,
  )
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const enteredUsername = role === 'hospital' ? (ACCOUNTS.find((a) => a.hospitalId === selectedHospitalId)?.username ?? '') : username
    const account = findAccount(enteredUsername, password)
    if (!account || account.role !== role) {
      setError('Wrong username or password.')
      return
    }
    setError(null)
    onLogin(account)
  }

  return (
    <div className="flex min-h-svh items-center justify-center p-6">
      <div className="w-full max-w-sm rounded-[20px] border border-black bg-white p-6">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-full border border-black bg-white font-display text-lg">
            S
          </span>
          <span className="font-display text-2xl leading-none">SAUDA</span>
        </div>

        <div className="mt-6 flex gap-2">
          <button
            type="button"
            data-testid="role-tab-admin"
            onClick={() => setRole('admin')}
            aria-pressed={role === 'admin'}
            className="flex-1 rounded-full border border-black px-3 py-1.5 text-sm font-bold"
            style={{ backgroundColor: role === 'admin' ? 'var(--color-lavender)' : 'var(--color-paper)' }}
          >
            Merchant
          </button>
          <button
            type="button"
            data-testid="role-tab-hospital"
            onClick={() => setRole('hospital')}
            aria-pressed={role === 'hospital'}
            className="flex-1 rounded-full border border-black px-3 py-1.5 text-sm font-bold"
            style={{ backgroundColor: role === 'hospital' ? 'var(--color-lavender)' : 'var(--color-paper)' }}
          >
            Hospital
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
          {role === 'hospital' ? (
            <div data-testid="hospital-picker" className="flex flex-col gap-2">
              {hospitalAccounts().map((account) => (
                <button
                  key={account.hospitalId}
                  type="button"
                  data-testid={`hospital-picker-${account.hospitalId}`}
                  onClick={() => setSelectedHospitalId(account.hospitalId)}
                  aria-pressed={account.hospitalId === selectedHospitalId}
                  className="flex items-center gap-3 rounded-[16px] border border-black px-3 py-2 text-left"
                  style={{
                    backgroundColor: account.hospitalId === selectedHospitalId ? 'var(--color-sky-wash)' : 'var(--color-paper)',
                  }}
                >
                  <HospitalAvatar id={account.hospitalId ?? account.username} size={32} />
                  <span className="font-bold">{account.label}</span>
                </button>
              ))}
            </div>
          ) : (
            <label className="flex flex-col gap-1 text-sm font-bold">
              Username
              <input
                data-testid="login-username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="rounded-full border border-black px-4 py-2 text-sm font-normal"
              />
            </label>
          )}

          <label className="flex flex-col gap-1 text-sm font-bold">
            Password
            <input
              data-testid="login-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="rounded-full border border-black px-4 py-2 text-sm font-normal"
            />
          </label>

          {error && (
            <p data-testid="login-error" className="text-sm font-bold text-red-700">
              {error}
            </p>
          )}

          <button
            type="submit"
            data-testid="login-submit"
            className="rounded-full border border-black bg-black px-4 py-2 text-sm font-bold text-white"
          >
            Sign in
          </button>
        </form>
      </div>
    </div>
  )
}
