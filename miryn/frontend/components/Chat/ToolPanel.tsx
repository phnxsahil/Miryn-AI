"use client";

import { useState } from "react";
import type { ToolRun } from "@/lib/types";
import { Wrench, Plus, Check, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

type Props = {
  pending: ToolRun[];
  onGenerate: (intent: string) => void;
  onApprove: (toolId: string) => void;
};

export default function ToolPanel({ pending, onGenerate, onApprove }: Props) {
  const [intent, setIntent] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = () => {
    if (intent.trim()) {
      setIsGenerating(true);
      onGenerate(intent.trim());
      setIntent("");
      // Reset generating state after a bit or when pending updates
      setTimeout(() => setIsGenerating(false), 2000);
    }
  };

  return (
    <div className="bg-card border border-white/[0.06] rounded-[32px] p-8 h-full flex flex-col shadow-sm">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-full bg-white/[0.03] border border-white/[0.06] flex items-center justify-center">
          <Wrench size={18} className="text-muted" />
        </div>
        <span className="mono-label !text-[12px] !text-muted uppercase tracking-[0.2em] font-bold">Neural Interfacing</span>
      </div>

      <div className="space-y-4">
        <div className="relative group">
          <input
            className="w-full bg-white/[0.02] border border-white/[0.06] rounded-2xl px-5 py-4 text-[14px] text-primary placeholder:text-muted focus:outline-none focus:border-accent/40 focus:bg-white transition-all shadow-sm"
            placeholder="Summon a new capability..."
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
          />
          <button
            className={`
              absolute right-2 top-2 p-2 rounded-xl transition-all
              ${intent.trim() ? "bg-accent text-white opacity-100 shadow-sm" : "bg-black/[0.05] text-muted opacity-0 group-hover:opacity-100"}
            `}
            onClick={handleGenerate}
            disabled={!intent.trim() || isGenerating}
          >
            {isGenerating ? <Loader2 size={18} className="animate-spin" /> : <Plus size={18} />}
          </button>
        </div>

        <div className="space-y-3 overflow-y-auto max-h-[150px] custom-scrollbar pr-2">
          <AnimatePresence initial={false}>
            {pending.map((tool) => (
              <motion.div 
                key={tool.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06] group hover:border-accent/20 transition-all shadow-sm"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="text-[14px] font-bold text-primary truncate">{tool.name || "Generated Tool"}</div>
                    {tool.description && (
                      <div className="text-[12px] text-muted mt-1 leading-relaxed line-clamp-2 italic font-medium">
                        {tool.description}
                      </div>
                    )}
                  </div>
                  <button
                    className="shrink-0 p-2 rounded-lg bg-accent/10 text-accent opacity-100 hover:bg-accent/20 transition-all"
                    onClick={() => onApprove(tool.id)}
                  >
                    <Check size={14} />
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

