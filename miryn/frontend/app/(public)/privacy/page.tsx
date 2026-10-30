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
    title: "Who we are",
    content: [
      "Miryn is an AI companion web application built and operated by Sahil Sharma, an independent developer based in India. There is no company behind Miryn yet, and this policy is written for the service as it actually runs today.",
      "You can reach us at worksahilsharma@gmail.com for anything in this policy. Our Grievance Officer for India is listed in section 10.",
    ],
  },
  {
    id: "02",
    title: "What we collect",
    content: [
      "Account data: your email address, password (stored only as a secure hash), display name, and the profile preferences you choose, such as goals, traits, conversation style and depth.",
      "Conversations and memory: the messages you exchange with Miryn, and the memory layer built from them - facts, beliefs, emotions, patterns and open loops extracted by our reflection engine, plus automated summaries. If you choose to import a chat history (for example, a ChatGPT export), we store and process that too.",
      "Technical data: your IP address, device and browser type, timestamps, and session records, used for security, rate limiting and abuse prevention.",
      "If you sign in with Google, we receive your basic Google profile and email from Google's sign-in service. We never see your Google password.",
    ],
  },
  {
    id: "03",
    title: "Sensitive personal data",
    content: [
      "Miryn is a companion for personal reflection, so your conversations may include information about your physical, physiological or mental health condition. Under India's Information Technology (Reasonable Security Practices and Procedures and Sensitive Personal Data or Information) Rules, 2011, this counts as sensitive personal data, along with your password.",
      "By creating an account and accepting this policy, you consent to our collecting and processing this data for the purposes described here. You can withdraw consent at any time by deleting your account and asking us to erase your data; after withdrawal we can no longer provide the service to you.",
    ],
  },
  {
    id: "04",
    title: "How we use your data",
    bullets: [
      "To provide Miryn and personalise it to you",
      "To maintain your memory layer across sessions",
      "To detect and prevent abuse, fraud and security breaches",
      "To send transactional emails (account verification, password resets, and check-ins you have agreed to)",
      "We do not sell your personal data.",
      "We do not use your conversations to train any model of our own.",
      "See the next section for how our AI provider handles conversation content - this matters.",
    ],
  },
  {
    id: "05",
    title: "AI processing & third-party providers",
    content: [
      "Miryn sends your conversation content to Google's Gemini API to generate replies. As of October 2026, Miryn's configuration uses Google's unpaid (free) API tier. Under Google's terms for unpaid services, Google may use submitted content and generated responses to provide, improve and develop its products and machine-learning technologies, and human reviewers at Google may read and annotate that content (Google states it disconnects this data from the Google account, API key and Cloud project before review). Google's terms also ask that sensitive, confidential or personal information not be submitted to the unpaid services - and Miryn is a personal reflection app, so this tension is real: anything you share in chat is sent to Google under those terms. You can read Google's Gemini API terms at ai.google.dev/gemini-api/terms. Please keep this in mind when deciding what to share; we are evaluating a paid tier under which Google does not use content for product improvement.",
      "We run on these providers, each processing data only as needed to deliver the service:",
    ],
    providers: [
      { name: "Google Gemini API", role: "AI response generation" },
      { name: "Google Sign-In", role: "Authentication (optional)" },
      { name: "Neon", role: "PostgreSQL database" },
      { name: "Render", role: "API server, background worker, key-value store" },
      { name: "Vercel", role: "Frontend hosting" },
      { name: "Resend", role: "Transactional email (when configured)" },
    ],
  },
  {
    id: "06",
    title: "Analytics",
    content: [
      "We do not currently run analytics, advertising trackers, or session recording on Miryn.",
      "If we enable privacy-limited, aggregate analytics in the future - page-view counts only, with no message content and no account identifiers - we will update this policy before switching it on.",
    ],
  },
  {
    id: "07",
    title: "Storage & security",
    content: [
      "Conversation and memory content is stored encrypted at rest. Passwords are stored only as salted hashes. All traffic is served over HTTPS.",
      "These are our reasonable security practices under Section 43A of the Information Technology Act, 2000. No system is perfectly secure; if a breach affects your personal data, we will tell you what happened and what we are doing about it.",
    ],
  },
  {
    id: "08",
    title: "Retention & deletion",
    content: [
      "We keep your data while your account is active. Some memory entries expire automatically as part of the memory system.",
      "You can delete individual memories at any time from the Memory page. When you delete your account from Settings, it is deactivated immediately and the email tied to it is anonymised - but account deletion does not by itself erase stored conversation and memory records. If you want those erased, email us at worksahilsharma@gmail.com and we will erase those records for you.",
      "Residual copies in provider backups and logs are removed on those providers' routine deletion cycles.",
    ],
  },
  {
    id: "09",
    title: "Your rights & data export",
    content: [
      "Miryn provides a JSON export of your memories, facts and identity profile. For a fuller archive, or to access or correct other personal data we hold about you, email worksahilsharma@gmail.com and we will respond within a reasonable time.",
      "India's Digital Personal Data Protection Act, 2023 and the DPDP Rules, 2025 are coming into force in phases: the Data Protection Board provisions began on 13 November 2025, and the main rights and duties (notice, consent, data fiduciary obligations and data principal rights) take effect on 13 May 2027. This policy already gives you the core rights that framework introduces - access, correction, erasure and grievance redressal - and we will keep aligning Miryn as its provisions come into force.",
    ],
  },
  {
    id: "10",
    title: "Grievance Officer (India)",
    content: [
      "In line with the Information Technology (Reasonable Security Practices and Procedures and Sensitive Personal Data or Information) Rules, 2011, we have designated a Grievance Officer:",
      "Sahil Sharma - worksahilsharma@gmail.com",
      "If you have a grievance about how your personal data is handled, write to us. We will acknowledge and redress it as soon as possible, and in any case within one month of receiving it.",
    ],
  },
  {
    id: "11",
    title: "Cookies",
    content: [
      "Miryn uses only strictly necessary storage and cookies for sign-in and session management. We do not use advertising or cross-site tracking cookies.",
    ],
  },
  {
    id: "12",
    title: "Children",
    content: [
      "Miryn is for users aged 18 and above. We do not knowingly collect personal data from anyone under 18. If we learn that an account belongs to someone under 18, we will delete it.",
    ],
  },
  {
    id: "13",
    title: "Processing outside India",
    content: [
      "Our providers may store and process your data on servers outside India. By using Miryn you consent to this, limited to the purposes described in this policy.",
    ],
  },
  {
    id: "14",
    title: "Changes to this policy",
    content: [
      "When this policy changes we will update this page and its effective date. For material changes, we will also flag the update inside the app before it takes effect.",
    ],
  },
];

