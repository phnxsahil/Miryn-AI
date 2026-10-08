"use client";

import { useEffect, useRef, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useChatStore } from "@/lib/store";
import type { Message, ToolRun, Notification } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";
import MessageBubble from "./MessageBubble";
import InputBox from "./InputBox";
import Link from "next/link";
import { AlertCircle, HeartPulse } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { MirynMark } from "@/components/visuals";

export default function ChatInterface() {
  const {
    messages,
    loading,
    streaming,
    conversationId,
    status,
    secondaryPanelsReady,
    streamingIndex,
    setMessages,
    appendMessage,
    updateStreamingMessage,
    setLoading,
    setStreaming,
    setConversationId,
    setStatus,
    setInsights,
    setConflicts,
    setPendingTools,
    setNotifications,
    setSecondaryPanelsReady,
    setStreamingIndex,
  } = useChatStore();

  const searchParams = useSearchParams();
  const router = useRouter();
  const idFromUrl = searchParams.get("id");

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const chatContainerRef = useRef<HTMLDivElement | null>(null);
  const isAutoScrolledRef = useRef(true);
  
  const chunkBufferRef = useRef("");
  const animationFrameRef = useRef<number | null>(null);
  const lastMessageRef = useRef<string | null>(null);

  const handleScroll = useCallback(() => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    // If user is within 100px of bottom, auto-scroll is enabled
    isAutoScrolledRef.current = scrollHeight - scrollTop - clientHeight < 100;
  }, []);

  useEffect(() => {
    api.loadToken();
  }, []);

  useEffect(() => {
    setInsights(null);
    setConflicts([]);
    setSecondaryPanelsReady(false);
    setStatus(null);
    if (idFromUrl) {
      setConversationId(idFromUrl);
      setLoading(true);
      api.getChatHistory(idFromUrl)
        .then((history) => {
          const nextHistory = (history as Message[]) || [];
          if (nextHistory.length > 0 || useChatStore.getState().messages.length === 0) {
            setMessages(nextHistory);
          }
          setLoading(false);
        })
        .catch((err) => {
          setMessages([]);
          setStatus(getErrorMessage(err, "Failed to load reflection history."));
          setLoading(false);
        });
    } else {
      setConversationId(null);
      setMessages([]);
    }
  }, [idFromUrl, setConflicts, setConversationId, setInsights, setLoading, setMessages, setSecondaryPanelsReady, setStatus]);

  useEffect(() => {
    if (messages.length === 0) return;
    let idleId: number | null = null;
    const timeoutId = window.setTimeout(() => {
      if (typeof window !== "undefined" && "requestIdleCallback" in window) {
        idleId = window.requestIdleCallback(() => setSecondaryPanelsReady(true));
      } else {
        setSecondaryPanelsReady(true);
      }
    }, 2000);

    return () => {
      if (timeoutId !== null) window.clearTimeout(timeoutId);
      if (idleId !== null && typeof window !== "undefined" && "cancelIdleCallback" in window) {
        window.cancelIdleCallback(idleId);
      }
    };
  }, [messages.length, setSecondaryPanelsReady]);

  useEffect(() => {
    if (!secondaryPanelsReady) return;
    api.listPendingTools().then((tools) => setPendingTools((tools as ToolRun[]) || [])).catch(() => null);
    api.listNotifications().then((notes) => setNotifications((notes as Notification[]) || [])).catch(() => null);
  }, [secondaryPanelsReady, setPendingTools, setNotifications]);

  useEffect(() => {
    if (!secondaryPanelsReady) return;
    const token = typeof window !== "undefined" ? localStorage.getItem("miryn_token") : null;
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const url = token ? `${baseUrl}/chat/events/stream?token=${token}` : `${baseUrl}/chat/events/stream`;
    const source = new EventSource(url, { withCredentials: false } as EventSourceInit);

    source.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "reflection.ready") setInsights(payload.payload || null);
        if (payload.type === "identity.conflict") setConflicts(payload.payload || []);
        if (payload.type === "notification.new") {
          const note = payload.payload as Notification;
          setNotifications((prev) => [note, ...prev]);
        }
      } catch {
        // ignore
      }
    };

    return () => source.close();
  }, [secondaryPanelsReady, setInsights, setConflicts, setNotifications]);

  const scrollToBottom = useCallback(() => {
    if (isAutoScrolledRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, scrollToBottom, streamingIndex]);

  useEffect(() => {
    return () => {
      if (animationFrameRef.current !== null) {
        window.cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  const flushChunkBuffer = useCallback(() => {
    if (!chunkBufferRef.current) return;
    const toApply = chunkBufferRef.current;
    chunkBufferRef.current = "";
    updateStreamingMessage(toApply);
  }, [updateStreamingMessage]);

  const sendMessage = async (rawMessage: string) => {
    const trimmed = rawMessage.trim();
    if (!trimmed || loading) return;
    lastMessageRef.current = trimmed;

    const timestamp = new Date().toISOString();
    appendMessage({ role: "user", content: trimmed, timestamp });
    setLoading(true);
    setStreaming(true);
    setStatus(null);

    let completed = false;

    try {
      const assistantTimestamp = new Date().toISOString();
      let nextIndex = 0;
      setMessages((prev) => {
        const next = [
          ...prev,
          {
            role: "assistant" as const,
            content: "",
            timestamp: assistantTimestamp,
          },
        ];
        nextIndex = next.length - 1;
        return next;
      });
      setStreamingIndex(nextIndex);

      for await (const event of api.streamMessage(trimmed, conversationId || undefined)) {
        if (event.error) throw new Error(event.error);
        if (event.chunk) {
          chunkBufferRef.current += event.chunk;
          if (animationFrameRef.current === null) {
            animationFrameRef.current = window.requestAnimationFrame(() => {
              flushChunkBuffer();
              animationFrameRef.current = null;
            });
          }
        }
        if (event.done && event.conversation_id) {
          flushChunkBuffer();
          if (!conversationId) {
            setConversationId(event.conversation_id);
            router.replace(`/chat?id=${event.conversation_id}`);
            window.setTimeout(() => {
              api.getChatHistory(event.conversation_id).then((history) => {
                const persistedHistory = history as Message[];
                if (persistedHistory.length > 0) setMessages(persistedHistory);
              }).catch(() => null);
            }, 1800);
          }
          completed = true;
          setLoading(false);
          setStreaming(false);
          setStreamingIndex(null);
          break;
        }
      }
      if (!completed) throw new Error("Connection lost during reflection.");
    } catch (error: unknown) {
      flushChunkBuffer();
      const errorMessage = getErrorMessage(error, "An error occurred during calibration.");
      setMessages((prev) => {
        const next = [...prev];
        const idx = useChatStore.getState().streamingIndex;
        if (idx !== null && next[idx]) {
          next[idx] = { ...next[idx], role: "system", content: errorMessage };
          return next;
        }
        next.push({ role: "system", content: errorMessage, timestamp: new Date().toISOString() });
        return next;
      });
      setStatus(errorMessage);
      setLoading(false);
      setStreaming(false);
      setStreamingIndex(null);
    }
  };

  const retryLastMessage = () => {
    if (!lastMessageRef.current || loading) return;
    setStatus(null);
    setMessages((prev) => {
      const withoutError = prev.filter((message) => message.role !== "system");
      return withoutError.at(-1)?.role === "user" ? withoutError.slice(0, -1) : withoutError;
    });
    void sendMessage(lastMessageRef.current);
  };

  return (
    <div className="flex flex-col h-screen bg-[color:var(--theme-bg)] text-[color:var(--theme-text)] overflow-hidden font-ui relative">
      {/* Subtle Impeccable Ambient Glow */}
      <div className="absolute top-0 right-1/3 w-[550px] h-[350px] bg-[radial-gradient(ellipse_at_top,_rgba(214,145,85,0.05),transparent_70%)] pointer-events-none" />

      {/* Minimalist Claude/ChatGPT Header */}
      <header className="h-14 px-5 md:px-6 flex items-center justify-between shrink-0 relative z-20 border-b border-[color:var(--theme-border)] bg-[color:var(--theme-bg)]/80 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2.5 px-2 py-1 text-sm font-semibold text-[color:var(--theme-text)]">
            <div className="w-6 h-6 rounded-lg bg-[color:var(--theme-surface)] border border-[color:var(--theme-border)] flex items-center justify-center">
              <MirynMark state="avatar" className="w-3.5 h-3.5 text-[color:var(--theme-accent)]" />
            </div>
            <span className="tracking-tight">Miryn</span>
          </div>

          {idFromUrl && (
            <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-[color:var(--theme-muted)] pl-3 border-l border-[color:var(--theme-border)]">
              <div className={`w-1.5 h-1.5 rounded-full ${loading ? "bg-[color:var(--theme-accent)] animate-pulse" : "bg-emerald-400"}`} />
              <span>{loading ? "Thinking..." : "Continuous Memory Synced"}</span>
            </div>
          )}
        </div>

        <Link
          href="/sanctuary"
          className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[color:var(--theme-overlay)] border border-[color:var(--theme-border)] hover:border-[color:var(--theme-accent)]/40 hover:bg-[color:var(--theme-overlay)] text-xs font-mono text-[color:var(--theme-text)] transition-all font-medium"
          title="Open Mind Sanctuary & Emotional Barometer"
        >
          <HeartPulse size={13} className="text-[color:var(--theme-accent)]" />
          <span className="hidden sm:inline">SANCTUARY</span>
        </Link>
      </header>

      {/* Error banner */}
      <AnimatePresence>
        {status && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-rose-500/10 border-b border-rose-500/20 text-rose-300 text-xs px-6 py-2.5 shrink-0 flex items-center justify-between z-30"
          >
            <div className="flex items-center gap-2">
              <AlertCircle size={14} />
              <span>{status}</span>
            </div>
            <div className="flex items-center gap-2">
              {lastMessageRef.current && (
                <button type="button" onClick={retryLastMessage} className="rounded px-2 py-1 font-medium hover:bg-rose-500/20">
                  Retry
                </button>
              )}
              <button onClick={() => setStatus(null)} className="hover:text-white transition-colors">✕</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Messages Scroll Area */}
      <div 
        ref={chatContainerRef} 
        onScroll={handleScroll} 
        className="flex-1 overflow-y-auto px-4 md:px-6 py-6 custom-scrollbar relative"
      >
        <div className="max-w-3xl mx-auto w-full">
          {/* Empty State Hero */}
          {messages.length === 0 && !loading && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col items-center justify-center min-h-[min(540px,calc(100vh-230px))] py-12 text-center relative"
            >
              <div className="w-10 h-10 rounded-2xl bg-[color:var(--theme-surface)] border border-[color:var(--theme-border)] flex items-center justify-center text-[color:var(--theme-accent)] mb-5 shadow-[0_0_20px_rgba(214,145,85,0.15)]">
                <MirynMark state="avatar" className="w-5 h-5 text-[color:var(--theme-accent)]" />
              </div>

              <h2 className="text-3xl md:text-4xl font-editorial italic tracking-tight text-[color:var(--theme-text)] mb-2.5">
                Where memory meets presence.
              </h2>
              <p className="text-xs md:text-sm text-[color:var(--theme-muted)] max-w-md mx-auto mb-8 leading-relaxed font-ui">
                An evolving companion with continuous 384-dim recall, versioned identity, and zero-knowledge encryption.
              </p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-[720px] text-left">
                {[
                  { title: "Decompress & Untangle", desc: "Quiet somatic check-in and 2-minute thought dump", prompt: "I'm feeling mentally scattered right now. Can we do a gentle, grounding 2-minute mind dump to untangle my thoughts?" },
                  { title: "Notice My Patterns & Loops", desc: "Reflect on subtle recurring cycles and blindspots", prompt: "Reflecting on who I am and our past conversations, what subconscious patterns or tensions have you noticed in me lately?" },
                  { title: "High-Stakes Decision", desc: "Balance core values with emotional clarity", prompt: "I need to make an important decision. Help me weigh the trade-offs without overthinking or second-guessing." },
                  { title: "Unburden Working Memory", desc: "Park swirling tasks and reset cognitive load", prompt: "I have too many open loops running in my head. Help me externalize them and park what can wait." }
                ].map((s) => (
                  <button
                    key={s.title}
                    onClick={() => sendMessage(s.prompt)}
                    className="p-4 rounded-2xl bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] hover:border-[color:var(--theme-accent)]/40 hover:bg-[color:var(--theme-card-hover)] transition-all group text-left shadow-sm"
                  >
                    <div className="text-[13.5px] font-medium text-[color:var(--theme-text)] mb-1 group-hover:text-white transition-colors">{s.title}</div>
                    <div className="text-xs text-[color:var(--theme-muted)] leading-relaxed">{s.desc}</div>
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Conversation Stream */}
          <div className="space-y-4">
            {messages.map((msg, idx) => (
              <MessageBubble
                key={`${msg.timestamp}-${idx}`}
                message={msg}
                isStreaming={streaming && idx === streamingIndex}
              />
            ))}
          </div>

          <div ref={messagesEndRef} className="h-24" />
        </div>
      </div>

      {/* Floating Bottom Input Area */}
      <div className="shrink-0 relative z-20">
        <div className="absolute bottom-full left-0 w-full h-20 bg-gradient-to-t from-[color:var(--theme-bg)] via-[color:var(--theme-bg)]/80 to-transparent pointer-events-none" />
        
        <div className="max-w-3xl mx-auto w-full px-4 md:px-0 pb-6">
          <InputBox onSend={sendMessage} disabled={loading} />
        </div>
      </div>
    </div>
  );
}
