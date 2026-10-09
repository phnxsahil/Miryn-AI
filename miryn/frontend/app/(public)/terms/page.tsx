import Link from "next/link";
import type { Metadata } from "next";
import MirynLogo from "@/components/MirynLogo";

export const metadata: Metadata = {
  title: "Terms of Service | Miryn",
  description: "Terms of service governing your use of Miryn, the AI companion platform.",
};

const TERMS = [
  {
    id: "01",
    title: "The nature of Miryn",
    content: [
      "Miryn is an AI-powered companion designed for personal reflection, emotional support, and identity exploration. It is a tool for self-discovery, not a medical device, licensed therapist, or clinical mental health service.",
      "Miryn does not provide medical advice, diagnosis, or treatment. The AI's responses are generated based on patterns in language and your conversation history — they are not clinical assessments.",
    ],
    callout: "Miryn is not a substitute for professional mental health support, therapy, or medical advice. If you are in crisis, please contact professional services immediately.",
    crisis: "Crisis resources: 988 Suicide & Crisis Lifeline (USA) · Crisis Text Line: text HOME to 741741 · International: findahelpline.com",
  },
  {
    id: "02",
    title: "Access requirements",
    bullets: [
      "You must be at least 18 years of age to use Miryn.",
      "By creating an account, you confirm you meet this requirement.",
      "You must provide accurate information during registration.",
      "One account per person — shared accounts are not permitted.",
      "You are responsible for maintaining the security of your account credentials.",
    ],
  },
  {
    id: "03",
    title: "Acceptable use",
    content: ["Miryn is a quiet room for honest reflection. To maintain this space for everyone, the following are prohibited:"],
    bullets: [
      "Generating, storing, or transmitting illegal content of any kind",
      "Attempting to manipulate the AI to produce harmful, hateful, or violent outputs",
      "Automated scraping, reverse engineering, or extracting our underlying model architecture",
      "Using the service to impersonate others or violate their privacy",
      "Circumventing rate limits, security measures, or access controls",
      "Creating multiple accounts to bypass restrictions or free tier limits",
    ],
  },
  {
    id: "04",
    title: "Intellectual property",
    content: [
      "You retain ownership of all content you submit to Miryn. By submitting content, you grant Miryn a limited, non-exclusive license to process and store that content solely for the purpose of providing the service to you.",
      "Miryn's software, design, trademarks, and system architecture are owned exclusively by Miryn Technologies, Inc. You may not copy, modify, or distribute any part of the service without express written consent.",
    ],
  },
  {
    id: "05",
    title: "Service availability & no warranty",
    content: [
      "Miryn is currently provided in beta. We make no guarantees regarding the accuracy or truthfulness of AI-generated insights, 100% uptime, or the persistence of all data during major architectural updates.",
      "The service is provided \"as-is\" without warranties of any kind, either express or implied. We will always provide advance notice of planned maintenance.",
    ],
  },
  {
    id: "06",
    title: "Limitation of liability",
    content: [
      "To the fullest extent permitted by law, Miryn Technologies, Inc. shall not be liable for any indirect, incidental, special, or consequential damages resulting from your use of or inability to use the service.",
      "Our total liability to you for any claim arising from these terms shall not exceed the amount you paid for the service in the 12 months preceding the claim.",
    ],
  },
  {
    id: "07",
    title: "Termination",
    content: [
      "You may delete your account at any time from Settings → Account → Delete account. Upon deletion, your data will be handled per our Privacy Policy.",
      "We may suspend or terminate accounts that violate these terms, with or without notice depending on the severity of the violation. We will provide notice and an opportunity to appeal for non-severe cases.",
    ],
  },
  {
    id: "08",
    title: "Changes to these terms",
    content: [
      "We may update these terms as Miryn evolves. For material changes, we will notify you via the email associated with your account at least 14 days in advance. Your continued use after that date constitutes acceptance.",
    ],
  },
  {
    id: "09",
    title: "Governing law",
    content: [
      "These terms are governed by the laws of the State of Delaware, United States, without regard to its conflict of law provisions. Any disputes shall be resolved through binding arbitration under AAA rules.",
    ],
  },
];

type Term = {
  id: string;
  title: string;
  content?: string[];
  bullets?: string[];
  callout?: string;
  crisis?: string;
};

