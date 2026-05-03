"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ChevronLeft, Fingerprint, Brain, Archive, Clock, Shield, Star, Activity, Sparkles, User, Info } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { api } from "@/lib/api";
import type { DemoPersonaDetail, Message } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";

type ViewMode = "identity" | "memory" | "history";

function TabLink({
  userId,
  view,
  current,
  children,
  icon: Icon
}: {
  userId: string;
  view: ViewMode;
  current: ViewMode;
  children: string;
  icon: any;
}) {
  const active = current === view;
  return (
    <Link
      href={`/compare/persona/${userId}?view=${view}`}
      className={`
        flex items-center gap-3 px-6 py-2.5 rounded-full transition-all relative
        ${active ? "text-primary" : "text-muted hover:text-primary"}
      `}
    >
      {active && (
        <motion.div 
          layoutId="activeTab"
          className="absolute inset-0 bg-card border border-white/[0.06] rounded-full shadow-sm"
        />
      )}
      <Icon size={16} className={active ? "text-accent" : "text-current"} />
      <span className="mono-label !text-[12px] uppercase tracking-widest relative z-10 font-bold">{children}</span>
    </Link>
  );
}

function MessageBlock({ message }: { message: Message }) {
  return (
    <div className="group rounded-[32px] border border-white/[0.04] bg-card p-8 hover:border-accent/10 transition-all">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${message.role === 'assistant' ? 'bg-accent' : 'bg-black/10'}`} />
          <span className="mono-label !text-[12px] !text-muted uppercase tracking-widest">{message.role}</span>
        </div>
        <span className="mono-label !text-[11px] !text-muted uppercase tracking-widest opacity-60">{new Date(message.timestamp).toLocaleString()}</span>
      </div>
      <p className="text-lg leading-relaxed text-primary/90 editorial-italic">&ldquo;{message.content}&rdquo;</p>
      {message.metadata && Object.keys(message.metadata).length > 0 && (
        <pre className="mt-8 whitespace-pre-wrap break-words rounded-2xl bg-white/[0.03] border border-white/[0.04] p-6 text-xs text-muted font-mono leading-relaxed overflow-x-auto">
          {JSON.stringify(message.metadata, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default function PersonaDetailView({ userId }: { userId: string }) {
  const searchParams = useSearchParams();
  const selectedView = (searchParams.get("view") || "identity") as ViewMode;
  const [detail, setDetail] = useState<DemoPersonaDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.loadToken();
    void api
      .getDemoPersonaDetail(userId)
      .then(setDetail)
      .catch((err) => setError(getErrorMessage(err, "Failed to load persona detail")));
  }, [userId]);

  const messages = useMemo(() => {
    if (!detail) return [];
    return detail.conversations.flatMap((conversation) => conversation.messages);
  }, [detail]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-12 bg-void">
        <div className="bg-card border border-red-500/20 rounded-[40px] p-12 text-center max-w-xl">
          <Shield className="w-12 h-12 text-red-500/40 mx-auto mb-6" />
          <h2 className="text-2xl font-bold mb-4 text-primary">Inspection Interrupted</h2>
          <p className="text-red-500/60 font-mono text-sm uppercase tracking-widest leading-loose">{error}</p>
        </div>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-void">
        <div className="flex flex-col items-center gap-8">
           <motion.div 
             animate={{ rotate: 360 }}
             transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
             className="w-16 h-16 rounded-full border-t-2 border-accent shadow-[0_0_20px_rgba(139,92,246,0.1)]"
           />
          <div className="mono-label !text-accent uppercase tracking-[0.3em] animate-pulse">Retrieving Neural Profile...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-void text-primary p-8 md:p-16 relative overflow-x-hidden">
      {/* Background Ambient Glows */}
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-accent/[0.05] rounded-full blur-[180px] pointer-events-none -z-10" />
      <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-accent/[0.02] rounded-full blur-[150px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header Section */}
        <header className="mb-20">
          <Link href="/compare" className="group inline-flex items-center gap-4 mb-10 text-muted hover:text-primary transition-all">
            <div className="w-10 h-10 rounded-full border border-white/[0.06] bg-white flex items-center justify-center group-hover:border-accent/40 transition-all shadow-sm">
               <ChevronLeft size={16} className="group-hover:text-accent transition-all" />
            </div>
            <span className="mono-label !text-[12px] uppercase tracking-[0.3em]">Back to Matrix</span>
          </Link>
          
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-12">
            <div className="space-y-6 max-w-3xl">
              <div className="flex items-center gap-4">
                <Fingerprint className="text-accent w-10 h-10" />
                <h2 className="mono-label !text-accent !text-sm uppercase tracking-[0.4em]">Inspection Active</h2>
              </div>
              <h1 className="text-6xl md:text-9xl font-bold tracking-tighter leading-[0.9]">
                {detail.profile.label}<span className="text-accent">.profile</span>
              </h1>
              <p className="text-2xl md:text-3xl text-muted editorial-italic leading-relaxed">
                "{detail.profile.goal}"
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 md:min-w-[320px]">
               <div className="bg-card border border-white/[0.06] p-8 rounded-[32px] shadow-sm">
                 <span className="mono-label !text-[11px] !text-muted uppercase tracking-widest block mb-1">Resonance</span>
                 <div className="text-3xl font-serif text-accent">{detail.identity.state}</div>
               </div>
               <div className="bg-card border border-white/[0.06] p-8 rounded-[32px] shadow-sm">
                 <span className="mono-label !text-[11px] !text-muted uppercase tracking-widest block mb-1">Architecture</span>
                 <div className="text-3xl font-serif text-primary">v{detail.identity.version}</div>
               </div>
               <div className="bg-card border border-white/[0.06] p-8 rounded-[32px] shadow-sm">
                 <span className="mono-label !text-[11px] !text-muted uppercase tracking-widest block mb-1">Drift Coefficient</span>
                 <div className="text-3xl font-serif text-primary">{detail.identity_metrics.drift?.toFixed(2) ?? "--"}</div>
               </div>
               <div className="bg-card border border-white/[0.06] p-8 rounded-[32px] shadow-sm">
                 <span className="mono-label !text-[11px] !text-muted uppercase tracking-widest block mb-1">Mood Trend</span>
                 <div className="text-3xl font-serif text-primary">{detail.emotion_metrics.trend}</div>
               </div>
            </div>
          </div>
        </header>

        {/* View Switcher */}
        <div className="mb-20 inline-flex items-center p-2 rounded-full bg-white/[0.03] border border-white/[0.06] shadow-sm">
          <TabLink userId={userId} view="identity" current={selectedView} icon={Brain}>Neural State</TabLink>
          <TabLink userId={userId} view="memory" current={selectedView} icon={Archive}>Archived Fragment</TabLink>
          <TabLink userId={userId} view="history" current={selectedView} icon={Clock}>Interactions</TabLink>
        </div>

        {/* Content Area */}
        <AnimatePresence mode="wait">
          <motion.div
            key={selectedView}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
          >
            {selectedView === "identity" && (
              <div className="space-y-20">
                <section className="grid md:grid-cols-2 gap-10">
                   <div className="bg-card border border-white/[0.06] p-10 rounded-[40px] relative overflow-hidden shadow-sm">
                      <div className="absolute top-0 right-0 p-8 opacity-[0.04]">
                        <Brain size={120} />
                      </div>
                      <div className="flex items-center gap-4 mb-10 relative z-10">
                        <Brain size={24} className="text-accent" />
                        <h2 className="mono-label !text-primary !text-sm uppercase tracking-widest">Trait Distribution</h2>
                      </div>
                      <div className="flex flex-wrap gap-3 relative z-10">
                        {Object.entries(detail.identity.traits || {}).map(([key, value]) => (
                          <div key={key} className="flex items-center gap-3 px-4 py-2 rounded-full bg-white/[0.03] border border-white/[0.06] hover:border-accent/40 transition-all cursor-default group shadow-sm">
                            <span className="mono-label !text-[12px] !text-muted group-hover:text-accent transition-colors uppercase tracking-widest">{key}</span>
                            <span className="text-xs text-primary font-mono font-medium">{typeof value === "number" ? value.toFixed(2) : String(value)}</span>
                          </div>
                        ))}
                      </div>
                   </div>

                   <div className="bg-card border border-white/[0.06] p-10 rounded-[40px] relative overflow-hidden shadow-sm">
                      <div className="absolute top-0 right-0 p-8 opacity-[0.04]">
                        <Activity size={120} />
                      </div>
                      <div className="flex items-center gap-4 mb-10 relative z-10">
                        <Activity size={24} className="text-accent" />
                        <h2 className="mono-label !text-primary !text-sm uppercase tracking-widest">Value Alignment</h2>
                      </div>
                      <div className="flex flex-wrap gap-3 relative z-10">
                        {Object.entries(detail.identity.values || {}).map(([key, value]) => (
                          <div key={key} className="flex items-center gap-3 px-4 py-2 rounded-full bg-white/[0.03] border border-white/[0.06] hover:border-accent/40 transition-all cursor-default group shadow-sm">
                            <span className="mono-label !text-[12px] !text-muted group-hover:text-accent transition-colors uppercase tracking-widest">{key}</span>
                            <span className="text-xs text-primary font-mono font-medium">{typeof value === "number" ? value.toFixed(2) : String(value)}</span>
                          </div>
                        ))}
                      </div>
                   </div>
                </section>

                <section className="grid md:grid-cols-2 gap-10">
                  <div className="space-y-8">
                     <div className="flex items-center gap-4 mb-6">
                       <Star className="text-accent" size={18} />
                       <h3 className="text-2xl font-bold tracking-tight">Epistemic Beliefs</h3>
                     </div>
                     <div className="space-y-4">
                       {detail.identity.beliefs.map((b, i) => (
                         <div key={i} className="p-10 rounded-[40px] bg-card border border-white/[0.06] shadow-sm hover:border-accent/30 transition-all group relative">
                           <span className="mono-label !text-[10px] !text-accent uppercase tracking-widest block mb-4">{b.topic}</span>
                           <p className="text-lg text-[#e0e0e0]/90 leading-relaxed editorial-italic">"{b.belief}"</p>
                         </div>
                       ))}
                     </div>
                  </div>

                  <div className="space-y-8">
                     <div className="flex items-center gap-4 mb-6">
                       <Sparkles className="text-white/30" size={18} />
                       <h3 className="text-2xl font-bold tracking-tight">Open Cognitive Loops</h3>
                     </div>
                     <div className="space-y-4">
                       {detail.identity.open_loops.map((l, i) => (
                         <div key={i} className="p-10 rounded-[40px] bg-card border border-white/[0.06] shadow-sm hover:border-white/[0.06] transition-all flex justify-between items-center group">
                           <div>
                             <span className="mono-label !text-[10px] !text-white/30 uppercase tracking-widest block mb-2">{l.topic}</span>
                             <div className="text-[12px] text-dim uppercase tracking-widest">Status: {l.status}</div>
                           </div>
                           <div className="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/[0.04]">
                             <span className="mono-label !text-white/30 !text-[10px]">PRIORITY P{l.importance}</span>
                           </div>
                         </div>
                       ))}
                     </div>
                  </div>
                </section>
              </div>
            )}

            {selectedView === "memory" && (
              <div className="grid gap-10 lg:grid-cols-3">
                {[
                  { title: "Ephemeral", items: detail.memory_snapshot.recent, icon: Clock, color: "text-accent" },
                  { title: "Axiomatic", items: detail.memory_snapshot.facts, icon: Brain, color: "text-dim/60" },
                  { title: "Resonant", items: detail.memory_snapshot.emotions, icon: Star, color: "text-white/30" },
                ].map((s) => (
                  <section key={s.title} className="space-y-8">
                    <div className="flex items-center gap-4 mb-6">
                      <s.icon size={16} className={s.color} />
                      <h3 className="text-xl font-bold tracking-tight">{s.title}</h3>
                    </div>
                    <div className="space-y-4">
                      {s.items.map((m) => (
                        <MessageBlock key={m.id || m.timestamp} message={m} />
                      ))}
                    </div>
                  </section>
                ))}
              </div>
            )}

            {selectedView === "history" && (
              <div className="space-y-12">
                 {detail.conversations.map((c) => (
                  <section key={c.id} className="bg-card border border-white/[0.06] rounded-[64px] p-16 hover:border-accent/10 transition-all shadow-sm">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-16 border-b border-white/[0.06] pb-12">
                      <div>
                        <div className="flex items-center gap-3 mb-2">
                           <Clock size={16} className="text-accent" />
                           <span className="mono-label !text-accent !text-sm uppercase tracking-widest font-bold">Conversation Retrieval</span>
                        </div>
                        <h2 className="text-4xl md:text-5xl font-bold tracking-tighter">{c.title}</h2>
                      </div>
                      <div className="text-xs mono-label !text-muted uppercase tracking-widest font-medium">
                        Node Synchronized {new Date(c.updated_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="space-y-8 max-w-4xl mx-auto">
                      {c.messages.map((m) => (
                        <MessageBlock key={m.id || m.timestamp} message={m} />
                      ))}
                    </div>
                  </section>
                ))}
                {messages.length === 0 && (
                  <div className="bg-card border border-white/[0.06] border-dashed p-32 rounded-[48px] text-center shadow-sm">
                    <span className="mono-label !text-muted uppercase tracking-[0.5em] text-sm">No interaction logs detected</span>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        <footer className="mt-40 text-center pb-20">
           <div className="inline-flex items-center gap-4 px-10 py-5 rounded-full bg-white/[0.03] border border-white/[0.06] hover:bg-black/[0.04] transition-all cursor-pointer shadow-sm">
             <Shield size={20} className="text-muted" />
             <span className="mono-label !text-[13px] !text-muted uppercase tracking-[0.2em] font-bold">Authenticated Neural Audit</span>
           </div>
        </footer>
      </div>
    </div>
  );
}

