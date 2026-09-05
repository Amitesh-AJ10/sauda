import { AnimatePresence, motion } from 'framer-motion'
import type { PaymentIndicatorState } from '../types/deal'

interface PaymentIndicatorProps {
  state: PaymentIndicatorState
}

/** Floating dollar sign when a payment link is sent; turns green once paid (STORY.md §7). */
export function PaymentIndicator({ state }: PaymentIndicatorProps) {
  return (
    <AnimatePresence>
      {state !== 'none' && (
        <motion.div
          data-testid="payment-indicator"
          data-state={state}
          role="img"
          aria-label={state === 'confirmed' ? 'Payment confirmed' : 'Payment link sent'}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: [0, -4, 0] }}
          exit={{ opacity: 0 }}
          transition={{ y: { repeat: Infinity, duration: 1.2 }, default: { duration: 0.2 } }}
          className={
            state === 'confirmed'
              ? 'pointer-events-none select-none text-3xl text-emerald-400 drop-shadow'
              : 'pointer-events-none select-none text-3xl text-amber-300 drop-shadow'
          }
        >
          💲
        </motion.div>
      )}
    </AnimatePresence>
  )
}
