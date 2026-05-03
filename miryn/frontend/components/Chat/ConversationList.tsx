"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { api } from "@/lib/api";
import type { Conversation } from "@/lib/types";
import { MoreHorizontal, Clock } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

// ── Fallback demo history for richer presentation ─────────────────────────────
const DEMO_CONVOS = [
  { id: "demo-1", title: "Who am I becoming lately?", updated_at: new Date(Date.now() - 1000 * 60 * 30).toISOString() },
  { id: "demo-2", title: "Blind spots in my work patterns", updated_at: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString() },
  { id: "demo-3", title: "Mapping my creative drift this month", updated_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString() },
  { id: "demo-4", title: "Open loops I keep postponing", updated_at: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString() },
  { id: "demo-5", title: "What my anxiety is really telling me", updated_at: new Date(Date.now() - 1000 * 60 * 60 * 72).toISOString() },
];

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  const h = Math.floor(m / 60);
  const d = Math.floor(h / 24);
  if (m < 1) return "Just now";
  if (m < 60) return `${m}m ago`;
  if (h < 24) return `${h}h ago`;
  return `${d}d ago`;
}

export default function ConversationList({ onItemClick }: { onItemClick?: () => void }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const pathname = usePathname();

  useEffect(() => {
    api.loadToken();
    api.listConversations()
      .then((convos) => {
        // If we get real convos, use them; otherwise show demo history
        setConversations(convos && convos.length > 0 ? convos : (DEMO_CONVOS as unknown as Conversation[]));
      })
      .catch(() => setConversations(DEMO_CONVOS as unknown as Conversation[]))
      .finally(() => setLoading(false));
  }, [pathname]);

  if (loading) {
    return (
      <div className="space-y-2 px-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-14 w-full bg-white/[0.02] rounded-2xl animate-pulse border border-white/[0.03]" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-1 px-3">
      <AnimatePresence>
        {conversations.slice(0, 8).map((conv, idx) => {
          const isActive = pathname.includes(conv.id);
          const timeStr = conv.updated_at ? timeAgo(conv.updated_at) : "";
          return (
            <motion.div
              key={conv.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.04 }}
            >
              <Link
                href={`/chat?id=${conv.id}`}
                onClick={onItemClick}
                className={`
                  group relative flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300
                  ${isActive
                    ? "bg-accent/[0.08] border border-accent/20"
                    : "hover:bg-white/[0.03] border border-transparent hover:border-white/[0.04]"
                  }
                `}
              >
                <div className={`w-1.5 h-1.5 rounded-full shrink-0 transition-colors ${
                  isActive ? "bg-accent shadow-[0_0_6px_rgba(200,184,255,0.5)]" : "bg-white/10 group-hover:bg-white/20"
                }`} />

                <div className="flex-1 min-w-0">
                  <p className={`text-[14px] truncate transition-colors leading-tight ${
                    isActive ? "text-primary font-bold" : "text-dim group-hover:text-primary"
                  }`}>
                    {conv.title || "Untitled Session"}
                  </p>
                  {timeStr && (
                    <div className="flex items-center gap-1 mt-0.5">
                      <Clock size={9} className="text-dim/50" />
                      <span className="text-[10px] text-dim/60 font-mono">{timeStr}</span>
                    </div>
                  )}
                </div>

                <button className="opacity-0 group-hover:opacity-100 p-1 text-dim hover:text-muted transition-all rounded-lg">
                  <MoreHorizontal size={14} />
                </button>

                {isActive && (
                  <motion.div
                    layoutId="active-conv"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-accent rounded-full"
                  />
                )}
              </Link>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
