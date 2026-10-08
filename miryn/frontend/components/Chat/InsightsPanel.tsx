"use client";

import type { ConversationInsights } from "@/lib/types";

export default function InsightsPanel({ insights, conflicts = [] }: {
  insights: ConversationInsights | null;
  conflicts?: Array<{ statement: string; conflict_with: string; severity?: number }>;
}) {
  const topics = insights?.topics || [];
  const reflection = insights?.insights?.trim();
  const mood = insights?.emotions?.primary_emotion;
  if (!reflection && !mood && !topics.length && !conflicts.length) return null;
  return (
    <aside aria-label="Conversation insights" className="space-y-3 rounded-xl bg-[color:var(--theme-surface)] px-4 py-3 text-sm leading-relaxed text-[color:var(--theme-muted)]">
      {reflection && <p className="text-[color:var(--theme-text)]">{reflection}</p>}
      {mood && <p><span className="font-medium text-[color:var(--theme-text)]">Mood:</span> {mood}</p>}
      {topics.length > 0 && <p><span className="font-medium text-[color:var(--theme-text)]">Topics:</span> {topics.join(", ")}</p>}
      {conflicts.map((conflict, index) => <p key={index}>{conflict.statement} · {conflict.conflict_with}</p>)}
    </aside>
  );
}
