"use client";

import { useEffect, useRef, type CSSProperties } from "react";
import Reveal from "./Reveal";

const copy = "Traditional AI tools reset every time you close the tab. Miryn is different. We built Miryn around an evolving identity engine that learns who you are over time—tracking your core beliefs, behavior patterns, emotions, and unresolved goals so every interaction feels deeply personal and continuous.";

export default function AboutReveal() {
  const stageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;

    const words = Array.from(stage.querySelectorAll<HTMLElement>(".about-word"));
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const setProgress = (progress: number) => {
      words.forEach((word, index) => {
        const wordProgress = Math.max(0, Math.min(1, progress * words.length - index));
        word.style.opacity = String(.25 + (wordProgress * .75));
      });
    };

    if (reduced) {
      setProgress(1);
      return;
    }

    let frame = 0;
    const update = () => {
      frame = 0;
      const range = Math.max(stage.offsetHeight - window.innerHeight, 1);
      const progress = Math.max(0, Math.min(1, -stage.getBoundingClientRect().top / range));
      setProgress(progress);
    };
    const schedule = () => {
      if (!frame) frame = window.requestAnimationFrame(update);
    };

    update();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <div ref={stageRef} className="about-scroll-stage">
      <div className="about-scroll-sticky">
        <Reveal className="section-heading section-heading--center">
          <p className="section-eyebrow section-eyebrow--about"><i />ABOUT MIRYN</p>
        </Reveal>
        <Reveal as="p" className="about-reveal mt-8 font-editorial text-3xl leading-[1.25] tracking-[-0.03em] text-[#FAFAFA] sm:text-4xl">
          {copy.split(" ").map((word, index) => <span className="about-word" style={{ "--word-index": index, "--word-progress": 0 } as CSSProperties} key={`${word}-${index}`}>{word} </span>)}
        </Reveal>
      </div>
    </div>
  );
}
