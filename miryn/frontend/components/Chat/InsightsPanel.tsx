"use client";

import type { ConversationInsights } from "@/lib/types";
import { Sparkles, AlertTriangle, Hash, Fingerprint, Activity, Quote } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function InsightsPanel({
  insights,
  conflicts,
}: {
  insights: ConversationInsights | null;
  conflicts?: Array<{ statement: string; conflict_with: string; severity?: number }>;
}) {
  const topics = insights?.topics || [];
  const entities = insights?.entities || [];
  const reflection = insights?.insights?.trim();
  const mood = insights?.emotions?.primary_emotion;
  const intensity = insights?.emotions?.intensity;
  const hasSupplemental = reflection || topics.length > 0 || entities.length > 0 || mood || (conflicts || []).length > 0;

  if (!hasSupplemental) return null;

  return (
    <motion.aside 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card border border-white/[0.06] rounded-[32px] p-10 mb-6 relative overflow-hidden shadow-sm"
    >
      {/* Subtle Background Glow */}
      <div className="absolute top-0 right-0 w-[200px] h-[200px] bg-accent/[0.05] blur-[80px] pointer-events-none" />

      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center">
            <Sparkles size={18} className="text-accent" />
          </div>
          <span className="mono-label !text-[13px] !text-primary uppercase tracking-[0.2em] font-bold">Metacognitive Layer</span>
        </div>
        
        {mood && (
          <div className="flex items-center gap-3 px-5 py-2 rounded-full bg-white/[0.03] border border-white/[0.06] shadow-sm">
            <Activity size={14} className="text-accent" />
            <span className="text-xs uppercase tracking-widest text-muted font-bold">Mood:</span>
            <span className="text-xs font-bold text-primary uppercase tracking-wider">{mood}</span>
            {typeof intensity === "number" && (
              <span className="text-xs text-accent font-mono ml-1 font-bold">{Math.round(intensity * 100)}%</span>
            )}
          </div>
        )}
      </div>

      {reflection && (
        <div className="mb-10 relative">
          <Quote className="absolute -top-3 -left-8 text-accent/10 w-10 h-10 -scale-x-100" />
          <p className="text-2xl text-primary leading-relaxed editorial-italic max-w-2xl font-medium">
            {reflection}
          </p>
        </div>
      )}

      <AnimatePresence>
        {conflicts && conflicts.length > 0 && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            className="mb-10 p-8 rounded-[32px] bg-red-500/[0.02] border border-red-500/10 relative overflow-hidden shadow-sm"
          >
            <div className="absolute top-0 left-0 w-[2px] h-full bg-red-500/40" />
            <div className="flex items-center gap-4 mb-6">
              <AlertTriangle size={20} className="text-red-600" />
              <span className="mono-label !text-[13px] !text-red-600 uppercase tracking-widest font-bold">Cognitive Dissonance Detected</span>
            </div>
            <ul className="space-y-4">
              {conflicts.map((c, idx) => (
                <li key={`conflict-${idx}`} className="text-sm text-muted leading-relaxed font-medium">
                  <span className="text-primary font-bold">{c.statement}</span>
                  <span className="mx-3 text-xs mono-label !text-red-500/40 uppercase font-bold">contradicts</span>
                  <span className="text-primary font-bold">{c.conflict_with}</span>
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex flex-wrap gap-3">
        {topics.map((topic, index) => (
          <div
            key={`topic-${topic}-${index}`}
            className="flex items-center gap-2.5 px-5 py-2.5 rounded-full bg-white/[0.03] border border-white/[0.06] text-[11px] mono-label text-muted hover:text-accent hover:border-accent/20 hover:bg-accent/[0.02] transition-all cursor-default shadow-sm font-bold"
          >
            <Hash size={12} className="text-accent" />
            {topic}
          </div>
        ))}
        {entities.map((entity, index) => (
          <div
            key={`entity-${entity}-${index}`}
            className="flex items-center gap-2.5 px-5 py-2.5 rounded-full bg-accent/5 border border-accent/20 text-[11px] mono-label text-accent hover:bg-accent/10 transition-all cursor-default shadow-sm font-bold"
          >
            <Fingerprint size={12} />
            {entity}
          </div>
        ))}
      </div>
    </motion.aside>
  );
}

