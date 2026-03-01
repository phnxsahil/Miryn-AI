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
    ? "bg-red-500/10 border-red-500/20 text-red-100"
    : isUser
      ? "bg-white/10 border-white/10 text-white"
      : "bg-white/5 border-white/10 text-white";

  return (
    <div className={`flex ${alignment}`}>
      <div className={`max-w-[70%] rounded-2xl px-4 py-3 text-sm leading-relaxed border whitespace-pre-wrap ${palette}`}>
        {isAssistant ? formatAssistantText(message.content) : message.content}
        {isStreaming && !isUser && (
          <span className="animate-pulse" />
        )}
      </div>
    </div>
  );
}
