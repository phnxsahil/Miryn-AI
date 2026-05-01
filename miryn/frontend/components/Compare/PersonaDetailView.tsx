"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { api } from "@/lib/api";
import type { DemoPersonaDetail, Message } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";

type ViewMode = "identity" | "memory" | "history";

function TabLink({
  userId,
  view,
  current,
  children,
}: {
  userId: string;
  view: ViewMode;
  current: ViewMode;
  children: string;
}) {
  return (
    <Link
      href={`/compare/persona/${userId}?view=${view}`}
      className={`rounded-full px-4 py-2 text-xs uppercase tracking-[0.2em] transition ${
        current === view ? "bg-white/10 text-white" : "text-secondary hover:bg-white/5 hover:text-white"
      }`}
    >
      {children}
    </Link>
  );
}

function MessageBlock({ message }: { message: Message }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/25 p-4">
      <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.2em] text-secondary">
        <span>{message.role}</span>
        <span>{new Date(message.timestamp).toLocaleString()}</span>
      </div>
      <p className="mt-3 text-sm leading-7 text-white/80">{message.content}</p>
      {message.metadata && Object.keys(message.metadata).length > 0 && (
        <pre className="mt-3 whitespace-pre-wrap break-words rounded-xl bg-black/30 p-3 text-xs text-white/55">
          {JSON.stringify(message.metadata, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default function PersonaDetailView({ userId }: { userId: string }) {
  const searchParams = useSearchParams();
  const selectedView = (searchParams.get("view") || "identity") as ViewMode;
  const [detail, setDetail] = useState<DemoPersonaDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.loadToken();
    void api
      .getDemoPersonaDetail(userId)
      .then(setDetail)
      .catch((err) => setError(getErrorMessage(err, "Failed to load persona detail")));
  }, [userId]);

  const messages = useMemo(() => {
    if (!detail) return [];
    return detail.conversations.flatMap((conversation) => conversation.messages);
  }, [detail]);

  if (error) {
    return <div className="p-8 text-red-300">{error}</div>;
  }

  if (!detail) {
    return <div className="p-8 text-secondary">Loading persona detail...</div>;
  }

  return (
    <div className="min-h-screen bg-void text-white">
      <div className="mx-auto max-w-6xl px-6 py-8 md:px-8 md:py-10">
        <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div className="space-y-3">
            <Link href="/compare" className="text-xs uppercase tracking-[0.24em] text-secondary transition hover:text-white">
              Back to Compare
            </Link>
            <div>
              <h1 className="text-3xl font-serif font-light md:text-5xl">{detail.profile.label}</h1>
              <p className="mt-2 text-sm text-secondary md:text-base">{detail.profile.subtitle}</p>
            </div>
            <p className="max-w-3xl text-sm leading-7 text-white/70">{detail.profile.goal}</p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm md:min-w-[260px]">
            <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
              <div className="text-[10px] uppercase tracking-[0.2em] text-secondary">State</div>
              <div className="mt-2 text-lg text-white">{detail.identity.state}</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
              <div className="text-[10px] uppercase tracking-[0.2em] text-secondary">Version</div>
              <div className="mt-2 text-lg text-white">v{detail.identity.version}</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
              <div className="text-[10px] uppercase tracking-[0.2em] text-secondary">Drift</div>
              <div className="mt-2 text-lg text-white">{detail.identity_metrics.drift?.toFixed(2) ?? "--"}</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
              <div className="text-[10px] uppercase tracking-[0.2em] text-secondary">Mood Trend</div>
              <div className="mt-2 text-lg text-white">{detail.emotion_metrics.trend}</div>
            </div>
          </div>
        </div>

        <div className="mt-8 inline-flex flex-wrap items-center rounded-full border border-white/10 bg-black/30 p-1">
          <TabLink userId={userId} view="identity" current={selectedView}>Identity</TabLink>
          <TabLink userId={userId} view="memory" current={selectedView}>Memory</TabLink>
          <TabLink userId={userId} view="history" current={selectedView}>Past Conversation</TabLink>
        </div>

        {selectedView === "identity" && (
          <div className="mt-8 space-y-6">
            <section className="grid gap-5 md:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-black/30 p-5">
                <div className="text-xs uppercase tracking-[0.24em] text-secondary">Traits</div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {Object.entries(detail.identity.traits || {}).map(([key, value]) => (
                    <span key={key} className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/80">
                      {key}: {typeof value === "number" ? value.toFixed(2) : String(value)}
                    </span>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/30 p-5">
                <div className="text-xs uppercase tracking-[0.24em] text-secondary">Values</div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {Object.entries(detail.identity.values || {}).map(([key, value]) => (
                    <span key={key} className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/80">
                      {key}: {typeof value === "number" ? value.toFixed(2) : String(value)}
                    </span>
                  ))}
                </div>
              </div>
            </section>

            <section className="grid gap-5 md:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-black/30 p-5">
                <div className="text-xs uppercase tracking-[0.24em] text-secondary">Beliefs</div>
                <div className="mt-4 space-y-4">
                  {detail.identity.beliefs.map((belief, index) => (
                    <div key={`${belief.topic}-${index}`} className="rounded-2xl border border-white/8 bg-black/20 p-4">
                      <div className="text-sm text-white">{belief.topic}</div>
                      <p className="mt-2 text-sm leading-7 text-white/75">{belief.belief}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/30 p-5">
                <div className="text-xs uppercase tracking-[0.24em] text-secondary">Open Loops</div>
                <div className="mt-4 space-y-4">
                  {detail.identity.open_loops.map((loop, index) => (
                    <div key={`${loop.topic}-${index}`} className="rounded-2xl border border-white/8 bg-black/20 p-4">
                      <div className="flex items-center justify-between gap-4">
                        <div className="text-sm text-white">{loop.topic}</div>
                        <div className="text-[10px] uppercase tracking-[0.2em] text-amber-200">P{loop.importance}</div>
                      </div>
                      <div className="mt-2 text-xs text-secondary">Status: {loop.status}</div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="grid gap-5 md:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-black/30 p-5">
                <div className="text-xs uppercase tracking-[0.24em] text-secondary">Patterns</div>
                <div className="mt-4 space-y-4">
                  {detail.identity.patterns.map((pattern, index) => (
                    <div key={`${pattern.pattern_type}-${index}`} className="rounded-2xl border border-white/8 bg-black/20 p-4">
                      <div className="text-sm text-white">{pattern.pattern_type}</div>
                      <p className="mt-2 text-sm leading-7 text-white/75">{pattern.description}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/30 p-5">
                <div className="text-xs uppercase tracking-[0.24em] text-secondary">Emotions</div>
                <div className="mt-4 space-y-4">
                  {detail.identity.emotions.map((emotion, index) => (
                    <div key={`${emotion.primary_emotion}-${index}`} className="rounded-2xl border border-white/8 bg-black/20 p-4">
                      <div className="text-sm text-white">{emotion.primary_emotion}</div>
                      <p className="mt-2 text-sm text-white/75">Intensity: {emotion.intensity?.toFixed(2) ?? "--"}</p>
                      {emotion.secondary_emotions?.length ? (
                        <p className="mt-2 text-xs text-secondary">{emotion.secondary_emotions.join(", ")}</p>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </div>
        )}

        {selectedView === "memory" && (
          <div className="mt-8 grid gap-5 lg:grid-cols-3">
            {[
              { title: "Recent", items: detail.memory_snapshot.recent },
              { title: "Facts", items: detail.memory_snapshot.facts },
              { title: "Emotion Tagged", items: detail.memory_snapshot.emotions },
            ].map((section) => (
              <section key={section.title} className="rounded-2xl border border-white/10 bg-black/30 p-5">
                <div className="text-xs uppercase tracking-[0.24em] text-secondary">{section.title}</div>
                <div className="mt-4 space-y-4">
                  {section.items.map((message) => (
                    <MessageBlock key={message.id || `${section.title}-${message.timestamp}`} message={message} />
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}

        {selectedView === "history" && (
          <div className="mt-8 space-y-6">
            {detail.conversations.map((conversation) => (
              <section key={conversation.id} className="rounded-2xl border border-white/10 bg-black/30 p-5">
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                  <div>
                    <div className="text-xs uppercase tracking-[0.24em] text-secondary">Conversation</div>
                    <h2 className="mt-2 text-2xl font-serif font-light">{conversation.title}</h2>
                  </div>
                  <div className="text-xs text-secondary">
                    Updated {new Date(conversation.updated_at).toLocaleString()}
                  </div>
                </div>
                <div className="mt-5 space-y-4">
                  {conversation.messages.map((message) => (
                    <MessageBlock key={message.id || `${conversation.id}-${message.timestamp}`} message={message} />
                  ))}
                </div>
              </section>
            ))}
            {messages.length === 0 && <div className="text-secondary">No past conversation data.</div>}
          </div>
        )}
      </div>
    </div>
  );
}
