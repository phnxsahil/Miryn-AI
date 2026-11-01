import type { Metadata } from "next";
import LandingNav from "../landing/LandingNav";
import landing from "../landing/LandingPage.module.css";
import styles from "./Changelog.module.css";

export const metadata: Metadata = {
  title: "What's New — Miryn AI",
  description:
    "A running log of what changed in Miryn and when: new capabilities, fixes, and reliability work, newest first.",
};

type Entry = {
  version: string;
  date: string;
  title: string;
  live?: boolean;
  points: string[];
};

const entries: Entry[] = [
  {
    version: "v0.8.3",
    date: "November 2, 2026",
    title: "Recent chat no longer crowds out saved memories",
    live: true,
    points: [
      "Fixed a memory-recall edge case: when a conversation had several short recent messages, they could fill every slot of the context sent to the model and no saved memory was included. Recent messages still come first, but up to 2 of the 5 slots are now kept for saved memories when relevant ones exist.",
      "The number of reserved slots is an engineering judgment call, not a measured quality improvement. Covered by offline tests that check the slot logic only; they do not measure answer quality.",
    ],
  },
  {
    version: "v0.8.2",
    date: "November 2, 2026",
    title: "Claude adapter merged, not enabled",
    points: [
      "The code that lets Miryn use Claude as a chat model is now merged. It is not switched on: no Claude key or settings have been added, so nothing is sent to Claude.",
      "Before any Claude call, the code checks a spend limit and sets aside that call's maximum possible cost. With no limit configured, calls are refused. This is a safeguard in our code, not a guarantee from the billing provider.",
      "Research notes (not a product feature): we tested whether a learned model could rank memories better than today's hand-tuned scoring, using made-up conversations only. The gain over plain semantic matching was small, so nothing is shipping from it.",
    ],
  },
  {
    version: "v0.8.1",
    date: "November 1, 2026",
    title: "What's New version log",
    points: [
      "Added this What's New page, a single running log of what changed and when, linked from the main navigation.",
    ],
  },
  {
    version: "v0.8.0",
    date: "October 30–31, 2026",
    title: "Landing refresh and a memory reliability round",
    points: [
      "New landing design with light and dark themes, landscape illustrations, themed legal pages and a consistent wordmark.",
      "India-focused Terms and Privacy rewrite: plain-language terms, public privacy and grievance contact.",
      "Added privacy-limited public-page analytics collection; no chat content is tracked.",
      "Improved filtering of recall-style questions and hypotheticals (\"what do you remember about...?\", Hinglish \"kya ...?\") so they are far less likely to be stored as memories, while facts embedded in them are still kept. Coverage keeps widening; unusual phrasings can still slip through.",
      "Corrections get a typed path: when you tell Miryn something changed (\"actually I moved to Bangalore\"), a supersession engine links the new fact to the old one and keeps an encrypted audit trail. The engine ships in production behind a feature flag, still off by default while validation finishes.",
      "Conversation-list timestamps now carry an explicit UTC offset, so chats no longer slide into \"Yesterday\" around local midnight.",
      "Sign-in and sign-up show the server's actual error message instead of a generic \"session expired\", and a failed credential attempt no longer clears a stored session.",
      "New offline evaluation suite for the memory heuristics, with regression tests pinning every false-positive class found during independent review.",
    ],
  },
  {
    version: "v0.7.0",
    date: "October 26–29, 2026",
    title: "Safety foundation and companion fixes",
    points: [
      "Safety overrides now apply across all companion personas, with a buffered reply reveal and no model retry after a safety block.",
      "Your chosen companion (Warm, Mirror, Coach) now persists reliably instead of reverting, and saving personalization no longer wipes learned beliefs.",
      "Google sign-in moved to a new OAuth client after the old project's origin mismatch.",
    ],
  },
  {
    version: "v0.6.0",
    date: "October 18–20, 2026",
    title: "Public launch",
    points: [
      "Miryn went live for everyone: free deployment on Vercel (frontend), Render (backend) and Neon (database), with signup and Google sign-in working end to end.",
      "Reply completion fix: AI answers no longer cut off mid-thought.",
      "New-account correctness pass: real identity progress, accurate personalization state, no demo placeholders.",
      "One shared visual language across the app, with the wave logo consistent everywhere.",
      "Persona voices reworked so Warm, Mirror and Coach actually sound different.",
    ],
  },
  {
    version: "v0.5.0",
    date: "October 7–10, 2026",
    title: "Native landing and a memory capture round",
    points: [
      "New native landing page: nav, hero, about, features, stats, charts, capabilities, insights, FAQ and contact, plus performance passes (WebP assets, lazy loading, cheaper blur).",
      "Broader memory capture: diet and allergies, birthdays, habits, training, relationships and stressors; importance scoring no longer saturates.",
      "Chat history pagination (latest 50, load earlier) and more readable memory labels and chat titles.",
      "Model-quota circuit breaker with a graceful busy reply instead of a failure.",
      "Mobile pass: touch targets, text sizes, settings tabs, onboarding overflow.",
      "Sanctuary clarity now derives from real signals.",
    ],
  },
  {
    version: "v0.4.0",
    date: "June 8, 2026",
    title: "ML retrieval upgrade",
    points: [
      "ML ranking model for memory retrieval merged, with a bulk-insert optimisation for identity evolution logs.",
    ],
  },
  {
    version: "v0.3.0",
    date: "May 2026",
    title: "Demo stabilisation",
    points: [
      "Backend and frontend finalised for demo, with SQLite migrations.",
      "Studio Charcoal visual overhaul and production stability fixes.",
      "Chat UI refactor and security fixes in demo cleanup logic.",
    ],
  },
  {
    version: "v0.2.0",
    date: "April 2026",
    title: "Memory ranking and analytics",
    points: [
      "Memory ranking model and evaluation metrics land in the repository.",
      "Data logging with emotion and identity analytics.",
      "Render deployment configuration and MVP fixes.",
    ],
  },
  {
    version: "v0.1.0",
    date: "March 2026",
    title: "Foundations",
    points: [
      "First full app sync: streaming chat, onboarding flow and the identity engine.",
      "Conversation list with LLM-generated titles.",
      "Health checks for the PostgreSQL and Redis backends.",
    ],
  },
];

export default function ChangelogPage() {
  return (
    <div className={landing.landing}>
      <LandingNav />
      <main className={styles.changelog}>
        <header className={styles.head}>
          <p className={styles.eyebrow}>Version Log</p>
          <h1 className="font-editorial">What&apos;s New</h1>
          <p className={styles.sub}>
            A running log of what changed and when, newest first.
          </p>
        </header>

        <ol className={styles.entries}>
          {entries.map((entry) => (
            <li key={entry.version} className={styles.entry}>
              <p className={styles.date}>
                {entry.version} · {entry.date}
              </p>
              <h2 className={`font-editorial ${styles.title}`}>
                {entry.title}
                {entry.live ? <span className={styles.livePill}>Live</span> : null}
              </h2>
              <ul className={styles.points}>
                {entry.points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </li>
          ))}
        </ol>

        <p className={styles.note}>
          Version numbers were assigned retroactively in November 2026 to group
          milestone changes; releases were not tagged at the time. Dates follow
          the repository history.
        </p>
      </main>
    </div>
  );
}
