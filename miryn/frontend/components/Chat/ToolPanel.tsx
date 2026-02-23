"use client";

import { useState } from "react";
import type { ToolRun } from "@/lib/types";

type Props = {
  pending: ToolRun[];
  onGenerate: (intent: string) => void;
  onApprove: (toolId: string) => void;
};

export default function ToolPanel({ pending, onGenerate, onApprove }: Props) {
  const [intent, setIntent] = useState("");

  return (
    <div className="border-t border-white/10 p-4 bg-void/80">
      <div className="flex items-center justify-between">
        <div className="text-xs uppercase tracking-[0.2em] text-secondary">Tools</div>
      </div>
      <div className="mt-3 flex gap-2">
        <input
          className="flex-1 bg-black/40 border border-white/10 rounded px-3 py-2 text-sm text-white"
          placeholder="Describe a tool to generate..."
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
        />
        <button
          className="px-3 py-2 text-xs uppercase tracking-[0.2em] bg-white/10 hover:bg-white/20 text-white"
          onClick={() => {
            if (intent.trim()) {
              onGenerate(intent.trim());
              setIntent("");
            }
          }}
        >
          Generate
        </button>
      </div>

      {pending.length > 0 && (
        <div className="mt-4 space-y-3">
          {pending.map((tool) => (
            <div key={tool.id} className="border border-white/10 rounded p-3">
              <div className="text-sm text-white">{tool.name || "Generated Tool"}</div>
              {tool.description && <div className="text-xs text-secondary mt-1">{tool.description}</div>}
              <div className="mt-2 flex justify-end">
                <button
                  className="px-3 py-1 text-xs uppercase tracking-[0.2em] bg-white/10 hover:bg-white/20 text-white"
                  onClick={() => onApprove(tool.id)}
                >
                  Approve
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
