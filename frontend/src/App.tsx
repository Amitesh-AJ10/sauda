import { Map } from './components/Map'
import { useDeals } from './hooks/useDeals'

function App() {
  const deals = useDeals()

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-4 bg-slate-950 text-slate-100">
      <h1 className="text-2xl font-semibold">Sauda</h1>
      <Map deals={deals} />
    </main>
  )
}

export default App
