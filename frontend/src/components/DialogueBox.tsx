import type { Deal } from '../types/deal'

interface DialogueBoxProps {
  deal: Deal | null
}

/** Retro RPG-style textbox showing the buyer's latest message (STORY.md §7). */
export function DialogueBox({ deal }: DialogueBoxProps) {
  const lastMessage = deal?.messages[deal.messages.length - 1] ?? null

  return (
    <div
      data-testid="dialogue-box"
      className="flex w-full items-start gap-3 rounded-none border-4 border-black bg-black/90 p-3 font-retro text-white shadow-[4px_4px_0_0_#000]"
    >
      <img
        src="/assets/sprites/buyer-avatar.png"
        alt=""
        aria-hidden="true"
        className="h-10 w-10 shrink-0 border-2 border-white bg-slate-700 object-contain"
        style={{ imageRendering: 'pixelated' }}
      />
      <div className="min-w-0 flex-1">
        <p className="font-pixel text-[9px] text-sky-300">AI BUYER:</p>
        <p className="mt-1 truncate text-lg leading-snug text-slate-100">
          {lastMessage ?? 'Waiting for the first lead…'}
        </p>
      </div>
    </div>
  )
}