const TLDR = [
  "We collect your email, profile preferences, conversations, and the memory built from them.",
  "Replies are generated by Google's Gemini API on its free tier - under Google's terms, Google may use that content to improve its products.",
  "We never sell your data, and we do not train any model of our own on your conversations.",
  "You can delete any memory, export your data, or delete your account at any time.",
  "Conversation content is stored encrypted at rest.",
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
    <div className="legal-page min-h-dvh bg-[color:var(--miryn-warm-black)] font-ui text-[color:var(--text-primary)] antialiased">
      <nav className="sticky top-0 z-50 flex h-14 items-center justify-between border-b border-[color:var(--miryn-card-border)] bg-[color:var(--nav-scrim)] px-6 backdrop-blur lg:px-12">
        <Link href="/" className="rounded-sm transition-opacity hover:opacity-80">
          <MirynLogo showText />
        </Link>
        <Link href="/" className="inline-flex min-h-11 items-center py-2.5 text-[13px] text-[color:var(--miryn-parchment-muted)] transition-colors hover:text-[color:var(--miryn-parchment)]">
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
            {["Last updated: October 31, 2026", "Effective: October 31, 2026"].map((t) => (
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
                <h2 className="text-[1.15rem] font-ui font-medium tracking-tight text-[color:var(--text-primary)]">{s.title}</h2>
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
            <a href="mailto:worksahilsharma@gmail.com" className="text-[color:var(--miryn-moss)] underline underline-offset-4 hover:text-[color:var(--miryn-parchment)]">
              worksahilsharma@gmail.com
            </a>
            . Grievances are answered within one month; other questions usually much sooner.
          </p>
        </div>

        <div className="mt-12 flex flex-wrap items-center justify-between gap-3 border-t border-[color:var(--miryn-card-border)] pt-6">
          <span className="text-[12px] text-[color:var(--text-dim)]">© 2026 Miryn · Operated by Sahil Sharma</span>
          <div className="flex gap-5 text-[12px]">
        <Link href="/terms" className="inline-flex min-h-11 items-center py-2.5 text-[color:var(--miryn-parchment-muted)] transition-colors hover:text-[color:var(--miryn-parchment)]">Terms of Service</Link>
        <Link href="/" className="inline-flex min-h-11 items-center py-2.5 text-[color:var(--miryn-parchment-muted)] transition-colors hover:text-[color:var(--miryn-parchment)]">Home</Link>
          </div>
        </div>
      </div>
    </div>
  );
      }
