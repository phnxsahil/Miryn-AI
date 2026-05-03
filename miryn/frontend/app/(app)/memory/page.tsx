"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { MemoryItem, MemorySnapshot } from "@/lib/types";
import { Archive, Clock, Trash2, Shield, Brain, Layers, Star, Plus } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

function MemoryCard({
  item,
  onForget,
}: {
  item: MemoryItem;
  onForget: (id: string) => void;
}) {
  const date = item.created_at ? new Date(item.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }) : "Unknown";
  const importance = item.importance_score || 0;

  return (
    <motion.div 
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="bg-card border border-white/[0.04] p-10 rounded-[40px] group hover:border-accent/30 transition-all duration-500 relative overflow-hidden"
    >
      <div className="absolute top-0 right-0 w-32 h-32 bg-accent/[0.02] blur-3xl pointer-events-none group-hover:bg-accent/[0.05] transition-colors" />
      
      <div className="flex justify-between items-start mb-8">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            {[1, 2, 3, 4, 5].map((i) => (
              <div 
                key={i} 
                className={`w-1.5 h-4 rounded-full transition-all duration-500 ${
                  (importance * 5) >= i ? "bg-accent shadow-[0_0_8px_rgba(200,184,255,0.4)]" : "bg-white/[0.06]"
                }`} 
              />
            ))}
          </div>
          <span className="mono-label !text-[11px] !text-dim uppercase tracking-widest ml-2">Resonance</span>
        </div>
        <span className="mono-label !text-[11px] !text-dim uppercase tracking-widest">{date}</span>
      </div>

      <p className="text-xl text-primary/80 leading-relaxed mb-10 editorial-italic h-32 overflow-hidden line-clamp-4">
        "{item.content || "Archived fragment..."}"
      </p>

      <div className="flex items-center justify-between pt-8 border-t border-white/[0.04]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-white/[0.03] border border-white/[0.06] flex items-center justify-center">
            <Shield size={12} className="text-dim" />
          </div>
          <span className="text-[10px] mono-label !text-dim uppercase tracking-[0.2em]">Vaulted Fragment</span>
        </div>
        <button
          onClick={() => onForget(item.id)}
          className="p-3 rounded-2xl text-dim hover:text-red-400 hover:bg-red-500/[0.06] transition-all opacity-0 group-hover:opacity-100"
          title="Forget this fragment"
        >
          <Trash2 size={16} />
        </button>
      </div>
    </motion.div>
  );
}

