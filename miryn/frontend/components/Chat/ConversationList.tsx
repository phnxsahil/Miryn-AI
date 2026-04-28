"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { api } from "@/lib/api";
import type { Conversation } from "@/lib/types";
import { MessageSquare } from "lucide-react";

export default function ConversationList({ onItemClick }: { onItemClick?: () => void }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const pathname = usePathname();

  useEffect(() => {
    api.loadToken();
    api.listConversations()
      .then(setConversations)
      .catch(() => setConversations([]))
      .finally(() => setLoading(false));
  }, [pathname]); // Reload when path changes (e.g. after starting a new chat)

  if (loading) {
    return <div className="px-3 py-2 text-xs text-secondary animate-pulse">Loading chats...</div>;
  }

  if (conversations.length === 0) {
    return <div className="px-3 py-2 text-xs text-secondary italic text-white/40">No recent chats</div>;
  }

  return (
    <div className="space-y-1">
      {conversations.map((conv) => {
        const isActive = pathname.includes(conv.id);
        return (
          <Link
            key={conv.id}
            href={`/chat?id=${conv.id}`}
            onClick={onItemClick}
            className={`
              flex items-center gap-3 px-3 py-2 rounded-xl text-xs transition-colors
              ${isActive 
                ? "bg-white/10 text-white" 
                : "text-secondary hover:bg-white/5 hover:text-white"
              }
            `}
          >
            <MessageSquare size={14} className={isActive ? "text-accent" : "text-secondary"} />
            <span className="truncate flex-1">{conv.title || "Untitled Chat"}</span>
          </Link>
        );
      })}
    </div>
  );
}
