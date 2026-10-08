import Link from "next/link";
import type { Metadata } from "next";
import MirynLogo from "@/components/MirynLogo";

export const metadata: Metadata = {
  title: "Privacy Policy | Miryn",
  description: "How Miryn collects, uses, and protects your personal data and conversation history.",
};

const SECTIONS = [
  {
    id: "01",
    title: "What we collect",
    content: [
      "To provide a space for honest reflection, Miryn requires certain data. We collect your email address for account authentication, the content of your conversations to maintain your memory layer, and the identity profile data (traits, beliefs, and patterns) extracted by our engine.",
      "We also collect technical data including your IP address, browser type, device identifiers, and timestamps to ensure system security and operational integrity. This data is never sold or shared with third parties for advertising.",
    ],
  },
  {
    id: "02",
    title: "How we use your data",
    bullets: [
      "To provide and improve the Miryn service personalized to you",
      "To maintain your memory layer across sessions",
      "To detect and prevent abuse, fraud, and security breaches",
      "To send transactional emails (account verification, password resets)",
      "We do not sell your data — ever.",
      "We do not use your conversations to train global AI models without your explicit, opt-in consent.",
      "Your data is your own; we are merely the architects of the vault.",
    ],
  },
  {
    id: "03",
    title: "Memory & Storage architecture",
    content: [
      "Conversation content is stored encrypted at rest using AES-256 encryption. We implement multi-tier memory (Transient, Episodic, and Core) to handle your data with appropriate levels of persistence and access control.",
      "You have full control over your memory. You can delete any specific memory at any time from the Memory page, or choose to erase your entire account and all associated data from Settings → Privacy → Delete account.",
    ],
  },
  {
    id: "04",
    title: "Third-party infrastructure",
    providers: [
      { name: "OpenAI / Anthropic", role: "LLM Processing" },
      { name: "Neon / Supabase", role: "Database Storage" },
      { name: "Vercel / Railway", role: "Hosting Infrastructure" },
      { name: "Resend", role: "Transactional Email" },
      { name: "PostHog", role: "Anonymised Analytics" },
      { name: "Google OAuth", role: "Authentication (Optional)" },
    ],
  },
  {
    id: "05",
    title: "Data ownership & your rights",
    content: [
      "Export: You can download your entire conversation history and identity profile at any time from Settings → Privacy → Export my data. Exports are delivered within 48 hours in standard JSON format.",
      "Deletion: Account deletion removes all data from our primary systems within 30 days. Encrypted backups are purged within 90 days. To request manual deletion of any remaining logs, contact privacy@miryn.ai.",
      "Access & Correction: You may request a copy of all personal data we hold about you, or ask us to correct inaccurate information, at any time.",
    ],
  },
  {
    id: "06",
    title: "Data retention",
    content: [
      "We retain your conversation data for as long as your account is active. If you delete your account, data is removed from active systems within 30 days and from encrypted backups within 90 days.",
      "Anonymised, aggregated analytics data may be retained indefinitely as it cannot be linked back to any individual.",
    ],
  },
  {
    id: "07",
    title: "Cookies",
    content: [
      "Miryn uses strictly necessary cookies for authentication and session management. We do not use tracking cookies or advertising cookies. You can review our full Cookie Policy at miryn.ai/cookies.",
    ],
  },
  {
    id: "08",
    title: "Changes to this policy",
    content: [
      "We will notify you via email and an in-app banner at least 14 days before any material changes to this policy take effect. Continued use of Miryn after that date constitutes acceptance of the updated policy.",
    ],
  },
];

const TLDR = [
  "We collect your email, conversations, and usage patterns to power Miryn.",
  "We never sell your data or use it for advertising.",
  "We never train global AI models on your data without explicit opt-in consent.",
  "You can export or delete your data at any time.",
  "Your conversations are encrypted at rest with AES-256.",
];

type Section = {
  id: string;
  title: string;
  content?: string[];
  bullets?: string[];
  providers?: { name: string; role: string }[];
};

