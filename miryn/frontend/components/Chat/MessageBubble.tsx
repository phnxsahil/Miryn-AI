"use client";

import { memo } from "react";
import type { Message } from "@/lib/types";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";

function ThinkingDots() {
  return (
    <div className="flex space-x-3 items-center py-4">
      <div className="flex space-x-1.5">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            animate={{ 
              scale: [1, 1.2, 1],
              opacity: [0.3, 1, 0.3] 
            }}
            transition={{ 
              duration: 1.5, 
              repeat: Infinity, 
              delay: i * 0.2,
              ease: "easeInOut"
            }}
            className="w-1.5 h-1.5 bg-accent rounded-full shadow-[0_0_8px_rgba(200,184,255,0.4)]"
          />
        ))}
      </div>
      <span className="mono-label !text-[12px] !text-accent tracking-widest uppercase font-bold">Calibrating Resonance...</span>
    </div>
  );
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

  const showThinking = isAssistant && isStreaming && !message.content;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
      className={`flex w-full ${isUser ? "justify-end" : "justify-start"} group mb-8`}
    >
      <div className={`flex gap-6 w-full ${isUser ? "max-w-[85%] md:max-w-[75%] flex-row-reverse" : "max-w-full flex-row"}`}>
        {/* Identity Marker */}
        <div className="shrink-0 pt-1">
          <div className={`w-2 h-10 rounded-full transition-all duration-500 ${
            isUser ? "bg-white/[0.06] group-hover:bg-white/[0.1]" : 
            isSystem ? "bg-red-500/40" : 
            "bg-accent shadow-[0_0_8px_rgba(200,184,255,0.3)]"
          }`} />
        </div>

        {/* Content Area */}
        <div className={`flex flex-col min-w-0 flex-1 ${isUser ? "items-end" : "items-start"} space-y-2`}>
          {/* Role Label */}
          <div className="flex items-center gap-3 px-1 mb-1">
            <span className="mono-label !text-[11px] !text-muted uppercase tracking-[0.2em] font-bold">
              {isUser ? "You" : isSystem ? "System" : "Miryn"}
            </span>
            {message.timestamp && (
              <span className="mono-label !text-[10px] !text-muted opacity-50">
                {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>

          <div className={`
            relative leading-relaxed transition-all w-full
            ${isUser ? "text-primary font-ui text-[16px] md:text-[18px] text-right bg-white/[0.03] px-6 py-4 rounded-[24px] rounded-tr-sm inline-block w-auto max-w-full" :
              isSystem ? "text-red-300 font-mono text-[14px] bg-red-500/[0.06] border border-red-500/10 px-6 py-4 rounded-[20px]" : 
              "text-primary/90 text-[16px] md:text-[17px] font-ui leading-[1.7]"}
          `}>
            {showThinking ? (
              <ThinkingDots />
            ) : (
              <div className={`prose prose-invert max-w-none ${isUser ? "whitespace-pre-wrap" : "prose-p:leading-relaxed prose-pre:bg-black/50 prose-pre:border prose-pre:border-white/10 prose-headings:text-primary prose-a:text-accent prose-strong:text-white"}`}>
                {isUser ? (
                   message.content
                ) : (
                   <ReactMarkdown
                     remarkPlugins={[remarkGfm]}
                     rehypePlugins={[rehypeHighlight]}
                   >
                     {message.content + (isStreaming && isAssistant ? " ▍" : "")}
                   </ReactMarkdown>
                )}
              </div>
            )}
          </div>

          {!isUser && isAssistant && !isStreaming && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1 }}
              className="flex items-center gap-2 pt-2 px-1"
            >
              <div className="w-1.5 h-1.5 rounded-full bg-accent/20" />
              <span className="mono-label !text-[11px] !text-muted">Integrated into Identity Layer</span>
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default memo(MessageBubble);
