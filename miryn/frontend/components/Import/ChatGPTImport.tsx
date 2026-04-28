"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import type { ImportStatus } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";

interface ChatGPTImportProps {
  onClose: () => void;
}

type Step = "instructions" | "upload" | "processing" | "complete";

export default function ChatGPTImport({ onClose }: ChatGPTImportProps) {
  const [step, setStep] = useState<Step>("instructions");
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<ImportStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.size > 50 * 1024 * 1024) {
        setError("File too large. Max 50MB.");
        return;
      }
      if (!selectedFile.name.endsWith(".json")) {
        setError("Please upload a .json file.");
        return;
      }
      setFile(selectedFile);
      setError(null);
    }
  };

  const startImport = async () => {
    if (!file) return;
    try {
      setError(null);
      await api.importChatGPT(file);
      setStep("processing");
    } catch (err) {
      setError(getErrorMessage(err, "Failed to start import."));
    }
  };

  useEffect(() => {
    if (step === "processing") {
      pollingRef.current = setInterval(async () => {
        try {
          const currentStatus = await api.getImportStatus();
          setStatus(currentStatus);
          if (currentStatus.status === "complete") {
            setStep("complete");
            if (pollingRef.current) clearInterval(pollingRef.current);
          } else if (currentStatus.status === "error") {
            setError(currentStatus.message || "An error occurred during import.");
            setStep("upload");
            if (pollingRef.current) clearInterval(pollingRef.current);
          }
        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 2000);
    }

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [step]);

  const stepVariants = {
    hidden: { opacity: 0, x: 20 },
    visible: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 },
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-void/80 backdrop-blur-sm">
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-full max-w-lg overflow-hidden border bg-surface border-white/10 rounded-2xl shadow-2xl"
      >
        <div className="p-6 border-b border-white/5 flex justify-between items-center">
          <h2 className="text-xl font-light text-white">ChatGPT Data Import</h2>
          <button
            onClick={onClose}
            className="text-secondary hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="p-8 min-h-[320px] flex flex-col justify-center">
          <AnimatePresence mode="wait">
            {step === "instructions" && (
              <motion.div
                key="instructions"
                variants={stepVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                className="space-y-6"
              >
                <div className="space-y-4 text-secondary text-sm leading-relaxed">
                  <p>
                    Seed Miryn with your past reflections. This allows the Identity Engine to immediately recognize long-term patterns.
                  </p>
                  <ol className="list-decimal list-inside space-y-2">
                    <li>Go to ChatGPT → Settings → Data Controls.</li>
                    <li>Select &quot;Export Data&quot; and wait for the email.</li>
                    <li>Download the ZIP and find <code className="text-accent-purple">conversations.json</code>.</li>
                  </ol>
                </div>
                <button
                  onClick={() => setStep("upload")}
                  className="w-full py-3 text-sm font-medium transition-all rounded-full bg-accent-purple text-void hover:scale-[1.02] active:scale-[0.98]"
                >
                  Proceed to Upload
                </button>
              </motion.div>
            )}

            {step === "upload" && (
              <motion.div
                key="upload"
                variants={stepVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                className="space-y-6"
              >
                <div
                  className={`relative border-2 border-dashed rounded-xl p-10 transition-colors flex flex-col items-center justify-center space-y-4 ${
                    file ? "border-accent-purple/50 bg-accent-purple/5" : "border-white/10 hover:border-white/20"
                  }`}
                >
                  <input
                    type="file"
                    accept=".json"
                    onChange={handleFileChange}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  <div className="text-4xl">📄</div>
                  <div className="text-center">
                    <p className="text-sm text-white font-light">
                      {file ? file.name : "Select conversations.json"}
                    </p>
                    <p className="text-xs text-secondary mt-1">Max size 50MB</p>
                  </div>
                </div>

                {error && (
                  <p className="text-xs text-red-400 text-center animate-pulse">{error}</p>
                )}

                <div className="flex space-x-3">
                  <button
                    onClick={() => setStep("instructions")}
                    className="flex-1 py-3 text-sm font-medium transition-all border rounded-full border-white/10 text-white hover:bg-white/5"
                  >
                    Back
                  </button>
                  <button
                    disabled={!file}
                    onClick={startImport}
                    className="flex-1 py-3 text-sm font-medium transition-all rounded-full bg-accent-purple text-void hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:hover:scale-100"
                  >
                    Initialize Import
                  </button>
                </div>
              </motion.div>
            )}

            {step === "processing" && (
              <motion.div
                key="processing"
                variants={stepVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                className="space-y-8 text-center"
              >
                <div className="space-y-2">
                  <p className="text-lg font-light text-white">Analyzing Memories...</p>
                  <p className="text-xs text-secondary tracking-widest uppercase">
                    {status?.progress || 0}% Complete
                  </p>
                </div>

                <div className="relative w-full h-1 overflow-hidden bg-white/5 rounded-full">
                  <motion.div
                    className="absolute top-0 left-0 h-full bg-accent-purple"
                    initial={{ width: 0 }}
                    animate={{ width: `${status?.progress || 0}%` }}
                    transition={{ type: "spring", bounce: 0, duration: 0.5 }}
                  />
                </div>

                <p className="text-sm text-secondary italic">
                  Miryn is identifying patterns and open loops from your history.
                </p>
              </motion.div>
            )}

            {step === "complete" && (
              <motion.div
                key="complete"
                variants={stepVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                className="space-y-8 text-center"
              >
                <div className="flex flex-col items-center space-y-4">
                  <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center text-2xl text-green-400 border border-green-500/20">
                    ✓
                  </div>
                  <div className="space-y-1">
                    <p className="text-lg font-light text-white">Import Complete</p>
                    <p className="text-sm text-secondary">
                      Your identity has been updated with historical context.
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 p-4 rounded-xl bg-white/5 border border-white/5">
                  <div className="text-center">
                    <p className="text-xl text-white font-mono">{status?.conversations_processed || 0}</p>
                    <p className="text-[10px] text-secondary uppercase tracking-tighter">Conversations</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xl text-accent-purple font-mono">{status?.memories_added || 0}</p>
                    <p className="text-[10px] text-secondary uppercase tracking-tighter">Insights Extracted</p>
                  </div>
                </div>

                <button
                  onClick={onClose}
                  className="w-full py-3 text-sm font-medium transition-all rounded-full bg-accent-purple text-void hover:scale-[1.02] active:scale-[0.98]"
                >
                  Return to The Void
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}
