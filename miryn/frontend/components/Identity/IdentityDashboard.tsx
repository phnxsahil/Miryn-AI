"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { EvolutionLogEntry, Identity } from "@/lib/types";

const tone = [
  "bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.08),_transparent_55%)]",
  "bg-[radial-gradient(circle_at_left,_rgba(255,255,255,0.06),_transparent_50%)]",
];

/**
 * Render a compact, styled pill element with an uppercase label.
 *
 * @param label - Text to display inside the pill
 * @returns A styled inline span element containing the provided label
 */
function Pill({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs tracking-[0.2em] uppercase text-white/80">
      {label}
    </span>
  );
}

/**
 * Renders a horizontal progress meter whose filled width reflects a numeric value.
 *
 * @param value - Progress value expected in the 0–1 range; values outside this range are clamped
 *                to the nearest boundary
 * @returns A JSX element of a rounded horizontal bar with its fill width set to `value * 100%`
 *          (clamped between `0%` and `100%`)
 */
function Meter({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div className="h-2 w-full rounded-full bg-white/10">
      <div
        className="h-2 rounded-full bg-gradient-to-r from-amber-400/80 via-amber-300/70 to-white/60"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

/**
 * Renders the Identity Dashboard UI and loads the current identity from the API on mount.
 *
 * The component fetches the identity, shows a loading state while fetching, displays an error message if loading fails, and when available renders summary stats, traits, values, beliefs, open loops, patterns, emotions, conflicts, and a privacy vault note.
 *
 * @returns The React element representing the identity dashboard
 */
export default function IdentityDashboard() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [evolution, setEvolution] = useState<EvolutionLogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.loadToken();
    api
      .getIdentity()
      .then(setIdentity)
      .catch((e) => setError(e.message || "Failed to load identity"));
    api
      .getEvolution()
      .then((data) => setEvolution(data || []))
      .catch(() => setEvolution([]));
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
    return <div className="text-red-400">{error}</div>;
  }

  if (!identity) {
    return <div className="text-secondary">Loading identity...</div>;
  }

  const traitKeys = Object.keys(identity.traits || {});
  const valueKeys = Object.keys(identity.values || {});

  return (
    <div className={`min-h-screen ${tone[0]} ${tone[1]} text-white`}>
      <div className="mx-auto max-w-6xl px-8 py-10">
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="text-xs uppercase tracking-[0.35em] text-secondary">
              Identity Dashboard
            </div>
            <h1 className="mt-3 text-4xl font-serif font-light">Miryn Profile</h1>
            <p className="mt-2 text-sm text-secondary">
              A living map of who you are becoming. Updated continuously as you speak.
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="rounded-full border border-amber-300/30 bg-amber-500/10 px-4 py-2 text-xs uppercase tracking-[0.2em] text-amber-200">
              State: {identity.state}
            </div>
            <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.2em] text-white/70">
              Version {identity.version}
            </div>
          </div>
        </div>

        <section className="mt-10 grid gap-6 md:grid-cols-4">
          <div className="rounded-2xl border border-white/10 bg-black/30 p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-secondary">Beliefs</div>
            <div className="mt-3 text-3xl font-serif">{stats?.beliefs}</div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-black/30 p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-secondary">Open Loops</div>
            <div className="mt-3 text-3xl font-serif">{stats?.loops}</div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-black/30 p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-secondary">Patterns</div>
            <div className="mt-3 text-3xl font-serif">{stats?.patterns}</div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-black/30 p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-secondary">Emotions</div>
            <div className="mt-3 text-3xl font-serif">{stats?.emotions}</div>
          </div>
        </section>

        <section className="mt-10 grid gap-8 md:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-black/40 p-6">
            <div className="text-xs uppercase tracking-[0.3em] text-secondary">Traits</div>
            <div className="mt-4 flex flex-wrap gap-2">
              {traitKeys.length === 0 && <span className="text-secondary">No traits yet.</span>}
              {traitKeys.map((key) => (
                <Pill key={key} label={key} />
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-black/40 p-6">
            <div className="text-xs uppercase tracking-[0.3em] text-secondary">Values</div>
            <div className="mt-4 flex flex-wrap gap-2">
              {valueKeys.length === 0 && <span className="text-secondary">No values yet.</span>}
              {valueKeys.map((key) => (
                <Pill key={key} label={key} />
              ))}
            </div>
          </div>
        </section>

        <section className="mt-10 grid gap-8 md:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-black/40 p-6">
            <div className="text-xs uppercase tracking-[0.3em] text-secondary">Beliefs</div>
            <div className="mt-4 space-y-4">
              {(identity.beliefs?.length ?? 0) === 0 && <div className="text-secondary">No beliefs yet.</div>}
              {(identity.beliefs ?? []).map((belief, idx) => (
                <div key={`belief-${idx}`} className="space-y-2">
                  <div className="text-sm text-white">{belief.topic}</div>
                  <div className="text-xs text-secondary">{belief.belief}</div>
                  <Meter value={belief.confidence ?? 0.5} />
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-black/40 p-6">
            <div className="text-xs uppercase tracking-[0.3em] text-secondary">Open Loops</div>
            <div className="mt-4 space-y-4">
              {(identity.open_loops?.length ?? 0) === 0 && <div className="text-secondary">No open loops yet.</div>}
              {(identity.open_loops ?? []).map((loop, idx) => (
                <div key={`loop-${idx}`} className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-sm text-white">{loop.topic}</div>
                    <div className="text-xs text-secondary">Status: {loop.status || "open"}</div>
                  </div>
                  <div className="text-xs text-amber-200">Priority {loop.importance ?? 1}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-10 grid gap-8 md:grid-cols-3">
          <div className="rounded-2xl border border-white/10 bg-black/40 p-6">
            <div className="text-xs uppercase tracking-[0.3em] text-secondary">Patterns</div>
            <div className="mt-4 space-y-3">
              {(identity.patterns?.length ?? 0) === 0 && <div className="text-secondary">No patterns yet.</div>}
              {(identity.patterns ?? []).map((pattern, idx) => (
                <div key={`pattern-${idx}`} className="space-y-1">
                  <div className="text-sm text-white">{pattern.pattern_type}</div>
                  <div className="text-xs text-secondary">{pattern.description}</div>
                  <Meter value={pattern.confidence ?? 0.5} />
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-black/40 p-6">
            <div className="text-xs uppercase tracking-[0.3em] text-secondary">Emotions</div>
            <div className="mt-4 space-y-3">
              {(identity.emotions?.length ?? 0) === 0 && <div className="text-secondary">No emotions logged yet.</div>}
              {(identity.emotions ?? []).map((emotion, idx) => (
                <div key={`emotion-${idx}`} className="space-y-1">
                  <div className="text-sm text-white">{emotion.primary_emotion}</div>
                  <div className="text-xs text-secondary">
                    Secondary: {(emotion.secondary_emotions || []).join(", ") || "—"}
                  </div>
                  <Meter value={emotion.intensity ?? 0.5} />
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-black/40 p-6">
            <div className="text-xs uppercase tracking-[0.3em] text-secondary">Conflicts</div>
            <div className="mt-4 space-y-3">
              {(identity.conflicts?.length ?? 0) === 0 && <div className="text-secondary">No conflicts detected.</div>}
              {(identity.conflicts ?? []).map((conflict, idx) => (
                <div key={`conflict-${idx}`} className="space-y-1">
                  <div className="text-xs text-white">{conflict.statement}</div>
                  <div className="text-xs text-amber-200">vs {conflict.conflict_with}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-10 rounded-2xl border border-white/10 bg-black/40 p-6">
          <div className="text-xs uppercase tracking-[0.3em] text-secondary">Privacy Vault</div>
          <p className="mt-3 text-sm text-secondary">
            Tier‑2 and Tier‑3 memory can be encrypted at rest when enabled on the server.
            This dashboard reflects your latest identity snapshot, not raw message logs.
          </p>
        </section>

        <section className="mt-10">
          <div className="text-xs uppercase tracking-[0.3em] text-secondary">Evolution Timeline</div>
          <div className="mt-4 space-y-4">
            {evolution.length === 0 && (
              <div className="rounded-2xl border border-white/10 bg-black/40 p-6 text-secondary">
                Nothing recorded yet - start a conversation
              </div>
            )}
            {evolution.map((entry) => {
              const date = new Date(entry.created_at).toLocaleDateString();
              const oldValue = entry.old_value ? JSON.stringify(entry.old_value) : null;
              const newValue = entry.new_value ? JSON.stringify(entry.new_value) : null;
              return (
                <div key={entry.id} className="rounded-2xl border border-white/10 bg-black/40 p-6">
                  <div className="text-sm text-white">
                    On {date}, Miryn noticed your {entry.field_changed} shifted
                  </div>
                  {(oldValue || newValue) && (
                    <div className="mt-3 grid gap-3 md:grid-cols-2">
                      {oldValue && (
                        <div className="rounded-xl border border-white/10 bg-black/30 p-3 text-xs text-secondary">
                          <div className="text-[10px] uppercase tracking-[0.2em] text-secondary">Old</div>
                          <div className="mt-2 text-white/70">{oldValue}</div>
                        </div>
                      )}
                      {newValue && (
                        <div className="rounded-xl border border-white/10 bg-black/30 p-3 text-xs text-secondary">
                          <div className="text-[10px] uppercase tracking-[0.2em] text-secondary">New</div>
                          <div className="mt-2 text-white/70">{newValue}</div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
