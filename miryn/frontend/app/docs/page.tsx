import Link from "next/link";
import type { Metadata } from "next";
import { MessageSquare, Sparkles, Database, Heart, Settings, ArrowLeft, ArrowRight, ShieldCheck, Cpu } from "lucide-react";

export const metadata: Metadata = {
  title: "Miryn Docs — How It Works",
  description: "Learn how Miryn's memory, identity, and companion features work together.",
};

const FEATURES = [
  {
    slug: "chat",
    icon: MessageSquare,
    name: "Chat & Workspace",
    tagline: "The heart of Miryn — a conversation that remembers.",
    desc: "Every conversation with Miryn is more than a chat. Miryn listens, learns, and weaves your words into a continuous thread of memory. Start a fresh conversation, attach context documents, or resume previous threads seamlessly.",
    steps: [
      "Click New Chat in the sidebar to start a fresh thread.",
      "Type your message or attach text/code files to provide rich context.",
      "Miryn responds using your 3-tier memory layer and dynamic identity model.",
      "Previous conversations appear in the sidebar with timestamps and kebab action menus.",
      "Use the kebab (⋮) menu on each conversation to rename or delete threads cleanly.",
    ],
  },
  {
    slug: "identity",
    icon: Sparkles,
    name: "Identity Layer",
    tagline: "Miryn builds a living model of who you are.",
    desc: "As you chat, Miryn extracts your core beliefs, behavioral patterns, unresolved open loops, and emotional baseline. This is your versioned Identity Model — a map of your evolving thoughts and values.",
    steps: [
      "Navigate to Identity Layer in the sidebar.",
      "View your Core Beliefs — fundamental convictions Miryn has synthesized.",
      "Explore Behavioral Patterns (e.g. creative focus rhythms, decision tendencies).",
      "Open Loops represent unresolved thoughts — click 'Continue in chat' to explore further.",
      "Observe your Emotional Baseline and personality traits updated across reflections.",
    ],
  },
  {
    slug: "memory",
    icon: Database,
    name: "Memory Bank",
    tagline: "Your personal context, curated and encrypted at rest.",
    desc: "Miryn stores memories across three tiers: Transient (short session cache), Episodic (7-day rolling window), and Core (permanent life context). You maintain full sovereignty to add, filter, or erase any memory.",
    steps: [
      "Navigate to Memory Bank from the sidebar.",
      "Filter by All, Core, Episodic, or Emotional memory tags.",
      "Search memory items using the instant search bar.",
      "Click '+ Add Memory' to manually store an important fact or preference.",
      "Delete any memory instantly using the delete action.",
    ],
  },
  {
    slug: "sanctuary",
    icon: Heart,
    name: "Mind Sanctuary",
    tagline: "A quiet space to reset, breathe, and reflect.",
    desc: "The Mind Sanctuary synthesizes your emotional state, cognitive load, and current life season into a reflective mirror. It features guided breathing exercises designed for grounding and mindfulness.",
    steps: [
      "Navigate to Mind Sanctuary from the sidebar.",
      "Review your Emotional Baseline and Cognitive Load indicators.",
      "Read your Current Life Season — a holistic phrase summarizing your present chapter.",
      "Engage in interactive breathing routines (Box, Relax, Coherence) with gentle pacing.",
      "Click Refresh to re-synthesize metrics from your latest chat sessions.",
    ],
  },
  {
    slug: "settings",
    icon: Settings,
    name: "Settings & Sovereignty",
    tagline: "Full control over your companion, privacy, and encryption.",
    desc: "Enterprise privacy controls allow you to export your data as JSON, purge episodic retention windows, revoke active device sessions, and configure daily check-ins.",
    steps: [
      "Profile: Set your display name, view member info, and update your avatar.",
      "Security: Change account credentials and inspect active browser sessions.",
      "Notifications: Toggle daily check-in reminders and weekly digests.",
      "Data & Privacy: Export complete JSON backups, purge short-term memory, or delete account.",
    ],
  },
];

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-[#0d0d11] text-[#e8e8ec] font-sans antialiased selection:bg-[#D69155]/20 selection:text-[#D69155]">
      {/* Top Navbar */}
      <nav className="sticky top-0 z-20 border-b border-white/[0.06] bg-[#0d0d11]/90 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-[#707080] hover:text-[#e8e8ec] transition-colors"
            >
              <ArrowLeft size={13} />
              <span>Landing</span>
            </Link>
            <span className="text-[#303040]">/</span>
            <span className="text-xs font-semibold text-[#e8e8ec] tracking-wide">Documentation</span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/chat"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#D69155] hover:bg-[#E8A870] text-[#0d0d11] font-semibold text-xs rounded-xl transition-all shadow-sm"
            >
              <span>Launch App</span>
              <ArrowRight size={13} />
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Body */}
      <div className="max-w-5xl mx-auto px-6 py-12 flex flex-col lg:flex-row gap-12">
        {/* Sidebar TOC */}
        <aside className="hidden lg:flex flex-col gap-1 w-52 shrink-0 sticky top-24 self-start">
          <p className="text-[10px] font-mono uppercase tracking-widest text-[#505060] mb-3">Sections</p>
          {FEATURES.map((f) => {
            const Icon = f.icon;
            return (
              <a
                key={f.slug}
                href={`#${f.slug}`}
                className="flex items-center gap-2.5 text-xs text-[#707080] hover:text-[#D69155] transition-colors py-2 px-2.5 rounded-lg hover:bg-white/[0.03]"
              >
                <Icon size={14} className="shrink-0" />
                <span className="truncate">{f.name}</span>
              </a>
            );
          })}
        </aside>

        {/* Content Area */}
        <main className="flex-1 space-y-16">
          {/* Header */}
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#D69155]/10 border border-[#D69155]/20 text-[#D69155] text-[11px] font-mono">
              <span>Miryn AI Documentation</span>
            </div>
            <h1 className="text-3xl font-semibold tracking-tight text-[#f0f0f4]">
              How Miryn Works
            </h1>
            <p className="text-sm text-[#808090] leading-relaxed max-w-2xl">
              Miryn is an AI companion built on persistent memory and an evolving identity model. 
              Unlike conventional stateless chat interfaces, Miryn constructs a longitudinal understanding 
              of your goals, values, patterns, and conversations with end-to-end user data sovereignty.
            </p>
          </div>

          {/* Architecture Cards */}
          <div className="bg-[#121219] border border-white/[0.07] rounded-2xl p-6 space-y-5">
            <h2 className="text-xs font-mono uppercase tracking-widest text-[#505060]">Architecture Foundations</h2>
            <div className="grid sm:grid-cols-3 gap-4">
              <div className="space-y-2 p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <div className="flex items-center gap-2 text-[#D69155]">
                  <Database size={15} />
                  <p className="text-xs font-semibold text-[#e8e8ec]">3-Tier Memory</p>
                </div>
                <p className="text-xs text-[#606070] leading-relaxed">
                  Transient (session) → Episodic (7-day rolling) → Core (permanent). Context is curated automatically.
                </p>
              </div>

              <div className="space-y-2 p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <div className="flex items-center gap-2 text-[#2dd4bf]">
                  <Cpu size={15} />
                  <p className="text-xs font-semibold text-[#e8e8ec]">Identity Engine</p>
                </div>
                <p className="text-xs text-[#606070] leading-relaxed">
                  Immutable, versioned identity states track core beliefs, open loops, and cognitive habits over time.
                </p>
              </div>

              <div className="space-y-2 p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <div className="flex items-center gap-2 text-[#a78bfa]">
                  <ShieldCheck size={15} />
                  <p className="text-xs font-semibold text-[#e8e8ec]">Encrypted at Rest</p>
                </div>
                <p className="text-xs text-[#606070] leading-relaxed">
                  Fernet encryption secures user messages. Full JSON data exports and account purge on demand.
                </p>
              </div>
            </div>
          </div>

          {/* Feature Sections */}
          <div className="space-y-16">
            {FEATURES.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <section key={feature.slug} id={feature.slug} className="scroll-mt-24 space-y-5">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-xl bg-[#D69155]/10 border border-[#D69155]/20 flex items-center justify-center shrink-0 text-[#D69155] mt-1">
                      <Icon size={18} />
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase tracking-widest text-[#505060]">
                        0{index + 1} / 0{FEATURES.length}
                      </span>
                      <h2 className="text-lg font-semibold text-[#e8e8ec] mt-0.5">{feature.name}</h2>
                      <p className="text-xs text-[#D69155] mt-0.5">{feature.tagline}</p>
                    </div>
                  </div>

                  <p className="text-sm text-[#808090] leading-relaxed max-w-2xl">{feature.desc}</p>

                  <div className="bg-[#121219] border border-white/[0.07] rounded-2xl p-5 space-y-3">
                    <p className="text-[11px] font-mono uppercase tracking-wider text-[#505060]">Workflow Guide</p>
                    <ol className="space-y-2.5">
                      {feature.steps.map((step, i) => (
                        <li key={i} className="flex items-start gap-3">
                          <span className="w-5 h-5 rounded-full bg-[#D69155]/10 border border-[#D69155]/20 text-[#D69155] text-[10px] font-mono flex items-center justify-center shrink-0 mt-0.5">
                            {i + 1}
                          </span>
                          <p className="text-xs text-[#c0c0c8] leading-relaxed">{step}</p>
                        </li>
                      ))}
                    </ol>
                  </div>
                </section>
              );
            })}
          </div>

          {/* Bottom CTA */}
          <div className="text-center py-12 border-t border-white/[0.06] space-y-4">
            <p className="text-sm text-[#808090]">Ready to experience companion AI with real memory?</p>
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-[#D69155] hover:bg-[#E8A870] text-[#0d0d11] font-semibold text-xs rounded-xl transition-all shadow-md"
            >
              <span>Open Miryn Workspace</span>
              <ArrowRight size={14} />
            </Link>
          </div>
        </main>
      </div>
    </div>
  );
}
