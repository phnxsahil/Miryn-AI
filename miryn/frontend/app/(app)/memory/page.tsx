"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { MemoryItem } from "@/lib/types";
import { Search, Trash2, Lock, Plus, X } from "lucide-react";
import LoadingState from "@/components/ui/LoadingState";

const TIERS = ["all", "core", "episodic", "emotions"] as const;
type Tier = typeof TIERS[number];

function MemoryCard({ item, onForget }: { item: MemoryItem; onForget: (id: string) => void }) {
  const tier = (item as Record<string, unknown>).memory_tier as string | undefined ?? "core";
  const date = item.created_at ? new Date(item.created_at).toLocaleDateString([], { month: "short", day: "numeric" }) : "";
  const isCore = tier === "core";
  return (
    <div className="group bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] hover:border-[color:var(--theme-border)] rounded-2xl p-5 flex flex-col gap-3 transition-all">
      <div className="flex items-center justify-between gap-2">
        <span className={`text-[10.5px] font-mono uppercase tracking-wider px-2.5 py-1 rounded-full border ${isCore ? "border-[color:var(--theme-accent)]/25 bg-[color:var(--theme-accent)]/08 text-[color:var(--theme-accent)]" : "border-[color:var(--theme-border)] bg-[color:var(--theme-overlay)] text-[color:var(--theme-dim)]"}`}>
          {isCore ? "Core" : "Episodic"}
        </span>
        <span className="text-xs text-[color:var(--theme-dim)]">{date}</span>
      </div>
      <p className="text-sm text-[color:var(--theme-muted)] leading-relaxed line-clamp-3 flex-1">
        {item.content || "Memory fragment"}
      </p>
      <div className="flex items-center justify-between pt-3 border-t border-[color:var(--theme-border)]">
        <div className="flex items-center gap-1.5 text-[color:var(--theme-dim)]">
          <Lock size={11} />
          <span className="text-[11px]">Encrypted</span>
        </div>
        <button onClick={() => onForget(item.id)} className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-[color:var(--theme-dim)] hover:text-red-400 hover:bg-red-500/10 transition-all" title="Forget this memory">
          <Trash2 size={13} />
        </button>
      </div>
    </div>
  );
}

