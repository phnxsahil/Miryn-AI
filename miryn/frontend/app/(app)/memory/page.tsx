"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus, Search, Trash2, X } from "lucide-react";
import { api } from "@/lib/api";
import type { MemoryItem, MemorySnapshot } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";

type Filter = "all" | "core" | "episodic" | "emotions";
export default function MemoryPage() {
  const [snapshot, setSnapshot] = useState<MemorySnapshot>({ facts: [], emotions: [], recent: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [adding, setAdding] = useState(false);
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try { setSnapshot(await api.getMemory()); }
    catch (cause) { setError(getErrorMessage(cause, "Could not load your memories.")); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const all = useMemo(() => {
    const byId = new Map<string, MemoryItem>();
    [...snapshot.facts, ...snapshot.emotions, ...snapshot.recent].forEach((item) => byId.set(item.id, item));
    return [...byId.values()].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  }, [snapshot]);
  const emotionIds = useMemo(() => new Set(snapshot.emotions.map((item) => item.id)), [snapshot.emotions]);
  const visible = all.filter((item) => {
    if (filter === "emotions" && !emotionIds.has(item.id)) return false;
    if (filter === "core" && item.memory_tier !== "core") return false;
    if (filter === "episodic" && item.memory_tier !== "episodic") return false;
    return item.content?.toLowerCase().includes(search.trim().toLowerCase());
  });

  const addMemory = async () => {
    if (!draft.trim() || saving) return;
    setSaving(true);
    setActionError(null);
    try {
      await api.createMemory({ content: draft.trim(), memory_tier: "core" });
      setDraft("");
      setAdding(false);
      await load();
    } catch (cause) { setActionError(getErrorMessage(cause, "Could not save this memory.")); }
    finally { setSaving(false); }
  };
  const removeMemory = async (id: string) => {
    setDeletingId(id);
    setActionError(null);
    try {
      await api.deleteMemory(id);
      await load();
    } catch (cause) { setActionError(getErrorMessage(cause, "Could not delete this memory.")); }
    finally { setDeletingId(null); }
  };

  return (
    <div className="mx-auto w-full max-w-3xl space-y-8 px-5 py-8 text-[color:var(--theme-text)] md:px-8 md:py-12">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div><h1 className="font-editorial text-3xl md:text-4xl">Memory</h1><p className="mt-2 max-w-xl text-sm leading-6 text-[color:var(--theme-muted)]">Review the context Miryn has kept from your conversations. You can add or remove a memory here.</p></div>
        <button type="button" onClick={() => setAdding((value) => !value)} className="inline-flex items-center gap-2 rounded-xl bg-[color:var(--theme-accent)] px-4 py-2.5 text-sm font-medium text-[color:var(--theme-accent-contrast)]"><Plus size={16} /> Add memory</button>
      </header>
      {adding && <div className="space-y-3 rounded-2xl border border-[color:var(--theme-border)] bg-[color:var(--theme-surface)] p-4">
        <div className="flex justify-between"><label htmlFor="memory-draft" className="text-sm font-medium">What should Miryn remember?</label><button type="button" onClick={() => setAdding(false)} aria-label="Close"><X size={16} /></button></div>
        <textarea id="memory-draft" value={draft} onChange={(event) => setDraft(event.target.value)} rows={3} className="w-full resize-y rounded-xl border border-[color:var(--theme-border)] bg-[color:var(--theme-input)] p-3 text-sm outline-none focus:border-[color:var(--theme-accent)]" />
        <button type="button" onClick={addMemory} disabled={saving || !draft.trim()} className="rounded-lg bg-[color:var(--theme-accent)] px-4 py-2 text-sm font-medium text-[color:var(--theme-accent-contrast)] disabled:opacity-50">{saving ? "Saving…" : "Save memory"}</button>
      </div>}
      {actionError && <p role="alert" className="text-sm text-[color:var(--theme-danger-text)]">{actionError}</p>}
      <div className="flex flex-wrap gap-3">
        <label className="relative min-w-48 flex-1"><Search size={16} className="absolute left-3 top-3 text-[color:var(--theme-muted)]" /><span className="sr-only">Search memories</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search memories" className="w-full rounded-xl border border-[color:var(--theme-border)] bg-[color:var(--theme-input)] py-2.5 pl-9 pr-3 text-sm outline-none focus:border-[color:var(--theme-accent)]" /></label>
        <div className="flex flex-wrap gap-1" role="group" aria-label="Memory filter">{(["all", "core", "episodic", "emotions"] as Filter[]).map((value) => <button type="button" key={value} onClick={() => setFilter(value)} aria-pressed={filter === value} className={`rounded-lg px-3 py-2 text-sm capitalize ${filter === value ? "bg-[color:var(--theme-card)] text-[color:var(--theme-text)]" : "text-[color:var(--theme-muted)] hover:bg-[color:var(--theme-overlay)]"}`}>{value}</button>)}</div>
      </div>
      {loading ? <p className="text-sm text-[color:var(--theme-muted)]">Loading memories…</p> : error ? <div role="alert" className="space-y-3 text-sm"><p>{error}</p><button type="button" onClick={() => void load()} className="text-[color:var(--theme-accent)] underline">Try again</button></div> : visible.length === 0 ? <p className="py-12 text-sm text-[color:var(--theme-muted)]">{all.length ? "No memories match this view." : "No saved memories yet. Your conversations can build context over time."}</p> : <ul className="divide-y divide-[color:var(--theme-border)]">{visible.map((item) => <li key={item.id} className="group flex gap-4 py-5">
        <div className="min-w-0 flex-1"><p className="whitespace-pre-wrap break-words text-[15px] leading-7">{item.content || "Memory without text"}</p><p className="mt-2 text-xs capitalize text-[color:var(--theme-muted)]">{item.memory_tier || "Memory"} · {new Date(item.created_at).toLocaleDateString()}</p></div>
        <button type="button" onClick={() => void removeMemory(item.id)} disabled={deletingId === item.id} aria-label="Delete memory" className="self-start rounded-lg p-2 text-[color:var(--theme-muted)] hover:bg-[color:var(--theme-overlay)] hover:text-[color:var(--theme-danger-text)] disabled:opacity-50"><Trash2 size={16} /></button>
      </li>)}</ul>}
    </div>
  );
}
