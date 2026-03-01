"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";

type PresetCard = {
  id: string;
  display_name: string;
  tagline: string;
  example_response: string;
};

const goalOptions = [
  "Think through decisions",
  "Creative work",
  "Emotional support",
  "Accountability",
  "Learning",
  "Just someone to talk to",
];

export default function OnboardingFlow() {
  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [context, setContext] = useState("");
  const [presets, setPresets] = useState<PresetCard[]>([]);
  const [selectedPreset, setSelectedPreset] = useState("companion");
  const [goals, setGoals] = useState<string[]>([]);
  const [directGentle, setDirectGentle] = useState(50);
  const [briefExpansive, setBriefExpansive] = useState(50);
  const [seedBelief, setSeedBelief] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const progress = useMemo(() => Math.round((step / 5) * 100), [step]);

  useEffect(() => {
    api.loadToken();
    api
      .listPresets()
      .then((data) => setPresets(Array.isArray(data) ? (data as PresetCard[]) : []))
      .catch(() => setPresets([]));
  }, []);

  const toggleGoal = (goal: string) => {
    setGoals((prev) => (prev.includes(goal) ? prev.filter((g) => g !== goal) : [...prev, goal]));
  };

  const handleSubmit = async (skipSeed = false) => {
    if (isSubmitting) return;
    api.loadToken();

    const responses = [
      { question: "Name", answer: name.trim() },
      { question: "AI use context", answer: context.trim() },
      { question: "Preset", answer: selectedPreset },
      { question: "Goals", answer: goals.join(", ") },
      { question: "Direct/Gentle (0-100)", answer: String(directGentle) },
      { question: "Brief/Expansive (0-100)", answer: String(briefExpansive) },
    ];

    try {
      setIsSubmitting(true);
      await api.completeOnboarding({
        responses,
        preset: selectedPreset,
        goals,
        seed_belief: skipSeed ? null : seedBelief.trim() || null,
        traits: {},
        values: {},
      });
      window.location.href = "/chat";
    } catch (e: unknown) {
      setStatus(getErrorMessage(e, "Failed to complete onboarding."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl">
      <div className="mb-6">
        <div className="mb-2 flex items-center justify-between text-xs uppercase tracking-[0.2em] text-secondary">
          <span>Step {step} of 5</span>
          <span>{progress}%</span>
        </div>
        <div className="h-2 w-full rounded-full bg-white/10">
          <div className="h-2 rounded-full bg-accent transition-all" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {step === 1 && (
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-serif font-light">Let's get to know you</h1>
            <p className="text-secondary mt-2">A quick foundation to personalize Miryn.</p>
          </div>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.2em] text-secondary">What's your name?</label>
            <input
              className="w-full rounded-2xl bg-white/5 border border-white/10 px-4 py-3 text-white"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="How should Miryn address you?"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.2em] text-secondary">
              In one sentence, what do you use AI for?
            </label>
            <input
              className="w-full rounded-2xl bg-white/5 border border-white/10 px-4 py-3 text-white"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Thinking, support, creative work..."
            />
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-serif font-light">How should Miryn show up for you?</h1>
            <p className="text-secondary mt-2">Pick the tone that feels most natural.</p>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {presets.map((preset) => (
              <button
                key={preset.id}
                onClick={() => setSelectedPreset(preset.id)}
                className={`rounded-2xl border p-5 text-left transition-all ${
                  selectedPreset === preset.id
                    ? "border-accent bg-accent/10"
                    : "border-white/10 bg-black/30 hover:border-white/20"
                }`}
              >
                <div className="text-sm font-medium text-white">{preset.display_name}</div>
                <div className="mt-1 text-xs text-secondary">{preset.tagline}</div>
                <div className="mt-3 rounded-lg bg-white/5 p-3 text-xs text-white/60 italic">
                  "{preset.example_response}"
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-serif font-light">What do you most want from Miryn?</h1>
            <p className="text-secondary mt-2">Pick any that resonate.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            {goalOptions.map((goal) => (
              <button
                key={goal}
                onClick={() => toggleGoal(goal)}
                className={`rounded-full border px-4 py-2 text-sm transition-all ${
                  goals.includes(goal)
                    ? "border-accent bg-accent/10 text-white"
                    : "border-white/10 bg-white/5 text-secondary hover:border-white/20"
                }`}
              >
                {goal}
              </button>
            ))}
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="space-y-8">
          <div>
            <h1 className="text-3xl font-serif font-light">How do you like to be spoken to?</h1>
            <p className="text-secondary mt-2">Adjust the tone and depth.</p>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between text-sm text-secondary">
              <span>Direct</span>
              <span>Gentle</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={directGentle}
              onChange={(e) => setDirectGentle(Number(e.target.value))}
              className="w-full accent-accent"
            />
          </div>
          <div className="space-y-3">
            <div className="flex justify-between text-sm text-secondary">
              <span>Brief</span>
              <span>Expansive</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={briefExpansive}
              onChange={(e) => setBriefExpansive(Number(e.target.value))}
              className="w-full accent-accent"
            />
          </div>
        </div>
      )}

      {step === 5 && (
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-serif font-light">Tell Miryn one thing you believe strongly.</h1>
            <p className="text-secondary mt-2">
              Optional -- but the more you give, the faster Miryn understands you.
            </p>
          </div>
          <textarea
            className="w-full rounded-2xl bg-white/5 border border-white/10 px-4 py-3 min-h-[140px] text-white"
            value={seedBelief}
            onChange={(e) => setSeedBelief(e.target.value)}
            placeholder="I believe that..."
          />
          <button
            className="text-xs uppercase tracking-[0.2em] text-secondary"
            onClick={() => handleSubmit(true)}
            disabled={isSubmitting}
          >
            Skip this step
          </button>
        </div>
      )}

      <div className="mt-10 flex items-center justify-between">
        {step > 1 ? (
          <button
            className="rounded-2xl border border-white/10 px-5 py-2 text-sm text-secondary disabled:opacity-40"
            onClick={() => setStep((prev) => Math.max(1, prev - 1))}
            disabled={isSubmitting}
          >
            Back
          </button>
        ) : (
          <div />
        )}
        <button
          className="rounded-2xl bg-accent text-black px-6 py-2 text-sm disabled:opacity-60"
          onClick={() => (step === 5 ? handleSubmit(false) : setStep((prev) => Math.min(5, prev + 1)))}
          disabled={isSubmitting}
          aria-busy={isSubmitting}
        >
          {step === 5 ? "Complete" : "Next"}
        </button>
      </div>

      {status && <div className="mt-4 text-sm text-secondary">{status}</div>}
    </div>
  );
}
