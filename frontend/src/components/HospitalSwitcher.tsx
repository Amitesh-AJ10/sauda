import type { Hospital } from '../api'

interface HospitalSwitcherProps {
  hospitals: Hospital[]
  selectedId: string | null
  onSelect: (id: string) => void
}

/** Pills to flip between the fixed hospital directory without opening a tab per hospital. */
export function HospitalSwitcher({ hospitals, selectedId, onSelect }: HospitalSwitcherProps) {
  return (
    <div data-testid="hospital-switcher" className="flex flex-wrap gap-2 border-b border-black bg-white p-3">
      {hospitals.map((hospital) => (
        <button
          key={hospital.id}
          type="button"
          data-testid={`hospital-tab-${hospital.id}`}
          onClick={() => onSelect(hospital.id)}
          aria-pressed={hospital.id === selectedId}
          className="rounded-full border border-black px-3 py-1.5 text-xs font-bold"
          style={{ backgroundColor: hospital.id === selectedId ? 'var(--color-lavender)' : 'var(--color-paper)' }}
        >
          {hospital.name}
        </button>
      ))}
    </div>
  )
}
