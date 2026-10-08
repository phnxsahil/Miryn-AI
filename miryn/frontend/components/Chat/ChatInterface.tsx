"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowDown, Lightbulb, X } from "lucide-react";
import { api } from "@/lib/api";
import { useChatStore } from "@/lib/store";
import type { Message, Notification, ToolRun } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";
import MessageBubble from "./MessageBubble";
import InputBox from "./InputBox";
import InsightsPanel from "./InsightsPanel";

const suggestions = [
  { title: "Plan my day", prompt: "Help me turn a messy list into a clear next step." },
  { title: "Write something", prompt: "Help me draft a message with the right tone." },
  { title: "Reflect on my week", prompt: "Help me reflect on this week's decisions, wins, and challenges." },
  { title: "Think through a decision", prompt: "Help me weigh the tradeoffs of a decision without overcomplicating it." },
];

export default function ChatInterface() {
  const { messages, loading, streaming, conversationId, status, secondaryPanelsReady, streamingIndex,
    insights, conflicts, setMessages, setLoading, setStreaming, setConversationId, setStatus,
    setInsights, setConflicts, setPendingTools, setNotifications, setSecondaryPanelsReady,
    setStreamingIndex, updateStreamingMessage } = useChatStore();
  const router = useRouter();
  const idFromUrl = useSearchParams().get("id");
  const scrollRef = useRef<HTMLDivElement>(null);
  const requestRef = useRef<AbortController | null>(null);
  const ownRouteRef = useRef<string | null>(null);
  const historyRequestRef = useRef(0);
  const pinnedRef = useRef(true);
  const [pinned, setPinned] = useState(true);
  const [insightsOpen, setInsightsOpen] = useState(false);
  const [savedIndex, setSavedIndex] = useState<number | null>(null);
  const [stoppedIndex, setStoppedIndex] = useState<number | null>(null);
  const [historyRetry, setHistoryRetry] = useState(0);
  const lastMessageRef = useRef<string | null>(null);

  useEffect(() => { api.loadToken(); }, []);
  useEffect(() => {
    if (ownRouteRef.current && ownRouteRef.current === idFromUrl) {
      ownRouteRef.current = null;
      return;
    }
    requestRef.current?.abort();
    const currentRequest = ++historyRequestRef.current;
    let active = true;
    setSavedIndex(null);
    setStoppedIndex(null);
    setStatus(null);
    setInsights(null);
    setConflicts([]);
    setConversationId(idFromUrl);
    setMessages([]);
    if (!idFromUrl) { setLoading(false); return; }
    setLoading(true);
    api.getChatHistory(idFromUrl).then((history) => {
      if (active && historyRequestRef.current === currentRequest) setMessages(history as Message[]);
    }).catch((error) => {
      if (active && historyRequestRef.current === currentRequest) setStatus(getErrorMessage(error, "Could not load this conversation."));
    }).finally(() => {
      if (active && historyRequestRef.current === currentRequest) setLoading(false);
    });
    return () => { active = false; };
  }, [historyRetry, idFromUrl, setConflicts, setConversationId, setInsights, setLoading, setMessages, setStatus]);

  useEffect(() => {
    if (!messages.length) return;
    const id = window.setTimeout(() => setSecondaryPanelsReady(true), 800);
    return () => window.clearTimeout(id);
  }, [messages.length, setSecondaryPanelsReady]);
  useEffect(() => {
    if (!secondaryPanelsReady) return;
    api.listPendingTools().then((items) => setPendingTools(items as ToolRun[])).catch(() => null);
    api.listNotifications().then((items) => setNotifications(items as Notification[])).catch(() => null);
  }, [secondaryPanelsReady, setPendingTools, setNotifications]);
  useEffect(() => {
    if (!secondaryPanelsReady) return;
    const source = new EventSource(api.getChatEventsUrl());
    source.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "reflection.ready") setInsights(payload.payload || null);
        if (payload.type === "identity.conflict") setConflicts(payload.payload || []);
        if (payload.type === "notification.new") setNotifications((prev) => [payload.payload as Notification, ...prev]);
      } catch { /* Ignore malformed background events. */ }
    };
    return () => source.close();
  }, [secondaryPanelsReady, setConflicts, setInsights, setNotifications]);

  const jumpToLatest = useCallback(() => {
    const area = scrollRef.current;
    if (area) area.scrollTop = area.scrollHeight;
    pinnedRef.current = true;
    setPinned(true);
  }, []);
  useEffect(() => { if (pinnedRef.current) jumpToLatest(); }, [messages, jumpToLatest]);
  useEffect(() => () => requestRef.current?.abort(), []);

  const confirmSaved = async (id: string, assistantContent: string, assistantIndex: number) => {
    // ponytail: bounded polling confirms a durable memory tier; the backend has no memory-saved event.
    for (let attempt = 0; attempt < 4; attempt++) {
      await new Promise((resolve) => window.setTimeout(resolve, 750 * (attempt + 1)));
      if (useChatStore.getState().conversationId !== id) return;
      try {
        const memory = await api.getMemory();
        const saved = [...memory.facts, ...memory.recent].some((item) =>
          item.content?.trim() === assistantContent.trim() && (item.memory_tier === "core" || item.memory_tier === "episodic"));
        if (saved) {
          setSavedIndex(assistantIndex);
          return;
        }
      } catch { /* A transient memory lookup failure should not interrupt the reply. */ }
    }
  };

  const sendMessage = async (rawMessage: string) => {
    const content = rawMessage.trim();
    if (!content || useChatStore.getState().loading || requestRef.current) return;
    lastMessageRef.current = content;
    const initial = useChatStore.getState().messages;
    const assistantIndex = initial.length + 1;
    const timestamp = new Date().toISOString();
    setMessages([...initial, { role: "user", content, timestamp }, { role: "assistant", content: "", timestamp }]);
    setStreamingIndex(assistantIndex);
    setSavedIndex(null);
    setStoppedIndex(null);
    setStatus(null);
    setLoading(true);
    setStreaming(true);
    jumpToLatest();
    const controller = new AbortController();
    requestRef.current = controller;
    let completed = false;
    let newId: string | undefined;
    try {
      for await (const event of api.streamMessage(content, conversationId || undefined, controller.signal)) {
        if (event.error) throw new Error(event.error);
        if (event.chunk) updateStreamingMessage(event.chunk);
        if (event.done) {
          newId = event.conversation_id;
          if (!useChatStore.getState().messages[assistantIndex]?.content.trim()) {
            throw new Error("Miryn returned an empty reply. Please retry.");
          }
          completed = true;
          break;
        }
      }
      if (!completed) throw new Error("The connection ended before Miryn finished. Please retry.");
      if (newId && !conversationId) {
        ownRouteRef.current = newId;
        setConversationId(newId);
        router.replace("/chat?id=" + newId);
      }
      const assistantContent = useChatStore.getState().messages[assistantIndex]?.content || "";
      if (assistantContent && (newId || conversationId)) void confirmSaved((newId || conversationId)!, assistantContent, assistantIndex);
    } catch (error) {
      if (newId && !conversationId) {
        ownRouteRef.current = newId;
        setConversationId(newId);
        router.replace("/chat?id=" + newId);
      }
      if (controller.signal.aborted) {
        setStoppedIndex(assistantIndex);
        setStatus("Reply stopped. This message may not have been saved.");
      } else {
        setStatus(getErrorMessage(error, "Miryn could not finish the reply."));
        if (!useChatStore.getState().messages[assistantIndex]?.content) {
          setMessages((current) => current.filter((_, index) => index !== assistantIndex));
        }
      }
    } finally {
      if (requestRef.current === controller) requestRef.current = null;
      setLoading(false);
      setStreaming(false);
      setStreamingIndex(null);
    }
  };

  const retry = () => {
    if (!lastMessageRef.current || loading) return;
    const content = lastMessageRef.current;
    setMessages((current) => {
      const lastUser = current.findLastIndex((message) => message.role === "user" && message.content === content);
      return lastUser < 0 ? current : current.slice(0, lastUser);
    });
    setStatus(null);
    window.setTimeout(() => void sendMessage(content), 0);
  };

  return (
    <div className="flex h-full min-h-0 flex-col bg-[color:var(--theme-bg)] text-[color:var(--theme-text)] font-ui">
      <header className={`${insights || conflicts.length > 0 ? "flex" : "hidden md:flex"} h-14 shrink-0 items-center justify-between border-b border-[color:var(--theme-border)] px-5 md:px-8`}>
        <span className="hidden text-sm font-semibold md:inline">Miryn</span>
        {(insights || conflicts.length > 0) && (
          <button type="button" onClick={() => setInsightsOpen((open) => !open)} aria-expanded={insightsOpen} className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-[color:var(--theme-muted)] hover:bg-[color:var(--theme-overlay)] hover:text-[color:var(--theme-text)]">
            <Lightbulb size={16} /> Insights
          </button>
        )}
      </header>
      {insightsOpen && (insights || conflicts.length > 0) && (
        <div className="max-h-64 overflow-y-auto border-b border-[color:var(--theme-border)] px-4 py-3">
          <div className="mx-auto max-w-3xl"><InsightsPanel insights={insights} conflicts={conflicts} /></div>
        </div>
      )}
      {status && (
        <div role="alert" className="flex items-center justify-between gap-3 border-b border-[color:var(--theme-danger-text)]/20 bg-[color:var(--theme-danger-bg)] px-5 py-2.5 text-sm text-[color:var(--theme-danger-text)]">
          <span>{status}</span><div className="flex shrink-0 items-center gap-2">{idFromUrl && messages.length === 0 ? <button type="button" onClick={() => setHistoryRetry((attempt) => attempt + 1)} className="underline underline-offset-2">Try again</button> : lastMessageRef.current && <button type="button" onClick={retry} className="underline underline-offset-2">Retry</button>}<button type="button" onClick={() => setStatus(null)} aria-label="Dismiss error"><X size={16} /></button></div>
        </div>
      )}
      <div className="relative min-h-0 flex-1">
        <div ref={scrollRef} onScroll={() => {
          const area = scrollRef.current;
          if (!area) return;
          const atBottom = area.scrollHeight - area.scrollTop - area.clientHeight < 80;
          pinnedRef.current = atBottom;
          setPinned(atBottom);
        }} className="h-full overflow-y-auto px-4 py-6 md:px-8 md:py-8">
          <div className="mx-auto w-full max-w-3xl">
            {loading && !streaming && messages.length === 0 && <p className="py-10 text-sm text-[color:var(--theme-muted)]">Loading conversation…</p>}
            {messages.length === 0 && !loading && !status && (
              <div className="flex min-h-[min(520px,60vh)] flex-col justify-center py-12">
                <h1 className="text-center font-editorial text-3xl leading-tight md:text-4xl">What can I help with today?</h1>
                <p className="mx-auto mt-3 max-w-md text-center text-sm leading-relaxed text-[color:var(--theme-muted)]">Start anywhere. Miryn can carry useful context into future conversations.</p>
                <div className="mx-auto mt-10 grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
                  {suggestions.map((item) => <button key={item.title} type="button" onClick={() => void sendMessage(item.prompt)} className="rounded-2xl border border-[color:var(--theme-border)] bg-[color:var(--theme-surface)] px-4 py-3.5 text-left text-sm font-medium transition-colors hover:bg-[color:var(--theme-card)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--theme-accent)]">{item.title}</button>)}
                </div>
              </div>
            )}
            <div className="space-y-7" aria-live="off">
              {messages.map((message, index) => <MessageBubble key={message.timestamp + "-" + index} message={message} isStreaming={streaming && index === streamingIndex} saved={index === savedIndex} stopped={index === stoppedIndex} />)}
            </div>
            <div className="h-8" />
          </div>
        </div>
        {!pinned && messages.length > 0 && <button type="button" onClick={jumpToLatest} className="absolute bottom-4 left-1/2 flex -translate-x-1/2 items-center gap-1.5 rounded-full border border-[color:var(--theme-border)] bg-[color:var(--theme-card)] px-3 py-2 text-xs shadow-lg"><ArrowDown size={14} /> Jump to latest</button>}
      </div>
      <div className="shrink-0 px-4 pb-4 pt-2 md:px-8 md:pb-6"><div className="mx-auto max-w-3xl"><InputBox onSend={sendMessage} streaming={streaming} onStop={() => requestRef.current?.abort()} disabled={loading && !streaming} /></div></div>
    </div>
  );
}
