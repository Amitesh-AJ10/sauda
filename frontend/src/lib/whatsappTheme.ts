/** "Sunlit conversation" WhatsApp-style palette — scoped to the hospital chat
 * page only (the dashboard/login keep the DESIGN.md sticker system). Flat
 * colors, no shadows, high surface contrast. */
export const whatsapp = {
  creamCanvas: '#fcf5eb',
  paperWhite: '#ffffff',
  paleBlueWash: '#f0f4f9',
  inkBlack: '#111b21',
  charcoal: '#1c1e21',
  warmGray: '#5e5e5e',
  incomingBubble: '#ffffff',
  outgoingBubble: '#d9fdd3',
  accentGreen: '#25d366',
}

// A faint, generic doodle wash (leaves/circles) — not a copy of WhatsApp's
// proprietary wallpaper art, just the same "sunlit paper" spirit. Inlined
// as a data URI so the page never depends on a network fetch.
const DOODLE_SVG = `<svg xmlns='http://www.w3.org/2000/svg' width='140' height='140'>
  <g fill='none' stroke='#c9bfae' stroke-width='1.4' opacity='0.28'>
    <circle cx='16' cy='18' r='4'/>
    <path d='M46 26 q12 -14 24 0 q12 14 24 0'/>
    <circle cx='108' cy='96' r='4'/>
    <path d='M14 100 q12 12 24 0'/>
    <path d='M90 20 l10 10 m0 -10 l-10 10'/>
    <circle cx='60' cy='110' r='3'/>
  </g>
</svg>`

export const doodleBackgroundImage = `url("data:image/svg+xml,${encodeURIComponent(DOODLE_SVG)}")`
