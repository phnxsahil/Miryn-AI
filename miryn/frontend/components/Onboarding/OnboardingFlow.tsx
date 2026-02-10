"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";

const questions = [
  "What do you want Miryn to remember about you?",
  "What values matter most to you right now?",
  "How should Miryn support you when you're struggling?",
  "What topics do you want to revisit regularly?",
];

export default function OnboardingFlow() {
  const [answers, setAnswers] = useState<string[]>(Array(questions.length).fill(""));
  const [status, setStatus] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateAnswer = (index: number, value: string) => {
    setAnswers((prev) => {
      const next = [...prev];
      next[index] = value;
      return next;
    });
  };

  const handleSubmit = async () => {
    if (isSubmitting) return;
    api.loadToken();

    const responses = questions.map((q, i) => ({
      question: q,
      answer: answers[i] || "",
    }));

    try {
      setIsSubmitting(true);
      await api.completeOnboarding({
        responses,
        traits: {},
        values: {},
      });
      setStatus("Onboarding complete. You can start chatting.");
    } catch (e: unknown) {
      setStatus(getErrorMessage(e, "Failed to complete onboarding."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl font-serif font-light">Onboarding</h1>
      <p className="text-secondary mt-2">Help Miryn learn how to support you.</p>

      <div className="mt-6 space-y-6">
        {questions.map((q, i) => (
          <div key={q} className="space-y-2">
            <div className="text-sm text-white/80">{q}</div>
            <textarea
              className="w-full rounded-md bg-white/5 border border-white/10 px-4 py-3 min-h-[100px]"
              value={answers[i]}
              onChange={(e) => updateAnswer(i, e.target.value)}
            />
          </div>
        ))}
      </div>

      <button
        className="mt-6 rounded-md bg-accent text-black px-6 py-3 disabled:opacity-60"
        onClick={handleSubmit}
        disabled={isSubmitting}
        aria-busy={isSubmitting}
      >
        {isSubmitting ? "Submitting..." : "Complete onboarding"}
      </button>

      {status && <div className="mt-4 text-sm text-secondary">{status}</div>}
    </div>
  );
}
