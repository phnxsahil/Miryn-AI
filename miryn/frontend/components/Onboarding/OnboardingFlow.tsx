"use client";

import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";
import { ArrowRight, Sparkles, Check, ChevronLeft, UploadCloud, Heart, Target, Lightbulb, MessageCircle } from "lucide-react";

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
  { id: "emotions", label: "Process emotions", icon: MessageCircle },
  { id: "creativity", label: "Explore ideas and creativity", icon: Sparkles },
  { id: "accountable", label: "Stay accountable", icon: Check },
  { id: "talk", label: "Just someone to talk to", icon: MessageCircle },
];

export default function OnboardingFlow() {
  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [presets, setPresets] = useState<PresetCard[]>([]);
  const [selectedPreset, setSelectedPreset] = useState("companion");
  const [goals, setGoals] = useState<string[]>([]);
  const [seedBelief, setSeedBelief] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);

  const progress = useMemo(() => (step / 5) * 100, [step]);

  useEffect(() => {
    api.loadToken();
    api.listPresets()
      .then((data) => setPresets(Array.isArray(data) ? (data as PresetCard[]) : []))
      .catch(() => setPresets([]));
  }, []);

  const toggleGoal = (goalLabel: string) => {
    setGoals((prev) => (prev.includes(goalLabel) ? prev.filter((g) => g !== goalLabel) : [...prev, goalLabel]));
  };

  const handleNext = () => {
    if (step < 5) setStep(step + 1);
    else handleComplete();
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleComplete = async (skipSeed = false) => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setStatus(null);

    const responses = [
      { question: "Name", answer: name.trim() },
      { question: "Preset", answer: selectedPreset },
      { question: "Goals", answer: goals.join(", ") },
      { question: "Seed Belief", answer: skipSeed ? "Skipped" : seedBelief.trim() },
    ];

    try {
      await api.completeOnboarding({
        responses,
        preset: selectedPreset,
        goals,
        seed_belief: skipSeed ? null : seedBelief.trim() || null,
        traits: {},
        values: {},
      });
      setShowCelebration(true);
    } catch (e: unknown) {
      setStatus(getErrorMessage(e, "Calibration failed. Please try again."));
      setIsSubmitting(false);
    }
  };

  if (showCelebration) {
    return (
      <div className="fixed inset-0 bg-void z-[100] flex flex-col items-center justify-center p-6 overflow-hidden font-ui">
        {/* Particle Effect (Decorative) */}
        <div className="absolute inset-0 pointer-events-none">
          {[...Array(20)].map((_, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 100 }}
              animate={{ opacity: [0, 0.6, 0], y: -200, x: (Math.random() - 0.5) * 400 }}
              transition={{ duration: 4 + Math.random() * 4, repeat: Infinity, delay: Math.random() * 5 }}
              className="absolute w-1 h-1 bg-[#c8b8ff] rounded-full blur-[1px]"
              style={{ left: `${Math.random() * 100}%`, top: `${Math.random() * 100}%` }}
            />
          ))}
        </div>

        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-[700px] h-[700px] bg-accent/[0.1] rounded-full blur-[150px]" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[400px] h-[400px] bg-accent/[0.05] rounded-full blur-[100px]" />
        </div>

        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1 }}
          className="relative z-10 w-full max-w-xl text-center space-y-10"
        >
          <div className="flex justify-center">
            <div className="w-[60px] h-[60px] rounded-full bg-[#c8b8ff]/[0.12] border border-[#c8b8ff]/[0.3] flex items-center justify-center">
              <Sparkles className="text-[#c8b8ff] w-7 h-7" />
            </div>
          </div>

          <div className="space-y-6">
            <h1 className="text-6xl font-bold text-primary tracking-tight leading-tight">
              Miryn is ready for you, <br />
              <span className="text-accent font-bold">{name || "Friend"}.</span>
            </h1>
            <p className="text-2xl editorial-italic text-muted max-w-lg mx-auto leading-relaxed font-medium">
              Your profile has been created. Miryn will learn more with every conversation.
            </p>
          </div>

          <div className="pt-6">
            <div className="bg-card border border-white/[0.06] rounded-[32px] p-8 relative overflow-hidden text-left max-w-sm mx-auto shadow-sm">
              <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-accent/30 to-transparent" />
              <div className="flex justify-between items-center mb-6">
                <span className="mono-label !text-muted uppercase tracking-widest font-bold">Starting Profile</span>
                <span className="mono-label !text-accent bg-accent/5 px-2 py-0.5 rounded font-bold">v1</span>
              </div>
              <div className="flex flex-wrap gap-2.5">
                <div className="h-10 px-4 rounded-full bg-accent/10 border border-accent/20 text-sm font-bold text-accent flex items-center">
                  Preset: {selectedPreset}
                </div>
                {goals.slice(0, 2).map((goal, i) => (
                  <div key={i} className="h-10 px-4 rounded-full bg-black/[0.03] border border-white/[0.06] text-sm text-muted flex items-center font-medium">
                    {goal}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="pt-8 flex flex-col items-center gap-4">
            <button 
              onClick={() => window.location.href = "/chat"}
              className="h-14 px-10 bg-[#c8b8ff] text-[#09090e] rounded-full font-bold text-lg hover:scale-[1.05] transition-all shadow-[0_0_30px_rgba(200,184,255,0.2)]"
            >
              Start your first conversation →
            </button>
            <p className="mono-label !text-[#4a4868] !text-[11px]">No pressure. Start whenever you&apos;re ready.</p>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-void text-primary font-ui relative overflow-hidden flex flex-col">
      {/* Persistent Elements */}
      <div className="fixed top-0 left-0 w-full h-[4px] bg-black/[0.05] z-[60]">
        <motion.div 
          className="h-full bg-accent" 
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>

      <div className="flex justify-between items-center px-12 py-10 relative z-50">
        <div className="text-2xl font-bold text-accent tracking-tight">Miryn</div>
        <div className="mono-label !text-muted font-bold uppercase tracking-widest">Step {step} of 5</div>
      </div>

      <main className="flex-1 flex flex-col items-center pt-24 px-6 pb-32">
        <AnimatePresence mode="wait">
          {step === 1 && (
            <motion.div 
              key="step1"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="w-full max-w-2xl text-center space-y-12"
            >
              <div className="space-y-6">
                <span className="mono-label !text-accent !tracking-[0.3em] font-bold uppercase">Welcome</span>
                <h1 className="text-6xl md:text-7xl font-bold tracking-tight leading-tight text-primary">
                  Before Miryn learns about you — <br />
                  <span className="text-accent font-bold">tell us your name.</span>
                </h1>
                <p className="text-2xl editorial-italic text-muted font-medium max-w-xl mx-auto leading-relaxed">
                  Not a username. Your actual name. The one you&apos;d want someone to use.
                </p>
              </div>

              <div className="relative max-w-lg mx-auto w-full pt-10">
                <input
                  type="text"
                  className="w-full h-20 bg-card border border-white/[0.06] rounded-[32px] px-10 text-2xl focus:outline-none focus:border-accent/50 focus:ring-8 focus:ring-accent/[0.05] transition-all placeholder:editorial-italic placeholder:text-muted shadow-sm"
                  placeholder="Your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoFocus
                />
                {name.length > 0 && (
                  <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="absolute -bottom-8 right-6 text-[#c8b8ff] text-sm"
                  >
                    Hi {name} 👋
                  </motion.div>
                )}
              </div>
              
              <p className="mono-label !text-[#4a4868] !text-[11px] pt-4">
                Miryn uses your name to personalise responses — not for marketing.
              </p>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div 
              key="step2"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="w-full max-w-4xl text-center space-y-12"
            >
              <div className="space-y-6">
                <h1 className="text-5xl md:text-6xl font-bold tracking-tight leading-tight text-primary">
                  How should Miryn show up for you?
                </h1>
                <p className="text-2xl editorial-italic text-muted font-medium max-w-xl mx-auto leading-relaxed">
                  Pick the archetype that feels most natural. You can change this later.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {presets.length > 0 ? presets.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => setSelectedPreset(preset.id)}
                    className={`group relative flex flex-col p-10 text-left rounded-[32px] border transition-all duration-300 ${
                      selectedPreset === preset.id 
                        ? "bg-accent/[0.06] border-accent shadow-[0_0_40px_rgba(200,184,255,0.1)]" 
                        : "bg-card border-white/[0.06] hover:border-white/[0.12] hover:bg-white/[0.04]"
                    }`}
                  >
                    <h3 className={`text-xl font-bold mb-3 ${selectedPreset === preset.id ? "text-accent" : "text-primary"}`}>
                      {preset.display_name}
                    </h3>
                    <p className="text-sm text-muted leading-relaxed mb-8 font-medium">{preset.tagline}</p>
                    <div className="mt-auto bg-white/[0.03] rounded-2xl p-5 border border-white/[0.06]">
                      <p className="text-sm text-muted editorial-italic leading-relaxed font-medium">
                        &ldquo;{preset.example_response}&rdquo;
                      </p>
                    </div>
                    {selectedPreset === preset.id && (
                      <motion.div 
                        layoutId="preset-check"
                        className="absolute top-4 right-4 w-6 h-6 rounded-full bg-[#c8b8ff] flex items-center justify-center"
                      >
                        <Check size={14} className="text-black" />
                      </motion.div>
                    )}
                  </button>
                )) : (
                  [1, 2, 3].map((i) => (
                    <div key={i} className="h-60 rounded-2xl bg-white/[0.02] animate-pulse border border-white/[0.07]" />
                  ))
                )}
              </div>
            </motion.div>
          )}

          {step === 3 && (
            <motion.div 
              key="step3"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="w-full max-w-3xl text-center space-y-12"
            >
              <div className="space-y-6">
                <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-primary">
                  What do you want from Miryn?
                </h1>
                <p className="text-2xl editorial-italic text-muted font-medium max-w-xl mx-auto leading-relaxed">
                  Pick everything that resonates. These shape how Miryn engages.
                </p>
              </div>

              <div className="flex flex-wrap justify-center gap-4">
                {goalOptions.map((goal) => (
                  <button
                    key={goal.id}
                    onClick={() => toggleGoal(goal.label)}
                    className={`h-14 px-8 rounded-full border flex items-center gap-4 transition-all shadow-sm ${
                      goals.includes(goal.label)
                        ? "bg-accent text-white border-accent font-bold"
                        : "bg-card border-white/[0.06] text-muted hover:border-white/[0.12] font-medium"
                    }`}
                  >
                    <goal.icon size={18} className={goals.includes(goal.label) ? "text-white" : "text-accent"} />
                    <span className="text-base">{goal.label}</span>
                  </button>
                ))}
                <button className="h-14 px-8 rounded-full border border-dashed border-white/[0.12] bg-transparent text-muted text-base hover:text-primary transition-colors font-medium">
                  + Add your own
                </button>
              </div>

              <div className="mono-label !text-[#4a4868] !text-[11px]">
                {goals.length} selected
              </div>
            </motion.div>
          )}

          {step === 4 && (
            <motion.div 
              key="step4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="w-full max-w-2xl text-center space-y-12"
            >
              <div className="space-y-6">
                <span className="mono-label !text-accent !tracking-[0.2em] font-bold uppercase">Optional — But Powerful</span>
                <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-primary">
                  Tell Miryn one true thing about you.
                </h1>
                <p className="text-2xl editorial-italic text-muted font-medium max-w-xl mx-auto leading-relaxed">
                  Something you actually believe about yourself or the world. A sentence you&apos;d write in a journal at 2am.
                </p>
              </div>

              <div className="relative w-full pt-6">
                <textarea
                  className="w-full h-56 bg-card border border-white/[0.06] rounded-[32px] px-8 py-8 text-2xl editorial-italic focus:outline-none focus:border-accent/40 focus:ring-8 focus:ring-accent/[0.05] transition-all placeholder:text-muted/30 resize-none shadow-sm"
                  placeholder="I always put others first, even when it costs me..."
                  value={seedBelief}
                  onChange={(e) => setSeedBelief(e.target.value)}
                />
                <div className="absolute bottom-4 right-6 mono-label !text-[#4a4868] !text-[10px]">
                  {seedBelief.length}/280
                </div>
              </div>

              <div className="space-y-6 pt-6">
                <div className="mono-label !text-muted uppercase tracking-widest font-bold">Need inspiration?</div>
                <div className="flex flex-wrap justify-center gap-3">
                  {["I'm harder on myself than others", "I hide when I'm overwhelmed", "I'm better than I think I am"].map((t, i) => (
                    <button 
                      key={i} 
                      onClick={() => setSeedBelief(t)}
                      className="text-sm px-6 py-3 rounded-full border border-white/[0.08] bg-white/[0.02] text-muted hover:text-accent hover:border-accent transition-all shadow-sm font-medium"
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              <button 
                onClick={() => handleComplete(true)}
                className="text-sm text-[#333333] hover:text-accent transition-colors"
              >
                Skip this for now &rarr;
              </button>
            </motion.div>
          )}

          {step === 5 && (
            <motion.div 
              key="step5"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="w-full max-w-3xl text-center space-y-12"
            >
              <div className="space-y-6">
                <span className="mono-label !text-accent !tracking-[0.2em] font-bold uppercase">Almost Ready</span>
                <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-primary">
                  One last thing.
                </h1>
                <p className="text-2xl editorial-italic text-muted font-medium max-w-xl mx-auto leading-relaxed">
                  You can import your ChatGPT or Gemini history to give Miryn a head start on knowing you.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="bg-card border border-white/[0.06] rounded-[32px] p-10 text-left space-y-8 group shadow-sm">
                  <div className="w-12 h-12 rounded-xl bg-[#10a37f]/10 border border-[#10a37f]/20 flex items-center justify-center font-bold text-[#10a37f] text-xl">C</div>
                  <div className="space-y-3">
                    <h3 className="text-2xl font-bold text-primary">Import from ChatGPT</h3>
                    <p className="text-base text-muted leading-relaxed font-medium">Upload your ChatGPT export file to seed Miryn&apos;s memory with what you&apos;ve already shared.</p>
                  </div>
                  <button className="w-full h-14 border border-white/[0.08] rounded-full text-base font-bold text-muted hover:bg-white/[0.03] transition-colors flex items-center justify-center gap-3">
                    <UploadCloud size={20} /> Upload export.zip
                  </button>
                </div>

                <div className="bg-card border border-white/[0.06] rounded-[32px] p-10 text-left space-y-8 group shadow-sm">
                  <div className="w-12 h-12 rounded-xl bg-[#4285f4]/10 border border-[#4285f4]/20 flex items-center justify-center font-bold text-[#4285f4] text-xl">G</div>
                  <div className="space-y-3">
                    <h3 className="text-2xl font-bold text-primary">Import from Gemini</h3>
                    <p className="text-base text-muted leading-relaxed font-medium">Upload your Google Takeout file to transfer your conversation history.</p>
                  </div>
                  <button className="w-full h-14 border border-white/[0.08] rounded-full text-base font-bold text-muted hover:bg-white/[0.03] transition-colors flex items-center justify-center gap-3">
                    <UploadCloud size={20} /> Upload takeout.zip
                  </button>
                </div>
              </div>

              <div className="space-y-8">
                <button 
                  onClick={handleNext}
                  className="text-sm text-[#4a4868] hover:text-accent transition-colors"
                >
                  Skip &mdash; I&apos;ll start fresh
                </button>

                <div className="space-y-4">
                <div className="space-y-6">
                  <div className="mono-label !text-muted uppercase tracking-widest font-bold">Here&apos;s what Miryn will know:</div>
                  <div className="flex flex-wrap justify-center gap-3">
                    {[name, `Preset: ${selectedPreset}`, `${goals.length} goals`, seedBelief ? "1 belief" : ""].filter(Boolean).map((p, i) => (
                      <div key={i} className="px-6 py-2 rounded-full bg-accent/10 border border-accent/20 text-accent text-[15px] font-bold shadow-sm">
                        {p}
                      </div>
                    ))}
                  </div>
                </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Bottom Nav */}
      <footer className="fixed bottom-0 left-0 w-full p-10 flex justify-between items-center border-t border-white/[0.06] bg-white/80 backdrop-blur-md z-50">
        <button 
          onClick={handleBack}
          disabled={step === 1 || isSubmitting}
          className={`flex items-center gap-3 text-base font-bold transition-colors ${step === 1 ? "opacity-0 pointer-events-none" : "text-muted hover:text-primary"}`}
        >
          <ChevronLeft size={22} /> Back
        </button>

        <div className="flex flex-col items-center">
           {status && <p className="text-sm text-red-600 mb-3 font-bold">{status}</p>}
           <button 
             onClick={handleNext}
             disabled={isSubmitting || (step === 1 && !name)}
              className="h-16 px-12 bg-accent text-[#09090e] rounded-full font-bold text-lg flex items-center gap-3 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 shadow-lg shadow-accent/20"
           >
             {isSubmitting ? <Loader2 size={24} className="animate-spin" /> : (step === 5 ? "Begin Calibration" : <>Continue <ArrowRight size={22} /></>)}
           </button>
        </div>

        <div className="w-[60px]" /> {/* Spacer */}
      </footer>
    </div>
  );
}

function Loader2({ size, className }: { size: number, className: string }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}

