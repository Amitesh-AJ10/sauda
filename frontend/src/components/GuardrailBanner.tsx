interface GuardrailBannerProps {
  violations: string[]
}

/** Flags any guardrail rewrite/block for the selected deal (PRD §6). */
export function GuardrailBanner({ violations }: GuardrailBannerProps) {
  if (violations.length === 0) return null

  return (
    <div
      data-testid="guardrail-banner"
      className="rounded-[20px] border border-black p-4"
      style={{ backgroundColor: 'var(--color-ember)' }}
    >
      <p className="font-bold text-white">⚠ Guardrail intervened</p>
      <ul className="mt-1 list-inside list-disc text-sm text-white">
        {violations.map((violation, index) => (
          <li key={index}>{violation}</li>
        ))}
      </ul>
    </div>
  )
}
