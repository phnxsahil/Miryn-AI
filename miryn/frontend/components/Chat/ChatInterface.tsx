"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { api } from "@/lib/api";
import type { Message, ConversationInsights, ChatResponsePayload } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";
import MessageBubble from "./MessageBubble";
import InputBox from "./InputBox";
import InsightsPanel from "./InsightsPanel";

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [insights, setInsights] = useState<ConversationInsights | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    api.loadToken();
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
    setStatus(null);

    try {
      const response = (await api.sendMessage(trimmed, conversationId || undefined)) as ChatResponsePayload;

      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      if (response.insights) {
        setInsights(response.insights);
      } else {
        setInsights(null);
      }

      appendMessage({
        role: "assistant",
        content: response.response,
        timestamp: new Date().toISOString(),
      });
    } catch (error: unknown) {
      const errorMessage = getErrorMessage(error, "Sorry, something went wrong. Please try again.");
      appendMessage({
        role: "system",
        content: errorMessage,
        timestamp: new Date().toISOString(),
      });
      setStatus(errorMessage);

      if (errorMessage.toLowerCase().includes("session expired")) {
        setTimeout(() => {
          window.location.href = "/login?expired=1";
        }, 800);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-void">
      <div className="border-b border-white/10 p-6">
        <h1 className="text-2xl font-light text-white">Miryn</h1>
        <p className="text-sm text-secondary">A quiet room for honest reflection.</p>
      </div>

      {status && (
        <div className="bg-red-500/10 border-y border-red-500/20 text-red-200 text-xs tracking-[0.2em] uppercase px-6 py-2">
          {status}
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, idx) => (
          <MessageBubble key={`${msg.timestamp}-${idx}`} message={msg} />
        ))}
        {loading && (
          <MessageBubble
            message={{
              role: "assistant",
              content: "Thinking...",
              timestamp: new Date().toISOString(),
            }}
          />
        )}
        <div ref={messagesEndRef} />
      </div>

      <InsightsPanel insights={insights} />
      <InputBox onSend={sendMessage} disabled={loading} />
    </div>
  );
}
