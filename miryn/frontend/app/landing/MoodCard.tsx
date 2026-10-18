import type { CSSProperties } from "react";

export type Mood = {
  title: string;
  copy: string;
  color: string;
};

export const moodItems: Mood[] = [
  { title: "Seeing red", copy: "You might be feeling a bit frustrated or tense.", color: "color-mix(in srgb, var(--theme-accent) 92%, var(--theme-text))" },
  { title: "Feeling light", copy: "Seems like you have a good day!", color: "color-mix(in srgb, var(--theme-accent) 72%, var(--theme-text))" },
  { title: "Feeling blue", copy: "It looks like something’s weighing on your mind.", color: "color-mix(in srgb, var(--theme-accent) 84%, var(--theme-bg))" },
  { title: "Lost in thought", copy: "Feeling a little anxious? Take a deep breath.", color: "color-mix(in srgb, var(--theme-accent) 64%, var(--theme-text))" },
];

export default function MoodCard({ mood, compact = false }: { mood: Mood; compact?: boolean }) {
  return (
    <article className={`mood-card${compact ? " mood-card--compact" : ""}`} style={{ "--mood": mood.color } as CSSProperties}>
      <div className="mood-card__heading"><h3>{mood.title}</h3><span>Today</span></div>
      <div className="mood-orb" aria-hidden="true"><span /></div>
      <div className="mood-card__date">Today <span>Thu, Apr 3</span></div>
      <div className="mood-card__divider" />
      <p>{mood.copy}</p>
    </article>
  );
}
