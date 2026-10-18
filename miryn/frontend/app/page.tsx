import Image from "next/image";
import type { ReactNode } from "react";
import type { Metadata } from "next";
import HeroCards from "./landing/HeroCards";
import AboutReveal from "./landing/AboutReveal";
import CountUp from "./landing/CountUp";
import LandingNav from "./landing/LandingNav";
import MoodCarousel from "./landing/MoodCarousel";
import Reveal from "./landing/Reveal";
import SpectrumOrb from "./landing/SpectrumOrb";
import ToolIcons from "./landing/ToolIcons";
import WaveChart from "./landing/WaveChart";
import styles from "./landing/LandingPage.module.css";

const stats = [
  ["Short, Episodic & Core Long-Term Memory", "3 layers", "Short, episodic, and core long-term memory for instant retrieval."],
  ["Background Identity Evolution", "24/7", "Asynchronous reflection workers continuously update your profile."],
  ["Fernet Payload Encryption", "100%", "Fernet payload encryption keeps private thoughts strictly yours."],
  ["Goal Completion Rate", "88%", "Open-loop tracking and async reflection close goals before they drift."],
] as const;

const moods = [
  ["Seeing red", "You might be feeling a bit frustrated or tense.", "#eb2c50"],
  ["Feeling light", "Seems like you have a good day!", "#fee435"],
  ["Feeling blue", "It looks like something’s weighing on your mind.", "#4788c8"],
  ["Lost in thought", "Feeling a little anxious? Take a deep breath.", "#5a54a4"],
] as const;