export default function PrivacyPolicy() {
  return (
    <div className="min-h-dvh bg-[color:var(--miryn-warm-black)] font-ui text-[color:var(--text-primary)] antialiased">
      <nav className="sticky top-0 z-50 flex h-14 items-center justify-between border-b border-[color:var(--miryn-card-border)] bg-[rgba(11,12,9,0.9)] px-6 backdrop-blur lg:px-12">
        <Link href="/" className="rounded-sm transition-opacity hover:opacity-80">
          <MirynLogo size={22} showText isDark />
        </Link>
        <Link href="/" className="text-[13px] text-[color:var(--miryn-parchment-muted)] transition-colors hover:text-[color:var(--miryn-parchment)]">
          ← Back to home
        </Link>
      </nav>

      <div className="mx-auto max-w-3xl px-6 py-14 lg:py-20">
        <header className="mb-12">
          <div className="mb-5 flex items-center gap-3">
            <span className="miryn-fragment">Legal</span>
            <span aria-hidden="true" className="text-[color:var(--miryn-card-border)]">·</span>
            <span className="miryn-fragment">Privacy policy</span>
          </div>
          <h1 className="text-[clamp(2rem,5vw,2.75rem)] leading-[1.1] tracking-tight" style={{ fontFamily: "var(--font-editorial)" }}>
            Your privacy is not a feature.
            <br />
            <span className="italic text-[color:var(--miryn-moss)]">It&apos;s the foundation.</span>
          </h1>
          <p className="mt-4 max-w-[62ch] text-[15px] leading-relaxed text-[color:var(--miryn-parchment-muted)]">
            Miryn is built for honest, private reflection. Here&apos;s exactly what we collect, how we use it, and how you stay in control.
          </p>
          <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-[12px] text-[color:var(--text-dim)] font-mono">
            {["Last updated: September 20, 2026", "Effective: September 20, 2026"].map((t) => (
              <span key={t}>{t}</span>
            ))}
          </div>
        </header>

        <div className="miryn-wall-card mb-12 p-6 sm:p-8">
          <p className="miryn-fragment mb-4">TL;DR</p>
          <ul className="space-y-2">
            {TLDR.map((item) => (
              <li key={item} className="flex items-start gap-3 text-[14.5px] leading-relaxed text-[color:var(--text-primary)]">
                <span aria-hidden="true" className="mt-0.5 shrink-0 text-[color:var(--miryn-moss)]">✓</span>
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="space-y-10">
          {(SECTIONS as Section[]).map((s) => (
            <section key={s.id} className="border-t border-[color:var(--miryn-card-border)] pt-7">
              <div className="mb-4 flex items-baseline gap-4">
                <span className="font-mono text-[11px] font-semibold text-[color:var(--miryn-moss)]">{s.id}</span>
                <h2 className="text-[1.15rem] font-medium tracking-tight text-[color:var(--text-primary)]">{s.title}</h2>
              </div>
              {s.content && (
                <div className="space-y-4">
                  {s.content.map((p, i) => (
                    <p key={i} className="max-w-[68ch] text-[14.5px] leading-[1.8] text-[color:var(--miryn-parchment-muted)]">{p}</p>
                  ))}
                </div>
              )}
              {s.bullets && (
                <ul className="space-y-2">
                  {s.bullets.map((b) => (
                    <li key={b} className="flex gap-3 text-[14.5px] leading-[1.7] text-[color:var(--miryn-parchment-muted)]">
                      <span aria-hidden="true" className="shrink-0 text-[color:var(--miryn-card-border)]">—</span>
                      {b}
                    </li>
                  ))}
                </ul>
              )}
              {s.providers && (
                <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-3">
                  {s.providers.map((p) => (
                    <div key={p.name} className="rounded-xl border border-[color:var(--miryn-card-border)] bg-[color:var(--miryn-surface)] px-4 py-3">
                      <p className="mb-1 text-[13px] font-medium text-[color:var(--text-primary)]">{p.name}</p>
                      <p className="font-mono text-[11px] text-[color:var(--text-dim)]">{p.role}</p>
                    </div>
                  ))}
                </div>
              )}
            </section>
          ))}
        </div>

        <div className="miryn-wall-card mt-14 p-6 sm:p-8">
          <p className="miryn-fragment mb-3">Questions</p>
          <p className="mb-2 text-[16px] font-medium text-[color:var(--text-primary)]">We&apos;re here to help</p>
          <p className="text-[14px] leading-relaxed text-[color:var(--miryn-parchment-muted)]">
            For any questions about this policy or your data, reach out to{" "}
            <a href="mailto:privacy@miryn.ai" className="text-[color:var(--miryn-moss)] underline underline-offset-4 hover:text-[color:var(--miryn-parchment)]">
              privacy@miryn.ai
            </a>
            . We typically respond within 2 business days.
          </p>
        </div>

        <div className="mt-12 flex flex-wrap items-center justify-between gap-3 border-t border-[color:var(--miryn-card-border)] pt-6">
          <span className="text-[12px] text-[color:var(--text-dim)]">© 2026 Miryn Technologies, Inc.</span>
          <div className="flex gap-5 text-[12px]">
            <Link href="/terms" className="text-[color:var(--miryn-parchment-muted)] transition-colors hover:text-[color:var(--miryn-parchment)]">Terms of Service</Link>
            <Link href="/" className="text-[color:var(--miryn-parchment-muted)] transition-colors hover:text-[color:var(--miryn-parchment)]">Home</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
