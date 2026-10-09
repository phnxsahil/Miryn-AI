"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SanctuaryPersona } from "@/lib/types";
import { Heart, Brain, Zap, Wind, RefreshCw, ChevronRight } from "lucide-react";
import LoadingState from "@/components/ui/LoadingState";
import Link from "next/link";

function BreathingExercise({ name, desc, pattern }: { name: string; desc: string; pattern: string }) {
  const [active, setActive] = useState(false);
  const [phase, setPhase] = useState("Ready");

  const start = () => {
    setActive(true);
    const phases = pattern.split("-").flatMap(p => {
      const n = parseInt(p);
      return Array(n).fill(null).map((_, i) => ({ label: p.startsWith("4") && i === 0 ? "Inhale" : p.startsWith("7") ? "Hold" : "Exhale", dur: 1000 }));
    });
    // ponytail: naive sequential timing, fine for demo breathing UX
    let i = 0;
    const run = () => {
      if (i >= phases.length) { setActive(false); setPhase("Ready"); return; }
      setPhase(phases[i].label);
      setTimeout(() => { i++; run(); }, phases[i].dur);
    };
    run();
  };

  return (
    <div className="bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-2xl p-5">
      <h3 className="text-sm font-semibold text-[color:var(--theme-text)]">{name}</h3>
      <p className="text-xs text-[color:var(--theme-dim)] mt-1 mb-4 leading-relaxed">{desc}</p>
      {active ? (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full border-2 border-[color:var(--theme-accent)] flex items-center justify-center animate-pulse"><Wind size={16} className="text-[color:var(--theme-accent)]" /></div>
          <span className="text-sm font-medium text-[color:var(--theme-accent)]">{phase}</span>
        </div>
      ) : (
        <button onClick={start} className="flex items-center gap-2 text-xs font-medium text-[color:var(--theme-accent)] hover:text-[color:var(--theme-accent)] transition-colors">
          <Wind size={13} />Begin {name}
        </button>
      )}
    </div>
  );
}

