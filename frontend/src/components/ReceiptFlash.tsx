import { motion } from 'framer-motion'

/** A pixelated receipt that briefly flashes over the Godown once the invoice is sent (STORY.md §7). */
export function ReceiptFlash() {
  return (
    <motion.div
      data-testid="receipt-flash"
      role="img"
      aria-label="Invoice sent"
      initial={{ opacity: 0, scale: 0.5, y: 6 }}
      animate={{ opacity: 1, scale: 1.15, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      className="pointer-events-none select-none text-3xl"
    >
      🧾
    </motion.div>
  )
}
