"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useSearchParams, useRouter } from "next/navigation";
import { MoreVertical, Pin, Pencil, Trash2, CheckCircle2 } from "lucide-react";
import { AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import type { Conversation } from "@/lib/types";

type MenuState = { id: string; top: number; right: number } | null;

export default function ConversationList({ onItemClick }: { onItemClick?: () => void }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [menu, setMenu] = useState<MenuState>(null);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [confirmClearAll, setConfirmClearAll] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const pathname = usePathname();
  const activeId = useSearchParams().get("id");
  const router = useRouter();
  const menuRef = useRef<HTMLDivElement | null>(null);

  const loadConversations = () => {
    api.loadToken();
    setLoading(true);
    api.listConversations()
      .then((convos) => {
        setConversations(convos || []);
        setError(false);
      })
      .catch(() => {
        setConversations([]);
        setError(true);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadConversations();
  }, [pathname, activeId]);

  useEffect(() => {
    const closeMenu = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) setMenu(null);
    };
    document.addEventListener("mousedown", closeMenu);
    return () => document.removeEventListener("mousedown", closeMenu);
  }, []);

  const grouped = useMemo(() => {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const yesterdayStart = todayStart - 86400000;
    const sevenDaysAgo = todayStart - 7 * 86400000;
    const sections: { title: string; items: Conversation[] }[] = [
      { title: "Today", items: [] },
      { title: "Yesterday", items: [] },
      { title: "Previous 7 Days", items: [] },
      { title: "Older", items: [] },
    ];

    conversations
      .filter((conversation) => !conversation.is_pinned)
      .forEach((conversation) => {
        const time = conversation.updated_at ? new Date(conversation.updated_at).getTime() : now.getTime();
        const section =
          time >= todayStart
            ? sections[0]
            : time >= yesterdayStart
            ? sections[1]
            : time >= sevenDaysAgo
            ? sections[2]
            : sections[3];
        section.items.push(conversation);
      });

    return sections.filter((section) => section.items.length > 0);
  }, [conversations]);

  const pinned = conversations.filter((conversation) => Boolean(conversation.is_pinned));

  const updateConversation = async (id: string, update: (conversation: Conversation) => Conversation) => {
    setConversations((current) => current.map((conversation) => (conversation.id === id ? update(conversation) : conversation)));
  };

  const rename = async (conversation: Conversation) => {
    const title = window.prompt("Rename conversation", conversation.title || "New chat")?.trim();
    if (!title || title === conversation.title) return;
    try {
      await api.updateConversationTitle(conversation.id, title);
      await updateConversation(conversation.id, (current) => ({ ...current, title }));
      setMenu(null);
    } catch {
      setActionError("That conversation couldn't be renamed. Please try again.");
    }
  };

  const togglePin = async (conversation: Conversation) => {
    const pinnedValue = !conversation.is_pinned;
    try {
      await api.setConversationPinned(conversation.id, pinnedValue);
      await updateConversation(conversation.id, (current) => ({ ...current, is_pinned: pinnedValue }));
      setMenu(null);
    } catch {
      setActionError("That conversation couldn't be updated. Please try again.");
    }
  };

  const remove = async (conversation: Conversation) => {
    try {
      await api.deleteConversation(conversation.id);
      setConversations((current) => current.filter((item) => item.id !== conversation.id));
      if (activeId === conversation.id) router.push("/chat");
      setConfirmDelete(null);
      setMenu(null);
    } catch {
      setActionError("That conversation couldn't be deleted. Please try again.");
      setConfirmDelete(null);
    }
  };

  const clearAll = async () => {
    try {
      await api.clearConversations();
      setConversations([]);
      setConfirmClearAll(false);
    } catch {
      setActionError("Couldn't clear all chats. Please try again.");
      setConfirmClearAll(false);
    }
  };

  const renderConversation = (conversation: Conversation) => {
    const isActive = activeId === conversation.id;
    return (
      <div key={conversation.id} className="group relative flex items-center">
        <Link
          href={`/chat?id=${conversation.id}`}
          onClick={onItemClick}
          className={`conversation-item flex flex-1 min-w-0 items-center justify-between rounded-lg px-2.5 py-2 pe-8 text-left transition-colors ${
            isActive
              ? "conversation-item-active text-[color:var(--theme-text)] font-medium bg-[color:var(--theme-overlay)]"
              : "text-[color:var(--theme-muted)] hover:bg-[color:var(--theme-overlay)] hover:text-[color:var(--theme-text)]"
          }`}
        >
          <span className="min-w-0 truncate text-[13px]">{conversation.title || "New chat"}</span>
          {Boolean(conversation.is_pinned) && (
            <Pin size={12} className="ms-1 shrink-0 text-[color:var(--theme-accent)]" aria-label="Pinned" />
          )}
        </Link>

        {/* Kebab menu button (MoreVertical) replacing old 0 / invisible button */}
        <button
          type="button"
          aria-label={`Options for ${conversation.title || "New chat"}`}
          onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
            const rect = event.currentTarget.getBoundingClientRect();
            setMenu(
              menu?.id === conversation.id
                ? null
                : { id: conversation.id, top: rect.bottom + 4, right: Math.max(12, window.innerWidth - rect.right) }
            );
          }}
          className="absolute end-1.5 top-1/2 -translate-y-1/2 flex h-6 w-6 items-center justify-center rounded text-[color:var(--theme-dim)] opacity-40 transition-all hover:bg-[color:var(--theme-overlay)] hover:text-[color:var(--theme-text)] hover:opacity-100 group-hover:opacity-100 focus:opacity-100"
        >
          <MoreVertical size={14} strokeWidth={2} aria-hidden="true" />
        </button>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="space-y-2 px-3 py-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-8 w-full animate-pulse rounded-lg bg-[color:var(--theme-overlay)]" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-3 py-4 text-xs leading-relaxed text-[color:var(--theme-dim)]">
        <p>Couldn&apos;t load your chats.</p>
        <button type="button" onClick={loadConversations} className="mt-2 text-[color:var(--theme-text)] hover:underline">
          Try again
        </button>
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <div className="px-3 py-4 text-xs leading-relaxed text-[color:var(--theme-dim)] flex flex-col items-center justify-center text-center gap-2">
        <CheckCircle2 size={16} className="text-[color:var(--miryn-moss)] opacity-60" />
        <span>No active threads. Start a new reflection anytime.</span>
      </div>
    );
  }

  return (
    <div className="space-y-3 px-2 pb-4 font-ui">
      {actionError && (
        <div role="alert" className="mx-2 rounded-lg bg-[color:var(--theme-danger-bg)] px-3 py-2 text-xs text-[color:var(--theme-danger-text)]">
          {actionError}
        </div>
      )}

      {/* Header bar with total count and Clear All option */}
      <div className="flex items-center justify-between px-2.5 py-1 text-[11px] font-semibold tracking-normal text-[color:var(--theme-dim)]">
        <span>CHATS ({conversations.length})</span>
        <button
          type="button"
          onClick={() => setConfirmClearAll(true)}
          className="text-[10px] uppercase tracking-wider text-[color:var(--theme-dim)] hover:text-red-400 transition-colors"
          title="Clear all past chats"
        >
          Clear all
        </button>
      </div>

      <AnimatePresence>
        {pinned.length > 0 && (
          <div className="space-y-0.5">
            <div className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-semibold tracking-normal text-[color:var(--theme-dim)]">
              <Pin size={12} /> Pinned
            </div>
            {pinned.map(renderConversation)}
          </div>
        )}
        {grouped.map((section) => (
          <div key={section.title} className="space-y-0.5">
            <div className="px-2.5 py-1 text-[11px] font-semibold tracking-normal text-[color:var(--theme-dim)]">{section.title}</div>
            {section.items.map(renderConversation)}
          </div>
        ))}
      </AnimatePresence>

      {/* Kebab popup menu */}
      {menu && (() => {
        const conversation = conversations.find((item) => item.id === menu.id);
        if (!conversation) return null;
        return (
          <div
            ref={menuRef}
            className="fixed z-[100] w-40 rounded-xl border border-[color:var(--theme-border)] bg-[color:var(--theme-card)] p-1.5 shadow-xl backdrop-blur-md"
            style={{ top: menu.top, right: menu.right }}
          >
            <button
              type="button"
              onClick={() => rename(conversation)}
              className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-xs text-[color:var(--theme-text)] hover:bg-[color:var(--theme-overlay)] transition-colors"
            >
              <Pencil size={14} /> Rename
            </button>
            <button
              type="button"
              onClick={() => togglePin(conversation)}
              className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-xs text-[color:var(--theme-text)] hover:bg-[color:var(--theme-overlay)] transition-colors"
            >
              <Pin size={14} /> {conversation.is_pinned ? "Unpin" : "Pin"}
            </button>
            <button
              type="button"
              onClick={() => {
                setConfirmDelete(conversation.id);
                setMenu(null);
              }}
              className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-xs text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <Trash2 size={14} /> Delete
            </button>
          </div>
        );
      })()}

      {/* Delete Single Chat Dialog */}
      {confirmDelete && (
        <div
          className="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-conversation-title"
        >
          <div className="w-full max-w-sm rounded-2xl border border-[color:var(--theme-border)] bg-[color:var(--theme-card)] p-5 shadow-2xl">
            <h2 id="delete-conversation-title" className="text-sm font-semibold text-[color:var(--theme-text)]">
              Delete conversation?
            </h2>
            <p className="mt-2 text-xs leading-relaxed text-[color:var(--theme-muted)]">
              This removes this chat from your history. Saved memories are managed separately.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setConfirmDelete(null)}
                className="rounded-lg px-3 py-2 text-xs text-[color:var(--theme-muted)] hover:bg-[color:var(--theme-overlay)]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  const conversation = conversations.find((item) => item.id === confirmDelete);
                  if (conversation) remove(conversation);
                }}
                className="rounded-lg bg-red-500 px-3 py-2 text-xs font-semibold text-white hover:bg-red-600 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Clear All Chats Dialog */}
      {confirmClearAll && (
        <div
          className="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="clear-all-title"
        >
          <div className="w-full max-w-sm rounded-2xl border border-[color:var(--theme-border)] bg-[color:var(--theme-card)] p-5 shadow-2xl">
            <h2 id="clear-all-title" className="text-sm font-semibold text-[color:var(--theme-text)]">
              Clear all chat history?
            </h2>
            <p className="mt-2 text-xs leading-relaxed text-[color:var(--theme-muted)]">
              This clears your chat history. Saved memories are managed separately.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setConfirmClearAll(false)}
                className="rounded-lg px-3 py-2 text-xs text-[color:var(--theme-muted)] hover:bg-[color:var(--theme-overlay)]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={clearAll}
                className="rounded-lg bg-red-500 px-3 py-2 text-xs font-semibold text-white hover:bg-red-600 transition-colors"
              >
                Clear all chats
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
