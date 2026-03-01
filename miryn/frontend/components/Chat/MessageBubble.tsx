import type { Message } from "@/lib/types";

function formatAssistantText(text: string): string {
  const trimmed = (text || "").trim();
  if (!trimmed) return "";

  // If the model already provided formatting, preserve it.
  if (trimmed.includes("\n")) return trimmed;

  // Avoid turning short replies into odd paragraph blocks.
  if (trimmed.length < 500) return trimmed;

  // Lightweight paragraphing for long, single-block replies.
  const sentences =
    trimmed.match(/[^.!?]+[.!?]+(?:\s+|$)|[^.!?]+$/g)?.map((s) => s.trim()).filter(Boolean) ?? [];
  if (sentences.length <= 3) return trimmed;

  const paragraphs: string[] = [];
  for (let i = 0; i < sentences.length; i += 3) {
    paragraphs.push(sentences.slice(i, i + 3).join(" "));
  }

  return paragraphs.join("\n\n");
}

function ThinkingDots() {
  return (
    <div className="flex space-x-1.5 items-center py-1 px-1">
      <div className="w-1.5 h-1.5 bg-white/40 rounded-full animate-[bounce_1s_infinite_0ms]" />
      <div className="w-1.5 h-1.5 bg-white/40 rounded-full animate-[bounce_1s_infinite_200ms]" />
      <div className="w-1.5 h-1.5 bg-white/40 rounded-full animate-[bounce_1s_infinite_400ms]" />
      <span className="ml-2 text-[10px] uppercase tracking-[0.2em] text-white/40 font-light">
        Miryn is reflecting
      </span>
    </div>
  );
}

export default function MessageBubble({
  message,
  isStreaming,
}: {
  message: Message;
  isStreaming?: boolean;
}) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const isAssistant = message.role === "assistant";

  const alignment = isUser ? "justify-end" : "justify-start";
  const palette = isSystem
    ? "bg-red-500/10 border-red-500/20 text-red-100 shadow-[0_0_20px_-5px_rgba(239,68,68,0.1)]"
    : isUser
      ? "bg-white/10 border-white/10 text-white shadow-sm"
      : "bg-white/5 border-white/10 text-white shadow-[0_0_30px_-10px_rgba(255,255,255,0.05)]";

  const showThinking = isAssistant && isStreaming && !message.content;

  return (
    <div className={`flex ${alignment} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
      <div className={`max-w-[85%] md:max-w-[70%] rounded-2xl px-4 py-3 text-sm leading-relaxed border whitespace-pre-wrap transition-all ${palette}`}>
        {showThinking ? (
          <ThinkingDots />
        ) : (
          <>
            {isAssistant ? formatAssistantText(message.content) : message.content}
            {isStreaming && !isUser && (
              <span className="inline-block w-1.5 h-4 ml-1 bg-white/50 animate-pulse align-middle" />
            )}
          </>
        )}
      </div>
    </div>
  );
}
