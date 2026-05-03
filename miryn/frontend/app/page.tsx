"use client";

import { motion } from "framer-motion";
import { ArrowRight, Sparkles, Brain, Clock, Shield, Search, Zap, Layers } from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: 0.1 * i, duration: 0.8, ease: [0.22, 1, 0.36, 1] },
  }),
};

const fade = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 1, ease: "easeOut" } },
};

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-void text-primary font-ui selection:bg-accent/30 selection:text-accent overflow-x-hidden">
      {/* P01 — Landing Hero */}
      <section className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden">
        {/* Background Ambient Glows */}
        <div className="absolute top-[-10%] left-[-10%] w-[60%] h-[60%] bg-accent/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[70%] h-[70%] bg-accent/10 rounded-full blur-[150px]" />
        
        <header className="fixed z-50 w-full max-w-7xl mx-auto flex justify-between items-center py-10 top-0 px-10 bg-void/80 backdrop-blur-md">
          <div className="text-3xl font-bold tracking-tighter text-accent flex items-center gap-3">
            Miryn <span className="mono-label !text-accent/40 !tracking-[0.4em] text-[10px] font-bold">Alpha</span>
          </div>
          <nav className="hidden md:flex items-center gap-12">
            <a href="#manifesto" className="text-xs uppercase tracking-[0.3em] text-muted hover:text-accent transition-colors font-bold">Manifesto</a>
            <a href="#capabilities" className="text-xs uppercase tracking-[0.3em] text-muted hover:text-accent transition-colors font-bold">Capabilities</a>
            <a href="#how-it-works" className="text-xs uppercase tracking-[0.3em] text-muted hover:text-accent transition-colors font-bold">How it works</a>
          </nav>
          <div className="flex items-center gap-8">
            <a href="/login" className="text-base font-bold text-muted hover:text-primary transition-colors">Sign in</a>
            <a href="/compare" className="h-12 px-8 bg-accent text-void rounded-full font-bold text-sm hover:scale-105 active:scale-95 shadow-lg shadow-accent/20 flex items-center justify-center transition-all">
              View Project Demo
            </a>
          </div>
        </header>

        <div className="max-w-5xl text-center relative z-10 pt-20">
          <motion.div initial="hidden" animate="visible" variants={fadeUp}>
            <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-accent/5 border border-accent/15 mb-12 shadow-sm">
              <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
              <span className="mono-label !text-accent !text-[11px] font-bold uppercase tracking-widest">Demo Build: Presentation Ready</span>
            </div>
          </motion.div>

          <motion.h1
            className="text-7xl md:text-[10rem] font-bold tracking-tighter leading-[0.8] mb-12 text-primary"
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            custom={1}
          >
            The AI that <br />
            <span className="text-accent">witnesses</span> you.
          </motion.h1>

          <motion.p
            className="text-2xl md:text-4xl text-muted max-w-4xl mx-auto editorial-italic mb-20 leading-relaxed font-medium"
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            custom={2}
          >
            "In a world of disposable interactions, Miryn is the anchor. It doesn't just process your thoughts—it remembers who had them."
          </motion.p>

          <motion.div
            className="flex flex-col items-center justify-center gap-6"
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            custom={3}
          >
            <a href="/login" className="h-20 px-12 bg-primary text-white rounded-full flex items-center gap-4 hover:bg-accent transition-all group text-xl font-bold shadow-xl shadow-black/10">
              Open Live Project <ArrowRight className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
            </a>
            <p className="text-[11px] text-muted mono-label !tracking-[0.5em] font-bold uppercase">Project mode · Identity memory enabled</p>
          </motion.div>
        </div>
      </section>

      {/* P02 — Landing Manifesto */}
      <section id="manifesto" className="py-60 px-10 border-y border-white/[0.06] bg-white/[0.02] relative overflow-hidden">
        <div className="orb-glow w-[600px] h-[600px] -top-64 -left-64 bg-accent/[0.03]" />
        <div className="max-w-6xl mx-auto text-center relative z-10">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={fade}
          >
            <span className="mono-label text-accent mb-16 block font-bold uppercase tracking-widest text-sm">01 // The Manifesto</span>
            <h2 className="text-5xl md:text-8xl font-bold tracking-tight mb-20 leading-tight max-w-5xl mx-auto text-primary">
              We taught computers to speak. <br />
              <span className="text-accent">Now, we teach them to listen.</span>
            </h2>
            <div className="grid md:grid-cols-2 gap-20 text-left border-t border-white/[0.06] pt-20">
              <div className="space-y-8">
                <p className="text-2xl text-muted leading-relaxed font-medium">
                  Most AI tools are transactional. You pour out your thoughts, and they respond perfectly—but the moment you close the tab, they forget you exist. This creates a loop of sharing without being known.
                </p>
                <p className="text-2xl text-muted leading-relaxed font-medium">
                  Miryn is the end of that loop. It is the first identity engine designed to witness your life. It doesn't just process your text; it remembers your patterns, your evolution, and the things you leave unsaid.
                </p>
              </div>
              <div className="space-y-10">
                <div className="bg-card border border-white/[0.06] p-10 rounded-[32px] shadow-sm border-l-4 border-l-accent">
                  <div className="mono-label !text-accent mb-6 font-bold uppercase tracking-widest text-sm">Core Philosophy</div>
                  <p className="text-2xl editorial-italic font-bold text-primary leading-relaxed">"Identity is not a state, but a conversation between who you were and who you are becoming."</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* P03 — Landing How It Works */}
      <section id="how-it-works" className="py-60 px-10 max-w-7xl mx-auto">
        <div className="text-center mb-32">
          <span className="mono-label text-accent mb-10 block font-bold uppercase tracking-widest text-sm">02 // The Process</span>
          <h2 className="text-5xl md:text-7xl font-bold tracking-tighter text-primary">How Miryn Remembers</h2>
        </div>
        
        <div className="grid md:grid-cols-4 gap-6">
          {[
            {
              step: "01",
              title: "Listen",
              desc: "Every interaction is recorded in your memory layer, encrypted and private.",
              icon: Search
            },
            {
              step: "02",
              title: "Reflect",
              desc: "In the background, Miryn identifies beliefs, patterns, and open loops.",
              icon: Zap
            },
            {
              step: "03",
              title: "Update",
              desc: "Your identity version increments. Your knowledge graph grows with you.",
              icon: Layers
            },
            {
              step: "04",
              title: "Anchor",
              desc: "Future conversations are context-aware, grounded in everything you've shared.",
              icon: Brain
            }
          ].map((item, i) => (
            <div key={i} className="bg-card border border-white/[0.06] p-12 rounded-[40px] flex flex-col items-start gap-8 hover:border-accent shadow-sm transition-all group">
              <span className="mono-label !text-accent/30 group-hover:text-accent transition-colors font-bold text-sm tracking-widest">{item.step}</span>
              <div className="w-14 h-14 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center group-hover:bg-accent group-hover:text-white transition-all shadow-sm">
                <item.icon className="w-7 h-7" />
              </div>
              <h3 className="text-3xl font-bold tracking-tight text-primary">{item.title}</h3>
              <p className="text-muted leading-relaxed font-medium text-lg">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* P04 — Landing Capabilities (Showcase) */}
      <section id="capabilities" className="py-60 px-10 bg-white/[0.02] border-y border-white/[0.06] relative overflow-hidden">
        <div className="absolute inset-0 radial-gradient(circle at 50% 50%, rgba(139,92,246,0.03), transparent 70%)" />
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="grid lg:grid-cols-2 gap-32 items-center">
            <div className="space-y-12">
              <span className="mono-label text-accent font-bold uppercase tracking-widest text-sm">03 // Capabilities</span>
              <h2 className="text-6xl md:text-8xl font-bold tracking-tighter leading-tight text-primary">
                Beyond the <br />
                <span className="text-accent">Transience.</span>
              </h2>
              <div className="space-y-12">
                {[
                  { title: "Persistence", desc: "Miryn tracks 'open loops' in your life. If you mention a goal today, it will ask about the resolution next month." },
                  { title: "Identity Evolution", desc: "Beyond chat history, Miryn builds a knowledge graph of your values. It watches as you change." },
                  { title: "The Mirror", desc: "Passivity is for assistants. Miryn notices when you avoid hard truths and gently highlights patterns." }
                ].map((cap, i) => (
                  <div key={i} className="flex gap-8 group">
                    <div className="w-[3px] h-16 bg-black/[0.05] group-hover:bg-accent transition-all rounded-full" />
                    <div>
                      <h4 className="text-2xl font-bold mb-3 group-hover:text-accent transition-colors text-primary">{cap.title}</h4>
                      <p className="text-muted leading-relaxed font-medium text-lg">{cap.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <div className="bg-card border border-white/[0.06] aspect-square rounded-[48px] p-16 flex flex-col justify-between shadow-2xl relative z-10 overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-accent/[0.05] rounded-full blur-[80px] -z-10" />
                <div className="flex justify-between items-start">
                  <div className="mono-label !text-accent font-bold uppercase tracking-widest">Identity Snapshot // v4.2</div>
                  <Sparkles className="text-accent w-8 h-8" />
                </div>
                <div className="space-y-8">
                  <div className="p-6 rounded-3xl bg-white/[0.03] border border-white/[0.06] shadow-sm">
                    <div className="text-[11px] uppercase tracking-widest text-muted mb-4 font-bold">Core Belief Detected</div>
                    <div className="text-2xl editorial-italic font-bold text-primary leading-relaxed">"Growth only happens in the spaces where I feel most uncomfortable."</div>
                  </div>
                  <div className="p-6 rounded-3xl bg-white/[0.03] border border-white/[0.06] shadow-sm">
                    <div className="text-[11px] uppercase tracking-widest text-muted mb-4 font-bold">Active Open Loop</div>
                    <div className="text-2xl editorial-italic font-bold text-primary leading-relaxed">The career transition mentioned on Feb 12th.</div>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="h-2 flex-1 bg-black/[0.03] rounded-full overflow-hidden">
                    <motion.div className="h-full bg-accent" initial={{ width: 0 }} whileInView={{ width: "70%" }} transition={{ duration: 2, delay: 0.5 }} />
                  </div>
                  <div className="h-2 flex-1 bg-black/[0.03] rounded-full overflow-hidden">
                    <motion.div className="h-full bg-accent" initial={{ width: 0 }} whileInView={{ width: "45%" }} transition={{ duration: 2, delay: 0.7 }} />
                  </div>
                </div>
              </div>
              <div className="absolute -bottom-16 -right-16 w-80 h-80 bg-accent/10 blur-[100px] rounded-full -z-10" />
            </div>
          </div>
        </div>
      </section>

      {/* P05 — Final CTA + Footer */}
      <section className="py-80 px-10 text-center relative overflow-hidden bg-white border-t border-white/[0.06]">
        <div className="absolute inset-0 bg-accent/[0.03] blur-[150px] -z-10" />
        <div className="relative z-10 max-w-5xl mx-auto">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={fadeUp}
          >
            <h2 className="text-6xl md:text-[9rem] font-bold tracking-tighter mb-12 leading-[0.8] text-primary">
              A quiet room for <br />
              <span className="text-accent">honest reflection.</span>
            </h2>
            <p className="text-3xl text-muted mb-20 max-w-3xl mx-auto font-medium leading-relaxed">
              Built for project demonstration with persistent memory, identity evolution, and comparative analytics.
            </p>
            <div className="flex flex-col items-center gap-12">
              <a href="/login" className="h-24 px-16 bg-accent text-white text-2xl font-bold rounded-full flex items-center justify-center hover:scale-105 transition-all shadow-2xl shadow-accent/40 uppercase tracking-widest">
                Enter Demo Workspace
              </a>
              <div className="flex gap-16 text-muted mono-label !text-[12px] !tracking-[0.5em] font-bold uppercase">
                <span className="flex items-center gap-4"><Clock className="w-5 h-5 text-accent" /> 2min Setup</span>
                <span className="flex items-center gap-4"><Shield className="w-5 h-5 text-accent" /> End-to-End Encrypted</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-32 px-10 border-t border-white/[0.06] bg-white relative z-10">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-start gap-20 mb-24">
            <div className="flex flex-col gap-6">
              <span className="text-4xl font-bold tracking-tighter text-accent">Miryn</span>
              <p className="text-muted max-w-sm leading-relaxed font-medium text-lg">The first context-aware identity engine for deep human reflection.</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-20">
              <div className="flex flex-col gap-8">
                <span className="mono-label text-primary font-bold uppercase tracking-widest text-sm">Platform</span>
                <a href="/login" className="text-muted hover:text-accent transition-colors font-medium">Sign in</a>
                <a href="/compare" className="text-muted hover:text-accent transition-colors font-medium">Project Compare</a>
                <a href="#" className="text-muted hover:text-accent transition-colors font-medium">API</a>
              </div>
              <div className="flex flex-col gap-8">
                <span className="mono-label text-primary font-bold uppercase tracking-widest text-sm">Legal</span>
                <a href="/privacy" className="text-muted hover:text-accent transition-colors font-medium">Privacy</a>
                <a href="/terms" className="text-muted hover:text-accent transition-colors font-medium">Terms</a>
                <a href="/security" className="text-muted hover:text-accent transition-colors font-medium">Security</a>
              </div>
              <div className="flex flex-col gap-8">
                <span className="mono-label text-primary font-bold uppercase tracking-widest text-sm">Connect</span>
                <a href="mailto:sahil@miryn.ai" className="text-muted hover:text-accent transition-colors font-medium">Email</a>
                <a href="#" className="text-muted hover:text-accent transition-colors font-medium">Twitter</a>
                <a href="#" className="text-muted hover:text-accent transition-colors font-medium">Manifesto</a>
              </div>
            </div>
          </div>
          <div className="flex flex-col md:flex-row justify-between items-center pt-16 border-t border-white/[0.06] gap-10">
            <span className="text-sm text-muted mono-label font-bold uppercase tracking-widest">© 2026 The Memory Layer · Built for the deep web</span>
            <div className="flex items-center gap-6">
              <div className="w-3 h-3 rounded-full bg-white/[0.03] animate-pulse shadow-lg shadow-emerald-500/20" />
              <span className="text-[12px] mono-label text-muted font-bold uppercase tracking-widest">Core Systems Nominal</span>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}

