interface IconProps {
  color?: string
  size?: number
}

/** Small hand-drawn glyphs for the WhatsApp-style composer — inline SVG, no icon font/library. */

export function AttachIcon({ color = '#111b21', size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M17 7.5 9 15.5a3 3 0 1 0 4.24 4.24l7.07-7.07a5 5 0 0 0-7.07-7.07L6 12.83"
        stroke={color}
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  )
}

export function MicIcon({ color = '#111b21', size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="9" y="3" width="6" height="11" rx="3" stroke={color} strokeWidth="1.8" />
      <path d="M5 11a7 7 0 0 0 14 0" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
      <path d="M12 18v3" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}

export function SendIcon({ color = '#ffffff', size = 18 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 12 20 4l-6 16-3-7-7-1Z" stroke={color} strokeWidth="1.6" strokeLinejoin="round" fill={color} />
    </svg>
  )
}
