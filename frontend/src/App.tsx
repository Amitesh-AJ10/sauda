import { AdminDashboard } from './pages/AdminDashboard'
import { HospitalChatPage } from './pages/HospitalChatPage'

/** `/hospital/<id>` is the hospital's own chat page; everything else is the merchant dashboard. */
function App() {
  const path = window.location.pathname

  if (path.startsWith('/hospital')) {
    const id = path.split('/')[2] ?? null
    return <HospitalChatPage initialHospitalId={id} />
  }

  return <AdminDashboard />
}

export default App