const faqs = [
  ["What is Miryn AI?", "Miryn is a personal AI companion with an evolving identity model and persistent memory. It learns your preferences, tracks your goals, and remembers details across conversations."],
  ["How does Miryn remember past conversations?", "Miryn uses a 3-tier memory pipeline—transient, 7-day vector episodic, and core long-term memory—to retrieve relevant context in real time whenever you talk."],
  ["Is my conversation history private and secure?", "Yes. Stored memory logs and context payloads are encrypted using Fernet AES encryption standards. Your data belongs strictly to you and is never sold or shared."],
  ["Can I view or delete what Miryn knows about me?", "Yes. You have complete control over your identity profile and can view, edit, or clear memories, open loops, or traits at any time from your account settings."],
  ["How is Miryn different from standard AI assistants?", "Standard AI tools reset after every thread. Miryn runs an active identity reflection engine that synthesizes your habits, goals, and values across sessions."],
  ["Is Miryn free to start?", "Yes. You can get started with Miryn for free and experience persistent AI companionship right away."],
] as const;

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "https://miryn.ai"),
  title: "Miryn AI — Persistent Memory & Evolving AI Companion",
  description: "Miryn is a private AI companion that remembers your goals, values, and patterns, then brings the right context back as you learn and evolve together.",
  alternates: { canonical: "/" },
  openGraph: {
    title: "Miryn AI — Persistent Memory & Evolving AI Companion",
    description: "A private AI companion that remembers, learns, and evolves with you.",
    url: "/",
    type: "website",
    images: [{ url: "/assets/YvyHGDMBNlHMvnGhZ52M3DnFDYc.webp", width: 849, height: 1200, alt: "Abstract Miryn AI memory texture" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Miryn AI — Persistent Memory & Evolving AI Companion",
    description: "A private AI companion that remembers, learns, and evolves with you.",
    images: ["/assets/YvyHGDMBNlHMvnGhZ52M3DnFDYc.webp"],
  },
};

export default function LandingPage() {
  return (
    <main className={`${styles.landing} landing font-ui`}>
      <LandingNav />

      <Reveal ambient as="section" id="hero" className="landing-hero relative isolate mx-auto max-w-7xl overflow-clip px-5 pb-24 pt-20 sm:px-8 sm:pt-28 lg:px-12 lg:pb-32 lg:pt-32">
        <div className={`${styles.sectionGlow} ${styles.sectionGlowHero}`} aria-hidden="true" />
        <div className={`${styles.heroGrid} pointer-events-none absolute inset-x-0 top-0 -z-10 h-[680px]`} aria-hidden="true" />
        <SpectrumOrb />
        <div className="hero-copy mx-auto max-w-6xl text-center">
          <div className={`${styles.reveal} mx-auto inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs text-[#A3A3A3]`}>
            <span aria-hidden="true">✦</span> Introducing Miryn AI — Next-Gen Companion
          </div>
          <h1 className={`${styles.revealDelay} mt-7 font-editorial text-4xl leading-[1.08] tracking-[-0.04em] text-[#FAFAFA] sm:text-6xl lg:text-[clamp(3rem,3.15vw,4rem)] xl:whitespace-nowrap`}>
            An AI Companion That Remembers, Learns, and Evolves With You.
          </h1>
          <p className="mx-auto mt-7 max-w-2xl text-base leading-7 text-[#A3A3A3] sm:text-lg">
            Miryn goes beyond standard chatbots. Powered by persistent long-term memory and a dynamic identity engine, Miryn understands your values, tracks your goals, and grows alongside you across every conversation.
          </p>
          <div className="mt-9 flex flex-col justify-center gap-3 sm:flex-row">
            <a href="/signup" className="inline-flex min-h-12 items-center justify-center rounded-full bg-[#FAFAFA] px-6 font-editorial text-base text-[#0A0A0A] transition-transform hover:-translate-y-0.5">Try Miryn Free</a>
            <a href="#features" className="inline-flex min-h-12 items-center justify-center rounded-full border border-white/15 px-6 font-editorial text-base text-[#FAFAFA] transition-colors hover:border-white/50">Explore Features →</a>
          </div>
        </div>

        <HeroCards />
        <ToolIcons />
      </Reveal>

      <section id="about" className="relative isolate overflow-clip mx-auto max-w-6xl px-5 py-20 sm:px-8 lg:py-28">
        <div className={`${styles.sectionGlow} ${styles.sectionGlowAbout}`} aria-hidden="true" />
        <div className="about-intro">
          <AboutReveal />
        </div>
        <div className="about-second-row mt-14 grid gap-8 lg:grid-cols-[.85fr_1.15fr] lg:items-center lg:gap-20">
          <Reveal>
            <h2 className="font-editorial text-4xl leading-tight tracking-[-0.03em] sm:text-5xl">A companion that keeps the thread.</h2>
          </Reveal>
          <Reveal>
          <div className="relative aspect-[16/9] overflow-hidden rounded-3xl border border-white/10 bg-[#151515] sm:aspect-[4/3]">
            <Image src="/assets/A4rnasqJDMazGtLN9cqF0u3G37Y.webp" alt="Soft abstract waves" fill sizes="(max-width: 640px) 90vw, 360px" className="object-cover opacity-75" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0A0A0A]/80 via-transparent to-white/10" />
            <span className="absolute bottom-5 left-5 font-editorial text-lg">Memory, with a pulse.</span>
          </div>
          </Reveal>
        </div>
      </section>

      <section id="features" className="relative isolate overflow-clip mx-auto max-w-6xl px-5 py-20 sm:px-8 lg:py-28">
        <div className={`${styles.sectionGlow} ${styles.sectionGlowFeatures}`} aria-hidden="true" />
        <Reveal className="max-w-3xl">
          <p className="section-eyebrow section-eyebrow--highlights"><i />CORE HIGHLIGHTS</p>
          <h2 className="mt-5 font-editorial text-4xl leading-tight tracking-[-0.04em] sm:text-6xl">Core systems for continuous understanding</h2>
        </Reveal>

        <div className="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map(([title, value, description], index) => (
            <Reveal as="article" key={title} delay={index * 70} className="feature-card rounded-2xl border border-white/10 bg-white/[0.035] p-5">
              <h3 className="min-h-10 font-editorial text-[13.5px] leading-5 text-[#A3A3A3]">{title}</h3>
              <p className="mt-5 font-editorial text-5xl tracking-[-0.04em] text-[#FAFAFA]"><CountUp value={value} /></p>
              <p className="mt-3 text-[13px] leading-5 text-[#A3A3A3]/75">{description}</p>
            </Reveal>
          ))}
        </div>

        <div className="mt-3 grid gap-3 lg:grid-cols-2">
          <Reveal><WaveChart title="Memory layer performance" label="Memory Retrieval" ticks={["16.0", "14.0", "12.0"]} accent="#a78bfa" variant="memory" /></Reveal>
          <Reveal><WaveChart title="Identity evolution over time" label="Identity Evolution" ticks={["100%", "80%", "60%"]} accent="#e7c86e" variant="identity" /></Reveal>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-20 sm:px-8 lg:py-28">
        <Reveal>
          <p className="section-eyebrow section-eyebrow--capabilities"><i />CORE CAPABILITIES</p>
          <h2 className="mt-5 max-w-3xl font-editorial text-4xl leading-tight tracking-[-0.04em] sm:text-6xl">Everything You Need in a Lifelong AI Companion</h2>
        </Reveal>

        <div className="mt-16 space-y-24 lg:space-y-32">
          <CapabilityRow title="Personality That Adapts to You" copy="Miryn logs versioned traits, values, core beliefs, and emotional nuances. Over time, Miryn tailors its communication style to match your preferences and emotional state.">
            <div className="rounded-3xl border border-white/10 bg-[#151515] p-5 shadow-2xl shadow-black/20 sm:p-7">
              <div className="flex items-center gap-3 border-b border-white/10 pb-5">
                <div className="h-9 w-9 rounded-full bg-gradient-to-br from-[#d4ffe9] to-[#6a7aff]" />
                <div><p className="text-sm text-[#FAFAFA]">Miryn</p><p className="text-xs text-[#525252]">Your reflective companion</p></div>
              </div>
              <p className="mt-7 font-editorial text-2xl leading-tight text-[#FAFAFA]">What are we working on today? 👋</p>
              <p className="mt-3 text-sm leading-6 text-[#A3A3A3]">Let’s reflect on what matters most and find the next useful step.</p>
              <div className="mt-8 flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-[#525252]"><span>You want some help?</span><span className="text-[#A3A3A3]">↗</span></div>
              <div className="mt-4 flex flex-wrap gap-2"><span className="rounded-full border border-white/10 px-3 py-1 text-xs text-[#A3A3A3]">🌿 Core Values</span><span className="rounded-full border border-white/10 px-3 py-1 text-xs text-[#A3A3A3]">🌱 Identity Signals</span></div>
            </div>
          </CapabilityRow>

          <CapabilityRow title="Context That Never Fades" copy="Combines fast Redis transient memory, 7-day vector search episodic memory, and long-term core memory to bring up relevant details in less than 1.5 seconds." reverse>
            <div className="relative min-h-[300px] overflow-hidden rounded-3xl border border-white/10 bg-[#111] p-6">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_60%_40%,rgb(var(--theme-accent-rgb)/.16),transparent_48%)]" />
              <div className="relative space-y-3 pt-5">
                {[['Transient memory', '2 hours', 'bg-[#9be7bd]'], ['Episodic memory', '7 days', 'bg-[#88baf4]'], ['Core memory', 'Always', 'bg-[#c9a4e8]']].map(([name, duration, color]) => <div key={name} className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-5 py-4"><span className="flex items-center gap-3 text-sm text-[#FAFAFA]"><span className={`h-2 w-2 rounded-full ${color}`} />{name}</span><span className="text-xs text-[#A3A3A3]">{duration}</span></div>)}
              </div>
              <div className="relative mt-8 flex flex-wrap gap-2"><span className="rounded-full bg-white/[0.07] px-3 py-1.5 text-xs text-[#A3A3A3]">🧠 Open Loops</span><span className="rounded-full bg-white/[0.07] px-3 py-1.5 text-xs text-[#A3A3A3]">🌙 Memory Recall</span><span className="rounded-full bg-white/[0.07] px-3 py-1.5 text-xs text-[#A3A3A3]">💖 Reflection</span><span className="rounded-full bg-white/[0.07] px-3 py-1.5 text-xs text-[#A3A3A3]">🧘 Daily Context</span></div>
            </div>
          </CapabilityRow>

          <CapabilityRow title="Emotional context, without the guesswork" copy="Miryn notices the emotional texture of your conversations and gives you a gentle, useful reflection instead of a generic mood label.">
            <div className="grid grid-cols-2 gap-3">
              {moods.map(([title, copy, color]) => <div key={title} className="min-h-[170px] rounded-3xl border border-white/10 bg-[#151515] p-4" style={{ borderTopColor: color }}><div className="flex items-start justify-between"><h3 className="font-editorial text-lg text-[#FAFAFA]">{title}</h3><span className="text-xs text-[#525252]">Today</span></div><p className="mt-8 text-[11px] text-[#525252]">Thu, Apr 3</p><p className="mt-2 text-xs leading-5 text-[#A3A3A3]">{copy}</p></div>)}
            </div>
          </CapabilityRow>

          <CapabilityRow title="Track Goals & Unresolved Ideas" copy="Never lose track of a project, thought, or goal. Miryn recognizes open loops in your life and reminds you when it’s time to check in." reverse>
            <div className="space-y-5">
            <div className="rounded-3xl border border-white/10 bg-[#151515] p-6">
              <div className="flex items-center justify-between border-b border-white/10 pb-5"><span className="font-editorial text-xl">Open loops</span><span className="rounded-full bg-[#d5f4dc] px-2.5 py-1 text-xs text-[#1c3b28]">3 active</span></div>
              <div className="mt-6 space-y-4">{['Prepare visa interview', 'Finish the personal essay', 'Return to morning walks'].map((item, index) => <div key={item} className="flex items-center gap-3 text-sm text-[#A3A3A3]"><span className={`h-3 w-3 rounded-full border ${index === 0 ? 'border-[#d5f4dc] bg-[#d5f4dc]' : 'border-[#525252]'}`} />{item}<span className="ml-auto text-xs text-[#525252]">{index === 0 ? 'today' : 'soon'}</span></div>)}</div>
            </div>
            <MoodCarousel />
            </div>
          </CapabilityRow>

          <CapabilityRow title="Understand Your Personal Growth" copy="Receive periodic reflection summaries highlighting mood patterns, stress triggers, and recurring thought loops across your daily logs.">
            <div className="rounded-3xl border border-white/10 bg-[#151515] p-6 sm:p-8"><p className="text-xs uppercase tracking-[0.2em] text-[#525252]">Reflection loop</p><div className="mt-8 grid gap-3 sm:grid-cols-3">{['Spot the Pattern', 'Find the Loop', 'Choose the Next Step'].map((step, index) => <div key={step} className="relative rounded-2xl border border-white/10 p-4"><span className="font-editorial text-2xl text-[#FAFAFA]">0{index + 1}</span><p className="mt-6 text-sm text-[#A3A3A3]">{step}</p>{index < 2 && <span className="absolute -right-3 top-1/2 hidden text-[#525252] sm:block">→</span>}</div>)}</div></div>
          </CapabilityRow>
        </div>
      </section>

      <section id="faq" className="mx-auto max-w-6xl px-5 py-20 sm:px-8 lg:py-28">
        <Reveal><p className="section-eyebrow section-eyebrow--faq"><i />FREQUENTLY ASKED QUESTIONS</p></Reveal>
        <Reveal><h2 className="mt-5 font-editorial text-4xl leading-tight tracking-[-0.04em] sm:text-6xl">Everything You Need to Know About Miryn</h2></Reveal>
        <div className="faq-grid mt-12">
          {[faqs.slice(0, 3), faqs.slice(3)].map((column, columnIndex) => <div className="faq-column" key={columnIndex}>
            {column.map(([question, answer], index) => <Reveal key={question} delay={index * 70}><details className="faq-row group"><summary><span>{question}</span><span className="faq-plus" aria-hidden="true">+</span></summary><p>{answer}</p></details></Reveal>)}
          </div>)}
        </div>
      </section>

      <section id="contact" className="relative isolate overflow-clip mx-auto max-w-6xl px-5 py-20 sm:px-8 lg:py-28">
        <div className={`${styles.sectionGlow} ${styles.sectionGlowContact}`} aria-hidden="true" />
        <Reveal className="contact-card rounded-[2rem] border border-white/10 bg-[#151515] px-6 py-16 text-center sm:px-12 lg:py-24"><div className="contact-aurora" aria-hidden="true" /><h2 className="relative font-editorial text-4xl tracking-[-0.04em] sm:text-6xl">We’d Love to Hear From You</h2><p className="relative mx-auto mt-5 max-w-xl text-base leading-7 text-[#A3A3A3] sm:text-lg">Have questions, suggestions, or feedback about Miryn? Our team is here to assist you.</p><a href="mailto:hello@miryn.ai" className="relative mt-8 inline-flex min-h-12 items-center justify-center rounded-full bg-[#FAFAFA] px-7 font-editorial text-base text-[#0A0A0A]">Send Message</a></Reveal>
      </section>

      <footer className="border-t border-white/10">
        <div className="mx-auto grid max-w-6xl gap-12 px-5 py-16 sm:px-8 lg:grid-cols-[1.5fr_1fr_1fr]">
          <Reveal><div><a href="/" className="inline-flex min-h-11 items-center font-editorial text-2xl text-[#FAFAFA]">Miryn AI</a><p className="mt-4 max-w-xs text-sm leading-6 text-[#A3A3A3]">Empowering Personal Growth Through Persistent Intelligence.</p></div></Reveal>
          <Reveal><FooterColumn title="Sections" links={[["About", "#about"], ["Features", "#features"], ["FAQ's", "#faq"], ["Contact", "#contact"]]} /></Reveal>
          <Reveal><FooterColumn title="Pages" links={[["Privacy & Security", "/privacy"], ["Terms of Service", "/terms"], ["Contact", "#contact"]]} /></Reveal>
        </div>
        <div className="mx-auto flex max-w-6xl flex-col gap-3 border-t border-white/10 px-5 py-6 text-xs text-[#8F8F8F] sm:flex-row sm:items-center sm:justify-between sm:px-8"><span>Miryn AI</span><span>© 2026 Miryn AI Inc. All rights reserved. · Designed &amp; Built by <a href="https://sharmasahil.me" target="_blank" rel="noopener noreferrer" className="inline-flex min-h-11 items-center text-[#A3A3A3] underline underline-offset-4">Sahil Sharma</a></span></div>
      </footer>

      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify({ "@context": "https://schema.org", "@type": "FAQPage", mainEntity: faqs.map(([name, text]) => ({ "@type": "Question", name, acceptedAnswer: { "@type": "Answer", text } })) }) }} />
    </main>
  );
}

function FooterColumn({ title, links }: { title: string; links: readonly (readonly [string, string])[] }) {
  return <div><p className="font-editorial text-base text-[#FAFAFA]">{title}</p><div className="mt-3 flex flex-col items-start">{links.map(([label, href]) => <a key={`${title}-${label}`} href={href} className="flex min-h-11 min-w-11 items-center text-sm text-[#A3A3A3] transition-colors hover:text-[#FAFAFA]">{label}</a>)}</div></div>;
}

function CapabilityRow({ title, copy, reverse = false, children }: { title: string; copy: string; reverse?: boolean; children: ReactNode }) {
  return (
    <Reveal as="div" className={`grid grid-cols-1 items-center gap-10 [&>*]:min-w-0 lg:grid-cols-2 lg:gap-20 ${reverse ? "lg:[&>*:first-child]:order-2" : ""}`}>
      <div><h3 className="font-editorial text-4xl leading-tight tracking-[-0.03em] text-[#FAFAFA]">{title}</h3><p className="mt-5 max-w-xl text-base leading-8 text-[#A3A3A3] sm:text-lg">{copy}</p></div>
      <div>{children}</div>
    </Reveal>
  );
}
