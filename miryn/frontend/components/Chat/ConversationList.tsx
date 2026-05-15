"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { api } from "@/lib/api";
import type { Conversation } from "@/lib/types";
import { MoreHorizontal } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const DEMO_CONVOS = [
  { id: "demo-1", title: "Reflecting on my habits", updated_at: new Date(Date.now() - 1000 * 60 * 30).toISOString() },
  { id: "demo-2", title: "Blind spots in my work", updated_at: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString() },
  { id: "demo-3", title: "Creative drift this month", updated_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString() },
  { id: "demo-4", title: "Open loops", updated_at: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString() },
];

export default function ConversationList({ onItemClick }: { onItemClick?: () => void }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const pathname = usePathname();

  useEffect(() => {
    api.loadToken();
    api.listConversations()
      .then((convos) => {
        setConversations(convos && convos.length > 0 ? convos : (DEMO_CONVOS as unknown as Conversation[]));
      })
      .catch(() => setConversations(DEMO_CONVOS as unknown as Conversation[]))
      .finally(() => setLoading(false));
  }, [pathname]);

  if (loading) {
    return (
      <div className="space-y-1 px-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-9 w-full bg-white/[0.02] rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-[2px] px-3">
      <AnimatePresence>
        {conversations.slice(0, 10).map((conv, idx) => {
          const isActive = pathname.includes(conv.id);
          return (
            <motion.div
              key={conv.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: idx * 0.03 }}
            >
              <Link
                href={`/chat?id=${conv.id}`}
                onClick={onItemClick}
                className={`
                  group relative flex items-center justify-between px-3 py-2 rounded-lg transition-colors
                  ${isActive
                    ? "bg-white/[0.08] text-white"
                    : "text-dim hover:bg-white/[0.04] hover:text-primary"
                  }
                `}
              >
                <div className="flex-1 min-w-0 pr-2">
                  <p className="text-[13px] truncate font-medium">
                    {conv.title || "New Chat"}
                  </p>
                </div>

                {/* Only show the dots when hovering or active, otherwise keep it clean */}
                <button className={`opacity-0 group-hover:opacity-100 p-1 text-dim hover:text-white transition-colors rounded ${isActive && 'opacity-100 text-white'}`}>
                  <MoreHorizontal size={14} />
                </button>
              </Link>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
