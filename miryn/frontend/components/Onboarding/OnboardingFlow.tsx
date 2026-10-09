"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";
import {
  Sparkles,
  Check,
  Heart,
  Target,
  Lightbulb,
  MessageCircle,
  Sliders,
  Shield,
  CheckCircle2,
} from "lucide-react";
import { ThoughtWall } from "@/components/visuals";
import Link from "next/link";

type PresetCard = {
  id: string;
  display_name: string;
  tagline: string;
  example_response: string;
};

const goalOptions = [
  { id: "understand", label: "Understand myself better", icon: Target },
  { id: "decisions", label: "Think through decisions", icon: Lightbulb },
  { id: "periods", label: "Work through hard periods", icon: Heart },
  { id: "habits", label: "Build better habits", icon: Sparkles },
  { id: "emotions", label: "Process emotions & grounding", icon: MessageCircle },
  { id: "creativity", label: "Explore ideas and creativity", icon: Sparkles },
  { id: "accountable", label: "Stay accountable & focused", icon: Check },
  { id: "talk", label: "Quiet companion to reflect with", icon: MessageCircle },
];

const fallbackPresets: PresetCard[] = [
  {
    id: "companion",
    display_name: "Warm Companion",
    tagline: "Warm, grounded emotional support for everyday thoughts and decisions.",
    example_response: "Let’s slow it down, breathe, and find the next useful step.",
  },
  {
    id: "mirror",
    display_name: "Thoughtful Mirror",
    tagline: "Direct reflection that helps you notice recurring patterns without judgment.",
    example_response: "You’ve described this tension before. What feels different now?",
  },
  {
    id: "coach",
    display_name: "Strategic Coach",
    tagline: "Clear, practical momentum when you want to unblock creative progress.",
    example_response: "What would make the next 20 minutes count the most?",
  },
];

