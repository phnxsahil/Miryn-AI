"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { MemoryItem, MemorySnapshot } from "@/lib/types";

function importanceDots(score: number | null | undefined) {
  const value = typeof score === "number" ? score : 0;
  if (value >= 0.66) return 3;
  if (value >= 0.33) return 2;
  return 1;
}

function MemoryCard({
  item,
  onForget,
}: {
  item: MemoryItem;
  onForget: (id: string) => void;
}) {
  const date = item.created_at ? new Date(item.created_at).toLocaleDateString() : "Unknown date";
  const dots = importanceDots(item.importance_score);

  return (
    <div className="rounded-2xl border border-white/10 bg-black/40 p-5">
      <div className="text-sm text-white">{item.content || "No content"}</div>
      <div className="mt-3 flex items-center justify-between text-xs text-secondary">
        <div>{date}</div>
        <div className="flex items-center gap-1">
          {Array.from({ length: dots }).map((_, idx) => (
            <span key={idx} className="h-2 w-2 rounded-full bg-accent/80" />
          ))}
        </div>
      </div>
      <button
        className="mt-4 text-xs uppercase tracking-[0.2em] text-secondary hover:text-white"
        onClick={() => onForget(item.id)}
      >
        Forget this
      </button>
    </div>
  );
}

export default function MemoryPage() {
  const [snapshot, setSnapshot] = useState<MemorySnapshot | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.loadToken();
    api
      .getMemory()
      .then((data) => setSnapshot(data))
      .finally(() => setLoading(false));
  }, []);

  const empty = useMemo(() => {
    if (!snapshot) return true;
    return (
      snapshot.recent.length === 0 &&
      snapshot.facts.length === 0 &&
      snapshot.emotions.length === 0
    );
  }, [snapshot]);

  const removeFromState = (id: string) => {
    if (!snapshot) return;
    setSnapshot({
      recent: snapshot.recent.filter((item) => item.id !== id),
      facts: snapshot.facts.filter((item) => item.id !== id),
      emotions: snapshot.emotions.filter((item) => item.id !== id),
    });
  };

  const handleForget = async (id: string) => {
    await api.deleteMemory(id);
    removeFromState(id);
  };

  if (loading) {
    return <div className="text-secondary">Loading memory...</div>;
  }

  if (!snapshot || empty) {
    return <div className="text-secondary">Nothing here yet - Miryn builds this as you talk</div>;
  }

  return (
    <div className="min-h-screen text-white">
      <div className="mx-auto max-w-6xl px-8 py-10 space-y-10">
        <div>
          <div className="text-xs uppercase tracking-[0.35em] text-secondary">Memory</div>
          <h1 className="mt-3 text-4xl font-serif font-light">Memory Snapshot</h1>
          <p className="mt-2 text-sm text-secondary">A live view of what Miryn is keeping.</p>
        </div>

        <section className="space-y-4">
          <div className="text-xs uppercase tracking-[0.3em] text-secondary">Recent</div>
          <div className="grid gap-4 md:grid-cols-2">
            {snapshot.recent.map((item) => (
              <MemoryCard key={item.id} item={item} onForget={handleForget} />
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <div className="text-xs uppercase tracking-[0.3em] text-secondary">Facts</div>
          <div className="grid gap-4 md:grid-cols-2">
            {snapshot.facts.map((item) => (
              <MemoryCard key={item.id} item={item} onForget={handleForget} />
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <div className="text-xs uppercase tracking-[0.3em] text-secondary">Emotions</div>
          <div className="grid gap-4 md:grid-cols-2">
            {snapshot.emotions.map((item) => (
              <MemoryCard key={item.id} item={item} onForget={handleForget} />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
