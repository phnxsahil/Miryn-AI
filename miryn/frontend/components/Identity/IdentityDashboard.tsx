"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { Identity } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";

function ListSection({ title, items, empty }: { title: string; items: string[]; empty: string }) {
  return <section className="border-t border-[color:var(--theme-border)] py-7">
    <div className="flex items-baseline justify-between gap-4"><h2 className="font-editorial text-2xl">{title}</h2><span className="text-xs text-[color:var(--theme-muted)]">{items.length}</span></div>
    {items.length ? <ul className="mt-4 space-y-3">{items.map((item, index) => <li key={index} className="text-[15px] leading-7 text-[color:var(--theme-muted)]">{item}</li>)}</ul> : <p className="mt-3 text-sm leading-6 text-[color:var(--theme-muted)]">{empty}</p>}
  </section>;
}

export default function IdentityDashboard() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const load = async () => {
    setError(null);
    try { setIdentity(await api.getIdentity()); }
    catch (cause) { setError(getErrorMessage(cause, "Could not load your identity.")); }
    finally { setLoading(false); setRefreshing(false); }
  };
  useEffect(() => { void load(); }, []);
  const traits = Object.entries(identity?.traits || {}).filter((entry): entry is [string, number] => typeof entry[1] === "number").slice(0, 6);
  const beliefs = identity?.beliefs?.map((item) => item.belief).filter(Boolean) || [];
  const patterns = identity?.patterns?.map((item) => item.description).filter(Boolean) || [];
  const openLoops = identity?.open_loops?.map((item) => item.topic).filter(Boolean) || [];
  const emotion = identity?.emotions?.[0]?.primary_emotion;
  return <div className="mx-auto w-full max-w-3xl space-y-8 px-5 py-8 text-[color:var(--theme-text)] md:px-8 md:py-12">
    <header className="flex items-start justify-between gap-4">
      <div><h1 className="font-editorial text-3xl md:text-4xl">Identity</h1><p className="mt-2 max-w-xl text-sm leading-6 text-[color:var(--theme-muted)]">What Miryn has learned about your beliefs, patterns, and unfinished threads.</p>{identity && <p className="mt-3 text-xs text-[color:var(--theme-muted)]">Version {identity.version}{emotion ? " · Recent mood: " + emotion : ""}</p>}</div>
      <button type="button" onClick={() => { setRefreshing(true); void load(); }} disabled={refreshing} aria-label="Refresh identity" className="rounded-lg p-2 text-[color:var(--theme-muted)] hover:bg-[color:var(--theme-overlay)] disabled:opacity-50"><RefreshCw size={17} className={refreshing ? "animate-spin" : ""} /></button>
    </header>
    {loading ? <p className="text-sm text-[color:var(--theme-muted)]">Loading identity…</p> : error ? <div role="alert" className="space-y-3 text-sm"><p>{error}</p><button type="button" onClick={() => void load()} className="text-[color:var(--theme-accent)] underline">Try again</button></div> : <>
      {traits.length > 0 && <section className="border-t border-[color:var(--theme-border)] py-7"><h2 className="font-editorial text-2xl">Traits</h2><dl className="mt-4 grid grid-cols-1 gap-x-8 gap-y-3 sm:grid-cols-2">{traits.map(([name, value]) => <div key={name} className="flex justify-between gap-3 text-sm"><dt className="capitalize text-[color:var(--theme-muted)]">{name}</dt><dd>{Math.round(value * 100)}%</dd></div>)}</dl></section>}
      <ListSection title="Beliefs" items={beliefs} empty="Nothing recorded yet. Miryn can learn what matters to you as you talk." />
      <ListSection title="Patterns" items={patterns} empty="No patterns noticed yet." />
      <ListSection title="Open loops" items={openLoops} empty="No unfinished threads right now." />
    </>}
  </div>;
}