export default function SanctuaryPage() {
  const [data, setData] = useState<SanctuaryPersona | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    try {
      const d = await api.getSanctuaryData();
      setData(d);
    } catch { setData(null); }
    finally { setLoading(false); setRefreshing(false); }
  };

  useEffect(() => { void load(); }, []);

  if (loading) return <LoadingState label="Loading your sanctuary—" />;

  const openLoops = data?.active_open_loops?.map(l => l.topic).filter(Boolean) ?? [];
  const values = data?.core_anchors?.map(anchor => anchor.label) ?? [];
  const hasLearnedData = Boolean(data && (
    openLoops.length > 0 ||
    data.primary_emotion !== null ||
    data.beliefs.length ||
    data.patterns.length ||
    data.conflicts.length
  ));

  return (
    <div className="flex flex-col gap-6 px-6 md:px-10 py-8 max-w-4xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-[11px] font-mono uppercase tracking-wider text-[color:var(--theme-dim)] mb-0.5">Sanctuary</p>
          <h1 className="text-xl font-semibold text-[color:var(--theme-text)]">Your space</h1>
          <p className="text-xs text-[color:var(--theme-dim)] mt-0.5">A quiet place to reflect, reset and see what&apos;s on your plate.</p>
        </div>
        <button onClick={() => { setRefreshing(true); void load(); }} disabled={refreshing} className="p-2 rounded-xl text-[color:var(--theme-dim)] hover:text-[color:var(--theme-muted)] hover:bg-[color:var(--theme-overlay)] transition-all disabled:opacity-50">
          <RefreshCw size={16} className={refreshing ? "animate-spin" : ""} />
        </button>
      </div>

      {!hasLearnedData && (
        <div className="rounded-2xl border border-[color:var(--theme-border)] bg-[color:var(--theme-card)] px-6 py-12 text-center">
          <p className="mx-auto max-w-md text-sm leading-6 text-[color:var(--text-dim)]">Chat with Miryn a bit and this fills in with what&apos;s on your mind.</p>
          <Link href="/chat" className="mt-5 inline-flex items-center gap-1.5 text-sm text-[color:var(--accent)] transition-colors hover:underline">
            Start chatting with Miryn <ChevronRight size={14} />
          </Link>
        </div>
      )}

      {hasLearnedData && <>
      {/* Status cards */}
      <div className="grid gap-3 md:grid-cols-3">
        {[
          { label: "Emotional Baseline", value: data?.primary_emotion, icon: Heart, color: "var(--theme-accent)" },
          { label: "Cognitive Load", value: data?.cognitive_load, icon: Brain, color: "var(--theme-accent)" },
          { label: "Open Loops", value: `${openLoops.length} active`, icon: Zap, color: "var(--accent)" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-2">
              <Icon size={14} style={{ color }} />
              <p className="text-[11px] font-mono uppercase tracking-wider text-[color:var(--theme-dim)]">{label}</p>
            </div>
            <p className={`text-base font-semibold ${value ? "text-[color:var(--theme-text)]" : "text-[color:var(--text-dim)]"}`}>{value || "Not enough data yet"}</p>
          </div>
        ))}
      </div>

      {/* Life season */}
      {data?.life_season && (
        <div className="bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-2xl p-5">
          <p className="text-[11px] font-mono uppercase tracking-wider text-[color:var(--theme-dim)] mb-2">Current Life Season</p>
          <p className="text-sm text-[color:var(--theme-muted)] leading-relaxed italic">&ldquo;{data.life_season}&rdquo;</p>
        </div>
      )}

      {/* Summary */}
      {data?.grounding_recommendation && (
        <div className="bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-2xl p-5">
          <p className="text-[11px] font-mono uppercase tracking-wider text-[color:var(--theme-dim)] mb-2">Living Mirror</p>
          <p className="text-sm text-[color:var(--theme-muted)] leading-relaxed">{data.grounding_recommendation}</p>
        </div>
      )}

      {/* Values */}
      {values.length > 0 && (
        <div className="bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-2xl p-5 space-y-3">
          <p className="text-[11px] font-mono uppercase tracking-wider text-[color:var(--theme-dim)]">Current Values</p>
          <div className="flex flex-wrap gap-2">
            {values.map((v, i) => (
              <span key={i} className="text-xs font-medium px-3 py-1.5 rounded-full border border-[color:var(--theme-accent)]/20 bg-[color:var(--theme-accent)]/5 text-[color:var(--theme-accent)]">{v}</span>
            ))}
          </div>
        </div>
      )}

      {/* Open Loops */}
      {openLoops.length > 0 && (
        <div className="bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-mono uppercase tracking-wider text-[color:var(--theme-dim)]">Open Loops</p>
            <span className="text-xs text-[color:var(--accent)] font-mono">{openLoops.length} unresolved</span>
          </div>
          <p className="text-xs text-[color:var(--theme-dim)] leading-relaxed">Open threads on your mind. Closing them frees cognitive space.</p>
          <div className="space-y-2">
            {openLoops.map((loop, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-[color:var(--theme-card)] rounded-xl border border-[color:var(--theme-border)]">
                <div className="w-1.5 h-1.5 rounded-full bg-[color:var(--accent)] shrink-0 mt-1.5" />
                <p className="text-sm text-[color:var(--theme-muted)]">{loop}</p>
              </div>
            ))}
          </div>
          <Link href="/chat" className="inline-flex items-center gap-1.5 text-xs text-[color:var(--theme-accent)] hover:text-[color:var(--theme-accent)] transition-colors">
            Resolve with Miryn <ChevronRight size={12} />
          </Link>
        </div>
      )}

      </>}

      {/* Breathing exercises */}
      <div className="space-y-3">
        <p className="text-[11px] font-mono uppercase tracking-wider text-[color:var(--theme-dim)]">Reset Exercises</p>
        <div className="grid md:grid-cols-3 gap-3">
          <BreathingExercise name="Box Breathing" desc="4-4-4-4 rhythm to de-escalate stress and anchor focus." pattern="4-4-4-4" />
          <BreathingExercise name="Relaxation Breath" desc="4-7-8 pattern to activate the parasympathetic system." pattern="4-7-8" />
          <BreathingExercise name="Coherent Breath" desc="5-5 cadence for heart rate coherence and calm." pattern="5-5" />
        </div>
      </div>
    </div>
  );
}

