"use client";

import { memo, useState } from "react";
import type { Message } from "@/lib/types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { Check, Copy } from "lucide-react";

function MessageBubble({ message, isStreaming = false, saved = false, stopped = false }: {
  message: Message;
  isStreaming?: boolean;
  saved?: boolean;
  stopped?: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch { /* Clipboard permission is optional. */ }
  };
  if (message.role === "system") return <p role="status" className="text-sm text-[color:var(--theme-danger-text)]">{message.content}</p>;
  if (message.role === "user") return (
    <div className="flex justify-end">
      <div className="max-w-[90%] whitespace-pre-wrap break-words rounded-2xl bg-[color:var(--theme-card)] px-4 py-3 text-[15px] leading-7 text-[color:var(--theme-text)] sm:max-w-[78%]">{message.content}</div>
    </div>
  );
  return (
    <div className="group min-w-0 text-[15px] leading-7 text-[color:var(--theme-text)] md:text-base">
      {isStreaming && !message.content ? (
        <span role="status" aria-label="Miryn is thinking" className="inline-flex items-center gap-1.5 py-2 text-[color:var(--theme-muted)]">
          <span className="chat-thinking-dot" /><span className="chat-thinking-dot" /><span className="chat-thinking-dot" />
        </span>
      ) : (
        <div className="prose max-w-none break-words text-[color:var(--theme-text)] prose-p:my-3 prose-p:leading-7 prose-pre:overflow-x-auto prose-pre:rounded-xl prose-pre:border prose-pre:border-[color:var(--theme-border)] prose-pre:bg-[color:var(--theme-sidebar)] prose-pre:p-4 prose-headings:text-[color:var(--theme-text)] prose-strong:text-[color:var(--theme-text)] prose-a:text-[color:var(--theme-accent)] prose-code:text-[color:var(--theme-accent)]">
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>{message.content}</ReactMarkdown>
          {isStreaming && <span className="chat-stream-cursor" aria-hidden="true" />}
        </div>
      )}
      {saved && <p className="mt-2 text-xs text-[color:var(--theme-muted)]">Saved to memory</p>}
      {stopped && <p className="mt-2 text-xs text-[color:var(--theme-muted)]">Response stopped</p>}
      {!isStreaming && !!message.content && (
        <button type="button" onClick={copy} aria-label="Copy response" className="mt-2 inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs text-[color:var(--theme-muted)] opacity-0 transition-opacity hover:bg-[color:var(--theme-overlay)] hover:text-[color:var(--theme-text)] focus:opacity-100 group-hover:opacity-100 group-focus-within:opacity-100 max-sm:opacity-100">
          {copied ? <Check size={14} /> : <Copy size={14} />}{copied ? "Copied" : "Copy"}
        </button>
      )}
    </div>
  );
}

export default memo(MessageBubble);
