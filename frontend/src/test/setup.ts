import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'
import '@testing-library/jest-dom/vitest'

// RTL's auto-cleanup relies on a global `afterEach`, which we don't enable
// (no `globals: true` in vitest.config.ts) — register it explicitly instead.
afterEach(() => {
  cleanup()
})
