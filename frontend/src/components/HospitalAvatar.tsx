const PALETTE = [
  'var(--color-sky-wash)',
  'var(--color-mint-pop)',
  'var(--color-lavender)',
  'var(--color-sunburst)',
  'var(--color-voltage-violet)',
]

/** Deterministic pastel per hospital id — same hospital always gets the same color. */
function colorFor(id: string): string {
  let hash = 0
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) >>> 0
  return PALETTE[hash % PALETTE.length]
}

interface HospitalAvatarProps {
  id: string
  size?: number
}

/** A small hand-drawn hospital-building glyph in a color-coded circle — no external image fetch. */
export function HospitalAvatar({ id, size = 40 }: HospitalAvatarProps) {
  return (
    <span
      data-testid="hospital-avatar"
      className="inline-flex shrink-0 items-center justify-center rounded-full border border-black"
      style={{ width: size, height: size, backgroundColor: colorFor(id) }}
      aria-hidden="true"
    >
      <svg viewBox="0 0 24 24" width={size * 0.62} height={size * 0.62} fill="none">
        <rect x="3" y="8" width="18" height="14" rx="1.5" fill="black" fillOpacity="0.9" />
        <rect x="7" y="2" width="6" height="8" rx="1" fill="black" fillOpacity="0.9" />
        <rect x="10.15" y="4" width="1.7" height="4" fill="white" />
        <rect x="8.65" y="5.5" width="4.7" height="1.7" fill="white" />
        <rect x="10.2" y="12" width="3.6" height="10" fill="white" />
        <rect x="5.5" y="14" width="2.4" height="2.4" fill="white" />
        <rect x="16.1" y="14" width="2.4" height="2.4" fill="white" />
      </svg>
    </span>
  )
}
