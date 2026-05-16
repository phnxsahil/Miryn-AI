"use client";

import { useState, useEffect, useRef } from "react";
import { ArrowUp, Loader2, Paperclip } from "lucide-react";

export default function InputBox({
  onSend,
  disabled,
}: {
  onSend: (message: string) => void;
  disabled?: boolean;
}) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
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
    <div className="relative w-full max-w-3xl mx-auto px-4 md:px-0">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          handleSend();
        }}
        className="relative flex items-end gap-2 p-2 bg-[#2f2f2f] rounded-[24px] border border-white/10 shadow-sm focus-within:bg-[#2f2f2f]/90 transition-colors"
      >
        <button
          type="button"
          className="p-2 ml-1 text-dim/50 rounded-full cursor-not-allowed"
          disabled
          aria-label="Attachments coming soon"
          title="Attachments coming soon"
        >
          <Paperclip size={20} />
        </button>

        <textarea
          ref={textareaRef}
          className="flex-1 bg-transparent border-none px-2 py-2.5 text-[15px] leading-relaxed placeholder:text-dim focus:ring-0 resize-none max-h-[200px] overflow-y-auto custom-scrollbar text-primary min-h-[44px]"
          placeholder="Message Miryn..."
          value={value}
          rows={1}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              handleSend();
            }
          }}
          disabled={disabled}
        />
        
        <button
          type="submit"
          className={`
            p-2 mb-0.5 mr-1 rounded-full flex items-center justify-center transition-colors h-8 w-8
            ${canSend ? "bg-white text-black hover:bg-white/90" : "bg-[#424242] text-dim/50 cursor-not-allowed"}
          `}
          disabled={!canSend}
        >
          {disabled ? <Loader2 size={16} className="animate-spin" /> : <ArrowUp size={18} strokeWidth={3} />}
        </button>
      </form>
      
      <div className="mt-2 text-center">
        <p className="text-[12px] text-dim/70">Miryn can make mistakes. Consider verifying important information.</p>
      </div>
    </div>
  );
}
