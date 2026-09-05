interface AuditTrailProps {
  entries: string[]
}

/** Plain-language "what the agent actually did" log — deterministic, not an LLM summary. */
export function AuditTrail({ entries }: AuditTrailProps) {
  if (entries.length === 0) return null

  return (
    <div data-testid="audit-trail" className="rounded-[20px] border border-black bg-white p-4">
      <p className="font-bold">Audit trail</p>
      <ol className="mt-2 flex flex-col gap-1.5">
        {entries.map((entry, index) => (
          <li key={index} className="text-sm text-black/80">
            {entry}
          </li>
        ))}
      </ol>
    </div>
  )
}
