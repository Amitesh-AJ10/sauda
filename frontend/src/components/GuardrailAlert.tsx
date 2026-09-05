import { motion } from 'framer-motion'

/** A siren icon flashing over the Godown when a guardrail catches an unsafe LLM draft (PRD §6). */
export function GuardrailAlert() {
  return (
    <motion.div
      data-testid="guardrail-alert"
      role="img"
      aria-label="Guardrail blocked an unsafe reply"
      initial={{ opacity: 0, scale: 0.6 }}
      animate={{ opacity: 1, scale: [1, 1.2, 1] }}
      exit={{ opacity: 0 }}
      transition={{ scale: { repeat: 2, duration: 0.4 }, default: { duration: 0.2 } }}
      className="pointer-events-none select-none text-3xl"
    >
      🚨
    </motion.div>
  )
}
