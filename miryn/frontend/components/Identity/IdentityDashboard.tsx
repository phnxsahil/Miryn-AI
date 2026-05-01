"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { EvolutionLogEntry, Identity } from "@/lib/types";
import ChatGPTImport from "@/components/Import/ChatGPTImport";

const tone = [
  "bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.08),_transparent_55%)]",
  "bg-[radial-gradient(circle_at_left,_rgba(255,255,255,0.06),_transparent_50%)]",
];

function ScoredPill({ label, value }: { label: string; value: unknown }) {
  const numValue = typeof value === "number" ? value : null;
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs tracking-[0.15em] uppercase text-white/80">
      {label}
      {numValue !== null && (
        <span className="text-[10px] text-accent font-mono tabular-nums">
          {numValue.toFixed(2)}
        </span>
      )}
    </span>
  );
}

function Meter({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div className="h-1.5 w-full rounded-full bg-white/5 border border-white/5 overflow-hidden">
      <div
        className="h-full rounded-full bg-gradient-to-r from-accent/40 via-accent/70 to-white/90 shadow-[0_0_10px_rgba(200,184,154,0.3)]"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export default function IdentityDashboard() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [evolution, setEvolution] = useState<EvolutionLogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showImport, setShowImport] = useState(false);

  useEffect(() => {
    api.loadToken();
    const loadData = () => {
      api
        .getIdentity()
        .then(setIdentity)
        .catch((e) => setError(e.message || "Failed to load identity"));
      api
        .getEvolution()
        .then((data) => setEvolution(data || []))
        .catch(() => setEvolution([]));
    };
    loadData();
  }, []);

  const stats = useMemo(() => {
    if (!identity) return null;
    return {
      beliefs: identity.beliefs?.length || 0,
      loops: identity.open_loops?.length || 0,
      patterns: identity.patterns?.length || 0,
      emotions: identity.emotions?.length || 0,
      conflicts: identity.conflicts?.length || 0,
    };
  }, [identity]);

  if (error) {
    return <div className="text-red-400 p-8 font-mono text-sm border border-red-900/50 bg-red-950/20 rounded-2xl">{error}</div>;
  }

  if (!identity) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-void">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-t-2 border-accent animate-spin" />
          <div className="text-secondary text-sm tracking-widest uppercase animate-pulse">Synchronizing Identity...</div>
        </div>
      </div>
    );
  }

  const traitKeys = Object.keys(identity.traits || {});
  const valueKeys = Object.keys(identity.values || {});

  return (
    <div className={`min-h-screen ${tone[0]} ${tone[1]} text-white bg-void`}>
      <div className="mx-auto max-w-6xl px-4 md:px-8 py-6 md:py-12">
        {/* Header Section */}
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between border-b border-white/5 pb-8 mb-12">
          <div>
            <div className="text-[10px] md:text-xs uppercase tracking-[0.4em] text-accent/70 mb-2">
              Cognitive Architecture / 001
            </div>
            <h1 className="text-3xl md:text-5xl font-serif font-extralight tracking-tight">
              Identity: <span className="text-accent italic">{identity.email || "Persona Alpha"}</span>
            </h1>
            <p className="mt-4 text-sm md:text-base text-secondary max-w-xl font-light leading-relaxed">
              A high-fidelity mapping of your digital psyche. This matrix evolves dynamically based on your interactions, beliefs, and emotional resonance.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="rounded-full border border-accent/20 bg-accent/5 px-4 py-2 text-[10px] uppercase tracking-widest text-accent">
              v{identity.version || "1.0"}
            </div>
            <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-[10px] uppercase tracking-widest text-secondary">
              Status: {identity.state}
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <section className="grid gap-4 md:gap-6 grid-cols-2 md:grid-cols-4 mb-12">
          {[
            { label: "Beliefs", val: stats?.beliefs },
            { label: "Open Loops", val: stats?.loops },
            { label: "Patterns", val: stats?.patterns },
            { label: "Emotions", val: stats?.emotions },
          ].map((s, i) => (
            <div key={i} className="group rounded-2xl border border-white/5 bg-white/[0.02] p-6 hover:bg-white/[0.04] transition-all duration-500">
              <div className="text-[10px] uppercase tracking-[0.3em] text-secondary group-hover:text-accent transition-colors">{s.label}</div>
              <div className="mt-4 text-3xl md:text-4xl font-serif font-light">{s.val}</div>
            </div>
          ))}
        </section>

        {/* Core Matrix Grid */}
        <div className="grid gap-8 md:gap-12 lg:grid-cols-2">
          {/* Left Column: Traits & Values */}
          <div className="space-y-8 md:space-y-12">
            <section className="rounded-3xl border border-white/5 bg-white/[0.01] p-8 backdrop-blur-sm">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-[10px] uppercase tracking-[0.5em] text-secondary">Trait Distribution</h2>
              </div>
              <div className="flex flex-wrap gap-3">
                {traitKeys.map((key) => (
                  <ScoredPill key={key} label={key} value={identity.traits[key]} />
                ))}
              </div>
            </section>

            <section className="rounded-3xl border border-white/5 bg-white/[0.01] p-8 backdrop-blur-sm">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-[10px] uppercase tracking-[0.5em] text-secondary">Axiological Values</h2>
              </div>
              <div className="flex flex-wrap gap-3">
                {valueKeys.map((key) => (
                  <ScoredPill key={key} label={key} value={identity.values[key]} />
                ))}
              </div>
            </section>
          </div>

          {/* Right Column: Beliefs & Patterns */}
          <div className="space-y-8 md:space-y-12">
            <section className="rounded-3xl border border-white/5 bg-white/[0.01] p-8 backdrop-blur-sm">
              <h2 className="text-[10px] uppercase tracking-[0.5em] text-secondary mb-8">Epistemic Beliefs</h2>
              <div className="space-y-6">
                {(identity.beliefs || []).map((belief, idx) => (
                  <div key={idx} className="space-y-3">
                    <div className="flex justify-between items-end">
                      <span className="text-sm font-medium text-white/90">{belief.topic}</span>
                      <span className="text-[10px] font-mono text-accent uppercase tracking-tighter">Confidence {(belief.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-xs text-secondary leading-relaxed italic">"{belief.belief}"</p>
                    <Meter value={belief.confidence} />
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-3xl border border-white/5 bg-white/[0.01] p-8 backdrop-blur-sm">
              <h2 className="text-[10px] uppercase tracking-[0.5em] text-secondary mb-8">Behavioral Patterns</h2>
              <div className="space-y-6">
                {(identity.patterns || []).map((pattern, idx) => (
                  <div key={idx} className="space-y-3">
                    <div className="text-sm font-medium text-white/90 capitalize">{pattern.pattern_type.replace(/_/g, ' ')}</div>
                    <p className="text-xs text-secondary leading-relaxed">{pattern.description}</p>
                    <Meter value={pattern.confidence} />
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>

        {/* Full Width Section: Evolution Timeline */}
        <section className="mt-12 md:mt-20">
          <div className="flex items-center gap-4 mb-10">
            <h2 className="text-[10px] uppercase tracking-[0.5em] text-secondary whitespace-nowrap">Evolution Timeline</h2>
            <div className="h-[1px] w-full bg-white/5" />
          </div>
          
          <div className="relative space-y-6">
            <div className="absolute left-6 top-0 bottom-0 w-[1px] bg-white/5 hidden md:block" />
            {evolution.length === 0 ? (
              <div className="text-secondary text-sm font-light italic">No evolution data recorded yet. Conversations will trigger matrix shifts.</div>
            ) : (
              evolution.map((entry, idx) => (
                <div key={entry.id} className="relative md:pl-16">
                  <div className="absolute left-5 top-8 w-2 h-2 rounded-full bg-accent/40 hidden md:block" />
                  <div className="rounded-3xl border border-white/5 bg-white/[0.01] p-6 md:p-8 hover:bg-white/[0.02] transition-colors">
                    <div className="flex items-center gap-4 mb-4">
                      <span className="text-[10px] font-mono text-accent">{new Date(entry.created_at).toLocaleDateString()}</span>
                      <span className="h-3 w-[1px] bg-white/10" />
                      <span className="text-[10px] uppercase tracking-widest text-secondary">{entry.field_changed} shift</span>
                    </div>
                    <div className="grid gap-6 md:grid-cols-2">
                      <div className="space-y-2">
                        <div className="text-[9px] uppercase tracking-widest text-secondary/40">From</div>
                        <div className="text-xs text-secondary font-light truncate max-w-full italic">{typeof entry.old_value === 'object' ? JSON.stringify(entry.old_value) : entry.old_value}</div>
                      </div>
                      <div className="space-y-2">
                        <div className="text-[9px] uppercase tracking-widest text-accent/40">To</div>
                        <div className="text-xs text-white/90 font-medium truncate max-w-full">{typeof entry.new_value === 'object' ? JSON.stringify(entry.new_value) : entry.new_value}</div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