export default function MemoryPage() {
  const [snapshot, setSnapshot] = useState<MemorySnapshot | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.loadToken();
    api.getMemory().then(setSnapshot).finally(() => setLoading(false));
  }, []);

  const empty = useMemo(() => {
    if (!snapshot) return true;
    return snapshot.recent.length === 0 && snapshot.facts.length === 0 && snapshot.emotions.length === 0;
  }, [snapshot]);

  const handleForget = async (id: string) => {
    await api.deleteMemory(id);
    if (!snapshot) return;
    setSnapshot({
      recent: snapshot.recent.filter((item) => item.id !== id),
      facts: snapshot.facts.filter((item) => item.id !== id),
      emotions: snapshot.emotions.filter((item) => item.id !== id),
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-void">
        <div className="flex flex-col items-center gap-10">
           <motion.div 
             animate={{ rotate: 360 }}
             transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
             className="w-16 h-16 rounded-full border-t-2 border-accent shadow-[0_0_20px_rgba(200,184,255,0.15)]"
           />
          <div className="mono-label !text-accent uppercase tracking-[0.4em] animate-pulse">Scanning Neural Archive...</div>
        </div>
      </div>
    );
  }

  if (!snapshot || empty) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-void p-12">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-card border border-white/[0.04] p-24 rounded-[60px] max-w-3xl text-center relative overflow-hidden"
        >
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-accent/[0.03] blur-[120px] pointer-events-none" />
          <div className="w-24 h-24 rounded-3xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mx-auto mb-12">
            <Archive className="w-10 h-10 text-dim" />
          </div>
          <h2 className="text-5xl font-bold tracking-tighter mb-8 text-primary">The Archive is Silent</h2>
          <p className="text-muted text-2xl editorial-italic leading-relaxed max-w-lg mx-auto">
            "Memory is not a recording; it is a construction. Start a reflection to begin the architecture of the self."
          </p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-void text-primary p-8 md:p-16 relative overflow-x-hidden">
      <div className="absolute top-0 left-0 w-[800px] h-[800px] bg-accent/[0.05] rounded-full blur-[180px] pointer-events-none -z-10" />
      
      <div className="max-w-7xl mx-auto relative z-10">
        <header className="mb-40 max-w-4xl">
          <div className="flex items-center gap-4 mb-10">
            <div className="w-10 h-10 rounded-xl bg-accent/[0.08] border border-accent/15 flex items-center justify-center">
              <Archive className="text-accent w-5 h-5" />
            </div>
            <span className="mono-label !text-accent uppercase tracking-[0.4em]">Persistence Layer</span>
          </div>
          <h1 className="text-6xl md:text-9xl font-bold tracking-tighter leading-[0.8] mb-12">Neural <span className="text-accent">Snapshot</span></h1>
          <p className="text-2xl md:text-3xl text-muted editorial-italic leading-relaxed max-w-3xl">
            A live retrieval of your mental architecture. These fragments represent the anchor points of your digital identity.
          </p>
        </header>

        <div className="space-y-32">
          {/* Recent Fragments */}
          <section>
            <div className="flex items-center gap-10 mb-16">
              <div className="flex items-center gap-5">
                <div className="w-12 h-12 rounded-full bg-accent/[0.06] flex items-center justify-center border border-accent/15">
                  <Clock className="w-6 h-6 text-accent" />
                </div>
                <h2 className="text-4xl font-bold tracking-tight">Recent Fragments</h2>
              </div>
              <div className="h-[1px] flex-1 bg-white/[0.04]" />
            </div>
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              <AnimatePresence>
                {snapshot.recent.map((item) => (
                  <MemoryCard key={item.id} item={item} onForget={handleForget} />
                ))}
              </AnimatePresence>
            </div>
          </section>

          {/* Axiomatic Facts */}
          <section>
            <div className="flex items-center gap-10 mb-16">
              <div className="flex items-center gap-5">
                <div className="w-12 h-12 rounded-full bg-white/[0.03] flex items-center justify-center border border-white/[0.06]">
                  <Brain className="w-6 h-6 text-dim" />
                </div>
                <h2 className="text-4xl font-bold tracking-tight">Axiomatic Facts</h2>
              </div>
              <div className="h-[1px] flex-1 bg-white/[0.04]" />
            </div>
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              <AnimatePresence>
                {snapshot.facts.map((item) => (
                  <MemoryCard key={item.id} item={item} onForget={handleForget} />
                ))}
              </AnimatePresence>
            </div>
          </section>

          {/* Emotional Resonance */}
          <section>
            <div className="flex items-center gap-10 mb-16">
              <div className="flex items-center gap-5">
                <div className="w-12 h-12 rounded-full bg-white/[0.03] flex items-center justify-center border border-white/[0.06]">
                  <Layers className="w-6 h-6 text-white/50" />
                </div>
                <h2 className="text-4xl font-bold tracking-tight">Resonant Patterns</h2>
              </div>
              <div className="h-[1px] flex-1 bg-white/[0.04]" />
            </div>
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              <AnimatePresence>
                {snapshot.emotions.map((item) => (
                  <MemoryCard key={item.id} item={item} onForget={handleForget} />
                ))}
              </AnimatePresence>
            </div>
          </section>
        </div>
        
        <footer className="mt-80 text-center pb-40">
           <div className="inline-flex items-center gap-5 px-10 py-5 rounded-full bg-white/[0.03] border border-white/[0.06] hover:border-accent/30 hover:bg-accent/[0.04] transition-all cursor-pointer group">
             <Plus size={20} className="text-accent group-hover:scale-110 transition-transform" />
             <span className="mono-label !text-[12px] !text-primary uppercase tracking-[0.3em]">Inject Manual Memory Fragment</span>
           </div>
        </footer>
      </div>
    </div>
  );
}

