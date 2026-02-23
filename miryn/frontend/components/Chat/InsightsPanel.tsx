"use client";

import type { ConversationInsights } from "@/lib/types";

/**
 * Render a supplemental insights panel showing reflection text, mood and intensity, possible contradictions, and topic/entity tags when data is available.
 *
 * The component reads these fields from `insights` when present: `topics`, `entities`, `insights` (reflection text), and `emotions.primary_emotion` / `emotions.intensity`.
 *
 * @param insights - Conversation insights object or `null`. Used to populate reflection, mood/intensity, topics, and entities.
 * @param conflicts - Optional array of conflict objects each containing `statement`, `conflict_with`, and an optional `severity`; when non-empty, a "Possible contradictions" block is rendered.
 * @returns The aside element containing supplemental insights, or `null` if no supplemental data is available.
 */
export default function InsightsPanel({
  insights,
  conflicts,
}: {
  insights: ConversationInsights | null;
  conflicts?: Array<{ statement: string; conflict_with: string; severity?: number }>;
}) {
  const topics = insights?.topics || [];
  const entities = insights?.entities || [];
  const reflection = insights?.insights?.trim();
  const mood = insights?.emotions?.primary_emotion;
  const intensity = insights?.emotions?.intensity;
  const hasSupplemental = reflection || topics.length > 0 || entities.length > 0 || mood || (conflicts || []).length > 0;

  if (!hasSupplemental) {
    return null;
  }

  return (
    <aside className="border-t border-white/10 bg-black/30 px-6 py-4 text-sm space-y-3">
      <div className="flex items-center justify-between text-xs uppercase tracking-[0.35em] text-secondary">
        <span>Reflection</span>
        {mood && (
          <span className="tracking-normal text-secondary/80">
            Mood: <span className="text-white">{mood}</span>
            {typeof intensity === "number" && (
              <span className="ml-1 text-secondary/60">({Math.round(intensity * 100)}%)</span>
            )}
          </span>
        )}
      </div>
      {reflection && <p className="text-white/80 leading-relaxed">{reflection}</p>}

      {conflicts && conflicts.length > 0 && (
        <div className="rounded border border-amber-500/30 bg-amber-500/10 p-3 text-amber-100">
          <div className="text-xs uppercase tracking-[0.2em] text-amber-200">Possible contradictions</div>
          <ul className="mt-2 space-y-1">
            {conflicts.map((c, idx) => (
              <li key={`conflict-${idx}`} className="text-xs leading-relaxed">
                {c.statement} <span className="text-amber-300">vs</span> {c.conflict_with}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {topics.map((topic, index) => (
          <span
            key={`topic-${topic}-${index}`}
            className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/80"
          >
            {topic}
          </span>
        ))}
        {entities.map((entity, index) => (
          <span
            key={`entity-${entity}-${index}`}
            className="inline-flex items-center rounded-full border border-white/5 bg-white/10 px-3 py-1 text-xs text-white"
          >
            {entity}
          </span>
        ))}
      </div>
    </aside>
  );
}
