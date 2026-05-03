"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { EvolutionLogEntry, Identity } from "@/lib/types";
import { Fingerprint, Zap, Brain, Activity, History, Shield, Globe, Star, Sparkles, ChevronRight, Info } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

function ScoredPill({ label, value }: { label: string; value: unknown }) {
  const numValue = typeof value === "number" ? value : null;
  return (
    <div className="flex items-center gap-3 rounded-full border border-white/[0.06] bg-white/[0.03] px-4 py-2 transition-all hover:border-accent/40 hover:bg-accent/5 group cursor-default shadow-sm">
      <span className="mono-label !text-[12px] !text-muted group-hover:text-accent transition-colors uppercase tracking-widest">
        {label}
      </span>
      {numValue !== null && (
        <span className="text-xs text-[#c8b8ff] font-mono font-medium">
          {numValue.toFixed(2)}
        </span>
      )}
    </div>
  );
}

function Meter({ value, label }: { value: number, label?: string }) {
  const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div className="space-y-2">
      {label && (
        <div className="flex justify-between items-center px-1">
          <span className="mono-label !text-[11px] !text-muted uppercase tracking-widest">{label}</span>
          <span className="mono-label !text-[11px] !text-[#c8b8ff]">{pct}%</span>
        </div>
      )}
      <div className="h-1.5 w-full rounded-full bg-white/[0.06] overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1.5, ease: [0.23, 1, 0.32, 1] }}
          className="h-full rounded-full bg-[#c8b8ff] shadow-[0_0_15px_rgba(200,184,255,0.15)]"
        />
      </div>
    </div>
  );
}

