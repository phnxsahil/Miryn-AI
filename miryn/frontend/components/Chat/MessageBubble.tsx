"use client";

import { memo, useEffect, useState } from "react";
import type { Message } from "@/lib/types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { Check, Copy, FileText, FileCode } from "lucide-react";
import { MirynMark } from "@/components/visuals";

function EnterpriseThinkingLoader() {
  const [phaseIndex, setPhaseIndex] = useState(0);
  const phases = [
    "Reflecting on continuous context...",
    "Consulting 384-dim memory layer...",
    "Harmonizing beliefs & emotional rhythms...",
    "Formulating response...",
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setPhaseIndex((prev) => (prev + 1) % phases.length);
    }, 2400);
    return () => clearInterval(interval);
  }, [phases.length]);

  return (
    <div className="py-2.5 space-y-2.5 max-w-sm animate-in fade-in duration-300">
      <div className="flex items-center gap-3">
        <div className="relative flex items-center justify-center w-4 h-4 shrink-0">
          <span className="absolute inline-flex h-full w-full rounded-full bg-[color:var(--theme-accent)]/25 animate-ping opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-[color:var(--theme-accent)] shadow-[0_0_10px_rgba(214,145,85,0.7)]" />
        </div>
        <span className="font-mono text-xs tracking-wide text-[color:var(--theme-muted)] transition-opacity duration-300">
          {phases[phaseIndex]}
        </span>
      </div>
      <div className="w-48 h-0.5 bg-[color:var(--theme-overlay)] rounded-full overflow-hidden">
        <div className="w-full h-full bg-gradient-to-r from-transparent via-[color:var(--theme-accent)]/60 to-transparent animate-shimmer" />
      </div>
    </div>
  );
}

interface ParsedUserContent {
  attachmentName?: string;
  attachmentSize?: string;
  attachmentCode?: string;
  cleanText: string;
}

function parseUserMessage(content: string): ParsedUserContent {
  const match = content.match(
    /^\[Attached File:\s*([^\s(]+(?:\s+[^\s(]+)*)\s*(?:\(([^)]+)\))?\]\s*(?:```[^\n]*\n([\s\S]*?)```)?\s*([\s\S]*)$/
  );

  if (match) {
    return {
      attachmentName: match[1],
      attachmentSize: match[2],
      attachmentCode: match[3],
      cleanText: match[4]?.trim() || "",
    };
  }

  return { cleanText: content };
}

function MessageBubble({
  message,
  isStreaming,
}: {
  message: Message;
  isStreaming?: boolean;
}) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const isAssistant = message.role === "assistant";
  const [copied, setCopied] = useState(false);

  const showThinking = isAssistant && isStreaming && !message.content;

  const handleCopy = () => {
    if (!message.content) return;
    void navigator.clipboard
      .writeText(message.content)
      .then(() => {
        setCopied(true);
        window.setTimeout(() => setCopied(false), 2000);
      })
      .catch(() => undefined);
  };

  const parsedUser = isUser ? parseUserMessage(message.content) : null;

  return (
    <div className={`w-full flex ${isUser ? "justify-end" : "justify-start"} group mb-6 font-ui`}>
      {isUser ? (
        /* User message: Minimalist tinted charcoal bubble with attachment preview */
        <div className="max-w-[85%] md:max-w-[72%] bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] text-[color:var(--theme-text)] px-5 py-3.5 rounded-[22px] text-[15px] leading-relaxed shadow-sm">
          {parsedUser?.attachmentName && (
            <div className="mb-2.5 pb-2.5 border-b border-[color:var(--theme-border)] flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-[color:var(--theme-overlay)] text-[color:var(--theme-accent)]">
                {parsedUser.attachmentName.match(/\.(ts|tsx|js|jsx|py|sql|json|html|css)$/i) ? (
                  <FileCode size={14} />
                ) : (
                  <FileText size={14} />
                )}
              </div>
              <div className="font-mono text-xs text-[color:var(--theme-text)] truncate max-w-[220px]">
                {parsedUser.attachmentName}
              </div>
              {parsedUser.attachmentSize && (
                <span className="text-[10px] font-mono text-[color:var(--theme-muted)]">
                  ({parsedUser.attachmentSize})
                </span>
              )}
            </div>
          )}

          <div className="whitespace-pre-wrap">
            {parsedUser?.cleanText || message.content}
          </div>
        </div>
      ) : isSystem ? (
        /* System message */
        <div className="w-full max-w-2xl mx-auto my-2 text-rose-300 font-mono text-xs bg-rose-500/[0.08] border border-rose-500/25 px-4 py-2.5 rounded-xl">
          {message.content}
        </div>
      ) : (
        /* Assistant message: Clean Claude/ChatGPT style open prose */
        <div className="flex gap-4 w-full max-w-full items-start">
          {/* Avatar Icon */}
          <div className="w-7 h-7 rounded-full bg-[color:var(--theme-surface)] border border-[color:var(--theme-border)] flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
            <MirynMark state="avatar" className="w-4 h-4 text-[color:var(--theme-accent)]" />
          </div>

          <div className="flex-1 min-w-0 space-y-2">
            {showThinking ? (
              <EnterpriseThinkingLoader />
            ) : (
              <div className="prose max-w-none text-[15px] md:text-[15.5px] leading-[1.75] text-[color:var(--theme-text)] prose-p:leading-[1.75] prose-p:my-2.5 prose-pre:bg-[color:var(--theme-sidebar)] prose-pre:border prose-pre:border-[color:var(--theme-border)] prose-pre:rounded-xl prose-pre:p-4 prose-headings:text-[color:var(--theme-text)] prose-headings:font-semibold prose-headings:tracking-tight prose-a:text-[color:var(--theme-accent)] hover:prose-a:underline prose-strong:text-[color:var(--theme-text)] prose-code:text-[color:var(--theme-accent)] prose-code:bg-[color:var(--theme-overlay)] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:before:content-none prose-code:after:content-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                >
                  {message.content + (isStreaming && isAssistant ? " ▍" : "")}
                </ReactMarkdown>
              </div>
            )}

            {/* Quick action bar */}
            {!isStreaming && message.content && (
              <div className="flex items-center gap-2 pt-1 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity">
                <button
                  onClick={handleCopy}
                  className="p-1.5 rounded-lg text-[color:var(--theme-muted)] hover:text-[color:var(--theme-text)] hover:bg-[color:var(--theme-overlay)] transition-colors flex items-center gap-1.5 text-xs font-mono"
                  title="Copy response"
                  aria-label="Copy response"
                >
                  {copied ? (
                    <>
                      <Check size={13} className="text-emerald-400" />
                      <span className="text-emerald-400 text-[11px]">COPIED</span>
                    </>
                  ) : (
                    <>
                      <Copy size={13} />
                      <span className="text-[11px]">COPY</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default memo(MessageBubble);