export default function TermsOfService() {
  return (
    <div className="min-h-dvh bg-[color:var(--miryn-warm-black)] font-ui text-[color:var(--text-primary)] antialiased">
      <nav className="sticky top-0 z-50 flex h-14 items-center justify-between border-b border-[color:var(--miryn-card-border)] bg-[color:var(--nav-scrim)] px-6 backdrop-blur lg:px-12">
        <Link href="/" className="rounded-sm transition-opacity hover:opacity-80">
          <MirynLogo size={22} showText />
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
            <span className="miryn-fragment">Terms of service</span>
          </div>
          <h1 className="text-[clamp(2rem,5vw,2.75rem)] leading-[1.1] tracking-tight" style={{ fontFamily: "var(--font-editorial)" }}>
            Clear terms.
            <br />
            <span className="italic text-[color:var(--miryn-moss)]">No surprises.</span>
          </h1>
          <p className="mt-4 max-w-[62ch] text-[15px] leading-relaxed text-[color:var(--miryn-parchment-muted)]">
            By using Miryn, you agree to these terms. We&apos;ve written them in plain language, because clarity is respect.
          </p>
          <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-[12px] text-[color:var(--text-dim)] font-mono">
            {["Last updated: September 20, 2026", "Effective: September 20, 2026"].map((t) => (
              <span key={t}>{t}</span>
            ))}
          </div>
        </header>

        <div className="space-y-10">
          {(TERMS as Term[]).map((s) => (
            <section key={s.id} className="border-t border-[color:var(--miryn-card-border)] pt-7">
              <div className="mb-4 flex items-baseline gap-4">
                <span className="font-mono text-[11px] font-semibold text-[color:var(--miryn-moss)]">{s.id}</span>
                <h2 className="text-[1.15rem] font-medium tracking-tight text-[color:var(--text-primary)]">{s.title}</h2>
              </div>

              {s.content && (
                <div className={`space-y-4 ${s.bullets ? "mb-4" : ""}`}>
                  {s.content.map((p, i) => (
                    <p key={i} className="max-w-[68ch] text-[14.5px] leading-[1.8] text-[color:var(--miryn-parchment-muted)]">{p}</p>
                  ))}
                </div>
              )}

              {s.callout && (
                <div className="my-4 rounded-xl border border-[color-mix(in_srgb,var(--theme-accent)_28%,transparent)] bg-[color-mix(in_srgb,var(--theme-accent)_7%,transparent)] px-5 py-4">
                  <p className="text-[14.5px] italic leading-[1.7] text-[color:var(--theme-accent)]">&ldquo;{s.callout}&rdquo;</p>
                  {s.crisis && (
                    <p className="mt-3 font-mono text-[12px] leading-relaxed text-[color:var(--miryn-parchment-muted)]">{s.crisis}</p>
                  )}
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
            </section>
          ))}
        </div>

        <div className="miryn-wall-card mt-14 p-6 sm:p-8">
          <p className="miryn-fragment mb-3">Agreement</p>
          <p className="mb-2 text-[16px] font-medium text-[color:var(--text-primary)]">By using Miryn, you agree to these terms.</p>
          <p className="text-[14px] leading-relaxed text-[color:var(--miryn-parchment-muted)]">
            Questions about these terms? Contact{" "}
            <a href="mailto:legal@miryn.ai" className="text-[color:var(--miryn-moss)] underline underline-offset-4 hover:text-[color:var(--miryn-parchment)]">
              legal@miryn.ai
            </a>
            . We respond within 5 business days.
          </p>
        </div>

        <div className="mt-12 flex flex-wrap items-center justify-between gap-3 border-t border-[color:var(--miryn-card-border)] pt-6">
          <span className="text-[12px] text-[color:var(--text-dim)]">© 2026 Miryn Technologies, Inc.</span>
          <div className="flex gap-5 text-[12px]">
            <Link href="/privacy" className="text-[color:var(--miryn-parchment-muted)] transition-colors hover:text-[color:var(--miryn-parchment)]">Privacy Policy</Link>
            <Link href="/" className="text-[color:var(--miryn-parchment-muted)] transition-colors hover:text-[color:var(--miryn-parchment)]">Home</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
