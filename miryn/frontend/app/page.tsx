import Image from "next/image";
import LandingNav from "./landing/LandingNav";
import styles from "./landing/LandingPage.module.css";

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
    </main>
  );
}
