/** "Sunlit conversation" WhatsApp-style palette — scoped to the hospital chat
 * page only (the dashboard/login keep the DESIGN.md sticker system). Flat
 * colors, no shadows, high surface contrast. */
export const whatsapp = {
  creamCanvas: '#fcf5eb',
  creamCanvasWarm: '#fff8ec',
  paperWhite: '#ffffff',
  paleBlueWash: '#f0f4f9',
  inkBlack: '#111b21',
  charcoal: '#1c1e21',
  warmGray: '#5e5e5e',
  incomingBubble: '#ffffff',
  outgoingBubble: '#d9fdd3',
  accentGreen: '#25d366',
}

// A faint, generic doodle wash — a denser mix of leaves, dots, waves and
// small plus/hex accents (medical-adjacent, never a literal cross-as-logo)
// so the canvas reads as textured paper rather than a flat block of color.
// Not a copy of WhatsApp's proprietary wallpaper art. Inlined as a data URI
// so the page never depends on a network fetch.
const DOODLE_SVG = `<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'>
  <g fill='none' stroke='#c9bfae' stroke-width='1.4' opacity='0.32'>
    <circle cx='18' cy='20' r='4'/>
    <circle cx='170' cy='40' r='3'/>
    <circle cx='40' cy='150' r='3'/>
    <circle cx='190' cy='190' r='4'/>
    <path d='M60 30 q12 -14 24 0 q12 14 24 0'/>
    <path d='M20 110 q12 12 24 0'/>
    <path d='M130 130 q12 -12 24 0 q12 12 24 0'/>
    <path d='M100 190 q12 10 24 0'/>
    <path d='M150 20 l10 10 m0 -10 l-10 10'/>
    <path d='M30 70 l8 8 m0 -8 l-8 8'/>
    <path d='M180 100 l8 8 m0 -8 l-8 8'/>
    <path d='M8 45 v10 M3 50 h10'/>
    <path d='M110 60 v10 M105 65 h10'/>
    <path d='M70 160 v10 M65 165 h10'/>
    <path d='M200 150 h14 M207 143 v14'/>
  </g>
</svg>`

export const doodleBackgroundImage = `url("data:image/svg+xml,${encodeURIComponent(DOODLE_SVG)}")`

// Layered background for the chat thread: the doodle wash sits on top of a
// soft warm gradient (still flat color stops, no drop shadow) so the
// canvas has gentle depth instead of reading as one flat block.
export const chatThreadBackground = {
  backgroundImage: `${doodleBackgroundImage}, linear-gradient(160deg, ${whatsapp.creamCanvasWarm} 0%, ${whatsapp.creamCanvas} 55%, ${whatsapp.creamCanvas} 100%)`,
  backgroundSize: '220px 220px, 100% 100%',
  backgroundRepeat: 'repeat, no-repeat',
} as const
