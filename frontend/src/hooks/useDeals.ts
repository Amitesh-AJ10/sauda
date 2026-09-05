import { useEffect, useState } from 'react'
import type { Deal } from '../types/deal'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const POLL_INTERVAL_MS = 4000

/** Polls GET /api/v1/deals every few seconds — no WebSocket for MVP. */
export function useDeals(intervalMs: number = POLL_INTERVAL_MS): Deal[] {
  const [deals, setDeals] = useState<Deal[]>([])

  useEffect(() => {
    let cancelled = false

    async function poll() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/deals`)
        if (!response.ok) return
        const data: Deal[] = await response.json()
        if (!cancelled) setDeals(data)
      } catch {
        // Backend unreachable — keep showing the last known state.
      }
    }

    poll()
    const id = setInterval(poll, intervalMs)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [intervalMs])

  return deals
}
