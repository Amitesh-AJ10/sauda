import { motion } from 'framer-motion'
import { DISPATCH_ANIMATION_SECONDS } from '../hooks/useDeliveryEvents'

interface DispatchSpriteProps {
  /** Vertical px offset so multiple concurrent trips don't overlap on the road. */
  laneOffset?: number
}

/** A Rapido-style driver riding from the Godown to the Hospital along the road (STORY.md §7). */
export function DispatchSprite({ laneOffset = 0 }: DispatchSpriteProps) {
  return (
    <motion.div
      data-testid="dispatch-sprite"
      role="img"
      aria-label="Delivery driver en route to Hospital"
      initial={{ left: '100%' }}
      animate={{ left: '0%' }}
      transition={{ duration: DISPATCH_ANIMATION_SECONDS, ease: 'linear' }}
      className="pointer-events-none absolute -translate-x-1/2 select-none"
      style={{ top: laneOffset }}
    >
      <img
        src="/assets/sprites/dispatch-driver.png"
        alt=""
        className="h-8 w-8"
        style={{ imageRendering: 'pixelated' }}
      />
    </motion.div>
  )
}
