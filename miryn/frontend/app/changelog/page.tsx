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
  date: string;
  title: string;
  live?: boolean;
  points: string[];
};

const entries: Entry[] = [
  {
    date: "October 31, 2026",
    title: "Memory reliability round",
    live: true,
    points: [
      "Improved filtering of recall-style questions and hypotheticals (\"what do you remember about...?\", Hinglish \"kya ...?\") so they are far less likely to be stored as memories, while facts embedded in them are still kept. Coverage keeps widening; unusual phrasings can still slip through.",
      "Corrections get a typed path: when you tell Miryn something changed (\"actually I moved to Bangalore\"), a supersession engine links the new fact to the old one and keeps an encrypted audit trail. The engine ships in production behind a feature flag, still off by default while validation finishes.",
      "Conversation-list timestamps now carry an explicit UTC offset, so chats no longer slide into \"Yesterday\" around local midnight.",
      "Sign-in and sign-up show the server's actual error message instead of a generic \"session expired\", and a failed credential attempt no longer clears a stored session.",
      "New offline evaluation suite for the memory heuristics, with regression tests pinning every false-positive class found during independent review.",
    ],
  },
  {
    date: "October 30, 2026",
    title: "Private owner analytics, clearer copy",
    points: [
      "Owner-only analytics dashboard with the actual build traffic configuration.",
      "Encryption wording on auth and FAQ pages scoped to capability language.",
    ],
  },
  {
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
    date: "June 8, 2026",
    title: "Memory ranking model",
    points: [
      "ML ranking model for memory retrieval merged, with a bulk-insert optimisation for identity evolution logs.",
    ],
  },
  {
    date: "May 2026",
    title: "Demo stabilisation",
    points: [
      "Backend and frontend finalised for demo, with SQLite migrations.",
      "Studio Charcoal visual overhaul and production stability fixes.",
      "Chat UI refactor and security fixes in demo cleanup logic.",
    ],
  },
  {
    date: "April 2026",
    title: "Foundations",
    points: [
      "Memory ranking model and evaluation metrics land in the repository.",
      "Render deployment configuration and MVP fixes.",
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
            <li key={entry.date} className={styles.entry}>
              <p className={styles.date}>{entry.date}</p>
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
          This log covers shipped changes to the Miryn app and site. Dates
          follow the repository history.
        </p>
      </main>
    </div>
  );
}
