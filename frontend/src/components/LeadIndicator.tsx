import { AnimatePresence, motion } from 'framer-motion'

interface LeadIndicatorProps {
  /** True while at least one deal is mid-negotiation — a new/active inbound lead. */
  active: boolean
}

/** Animated exclamation mark over the Hospital (STORY.md §7). */
export function LeadIndicator({ active }: LeadIndicatorProps) {
  return (
    <AnimatePresence>
      {active && (
        <motion.div
          data-testid="lead-indicator"
          role="img"
          aria-label="New inbound lead"
          initial={{ opacity: 0, y: 6, scale: 0.6 }}
          animate={{ opacity: 1, y: [0, -6, 0], scale: 1 }}
          exit={{ opacity: 0, scale: 0.6 }}
          transition={{ y: { repeat: Infinity, duration: 0.8 }, default: { duration: 0.2 } }}
          className="pointer-events-none select-none text-3xl text-amber-400 drop-shadow"
        >
          ❗
        </motion.div>
      )}
    </AnimatePresence>
  )
}