export default function OnboardingFlow() {
  const [name, setName] = useState("");
  const [selectedPreset, setSelectedPreset] = useState("companion");
  const [goals, setGoals] = useState<string[]>(["Process emotions & grounding", "Think through decisions"]);
  const [seedBelief, setSeedBelief] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    api.loadToken();
    api.getMe()
      .then((me) => {
        if (me?.full_name) setName(me.full_name);
      })
      .catch(() => null);
  }, []);

  const toggleGoal = (goalLabel: string) => {
    setGoals((prev) =>
      prev.includes(goalLabel) ? prev.filter((g) => g !== goalLabel) : [...prev, goalLabel]
    );
  };

  const handleSaveCalibration = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setStatus(null);

    const responses = [
      { question: "Name", answer: name.trim() || "Companion" },
      { question: "Preset", answer: selectedPreset },
      { question: "Goals", answer: goals.join(", ") },
      { question: "Seed Belief", answer: seedBelief.trim() || "None" },
    ];

    try {
      await api.completeOnboarding({
        responses,
        preset: selectedPreset,
        goals,
        seed_belief: seedBelief.trim() || null,
        traits: {},
        values: {},
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (e: unknown) {
      setStatus(getErrorMessage(e, "Your calibration could not be saved. Please try again."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[color:var(--miryn-warm-black)] text-[color:var(--text-primary)] p-6 md:p-14 relative overflow-x-hidden font-ui">
      <ThoughtWall preset="onboarding" className="opacity-30" />

      <div className="max-w-4xl mx-auto relative z-10 space-y-10">
        {/* Header */}
        <header className="space-y-4 pb-6 border-b border-[color:var(--miryn-card-border)]">
          <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-[color:var(--accent-wash)] border border-[color:var(--accent-edge)] text-xs text-[color:var(--miryn-moss)] font-medium">
            <Sliders size={14} />
            <span>Companion Dynamic Tuning</span>
          </div>

          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-[color:var(--miryn-parchment)]">
            Companion <span className="text-[color:var(--miryn-moss)]">Calibration</span>
          </h1>

          <p className="text-base md:text-lg text-[color:var(--miryn-parchment-muted)] editorial-italic leading-relaxed">
            Fine-tune how Miryn listens, reflects, and attunes to your emotional and cognitive rhythms.
          </p>
        </header>

        {/* Status / Success Alert */}
        <AnimatePresence>
          {saveSuccess && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="p-4 rounded-2xl bg-[color:var(--accent-wash-max)] border border-[color:var(--miryn-moss)]/40 text-xs text-[color:var(--miryn-parchment)] flex items-center justify-between"
            >
              <div className="flex items-center gap-2.5">
                <CheckCircle2 size={16} className="text-[color:var(--miryn-moss)]" />
                <span>Companion calibration saved. Miryn is now tuned to this conversational dynamic.</span>
              </div>
              <Link href="/chat" className="text-[color:var(--miryn-moss)] hover:underline font-semibold">
                Go to Chat →
              </Link>
            </motion.div>
          )}

          {status && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-xs text-red-300"
            >
              {status}
            </motion.div>
          )}
        </AnimatePresence>

        {/* 1. Dynamic Stance Selection */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-[color:var(--theme-dim)]">
            <span>1. Conversational Stance &amp; Tone</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {fallbackPresets.map((preset) => (
              <button
                key={preset.id}
                type="button"
                onClick={() => setSelectedPreset(preset.id)}
                className={`p-6 rounded-3xl border text-left transition-all space-y-3 relative group ${
                  selectedPreset === preset.id
                    ? "bg-[color:var(--accent-wash)] border-[color:var(--miryn-moss)] shadow-[0_0_30px_var(--accent-glow)]"
                    : "bg-[color:var(--miryn-card)] border-[color:var(--miryn-card-border)] hover:border-[color:var(--accent-edge)]"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-base text-[color:var(--miryn-parchment)]">{preset.display_name}</span>
                  {selectedPreset === preset.id && (
                    <div className="w-5 h-5 rounded-full bg-[color:var(--miryn-moss)] flex items-center justify-center text-black">
                      <Check size={12} strokeWidth={3} />
                    </div>
                  )}
                </div>

                <p className="text-xs text-[color:var(--miryn-parchment-muted)] leading-relaxed">
                  {preset.tagline}
                </p>

                <div className="pt-2 text-[11px] font-mono text-[color:var(--miryn-moss)] opacity-80 border-t border-[color:var(--miryn-card-border)]">
                  &ldquo;{preset.example_response}&rdquo;
                </div>
              </button>
            ))}
          </div>
        </section>

        {/* 2. Mental Health & Focus Intentions */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-[color:var(--theme-dim)]">
            <span>2. Focus &amp; Psychological Intentions</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {goalOptions.map((goal) => {
              const active = goals.includes(goal.label);
              const Icon = goal.icon;
              return (
                <button
                  key={goal.id}
                  type="button"
                  onClick={() => toggleGoal(goal.label)}
                  className={`p-4 rounded-2xl border text-left transition-all flex items-center gap-3 ${
                    active
                      ? "bg-[color:var(--accent-wash-strong)] border-[color:var(--miryn-moss)] text-[color:var(--miryn-parchment)]"
                      : "bg-[color:var(--miryn-surface)] border-[color:var(--miryn-card-border)] text-[color:var(--miryn-parchment-muted)] hover:border-[color:var(--accent-edge)]"
                  }`}
                >
                  <Icon size={16} className={active ? "text-[color:var(--miryn-moss)]" : "text-[color:var(--theme-dim)]"} />
                  <span className="text-xs font-medium">{goal.label}</span>
                </button>
              );
            })}
          </div>
        </section>

        {/* 3. Philosophical Anchor / Seed Belief */}
        <section className="miryn-wall-card p-7 rounded-3xl space-y-4">
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-[color:var(--miryn-parchment)]">3. Core Philosophical Anchor (Seed Belief)</h3>
            <p className="text-xs text-[color:var(--miryn-parchment-muted)]">
              An unshakeable value or worldview you want Miryn to hold in context during all discussions.
            </p>
          </div>

          <textarea
            value={seedBelief}
            onChange={(e) => setSeedBelief(e.target.value)}
            placeholder="e.g. Authenticity and sustainable pace matter more to me than artificial urgency. I want to build deep, meaningful work."
            rows={3}
            className="w-full rounded-2xl bg-[color:var(--miryn-surface)] border border-[color:var(--miryn-card-border)] p-4 text-xs text-[color:var(--miryn-parchment)] placeholder:text-[color:var(--theme-dim)] focus:outline-none focus:border-[color:var(--miryn-moss)] transition-colors resize-none"
          />

          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center gap-2 text-xs text-[color:var(--theme-dim)]">
              <Shield size={12} className="text-[color:var(--miryn-moss)]" />
              <span>Zero-knowledge client-encrypted calibration</span>
            </div>

            <button
              type="button"
              onClick={handleSaveCalibration}
              disabled={isSubmitting}
              className="px-6 py-2.5 rounded-xl bg-[color:var(--miryn-parchment)] text-[color:var(--miryn-warm-black)] font-semibold text-xs hover:bg-[color:var(--miryn-moss)] hover:text-black transition-all shadow-md disabled:opacity-50"
            >
              {isSubmitting ? "Calibrating..." : "Apply Calibration"}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