export default function IdentityDashboard() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [evolution, setEvolution] = useState<EvolutionLogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.loadToken();
    const loadData = () => {
      api.getIdentity().then(setIdentity).catch((e) => setError(e.message || "Failed to load identity"));
      api.getEvolution().then((data) => setEvolution(data || [])).catch(() => setEvolution([]));
    };
    loadData();
  }, []);

  const stats = useMemo(() => {
    if (!identity) return null;
    return {
      beliefs: identity.beliefs?.length || 0,
      loops: identity.open_loops?.length || 0,
      patterns: identity.patterns?.length || 0,
      conflicts: identity.conflicts?.length || 0,
    };
  }, [identity]);

  if (error) {
    return (
      <div className="p-12 max-w-2xl mx-auto">
        <div className="bg-[#050505] border border-red-500/10 rounded-[32px] p-10 text-center">
          <Shield className="w-12 h-12 text-red-500/40 mx-auto mb-6" />
          <h2 className="text-2xl font-semibold mb-4 text-white">Sync Interrupted</h2>
          <p className="text-red-400/60 font-mono text-xs uppercase tracking-widest leading-loose">{error}</p>
        </div>
      </div>
    );
  }

  if (!identity) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-void">
        <div className="flex flex-col items-center gap-8">
          <div className="relative">
            <div className="w-20 h-20 rounded-full border border-white/[0.06] flex items-center justify-center">
               <motion.div 
                 animate={{ rotate: 360 }}
                 transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                 className="w-14 h-14 rounded-full border-t-2 border-accent shadow-[0_0_20px_rgba(139,92,246,0.1)]"
               />
            </div>
          </div>
          <div className="mono-label !text-accent uppercase tracking-[0.3em] animate-pulse">Reconstituting Matrix...</div>
        </div>
      </div>
    );
  }

  const traitKeys = Object.keys(identity.traits || {});
  const valueKeys = Object.keys(identity.values || {});

  return (
    <div className="min-h-screen bg-void text-primary p-8 md:p-16 relative overflow-x-hidden">
      {/* Background Ambient Glows */}
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-accent/[0.04] rounded-full blur-[180px] pointer-events-none -z-10" />
      <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-accent/[0.02] rounded-full blur-[150px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto">
        {/* Breadcrumb / Status */}
        <div className="flex items-center gap-4 mb-12">
           <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/[0.03] border border-white/[0.06]">
             <div className="w-2 h-2 rounded-full bg-accent" />
             <span className="mono-label !text-[12px] !text-muted uppercase tracking-widest">Resonance Active</span>
           </div>
           <div className="h-[1px] w-12 bg-black/[0.08]" />
           <span className="mono-label !text-[12px] !text-muted uppercase tracking-widest">ID: {identity.id?.slice(0, 12)}</span>
        </div>

        {/* Hero Header */}
        <header className="mb-24 flex flex-col md:flex-row md:items-end justify-between gap-12">
          <div className="space-y-6 max-w-3xl">
            <div className="flex items-center gap-4">
               <Fingerprint className="text-accent w-10 h-10" />
               <h2 className="mono-label !text-accent !text-sm uppercase tracking-[0.4em]">Identity Protocol</h2>
            </div>
            <h1 className="text-6xl md:text-9xl font-bold tracking-tighter leading-[0.9]">
              {(identity as any).email?.split('@')[0] || "anon"}<span className="text-accent">.matrix</span>
            </h1>
            <p className="text-2xl md:text-3xl text-muted editorial-italic leading-relaxed">
              &ldquo;A reflection of thoughts, patterns, and beliefs woven into a digital persistent layer. Current sync: {identity.version || "1.0.4"}&rdquo;
            </p>
          </div>
          
          <div className="flex flex-col items-end gap-3">
             <div className="text-right">
               <span className="mono-label !text-[12px] !text-muted uppercase tracking-widest block mb-2 text-right">System State</span>
               <div className="px-10 py-4 rounded-3xl bg-accent/5 border border-accent/10">
                 <span className="text-accent font-bold text-xl uppercase tracking-widest">{identity.state}</span>
               </div>
             </div>
          </div>
        </header>

        {/* Stats Matrix */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-24">
          {[
            { label: "Epistemic Beliefs", val: stats?.beliefs, icon: Star, color: "text-accent" },
            { label: "Active Loops", val: stats?.loops, icon: Zap, color: "text-white/50" },
            { label: "Observed Behaviors", val: stats?.patterns, icon: Activity, color: "text-dim" },
            { label: "Identity Conflicts", val: stats?.conflicts, icon: Shield, color: "text-red-500" },
          ].map((s, i) => (
            <motion.div 
              key={i} 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="bg-card border border-white/[0.06] p-8 rounded-[32px] group hover:border-accent/10 transition-all relative overflow-hidden shadow-sm"
            >
              <div className="absolute -right-4 -bottom-4 opacity-[0.03] group-hover:opacity-[0.06] transition-opacity">
                <s.icon size={120} />
              </div>
              <div className="flex items-center justify-between mb-6 relative z-10">
                <div className={`p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] ${s.color}`}>
                  <s.icon size={18} />
                </div>
                <span className="mono-label !text-[11px] !text-muted uppercase tracking-widest">Metric {i+1}</span>
              </div>
              <div className="text-6xl font-bold tracking-tighter mb-2 relative z-10">{s.val}</div>
              <div className="mono-label !text-muted !text-[12px] uppercase tracking-widest relative z-10">{s.label}</div>
            </motion.div>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-12">
          {/* Belief Matrix */}
          <div className="lg:col-span-2 space-y-12">
            <section>
              <div className="flex items-center gap-6 mb-10">
                <div className="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center">
                  <Star size={18} className="text-accent" />
                </div>
                <h2 className="text-2xl font-bold tracking-tight">Epistemic Belief Layers</h2>
              </div>
              
              <div className="grid md:grid-cols-2 gap-6">
                {(identity.beliefs || []).map((belief, idx) => (
                  <motion.div 
                    key={idx}
                    whileHover={{ y: -4 }}
                    className="p-8 rounded-[32px] bg-card border border-white/[0.06] hover:border-accent/20 transition-all relative group shadow-sm"
                  >
                    <div className="flex justify-between items-start mb-6">
                      <div className="space-y-1">
                        <span className="mono-label !text-[12px] !text-accent uppercase tracking-widest">{belief.topic}</span>
                        <div className="text-sm text-muted">Node Persistence</div>
                      </div>
                      <div className="px-3 py-1 rounded-full bg-white/[0.03] border border-white/[0.06]">
                        <span className="mono-label !text-[11px] !text-primary">{((belief.confidence ?? 0) * 100).toFixed(0)}% CONFIDENCE</span>
                      </div>
                    </div>
                    <p className="text-xl text-primary/90 leading-relaxed editorial-italic mb-8 h-24 overflow-hidden">
                      &ldquo;{belief.belief}&rdquo;
                    </p>
                    <Meter value={belief.confidence ?? 0} />
                  </motion.div>
                ))}
              </div>
            </section>

            <section>
              <div className="flex items-center gap-6 mb-10">
                <div className="w-10 h-10 rounded-full bg-white/[0.03] flex items-center justify-center">
                  <Activity size={18} className="text-dim/60" />
                </div>
                <h2 className="text-2xl font-bold tracking-tight">Behavioral Vectors</h2>
              </div>
              
              <div className="space-y-4">
                {(identity.patterns || []).map((pattern, idx) => (
                  <div key={idx} className="group p-8 rounded-[32px] bg-card border border-white/[0.06] hover:border-accent/10 transition-all flex flex-col md:flex-row gap-8 items-center shadow-sm">
                    <div className="w-full md:w-48 space-y-1">
                      <span className="mono-label !text-[12px] !text-dim uppercase tracking-widest">{pattern.pattern_type}</span>
                      <div className="text-[12px] text-muted uppercase tracking-widest">Observed Pattern</div>
                    </div>
                    <div className="flex-1 space-y-4 w-full">
                       <p className="text-base text-muted leading-relaxed">&ldquo;{pattern.description}&rdquo;</p>
                       <Meter value={pattern.confidence ?? 0} />
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {/* Personality Architecture */}
          <div className="lg:col-span-1 space-y-10">
             <section className="bg-card border border-white/[0.06] rounded-[40px] p-10 relative overflow-hidden shadow-sm">
                <div className="absolute top-0 right-0 p-8 opacity-[0.04]">
                  <Brain size={120} />
                </div>
                <div className="flex items-center gap-4 mb-10 relative z-10">
                  <Brain size={24} className="text-accent" />
                  <h2 className="mono-label !text-primary !text-sm uppercase tracking-widest">Trait Distribution</h2>
                </div>
                <div className="flex flex-wrap gap-3 relative z-10">
                  {traitKeys.map((key) => (
                    <ScoredPill key={key} label={key} value={identity.traits[key]} />
                  ))}
                </div>
             </section>

             <section className="bg-card border border-white/[0.06] rounded-[40px] p-10 relative overflow-hidden shadow-sm">
                <div className="absolute top-0 right-0 p-8 opacity-[0.04]">
                  <Globe size={120} />
                </div>
                <div className="flex items-center gap-4 mb-10 relative z-10">
                  <Globe size={24} className="text-accent" />
                  <h2 className="mono-label !text-primary !text-sm uppercase tracking-widest">Core Value Map</h2>
                </div>
                <div className="flex flex-wrap gap-3 relative z-10">
                  {valueKeys.map((key) => (
                    <ScoredPill key={key} label={key} value={identity.values[key]} />
                  ))}
                </div>
             </section>

             <div className="p-10 rounded-[40px] bg-accent/5 border border-accent/10 space-y-6 shadow-sm">
                <div className="flex items-center gap-3">
                   <Info size={20} className="text-accent" />
                   <span className="mono-label !text-accent !text-sm uppercase tracking-widest">Architecture Note</span>
                </div>
                <p className="text-base text-muted leading-relaxed">
                  Identity resonance is calculated based on consistency across conversational nodes. Higher values indicate deeper structural alignment with the core persona.
                </p>
             </div>
          </div>
        </div>

        {/* Evolution Timeline */}
        <section className="mt-32">
          <div className="flex items-center gap-8 mb-16">
            <div className="flex items-center gap-4">
              <History className="text-accent w-6 h-6" />
              <h2 className="text-3xl font-bold tracking-tight">Evolution Timeline</h2>
            </div>
            <div className="h-[1px] flex-1 bg-gradient-to-r from-white/[0.05] to-transparent" />
          </div>

          <div className="relative space-y-6">
            {/* Vertical Line */}
            <div className="absolute left-[31px] top-4 bottom-4 w-[1px] bg-white/[0.03] hidden md:block" />

            {evolution.length === 0 ? (
              <div className="bg-card border border-white/[0.06] border-dashed p-20 rounded-[32px] text-center shadow-sm">
                <span className="mono-label !text-muted uppercase tracking-[0.5em]">No significant shifts detected</span>
              </div>
            ) : (
              evolution.slice(0, 8).map((entry, idx) => (
                <motion.div 
                  key={entry.id}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.1 }}
                  className="relative pl-0 md:pl-20 group"
                >
                  <div className="absolute left-[26px] top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-white border border-black/[0.1] group-hover:border-accent group-hover:scale-110 transition-all hidden md:block z-10 shadow-sm" />
                  
                  <div className="bg-card border border-white/[0.06] rounded-[48px] p-10 flex flex-col md:flex-row gap-10 hover:border-accent/10 transition-all shadow-sm">
                    <div className="md:w-48 shrink-0 space-y-2">
                      <div className="flex items-center gap-3 text-muted">
                        <span className="mono-label !text-[12px] font-medium tracking-widest">{new Date(entry.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                      </div>
                      <div className="text-accent font-bold uppercase tracking-[0.2em] text-sm">{entry.field_changed} Shift</div>
                    </div>
                    
                    <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-3">
                         <span className="mono-label !text-[11px] !text-muted uppercase tracking-widest block">Original State</span>
                         <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm text-muted font-mono truncate">
                           {typeof entry.old_value === 'object' ? JSON.stringify(entry.old_value) : entry.old_value}
                         </div>
                      </div>
                      <div className="space-y-3 relative">
                         <div className="absolute -left-6 top-1/2 -translate-y-1/2 text-black/5 hidden md:block">
                           <ChevronRight size={16} />
                         </div>
                         <span className="mono-label !text-[11px] !text-accent uppercase tracking-widest block">New Convergence</span>
                         <div className="p-4 rounded-xl bg-accent/5 border border-accent/10 text-sm text-primary font-mono truncate">
                           {typeof entry.new_value === 'object' ? JSON.stringify(entry.new_value) : entry.new_value}
                         </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </section>

        {/* Footer Note */}
        <footer className="mt-40 text-center pb-20">
           <div className="inline-flex items-center gap-4 px-6 py-3 rounded-full bg-white/[0.03] border border-white/[0.06]">
             <Shield size={16} className="text-muted" />
             <span className="mono-label !text-[12px] !text-muted uppercase tracking-widest">End-to-End Encrypted Persistence Layer</span>
           </div>
        </footer>
      </div>
    </div>
  );
}

