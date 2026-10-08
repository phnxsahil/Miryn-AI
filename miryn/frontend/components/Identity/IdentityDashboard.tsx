"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Identity } from "@/lib/types";
import { Brain, Star, Zap, AlertCircle, RefreshCw, User } from "lucide-react";
import LoadingState from "@/components/ui/LoadingState";

function StatCard({ label, value, icon: Icon }: { label: string; value: number; icon: React.ElementType }) {
  return (
    <div className="bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-2xl p-5 flex flex-col gap-2">
      <div className="flex items-center gap-2 text-[color:var(--theme-dim)]">
        <Icon size={14} />
        <span className="text-[11px] font-mono uppercase tracking-wider">{label}</span>
      </div>
      <span className="text-3xl font-semibold text-[color:var(--theme-text)]">{value}</span>
    </div>
  );
}

function TagList({ items, color = "var(--theme-accent)" }: { items: string[]; color?: string }) {
  if (!items.length) return <p className="text-sm text-[color:var(--theme-dim)] italic">Nothing recorded yet — start chatting with Miryn.</p>;
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item, i) => (
        <span key={i} style={{ borderColor: `${color}25`, backgroundColor: `${color}08`, color }} className="text-xs font-medium px-3 py-1.5 rounded-full border">
          {item}
        </span>
      ))}
    </div>
  );
}

function TraitBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs">
        <span className="text-[color:var(--theme-muted)] capitalize">{label}</span>
        <span className="text-[color:var(--theme-accent)] font-mono">{pct}%</span>
      </div>
      <div className="h-1 bg-[color:var(--theme-overlay)] rounded-full overflow-hidden">
        <div className="h-full bg-gradient-to-r from-[color:var(--theme-accent)] to-[color:var(--theme-accent-strong)] rounded-full transition-all duration-700" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function IdentityDashboard() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setError(null);
      const data = await api.getIdentity();
      setIdentity(data);
    } catch {
      setError("Could not load your identity. Chat with Miryn to start building it.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { void load(); }, []);

  const refresh = () => { setRefreshing(true); void load(); };

  if (loading) return <LoadingState label="Loading your identity…" />;

  const beliefs = identity?.beliefs?.map((b: { content?: string; description?: string } | string) =>
    typeof b === "string" ? b : b.content || b.description || ""
  ).filter(Boolean) ?? [];

  const patterns = identity?.patterns?.map((p: { name?: string; pattern?: string } | string) =>
    typeof p === "string" ? p : p.name || p.pattern || ""
  ).filter(Boolean) ?? [];

  const openLoops = identity?.open_loops?.map((o: { description?: string; title?: string } | string) =>
    typeof o === "string" ? o : o.description || o.title || ""
  ).filter(Boolean) ?? [];

  const traits = identity?.traits && typeof identity.traits === "object" && !Array.isArray(identity.traits)
    ? Object.entries(identity.traits as Record<string, number>).slice(0, 6)
    : [];

  const emotionState = identity?.emotions?.[0]?.primary_emotion ?? identity?.current_emotion_state ?? null;

  return (
    <div className="flex flex-col gap-8 px-6 md:px-10 py-8 max-w-4xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] flex items-center justify-center">
            <User size={24} className="text-[color:var(--theme-accent)]" />
          </div>
          <div>
            <p className="text-[11px] font-mono uppercase tracking-wider text-[color:var(--theme-dim)] mb-0.5">Identity Layer</p>
            <h1 className="text-2xl font-semibold text-[color:var(--theme-text)]">Your Identity Model</h1>
            <p className="text-sm text-[color:var(--theme-dim)] mt-0.5">A living map of your beliefs, patterns, and emotional baseline</p>
          </div>
        </div>
        <button onClick={refresh} disabled={refreshing} className="p-2 rounded-xl text-[color:var(--theme-dim)] hover:text-[color:var(--theme-muted)] hover:bg-[color:var(--theme-overlay)] transition-all disabled:opacity-50">
          <RefreshCw size={16} className={refreshing ? "animate-spin" : ""} />
        </button>
      </div>

      {error && (
        <div className="bg-[color:var(--theme-card)] border border-[color:var(--theme-accent)]/20 rounded-2xl px-5 py-4 flex items-center gap-3 text-sm text-[color:var(--theme-muted)]">
          <Brain size={16} className="text-[color:var(--theme-accent)] shrink-0" />
          {error}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Beliefs" value={beliefs.length} icon={Star} />
        <StatCard label="Open Loops" value={openLoops.length} icon={AlertCircle} />
        <StatCard label="Patterns" value={patterns.length} icon={Zap} />
        <StatCard label="Version" value={identity?.version ?? 1} icon={Brain} />
      </div>

      {/* Emotion + Traits */}
      {(emotionState || traits.length > 0) && (
        <div className="grid md:grid-cols-2 gap-4">
          {emotionState && (
            <div className="bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-2xl p-5">
              <p className="text-[11px] font-mono uppercase tracking-wider text-[color:var(--theme-dim)] mb-3">Current State</p>
              <p className="text-lg font-semibold text-[color:var(--theme-accent)] capitalize">{emotionState}</p>
              <p className="text-xs text-[color:var(--theme-dim)] mt-1">Emotional baseline from recent reflections</p>
            </div>
          )}
          {traits.length > 0 && (
            <div className="bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-2xl p-5">
              <p className="text-[11px] font-mono uppercase tracking-wider text-[color:var(--theme-dim)] mb-4">Traits</p>
              <div className="space-y-3">
                {traits.map(([k, v]) => <TraitBar key={k} label={k} value={v} />)}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Beliefs */}
      <div className="bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-2xl p-5 space-y-4">
        <div className="flex items-center gap-2">
          <Star size={14} className="text-[color:var(--theme-accent)]" />
          <h2 className="text-sm font-semibold text-[color:var(--theme-text)]">Core Beliefs</h2>
        </div>
        <TagList items={beliefs} color="var(--theme-accent)" />
      </div>

      {/* Patterns */}
      <div className="bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-2xl p-5 space-y-4">
        <div className="flex items-center gap-2">
          <Zap size={14} className="text-[#2dd4bf]" />
          <h2 className="text-sm font-semibold text-[color:var(--theme-text)]">Behavioral Patterns</h2>
        </div>
        <TagList items={patterns} color="#2dd4bf" />
      </div>

      {/* Open Loops */}
      <div className="bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-2xl p-5 space-y-4">
        <div className="flex items-center gap-2">
          <AlertCircle size={14} className="text-[#a78bfa]" />
          <h2 className="text-sm font-semibold text-[color:var(--theme-text)]">Open Loops <span className="text-[color:var(--theme-dim)] font-normal text-xs ml-1">(unresolved threads)</span></h2>
        </div>
        <TagList items={openLoops} color="#a78bfa" />
      </div>
    </div>
  );
}
