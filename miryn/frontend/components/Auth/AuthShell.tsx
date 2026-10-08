"use client";

import Link from "next/link";
import Image from "next/image";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import MirynLogo from "@/components/MirynLogo";

type AuthShellProps = {
  children: ReactNode;
  mode?: "split" | "centered";
  fragment?: string;
  heading?: string;
  title?: string;
  subtitle?: string;
};

export function AuthError({ message, id }: { message: string; id?: string }) {
  return (
    <div id={id} className="miryn-error mb-5 flex items-center gap-2.5 rounded-xl border border-red-500/20 bg-red-500/10 p-3.5 text-xs text-red-300 font-mono" role="alert">
      <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse flex-shrink-0" />
      <span>{message}</span>
    </div>
  );
}

function AuthFooter() {
  return (
    <div className="relative z-10 mx-auto mt-6 w-full max-w-[38ch] text-center">
      <p className="text-xs leading-relaxed text-[color:var(--theme-dim)]">
        Conversations are encrypted in storage. Review or forget saved memories anytime.
      </p>
      <p className="mt-2.5 flex items-center justify-center gap-3 text-xs text-[color:var(--theme-muted)]">
        <Link href="/terms" className="underline decoration-white/10 underline-offset-4 transition-colors hover:text-[color:var(--theme-text)]">
          Terms
        </Link>
        <span aria-hidden="true" className="text-[color:var(--theme-text)]/20">·</span>
        <Link href="/privacy" className="underline decoration-white/10 underline-offset-4 transition-colors hover:text-[color:var(--theme-text)]">
          Privacy
        </Link>
      </p>
    </div>
  );
}

// ── Animated chat demo ────────────────────────────────────────────────────────
const CHAT_SEQUENCE = [
  {
    role: "miryn" as const,
    tag: "MEMORY RECALL · 7d VECTOR",
    text: "You mentioned last Tuesday that your project deadline is this Friday. How is it looking?",
    delay: 400,
  },
  {
    role: "user" as const,
    text: "Still behind. Haven't started the final section yet.",
    delay: 1600,
  },
  {
    role: "miryn" as const,
    tag: "IDENTITY · BEHAVIOR PATTERN",
    text: "That tracks — you tend to front-load research and push execution late. Let's block 90 minutes today for the draft.",
    delay: 3000,
  },
  {
    role: "user" as const,
    text: "Okay, let's do it.",
    delay: 4600,
  },
];

type BubbleItem = (typeof CHAT_SEQUENCE)[number];

function ChatBubble({ item, visible }: { item: BubbleItem; visible: boolean }) {
  const style: React.CSSProperties = {
    opacity: visible ? 1 : 0,
    transform: visible ? "translateY(0)" : "translateY(12px)",
    transition: "opacity 0.5s cubic-bezier(0.16, 1, 0.3, 1), transform 0.5s cubic-bezier(0.16, 1, 0.3, 1)",
  };

  if (item.role === "miryn") {
    return (
      <div className="flex items-start gap-3" style={style}>
        <div className="flex-shrink-0 w-8 h-8 rounded-full overflow-hidden border border-[color:var(--theme-border)] bg-[color:var(--theme-surface)] flex items-center justify-center shadow-md">
          <Image src="/miryn-logo.png" alt="Miryn" width={32} height={32} className="object-cover" />
        </div>
        <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-[color:var(--theme-surface)] border border-[color:var(--theme-border)] px-4 py-3 shadow-lg">
          {"tag" in item && item.tag && (
            <div className="mb-2 inline-flex items-center gap-1.5 font-mono text-[9px] uppercase tracking-wider text-[color:var(--theme-accent)] bg-[color:var(--theme-accent)]/10 border border-[color:var(--theme-accent)]/20 rounded-full px-2.5 py-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[color:var(--theme-accent-strong)] animate-pulse" />
              {item.tag}
            </div>
          )}
          {"tag" in item && item.tag && <br />}
          <p className="text-[13px] leading-relaxed text-[color:var(--theme-text)] font-sans">{item.text}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-end" style={style}>
      <div className="max-w-[78%] rounded-2xl rounded-tr-sm bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] px-4 py-3 shadow-md">
        <p className="text-[13px] leading-relaxed text-[color:var(--theme-text)] font-sans">{item.text}</p>
      </div>
    </div>
  );
}

function AnimatedChat() {
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    const timers = CHAT_SEQUENCE.map((item, i) =>
      window.setTimeout(() => setVisibleCount((c) => Math.max(c, i + 1)), item.delay)
    );
    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="flex flex-col gap-3.5 bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] p-5 rounded-2xl">
      {CHAT_SEQUENCE.map((item, i) => (
        <ChatBubble key={i} item={item} visible={i < visibleCount} />
      ))}
    </div>
  );
}
// ─────────────────────────────────────────────────────────────────────────────

