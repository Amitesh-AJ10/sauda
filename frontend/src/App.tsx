import { Map } from './components/Map'
import { useDeals } from './hooks/useDeals'

function App() {
  const deals = useDeals()

  return (
    <main className="flex min-h-svh items-center justify-center bg-slate-950 p-4">
      <Map deals={deals} />
    </main>
  )
}

export default App