export default function MemoryPage() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [tier, setTier] = useState<Tier>("all");
  const [showAdd, setShowAdd] = useState(false);
  const [newMemory, setNewMemory] = useState("");
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    (async () => {
      try { setMemories(await api.getMemories() ?? []); }
      catch { setMemories([]); }
      finally { setLoading(false); }
    })();
  }, []);

  const filtered = useMemo(() => {
    let m = memories;
    if (tier !== "all") m = m.filter(x => ((x as Record<string,unknown>).memory_tier === (tier === "core" ? "core" : tier === "episodic" ? "episodic" : tier) || (tier === "emotions" && ((x as Record<string,unknown>).memory_tier === "emotion" || x.content?.toLowerCase().includes("feel")))));
    if (search.trim()) m = m.filter(x => x.content?.toLowerCase().includes(search.toLowerCase()));
    return m;
  }, [memories, tier, search]);

  const stats = useMemo(() => ({
    total: memories.length,
    core: memories.filter(m => (m as Record<string,unknown>).memory_tier === "core").length,
    episodic: memories.filter(m => (m as Record<string,unknown>).memory_tier !== "core").length,
  }), [memories]);

  const handleForget = async (id: string) => {
    try { await api.deleteMemory(id); setMemories(m => m.filter(x => x.id !== id)); }
    catch { /* silent */ }
  };

  const handleAdd = async () => {
    if (!newMemory.trim()) return;
    setAdding(true);
    try {
      await api.addMemory({ content: newMemory, memory_type: "user_note" });
      setMemories(await api.getMemories() ?? []);
      setNewMemory("");
      setShowAdd(false);
    } catch { /* silent */ }
    finally { setAdding(false); }
  };

  if (loading) return <LoadingState label="Loading memories..." />;

  return (
    <div className="flex flex-col gap-6 px-6 md:px-10 py-8 max-w-5xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-[11px] font-mono uppercase tracking-wider text-[color:var(--theme-dim)] mb-0.5">Memory Bank</p>
          <h1 className="text-xl font-semibold text-[color:var(--theme-text)]">Your Memories</h1>
          <p className="text-xs text-[color:var(--theme-dim)] mt-0.5">Miryn remembers what matters — review and curate your stored context</p>
        </div>
        <button onClick={() => setShowAdd(v => !v)} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-[color:var(--theme-accent-contrast)] bg-[color:var(--theme-accent)] hover:bg-[color:var(--theme-accent-strong)] rounded-xl transition-colors">
          <Plus size={15} />Add Memory
        </button>
      </div>

      {/* Add memory panel */}
      {showAdd && (
        <div className="bg-[color:var(--theme-card)] border border-[color:var(--theme-accent)]/20 rounded-2xl p-5 space-y-3 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-[color:var(--theme-text)]">Add a memory</p>
            <button onClick={() => setShowAdd(false)} className="text-[color:var(--theme-dim)] hover:text-[color:var(--theme-muted)]"><X size={15} /></button>
          </div>
          <textarea value={newMemory} onChange={e => setNewMemory(e.target.value)} placeholder="Something you want Miryn to remember about you..." rows={3} className="w-full bg-[color:var(--theme-input)] border border-[color:var(--theme-border)] rounded-xl px-4 py-3 text-sm text-[color:var(--theme-text)] outline-none focus:border-[color:var(--theme-accent)]/30 resize-none placeholder:text-[color:var(--theme-dim)]" />
          <button onClick={handleAdd} disabled={adding || !newMemory.trim()} className="px-5 py-2 text-sm font-semibold text-[color:var(--theme-accent-contrast)] bg-[color:var(--theme-accent)] hover:bg-[color:var(--theme-accent-strong)] rounded-xl transition-colors disabled:opacity-50">
            {adding ? "Saving..." : "Save memory"}
          </button>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        {[["Total", stats.total], ["Core", stats.core], ["Episodic", stats.episodic]].map(([l,v]) => (
          <div key={l} className="bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-2xl p-4">
            <p className="text-[11px] font-mono uppercase tracking-wider text-[color:var(--theme-dim)]">{l}</p>
            <p className="text-2xl font-semibold text-[color:var(--theme-text)] mt-1">{v}</p>
          </div>
        ))}
      </div>

      {/* Search + filter */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[color:var(--theme-dim)]" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search memories..." className="w-full pl-9 pr-4 py-2.5 bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-xl text-sm text-[color:var(--theme-text)] outline-none focus:border-[color:var(--theme-accent)]/30 placeholder:text-[color:var(--theme-dim)]" />
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {TIERS.map(t => (
            <button key={t} onClick={() => setTier(t)} className={`px-3.5 py-2 rounded-xl text-xs font-medium transition-all capitalize ${tier === t ? "bg-[color:var(--theme-accent)]/10 border border-[color:var(--theme-accent)]/25 text-[color:var(--theme-accent)]" : "bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] text-[color:var(--theme-dim)] hover:text-[color:var(--theme-muted)]"}`}>
              {t === "all" ? `All (${stats.total})` : t === "core" ? `Core (${stats.core})` : t === "episodic" ? `Episodic (${stats.episodic})` : "Emotions"}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      {filtered.length === 0
        ? <div className="text-center py-20 text-[color:var(--theme-dim)] text-sm">
            {search ? "No memories match your search." : "No memories yet — start chatting with Miryn and they will appear here."}
          </div>
        : <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map(m => <MemoryCard key={m.id} item={m} onForget={handleForget} />)}
          </div>
      }
    </div>
  );
}