export default function AuthShell({ children, title, subtitle }: AuthShellProps) {
  return (
    <div className="grid min-h-dvh grid-cols-1 bg-[color:var(--theme-bg)] font-ui text-[color:var(--theme-text)] md:grid-cols-[52%_48%]">

      {/* ── Left panel ── */}
      <aside className="hidden min-h-dvh md:flex md:flex-col relative overflow-hidden bg-[color:var(--theme-sidebar)] border-r border-[color:var(--theme-border)]">
        {/* Ambient glows */}
        <div
          className="pointer-events-none absolute -top-32 -left-20 w-[500px] h-[500px] rounded-full -z-0 opacity-20"
          style={{ background: "radial-gradient(circle, var(--theme-accent) 0%, transparent 70%)" }}
        />
        <div
          className="pointer-events-none absolute -bottom-20 -right-16 w-[420px] h-[420px] rounded-full -z-0 opacity-15"
          style={{ background: "radial-gradient(circle, var(--theme-accent) 0%, transparent 70%)" }}
        />

        <header className="p-8 lg:p-10 relative z-10">
          <Link href="/" className="inline-flex rounded-sm transition-opacity hover:opacity-80">
            <MirynLogo size={28} showText glow />
          </Link>
        </header>

        <div className="flex flex-1 flex-col justify-center px-10 pb-[10vh] lg:px-14 relative z-10 gap-8">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[color:var(--theme-overlay)] border border-[color:var(--theme-border)] mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-[color:var(--theme-accent)]" />
              <span className="font-mono text-[10px] uppercase tracking-widest text-[color:var(--theme-muted)]">
                Persistent Intelligence
              </span>
            </div>
            <h1 className="text-[clamp(2rem,3.2vw,2.9rem)] font-light leading-[1.12] tracking-tight text-[color:var(--theme-text)]">
              An AI that actually{" "}
              <span className="font-editorial italic text-[color:var(--theme-accent)]">knows you.</span>
            </h1>
            <p className="mt-3.5 text-sm text-[color:var(--theme-muted)] leading-relaxed max-w-[40ch]">
              Continuous context across weeks, versioned identity evolution, and zero cold starts.
            </p>
          </div>

          <AnimatedChat />

          <div className="flex items-center justify-between text-[color:var(--theme-dim)] text-[10px] font-mono tracking-wider">
            <span>{"// 384-DIM PGVECTOR"}</span>
            <span>FERNET ENCRYPTED</span>
            <span>&lt;1.5S HYBRID RETRIEVAL</span>
          </div>
        </div>
      </aside>

      {/* ── Right panel ── */}
      <section className="flex min-h-dvh flex-col bg-[color:var(--theme-bg)] px-5 py-6 sm:px-8 md:px-10 lg:px-16 justify-center">
        <header className="flex justify-center py-4 md:hidden">
          <Link href="/" className="rounded-sm transition-opacity hover:opacity-80">
            <MirynLogo size={26} showText glow />
          </Link>
        </header>

        <div className="mx-auto flex w-full max-w-[420px] flex-1 flex-col justify-center py-6">
          <main>
            {title ? (
              <div className="mb-6 text-center">
                <h2 className="text-2xl font-medium tracking-tight text-[color:var(--theme-text)]">
                  {title}
                </h2>
                {subtitle ? (
                  <p className="mt-2 text-sm leading-relaxed text-[color:var(--theme-muted)]">{subtitle}</p>
                ) : null}
              </div>
            ) : null}
            {children}
          </main>
          <AuthFooter />
        </div>
      </section>
    </div>
  );
}
