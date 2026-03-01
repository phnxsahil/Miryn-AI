"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Message, ConversationInsights, ToolRun, Notification } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";
import MessageBubble from "./MessageBubble";
import InputBox from "./InputBox";
import InsightsPanel from "./InsightsPanel";
import ToolPanel from "./ToolPanel";
import NotificationsPanel from "./NotificationsPanel";

/**
 * Full chat UI component that manages conversation state, message flow, tools, insights, and notifications.
 *
 * Initializes the auth token on mount, fetches pending tools and notifications, and subscribes to server-sent events to update insights, identity conflicts, and new notifications in real time. Exposes an input for sending messages, displays message history (including assistant/system responses and temporary "Thinking..." state), and provides panels for insights, notifications, and tool generation/approval.
 *
 * @returns The rendered chat interface element (React JSX).
 */
export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const searchParams = useSearchParams();
  const idFromUrl = searchParams.get("id");
  const [conversationId, setConversationId] = useState<string | null>(idFromUrl);
  const [status, setStatus] = useState<string | null>(null);
  const [insights, setInsights] = useState<ConversationInsights | null>(null);
  const [conflicts, setConflicts] = useState<Array<{ statement: string; conflict_with: string; severity?: number }>>([]);
  const [pendingTools, setPendingTools] = useState<ToolRun[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const streamingIndexRef = useRef<number | null>(null);
  const [streaming, setStreaming] = useState(false);

  useEffect(() => {
    api.loadToken();
  }, []);

  // Handle URL change: load history or reset for new chat
  useEffect(() => {
    if (idFromUrl) {
      setConversationId(idFromUrl);
      setLoading(true);
      api.getChatHistory(idFromUrl)
        .then((history) => {
          setMessages((history as Message[]) || []);
          setLoading(false);
        })
        .catch((err) => {
          setStatus(getErrorMessage(err, "Failed to load chat history"));
          setLoading(false);
        });
    } else {
      setConversationId(null);
      setMessages([]);
      setInsights(null);
      setConflicts([]);
    }
  }, [idFromUrl]);

  useEffect(() => {
    api.listPendingTools().then((tools) => setPendingTools((tools as ToolRun[]) || [])).catch(() => null);
    api.listNotifications().then((notes) => setNotifications((notes as Notification[]) || [])).catch(() => null);
  }, []);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("miryn_token") : null;
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const url = token ? `${baseUrl}/chat/events/stream?token=${token}` : `${baseUrl}/chat/events/stream`;
    const source = new EventSource(url, { withCredentials: false } as EventSourceInit);

    source.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "reflection.ready") {
          setInsights(payload.payload || null);
        }
        if (payload.type === "identity.conflict") {
          setConflicts(payload.payload || []);
        }
        if (payload.type === "notification.new") {
          const note = payload.payload as Notification;
          setNotifications((prev) => [note, ...prev]);
        }
      } catch {
        return;
      }
    };

    source.onerror = () => {
      source.close();
    };

    return () => source.close();
  }, []);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, scrollToBottom]);

  const appendMessage = useCallback((message: Message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const sendMessage = async (rawMessage: string) => {
    const trimmed = rawMessage.trim();
    if (!trimmed || loading) return;

    const timestamp = new Date().toISOString();
    appendMessage({ role: "user", content: trimmed, timestamp });
    setLoading(true);
    setStreaming(true);
    setStatus(null);

    let completed = false;

    try {
      const assistantTimestamp = new Date().toISOString();
      setMessages((prev) => {
        const next = [
          ...prev,
          {
            role: "assistant" as const,
            content: "",
            timestamp: assistantTimestamp,
          },
        ];
        streamingIndexRef.current = next.length - 1;
        return next;
      });

      for await (const event of api.streamMessage(trimmed, conversationId || undefined)) {
        if (event.error) {
          throw new Error(event.error);
        }
        if (event.chunk) {
          setMessages((prev) => {
            const next = [...prev];
            const idx = streamingIndexRef.current;
            if (idx !== null && next[idx]) {
              next[idx] = { ...next[idx], content: `${next[idx].content}${event.chunk}` };
            }
            return next;
          });
        }
        if (event.done && event.conversation_id) {
          if (!conversationId) {
            setConversationId(event.conversation_id);
          }
          completed = true;
          setLoading(false);
          setStreaming(false);
          streamingIndexRef.current = null;
          break;
        }
      }
      if (!completed) {
        throw new Error("The connection was lost before Miryn could finish reflecting.");
      }
    } catch (error: unknown) {
      const errorMessage = getErrorMessage(error, "Sorry, something went wrong. Please try again.");
      setMessages((prev) => {
        const next = [...prev];
        const idx = streamingIndexRef.current;
        if (idx !== null && next[idx]) {
          next[idx] = { ...next[idx], role: "system", content: errorMessage };
          return next;
        }
        next.push({
          role: "system",
          content: errorMessage,
          timestamp: new Date().toISOString(),
        });
        return next;
      });
      setStatus(errorMessage);

      if (errorMessage.toLowerCase().includes("session expired")) {
        setTimeout(() => {
          window.location.href = "/login?expired=1";
        }, 800);
      }
      setLoading(false);
      setStreaming(false);
      streamingIndexRef.current = null;
    }
  };

  const generateTool = async (intent: string) => {
    try {
      await api.generateTool(intent);
      const tools = (await api.listPendingTools()) as ToolRun[];
      setPendingTools(tools || []);
    } catch (error: unknown) {
      const errorMessage = getErrorMessage(error, "Failed to generate tool.");
      setStatus(errorMessage);
    }
  };

  const approveTool = async (toolId: string) => {
    try {
      const res = (await api.approveTool(toolId)) as { result?: { output?: string; error?: string } };
      if (res?.result?.output) {
        appendMessage({
          role: "system",
          content: `Tool output: ${res.result.output}`,
          timestamp: new Date().toISOString(),
        });
      }
      if (res?.result?.error) {
        appendMessage({
          role: "system",
          content: `Tool error: ${res.result.error}`,
          timestamp: new Date().toISOString(),
        });
      }
      const tools = (await api.listPendingTools()) as ToolRun[];
      setPendingTools(tools || []);
    } catch (error: unknown) {
      const errorMessage = getErrorMessage(error, "Failed to run tool.");
      setStatus(errorMessage);
    }
  };

  const markNotificationRead = async (id: string) => {
    try {
      await api.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((note) => (note.id === id ? { ...note, status: "read" } : note))
      );
    } catch (error: unknown) {
      const errorMessage = getErrorMessage(error, "Failed to mark notification.");
      setStatus(errorMessage);
    }
  };

  const notificationCount = notifications.filter((n) => n.status === "new").length;

  return (
    <div className="flex flex-col h-[100dvh] md:h-screen bg-void max-h-screen overflow-hidden">
      <div className="hidden md:flex border-b border-white/10 p-6 items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-light text-white">Miryn</h1>
          <p className="text-sm text-secondary">A quiet room for honest reflection.</p>
        </div>
        {notificationCount > 0 && (
          <div className="text-xs uppercase tracking-[0.2em] text-amber-200">
            Notifications <span className="ml-2 rounded-full bg-amber-500/20 px-2 py-1">{notificationCount}</span>
          </div>
        )}
      </div>

      {status && (
        <div className="bg-red-500/10 border-y border-red-500/20 text-red-200 text-[10px] md:text-xs tracking-[0.2em] uppercase px-4 md:px-6 py-2 shrink-0">
          {status}
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
        {messages.map((msg, idx) => (
          <MessageBubble
            key={`${msg.timestamp}-${idx}`}
            message={msg}
            isStreaming={streaming && idx === streamingIndexRef.current}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="shrink-0">
        <InsightsPanel insights={insights} conflicts={conflicts} />
        <NotificationsPanel notifications={notifications} onMarkRead={markNotificationRead} />
        <ToolPanel pending={pendingTools} onGenerate={generateTool} onApprove={approveTool} />
        <InputBox onSend={sendMessage} disabled={loading} />
      </div>
    </div>
  );
}
