import { AdminDashboard } from './pages/AdminDashboard'
import { HospitalChatPage } from './pages/HospitalChatPage'
import { LoginPage } from './pages/LoginPage'
import { ACCOUNTS } from './lib/accounts'
import { useSession } from './hooks/useSession'

/** Login-gated: the merchant signs in as admin, each hospital signs in with its own
 * hardcoded account and only ever sees its own chat — never anyone else's. */
function App() {
  const { account, login, logout } = useSession(ACCOUNTS)

  if (!account) {
    const path = window.location.pathname
    const preselectHospitalId = path.startsWith('/hospital/') ? path.split('/')[2] ?? null : null
    return <LoginPage onLogin={login} preselectHospitalId={preselectHospitalId} />
  }

  if (account.role === 'admin') {
    return <AdminDashboard onLogout={logout} />
  }

  return <HospitalChatPage hospitalId={account.hospitalId as string} hospitalName={account.label} onLogout={logout} />
}

export default App
