"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Message, ConversationInsights, ToolRun, Notification } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";
import MessageBubble from "./MessageBubble";
import InputBox from "./InputBox";
import InsightsPanel from "./InsightsPanel";
import { Sparkles, Bell, Brain, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const ToolPanel = dynamic(() => import("./ToolPanel"));
const NotificationsPanel = dynamic(() => import("./NotificationsPanel"));

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
  const [secondaryPanelsReady, setSecondaryPanelsReady] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const streamingIndexRef = useRef<number | null>(null);
  const chunkBufferRef = useRef("");
  const animationFrameRef = useRef<number | null>(null);
  const [streaming, setStreaming] = useState(false);

  useEffect(() => {
    api.loadToken();
  }, []);

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
    let timeoutId: number | null = null;
    let idleId: number | null = null;

    if (typeof window !== "undefined" && "requestIdleCallback" in window) {
      idleId = window.requestIdleCallback(() => setSecondaryPanelsReady(true), { timeout: 1200 });
    } else {
      timeoutId = (window as any).setTimeout(() => setSecondaryPanelsReady(true), 500);
    }

    return () => {
      if (timeoutId !== null) window.clearTimeout(timeoutId);
      if (idleId !== null && typeof window !== "undefined" && "cancelIdleCallback" in window) {
        window.cancelIdleCallback(idleId);
      }
    };
  }, []);

  useEffect(() => {
    if (!secondaryPanelsReady) return;
    api.listPendingTools().then((tools) => setPendingTools((tools as ToolRun[]) || [])).catch(() => null);
    api.listNotifications().then((notes) => setNotifications((notes as Notification[]) || [])).catch(() => null);
  }, [secondaryPanelsReady]);

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
        return;
      }
    };

    source.onerror = () => source.close();
    return () => source.close();
  }, [secondaryPanelsReady]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, scrollToBottom]);

  useEffect(() => {
    return () => {
      if (animationFrameRef.current !== null) {
        window.cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  const appendMessage = useCallback((message: Message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const flushChunkBuffer = useCallback(() => {
    if (!chunkBufferRef.current) return;
    const toApply = chunkBufferRef.current;
    chunkBufferRef.current = "";
    setMessages((prev) => {
      const next = [...prev];
      const idx = streamingIndexRef.current;
      if (idx !== null && next[idx]) {
        next[idx] = { ...next[idx], content: `${next[idx].content}${toApply}` };
      }
      return next;
    });
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
          if (!conversationId) setConversationId(event.conversation_id);
          completed = true;
          setLoading(false);
          setStreaming(false);
          streamingIndexRef.current = null;
          break;
        }
      }
      if (!completed) throw new Error("Connection lost during reflection.");
    } catch (error: unknown) {
      flushChunkBuffer();
      const errorMessage = getErrorMessage(error, "An error occurred during calibration.");
      setMessages((prev) => {
        const next = [...prev];
        const idx = streamingIndexRef.current;
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
      streamingIndexRef.current = null;
    }
  };

  const generateTool = async (intent: string) => {
    try {
      await api.generateTool(intent);
      const tools = (await api.listPendingTools()) as ToolRun[];
      setPendingTools(tools || []);
    } catch (error: unknown) {
      setStatus(getErrorMessage(error, "Failed to generate tool."));
    }
  };

  const approveTool = async (toolId: string) => {
    try {
      const res = (await api.approveTool(toolId)) as { result?: { output?: string; error?: string } };
      if (res?.result?.output) {
        appendMessage({ role: "system", content: `Tool output: ${res.result.output}`, timestamp: new Date().toISOString() });
      }
      const tools = (await api.listPendingTools()) as ToolRun[];
      setPendingTools(tools || []);
    } catch (error: unknown) {
      setStatus(getErrorMessage(error, "Failed to run tool."));
    }
  };

  const markNotificationRead = async (id: string) => {
    try {
      await api.markNotificationRead(id);
      setNotifications((prev) => prev.map((note) => (note.id === id ? { ...note, status: "read" } : note)));
    } catch (error: unknown) {
      setStatus(getErrorMessage(error, "Failed to update notification."));
    }
  };

  const unreadCount = notifications.filter((n) => n.status === "new").length;

  return (
    <div className="flex flex-col h-screen bg-void overflow-hidden font-ui relative">
      {/* Background ambient glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-4xl h-[400px] bg-accent/[0.05] blur-[150px] pointer-events-none -z-10" />

      {/* Header */}
      <header className="px-10 py-8 flex items-center justify-between shrink-0 relative z-20 border-b border-white/[0.04] bg-[#0f0f17]/80 backdrop-blur-xl">
        <div className="flex items-center gap-6">
          <div className="flex flex-col">
            <h1 className="text-xl font-bold tracking-tight text-primary">
              {idFromUrl ? "Active Reflection" : "New Session"}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <div className={`w-2 h-2 rounded-full ${loading ? "bg-accent animate-pulse" : "bg-white/10"}`} />
              <span className="mono-label !text-[11px] !text-dim uppercase tracking-widest">
                {loading ? "Listening..." : "Standing By"}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-5">
           <div className="hidden md:flex items-center gap-3 px-5 py-2.5 rounded-full bg-accent/[0.06] border border-accent/15">
             <Brain size={16} className="text-accent" />
             <span className="mono-label !text-[11px] !text-accent tracking-widest">Resonance: 98.4%</span>
           </div>
           
           <div className="relative">
             <button className="p-3 rounded-full bg-white/[0.03] border border-white/[0.06] text-dim hover:text-primary transition-all">
               <Bell size={20} />
               {unreadCount > 0 && <span className="absolute top-2.5 right-2.5 w-2.5 h-2.5 bg-accent rounded-full shadow-[0_0_10px_rgba(200,184,255,0.4)]" />}
             </button>
           </div>
        </div>
      </header>

      {/* Error Bar */}
      <AnimatePresence>
        {status && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-[rgba(226,75,74,0.08)] border-l-2 border-l-[#e24b4a] text-[#c17070] text-[11px] mono-label tracking-widest px-8 py-3 shrink-0 flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <AlertCircle size={14} />
              {status}
            </div>
            <button onClick={() => setStatus(null)} className="hover:text-white transition-colors">✕</button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Reflective Canvas (Messages Area) */}
      <div className="flex-1 overflow-y-auto px-6 py-12 custom-scrollbar relative">
        <div className="max-w-3xl mx-auto w-full">
          {messages.length === 0 && !loading && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1.2, ease: "easeOut" }}
              className="flex flex-col items-center justify-center py-24 text-center"
            >
              <div className="w-24 h-24 rounded-full bg-accent/[0.06] border border-accent/15 flex items-center justify-center mb-10 accent-glow">
                <Sparkles className="text-accent w-12 h-12" />
              </div>
              <h2 className="text-5xl md:text-6xl font-bold tracking-tight text-primary mb-8">The Mirror is Ready.</h2>
              <p className="text-2xl editorial-italic text-muted max-w-xl mb-20 leading-relaxed">
                "What we notice about ourselves is the beginning of who we can become."
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl">
                {[
                  { title: "Reflective Journey", desc: "Help me reflect on my last 7 days", prompt: "Help me reflect on my week" },
                  { title: "Pattern Recognition", desc: "Analyze my recent identity shifts", prompt: "Analyze my recent patterns" },
                  { title: "Blind Spot Check", desc: "Show me what I might be missing", prompt: "Reveal my blind spots" },
                  { title: "System Calibration", desc: "Sync my core belief architecture", prompt: "Calibrate my identity" }
                ].map((s) => (
                  <button
                    key={s.title}
                    onClick={() => sendMessage(s.prompt)}
                    className="p-8 rounded-[32px] bg-card border border-white/[0.04] text-left hover:border-accent/30 hover:bg-accent/[0.03] transition-all group relative overflow-hidden"
                  >
                    <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-accent/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    <h3 className="text-lg font-bold text-primary mb-2">{s.title}</h3>
                    <p className="text-sm text-muted group-hover:text-primary/70 transition-colors">{s.desc}</p>
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          <div className="space-y-4">
            {messages.map((msg, idx) => (
              <MessageBubble
                key={`${msg.timestamp}-${idx}`}
                message={msg}
                isStreaming={streaming && idx === streamingIndexRef.current}
              />
            ))}
          </div>

          {loading && !streaming && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex gap-8 items-start py-12"
            >
              <div className="w-2 h-10 rounded-full bg-accent/20 animate-pulse" />
              <div className="flex-1 space-y-6">
                <div className="h-5 bg-white/[0.04] rounded-full w-3/4 animate-pulse" />
                <div className="h-5 bg-white/[0.04] rounded-full w-1/2 animate-pulse" />
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} className="h-32" />
        </div>
      </div>

      {/* Floating Insight Area & Input */}
      <div className="shrink-0 relative z-20">
        {/* Subtle top gradient to separate messages from input */}
        <div className="absolute bottom-full left-0 w-full h-32 bg-gradient-to-t from-[#09090e] to-transparent pointer-events-none" />
        
        <div className="max-w-4xl mx-auto w-full px-6 pb-10">
          <div className="mb-6">
            <InsightsPanel insights={insights} conflicts={conflicts} />
          </div>
          
          <AnimatePresence>
            {secondaryPanelsReady && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6"
              >
                <NotificationsPanel notifications={notifications} onMarkRead={markNotificationRead} />
                <ToolPanel pending={pendingTools} onGenerate={generateTool} onApprove={approveTool} />
              </motion.div>
            )}
          </AnimatePresence>

          <InputBox onSend={sendMessage} disabled={loading} />
        </div>
      </div>
    </div>
  );
}
