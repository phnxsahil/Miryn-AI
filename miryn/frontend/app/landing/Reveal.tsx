"use client";

import { createElement, useEffect, useRef, type CSSProperties, type HTMLAttributes, type ReactNode } from "react";

let sharedObserver: IntersectionObserver | null = null;

function getObserver() {
  if (sharedObserver || typeof IntersectionObserver === "undefined") return sharedObserver;
  sharedObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.target.hasAttribute("data-ambient")) {
        entry.target.classList.toggle("is-near", entry.isIntersecting);
        return;
      }
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-revealed");
      sharedObserver?.unobserve(entry.target);
    });
  }, { threshold: .15, rootMargin: "200px 0px" });
  return sharedObserver;
}

type RevealProps = {
  children: ReactNode;
  as?: keyof JSX.IntrinsicElements;
  className?: string;
  delay?: number;
  ambient?: boolean;
} & HTMLAttributes<HTMLElement>;

export default function Reveal({ children, as = "div", className = "", delay = 0, ambient = false, style, ...props }: RevealProps) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    document.documentElement.classList.add("js");
    const element = ref.current;
    const observer = getObserver();
    if (!element || !observer || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      element?.classList.add("is-revealed");
      element?.classList.add("is-near");
      return;
    }
    observer.observe(element);
    return () => observer.unobserve(element);
  }, [ambient]);

  const revealStyle = { ...style, "--reveal-delay": `${delay}ms` } as CSSProperties;
  return createElement(as, { ...props, ref, className: `${ambient ? "landing-ambient" : "landing-reveal"} ${className}`, "data-reveal": ambient ? undefined : "true", "data-ambient": ambient ? "true" : undefined, style: revealStyle }, children);
}
