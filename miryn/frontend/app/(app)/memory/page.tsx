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
    <div className="group bg-[#121219] border border-white/[0.07] hover:border-white/[0.14] rounded-2xl p-5 flex flex-col gap-3 transition-all">
      <div className="flex items-center justify-between gap-2">
        <span className={`text-[10.5px] font-mono uppercase tracking-wider px-2.5 py-1 rounded-full border ${isCore ? "border-[#D69155]/25 bg-[#D69155]/08 text-[#D69155]" : "border-white/[0.08] bg-white/[0.04] text-[#505060]"}`}>
          {isCore ? "Core" : "Episodic"}
        </span>
        <span className="text-xs text-[#404050]">{date}</span>
      </div>
      <p className="text-sm text-[#c0c0c8] leading-relaxed line-clamp-3 flex-1">
        {item.content || "Memory fragment"}
      </p>
      <div className="flex items-center justify-between pt-3 border-t border-white/[0.05]">
        <div className="flex items-center gap-1.5 text-[#404050]">
          <Lock size={11} />
          <span className="text-[11px]">Encrypted</span>
        </div>
        <button onClick={() => onForget(item.id)} className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-[#505060] hover:text-red-400 hover:bg-red-500/10 transition-all" title="Forget this memory">
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
          <p className="text-[11px] font-mono uppercase tracking-wider text-[#505060] mb-0.5">Memory Bank</p>
          <h1 className="text-xl font-semibold text-[#e8e8ec]">Your Memories</h1>
          <p className="text-xs text-[#505060] mt-0.5">Miryn remembers what matters — review and curate your stored context</p>
        </div>
        <button onClick={() => setShowAdd(v => !v)} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-[#0d0d11] bg-[#D69155] hover:bg-[#E8A870] rounded-xl transition-colors">
          <Plus size={15} />Add Memory
        </button>
      </div>

      {/* Add memory panel */}
      {showAdd && (
        <div className="bg-[#121219] border border-[#D69155]/20 rounded-2xl p-5 space-y-3 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-[#e8e8ec]">Add a memory</p>
            <button onClick={() => setShowAdd(false)} className="text-[#505060] hover:text-[#c0c0c8]"><X size={15} /></button>
          </div>
          <textarea value={newMemory} onChange={e => setNewMemory(e.target.value)} placeholder="Something you want Miryn to remember about you..." rows={3} className="w-full bg-[#1e1e28] border border-white/[0.07] rounded-xl px-4 py-3 text-sm text-[#e8e8ec] outline-none focus:border-[#D69155]/30 resize-none placeholder:text-[#404050]" />
          <button onClick={handleAdd} disabled={adding || !newMemory.trim()} className="px-5 py-2 text-sm font-semibold text-[#0d0d11] bg-[#D69155] hover:bg-[#E8A870] rounded-xl transition-colors disabled:opacity-50">
            {adding ? "Saving..." : "Save memory"}
          </button>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        {[["Total", stats.total], ["Core", stats.core], ["Episodic", stats.episodic]].map(([l,v]) => (
          <div key={l} className="bg-[#121219] border border-white/[0.07] rounded-2xl p-4">
            <p className="text-[11px] font-mono uppercase tracking-wider text-[#505060]">{l}</p>
            <p className="text-2xl font-semibold text-[#e8e8ec] mt-1">{v}</p>
          </div>
        ))}
      </div>

      {/* Search + filter */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#505060]" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search memories..." className="w-full pl-9 pr-4 py-2.5 bg-[#121219] border border-white/[0.07] rounded-xl text-sm text-[#e8e8ec] outline-none focus:border-[#D69155]/30 placeholder:text-[#404050]" />
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {TIERS.map(t => (
            <button key={t} onClick={() => setTier(t)} className={`px-3.5 py-2 rounded-xl text-xs font-medium transition-all capitalize ${tier === t ? "bg-[#D69155]/10 border border-[#D69155]/25 text-[#D69155]" : "bg-[#121219] border border-white/[0.07] text-[#505060] hover:text-[#c0c0c8]"}`}>
              {t === "all" ? `All (${stats.total})` : t === "core" ? `Core (${stats.core})` : t === "episodic" ? `Episodic (${stats.episodic})` : "Emotions"}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      {filtered.length === 0
        ? <div className="text-center py-20 text-[#404050] text-sm">
            {search ? "No memories match your search." : "No memories yet — start chatting with Miryn and they will appear here."}
          </div>
        : <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map(m => <MemoryCard key={m.id} item={m} onForget={handleForget} />)}
          </div>
      }
    </div>
  );
}

