"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Identity } from "@/lib/types";

export default function IdentityCard() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.loadToken();
    api
      .getIdentity()
      .then(setIdentity)
      .catch((e) => setError(e.message || "Failed to load identity"));
  }, []);

  if (error) {
    return <div className="text-red-400">{error}</div>;
  }

  if (!identity) {
    return <div className="text-secondary">Loading identity...</div>;
  }

  return (
    <div className="max-w-4xl bg-card border border-white/[0.06] rounded-[32px] p-10 shadow-sm relative overflow-hidden">
      <div className="absolute top-0 right-0 w-40 h-40 bg-accent/5 rounded-full blur-3xl -z-10" />
      
      <header className="mb-10">
        <h1 className="text-4xl font-bold tracking-tight text-primary">Identity</h1>
        <div className="mt-2 text-sm text-muted font-bold uppercase tracking-widest">Version {identity.version}</div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <section className="space-y-4">
          <div className="text-primary font-bold uppercase tracking-widest text-xs">Traits Architecture</div>
          <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-6">
            <pre className="text-sm text-muted whitespace-pre-wrap font-mono">
              {JSON.stringify(identity.traits, null, 2)}
            </pre>
          </div>
        </section>
        
        <section className="space-y-4">
          <div className="text-primary font-bold uppercase tracking-widest text-xs">Core Values</div>
          <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-6">
            <pre className="text-sm text-muted whitespace-pre-wrap font-mono">
              {JSON.stringify(identity.values, null, 2)}
            </pre>
          </div>
        </section>

        <section className="space-y-4">
          <div className="text-primary font-bold uppercase tracking-widest text-xs">Epistemic Beliefs</div>
          <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-6">
            <pre className="text-sm text-muted whitespace-pre-wrap font-mono">
              {JSON.stringify(identity.beliefs, null, 2)}
            </pre>
          </div>
        </section>

        <section className="space-y-4">
          <div className="text-primary font-bold uppercase tracking-widest text-xs">Open Loops</div>
          <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-6">
            <pre className="text-sm text-muted whitespace-pre-wrap font-mono">
              {JSON.stringify(identity.open_loops, null, 2)}
            </pre>
          </div>
        </section>
      </div>
    </div>
  );
}
