import Image from "next/image";
import type { ReactNode } from "react";
import LandingNav from "./landing/LandingNav";
import styles from "./landing/LandingPage.module.css";

const stats = [
  ["Short, Episodic & Core Long-Term Memory", "3 layers", "Short, episodic, and core long-term memory for instant retrieval."],
  ["Background Identity Evolution", "24/7", "Asynchronous reflection workers continuously update your profile."],
  ["Fernet Payload Encryption", "100%", "Fernet payload encryption keeps private thoughts strictly yours."],
  ["Goal Completion Rate", "88%", "Open-loop tracking and async reflection close goals before they drift."],
] as const;

const moods = [
  ["Seeing red", "You might be feeling a bit frustrated or tense.", "#e9806e"],
  ["Feeling light", "Seems like you have a good day!", "#d2edb4"],
  ["Feeling blue", "It looks like something’s weighing on your mind.", "#8bb8ef"],
  ["Lost in thought", "Feeling a little anxious? Take a deep breath.", "#c5a4dd"],
] as const;

export default function LandingPage() {
  return (
    <main className={`${styles.landing} font-ui`}>
      <LandingNav />

      <section id="hero" className="relative isolate mx-auto max-w-7xl px-5 pb-24 pt-20 sm:px-8 sm:pt-28 lg:px-12 lg:pb-32 lg:pt-32">
        <div className={`${styles.heroGrid} pointer-events-none absolute inset-x-0 top-0 -z-10 h-[680px]`} />
        <div className="mx-auto max-w-4xl text-center">
          <div className={`${styles.reveal} mx-auto inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs text-[#A3A3A3]`}>
            <span aria-hidden="true">✦</span> Introducing Miryn AI — Next-Gen Companion
          </div>
          <h1 className={`${styles.revealDelay} mt-7 font-editorial text-4xl leading-[1.08] tracking-[-0.04em] text-[#FAFAFA] sm:text-6xl lg:text-[68px]`}>
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

        <div className="relative mx-auto mt-16 h-[300px] max-w-4xl overflow-hidden rounded-[2rem] border border-white/10 bg-[#12151c] shadow-[0_0_100px_rgba(86,133,255,0.12)] sm:h-[440px]">
          <div className={`${styles.orb} absolute inset-0`} />
          <div className={`${styles.orbCore} absolute left-1/2 top-1/2 h-44 w-44 -translate-x-1/2 -translate-y-1/2 rounded-full sm:h-64 sm:w-64`} />
          <Image src="/assets/Uhwo2wpkTp0XMacGw2OugvIL0U.webp" alt="Abstract black and white memory layers" fill priority sizes="(max-width: 640px) 90vw, 896px" className="object-cover opacity-15 mix-blend-screen" />
          <div className={`${styles.grain} absolute inset-0`} />
          <div className="absolute bottom-5 left-5 rounded-full border border-white/10 bg-black/30 px-3 py-1.5 text-xs text-[#A3A3A3] backdrop-blur-md sm:bottom-7 sm:left-7">Persistent context · always with you</div>
        </div>
      </section>

      <section id="about" className="mx-auto grid max-w-6xl gap-10 px-5 py-20 sm:px-8 lg:grid-cols-[.8fr_1.2fr] lg:items-center lg:gap-20 lg:py-28">
        <div>
          <p className="font-editorial text-sm uppercase tracking-[0.22em] text-[#A3A3A3]">ABOUT MIRYN</p>
          <h2 className="mt-5 font-editorial text-4xl leading-tight tracking-[-0.03em] sm:text-5xl">A companion that keeps the thread.</h2>
        </div>
        <div className="grid gap-7 sm:grid-cols-[.9fr_1.1fr] sm:items-center">
          <div className="relative aspect-[4/5] overflow-hidden rounded-3xl border border-white/10 bg-[#151515]">
            <Image src="/assets/A4rnasqJDMazGtLN9cqF0u3G37Y.webp" alt="Soft abstract waves" fill sizes="(max-width: 640px) 90vw, 360px" className="object-cover opacity-75" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0A0A0A]/80 via-transparent to-white/10" />
            <span className="absolute bottom-5 left-5 font-editorial text-lg">Memory, with a pulse.</span>
          </div>
          <p className="text-base leading-8 text-[#A3A3A3] sm:text-lg">
            Traditional AI tools reset every time you close the tab. Miryn is different. We built Miryn around an evolving identity engine that learns who you are over time—tracking your core beliefs, behavior patterns, emotions, and unresolved goals so every interaction feels deeply personal and continuous.
          </p>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-6xl px-5 py-20 sm:px-8 lg:py-28">
        <div className="max-w-3xl">
          <p className="font-editorial text-sm uppercase tracking-[0.22em] text-[#A3A3A3]">CORE HIGHLIGHTS</p>
          <h2 className="mt-5 font-editorial text-4xl leading-tight tracking-[-0.04em] sm:text-6xl">Core systems for continuous understanding</h2>
        </div>

        <div className="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map(([title, value, description]) => (
            <article key={title} className="rounded-2xl border border-white/10 bg-white/[0.035] p-5">
              <h3 className="min-h-10 text-[13.5px] leading-5 text-[#A3A3A3]">{title}</h3>
              <p className="mt-5 font-editorial text-5xl tracking-[-0.04em] text-[#FAFAFA]">{value}</p>
              <p className="mt-3 text-[13px] leading-5 text-[#A3A3A3]/75">{description}</p>
            </article>
          ))}
        </div>

        <div className="mt-3 grid gap-3 lg:grid-cols-2">
          <ChartCard title="Memory layer performance" label="Memory Retrieval" ticks={["16.0", "14.0", "12.0"]} points="8,64 55,52 102,55 149,34 196,38 243,19 290,25 337,8" area="8,64 55,52 102,55 149,34 196,38 243,19 290,25 337,8 337,82 8,82" />
          <ChartCard title="Identity evolution over time" label="Identity Evolution" ticks={["100%", "80%", "60%"]} points="8,69 55,62 102,64 149,48 196,43 243,30 290,25 337,10" area="8,69 55,62 102,64 149,48 196,43 243,30 290,25 337,10 337,82 8,82" />
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-20 sm:px-8 lg:py-28">
        <p className="font-editorial text-sm uppercase tracking-[0.22em] text-[#A3A3A3]">CORE CAPABILITIES</p>
        <h2 className="mt-5 max-w-3xl font-editorial text-4xl leading-tight tracking-[-0.04em] sm:text-6xl">Everything You Need in a Lifelong AI Companion</h2>

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
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_60%_40%,rgba(107,229,190,.16),transparent_48%)]" />
              <div className="relative space-y-3 pt-5">
                {[['Transient memory', '2 hours', 'bg-[#9be7bd]'], ['Episodic memory', '7 days', 'bg-[#88baf4]'], ['Core memory', 'Always', 'bg-[#c9a4e8']].map(([name, duration, color]) => <div key={name} className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-5 py-4"><span className="flex items-center gap-3 text-sm text-[#FAFAFA]"><span className={`h-2 w-2 rounded-full ${color}`} />{name}</span><span className="text-xs text-[#A3A3A3]">{duration}</span></div>)}
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
            <div className="rounded-3xl border border-white/10 bg-[#151515] p-6">
              <div className="flex items-center justify-between border-b border-white/10 pb-5"><span className="font-editorial text-xl">Open loops</span><span className="rounded-full bg-[#d5f4dc] px-2.5 py-1 text-xs text-[#1c3b28]">3 active</span></div>
              <div className="mt-6 space-y-4">{['Prepare visa interview', 'Finish the personal essay', 'Return to morning walks'].map((item, index) => <div key={item} className="flex items-center gap-3 text-sm text-[#A3A3A3]"><span className={`h-3 w-3 rounded-full border ${index === 0 ? 'border-[#d5f4dc] bg-[#d5f4dc]' : 'border-[#525252]'}`} />{item}<span className="ml-auto text-xs text-[#525252]">{index === 0 ? 'today' : 'soon'}</span></div>)}</div>
            </div>
          </CapabilityRow>

          <CapabilityRow title="Understand Your Personal Growth" copy="Receive periodic reflection summaries highlighting mood patterns, stress triggers, and recurring thought loops across your daily logs.">
            <div className="rounded-3xl border border-white/10 bg-[#151515] p-6 sm:p-8"><p className="text-xs uppercase tracking-[0.2em] text-[#525252]">Reflection loop</p><div className="mt-8 grid gap-3 sm:grid-cols-3">{['Spot the Pattern', 'Find the Loop', 'Choose the Next Step'].map((step, index) => <div key={step} className="relative rounded-2xl border border-white/10 p-4"><span className="font-editorial text-2xl text-[#FAFAFA]">0{index + 1}</span><p className="mt-6 text-sm text-[#A3A3A3]">{step}</p>{index < 2 && <span className="absolute -right-3 top-1/2 hidden text-[#525252] sm:block">→</span>}</div>)}</div></div>
          </CapabilityRow>
        </div>
      </section>
    </main>
  );
}

function ChartCard({ title, label, ticks, points, area }: { title: string; label: string; ticks: string[]; points: string; area: string }) {
  return (
    <article className="rounded-3xl border border-white/10 bg-white/[0.035] p-5 sm:p-7">
      <p className="text-sm text-[#A3A3A3]">{title}</p>
      <p className="mt-2 font-editorial text-2xl">{label}</p>
      <div className="mt-7 grid grid-cols-[38px_1fr] gap-3">
        <div className="flex h-28 flex-col justify-between text-[10px] text-[#525252]">{ticks.map((tick) => <span key={tick}>{tick}</span>)}</div>
        <div>
          <svg viewBox="0 0 345 90" className="h-28 w-full overflow-visible" role="img" aria-label={`${label} chart`} preserveAspectRatio="none"><path d={area} fill="rgba(159, 235, 199, .12)" /><polyline points={points} fill="none" stroke="#9fe9c5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
          <div className="mt-2 flex justify-between text-[10px] text-[#525252]"><span>Week 1</span><span>Week 4</span></div>
        </div>
      </div>
    </article>
  );
}

function CapabilityRow({ title, copy, reverse = false, children }: { title: string; copy: string; reverse?: boolean; children: ReactNode }) {
  return (
    <div className={`grid items-center gap-10 lg:grid-cols-2 lg:gap-20 ${reverse ? "lg:[&>*:first-child]:order-2" : ""}`}>
      <div><h3 className="font-editorial text-4xl leading-tight tracking-[-0.03em] text-[#FAFAFA]">{title}</h3><p className="mt-5 max-w-xl text-base leading-8 text-[#A3A3A3] sm:text-lg">{copy}</p></div>
      <div>{children}</div>
    </div>
  );
}
