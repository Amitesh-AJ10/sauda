/** Top bar: brand mark + wordmark, per DESIGN.md's logo/nav conventions. */
export function Header() {
  return (
    <header className="flex items-center justify-between gap-4 border-b border-black bg-white px-6 py-4">
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-full border border-black bg-white font-display text-lg">
          S
        </span>
        <span className="font-display text-2xl leading-none">SAUDA</span>
      </div>
      <p className="hidden text-sm text-black/60 sm:block">Autonomous B2B deal closer</p>
    </header>
  )
}
