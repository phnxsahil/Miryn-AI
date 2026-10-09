"use client";

import { createElement, useEffect, useRef, type CSSProperties, type HTMLAttributes, type ReactNode } from "react";

const observed = new WeakSet<Element>();
let sharedObserver: IntersectionObserver | null = null;

function getObserver() {
  if (sharedObserver || typeof IntersectionObserver === "undefined") return sharedObserver;
  sharedObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-revealed");
      sharedObserver?.unobserve(entry.target);
    });
  }, { threshold: .15, rootMargin: "0px 0px -8%" });
  return sharedObserver;
}

type RevealProps = {
  children: ReactNode;
  as?: keyof JSX.IntrinsicElements;
  className?: string;
  delay?: number;
} & HTMLAttributes<HTMLElement>;

export default function Reveal({ children, as = "div", className = "", delay = 0, style, ...props }: RevealProps) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    document.documentElement.classList.add("js");
    const element = ref.current;
    const observer = getObserver();
    if (!element || !observer || observed.has(element) || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      element?.classList.add("is-revealed");
      return;
    }
    observed.add(element);
    observer.observe(element);
    return () => observer.unobserve(element);
  }, []);

  const revealStyle = { ...style, "--reveal-delay": `${delay}ms` } as CSSProperties;
  return createElement(as, { ...props, ref, className: `landing-reveal ${className}`, "data-reveal": "true", style: revealStyle }, children);
}
