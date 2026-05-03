"use client";

import { useState, useEffect, useRef } from "react";
import { Send, Command, Loader2, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function InputBox({
  onSend,
  disabled,
}: {
  onSend: (message: string) => void;
  disabled?: boolean;
}) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const [isFocused, setIsFocused] = useState(false);
  const canSend = value.trim().length > 0 && !disabled;

  useEffect(() => {
    if (!textareaRef.current) return;
    const element = textareaRef.current;
    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, 200)}px`;
  }, [value]);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <div className="relative max-w-3xl mx-auto w-full px-4 md:px-0">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          handleSend();
        }}
        className={`
          relative flex items-end gap-3 p-2.5 pl-8 rounded-[40px] transition-all duration-500
          ${isFocused ? "bg-card border-accent/20 shadow-[0_0_40px_rgba(200,184,255,0.08)]" : "bg-card border-white/[0.06]"}
          border
        `}
      >
        <div className="absolute -top-12 left-8 flex items-center gap-2">
           <AnimatePresence>
             {isFocused && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="flex items-center gap-2"
                >
                  <Sparkles size={14} className="text-accent" />
                  <span className="mono-label !text-[12px] !text-accent uppercase tracking-widest font-bold">Active Listening Mode</span>
                </motion.div>
             )}
           </AnimatePresence>
        </div>

        <textarea
          ref={textareaRef}
          className="flex-1 bg-transparent border-none px-0 py-4 text-[17px] leading-relaxed placeholder:text-dim focus:ring-0 resize-none max-h-[200px] overflow-y-auto custom-scrollbar text-primary"
          placeholder="What's on your mind? Reflect with Miryn..."
          value={value}
          rows={1}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              handleSend();
            }
          }}
          disabled={disabled}
        />
        
        <div className="flex items-center gap-3 pr-2 pb-2">
          <button
            type="submit"
            className={`
              w-12 h-12 rounded-full transition-all duration-500 flex items-center justify-center
              ${canSend ? "bg-accent text-void shadow-[0_0_20px_rgba(200,184,255,0.3)] hover:scale-105 active:scale-95" : "bg-white/[0.04] text-dim cursor-not-allowed"}
            `}
            disabled={!canSend}
          >
            {disabled ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
          </button>
        </div>
      </form>
      
      <div className="mt-5 flex justify-between items-center px-10">
        <div className="flex items-center gap-4">
          <span className="mono-label !text-[11px] !text-muted flex items-center gap-2 uppercase tracking-widest font-medium">
            <Command size={12} /> + Enter to send
          </span>
        </div>
        <p className="text-[11px] mono-label !text-muted uppercase tracking-[0.2em] font-medium opacity-60">
          End-to-end encrypted reflection
        </p>
      </div>
    </div>
  );
}

