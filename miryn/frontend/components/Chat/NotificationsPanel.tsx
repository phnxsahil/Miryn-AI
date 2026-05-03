"use client";

import type { Notification } from "@/lib/types";
import { Bell, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

type Props = {
  notifications: Notification[];
  onMarkRead: (id: string) => void;
};

export default function NotificationsPanel({ notifications, onMarkRead }: Props) {
  if (!notifications.length) {
    return null;
  }

  return (
    <div className="bg-card border border-white/[0.06] rounded-[32px] p-8 h-full flex flex-col shadow-sm">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-full bg-white/[0.03] border border-white/[0.06] flex items-center justify-center">
          <Bell size={18} className="text-muted" />
        </div>
        <span className="mono-label !text-[12px] !text-muted uppercase tracking-[0.2em] font-bold">Signal Feed</span>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto max-h-[200px] custom-scrollbar pr-2">
        <AnimatePresence initial={false}>
          {notifications.map((note) => (
            <motion.div 
              key={note.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              className={`
                group relative flex items-center justify-between gap-4 px-5 py-3.5 rounded-2xl border transition-all
                ${note.status === "new" 
                  ? "bg-white/[0.03] border-white/[0.06] shadow-sm" 
                  : "bg-transparent border-transparent opacity-40"}
              `}
            >
              <div className="flex-1 min-w-0">
                <div className="text-[13px] text-primary/70 truncate leading-relaxed font-medium">
                  {typeof note.payload?.message === "string" ? note.payload.message : note.type}
                </div>
              </div>

              {note.status === "new" && (
                <button
                  onClick={() => onMarkRead(note.id)}
                  className="shrink-0 p-2 rounded-full bg-accent/10 text-accent opacity-0 group-hover:opacity-100 transition-all hover:bg-accent/20"
                  aria-label="Mark as read"
                >
                  <Check size={14} />
                </button>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

