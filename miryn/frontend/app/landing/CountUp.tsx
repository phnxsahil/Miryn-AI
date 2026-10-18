"use client";

import { useEffect, useRef, useState } from "react";

type CountUpProps = { value: string };

export default function CountUp({ value }: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const [display, setDisplay] = useState(value);

  useEffect(() => {
    const element = ref.current;
    const match = value.match(/^(\d+)(.*)$/);
    if (!element || !match || typeof IntersectionObserver === "undefined") return;

    const target = Number(match[1]);
    const suffix = match[2];
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const render = (amount: number) => setDisplay(`${Math.round(amount)}${suffix}`);
    if (!reduced) render(0);
    let frame = 0;
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      observer.disconnect();
      if (reduced) {
        render(target);
        return;
      }
      const started = performance.now();
      const tick = (now: number) => {
        const progress = Math.min(1, (now - started) / 850);
        render(target * (1 - Math.pow(1 - progress, 3)));
        if (progress < 1) frame = window.requestAnimationFrame(tick);
      };
      frame = window.requestAnimationFrame(tick);
    }, { threshold: .35 });

    observer.observe(element);
    return () => {
      observer.disconnect();
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, [value]);

  return <span ref={ref}>{display}</span>;
}
