"use client";

import { useEffect, useRef, useState } from "react";
import MirynLogo from "@/components/MirynLogo";
import { useTheme } from "@/components/ThemeProvider";
import { Sun, Moon } from "lucide-react";

const links = [
  ["About", "#about"],
  ["Features", "#features"],
  ["FAQ's", "#faq"],
  ["Contact", "#contact"],
  ["What's New", "/blog/changelog.html"],
] as const;

export default function LandingNav() {
  const { toggleTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const sentinel = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!sentinel.current || typeof IntersectionObserver === "undefined") return;
    // ponytail: a 24px sentinel replaces scroll-time layout reads and state scheduling.
    const observer = new IntersectionObserver(([entry]) => setScrolled(!entry.isIntersecting));
    observer.observe(sentinel.current);
    return () => observer.disconnect();
  }, []);

  return (
    <>
    <span ref={sentinel} aria-hidden="true" className="pointer-events-none absolute left-0 top-0 h-6 w-px" />
    <header className="landing-nav-wrap">
      <nav className={`landing-nav${scrolled ? " landing-nav--scrolled" : ""}`}>
        <a href="/" className="landing-brand" onClick={() => setOpen(false)}>
          <MirynLogo showText={false} />
          <span>Miryn</span>
        </a>

        <div className="hidden items-center gap-7 md:flex">
          {links.map(([label, href]) => (
            <a key={href} href={href} className="flex min-h-11 min-w-11 items-center justify-center px-1 font-ui text-sm text-[#A3A3A3] transition-colors hover:text-[#FAFAFA]">
              {label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-2">
        <button type="button" onClick={toggleTheme} aria-label="Toggle color theme" className="landing-theme-toggle flex h-11 w-11 items-center justify-center rounded-full border border-white/15 text-[#FAFAFA]">
          <Sun className="landing-theme-sun h-5 w-5" aria-hidden="true" />
          <Moon className="landing-theme-moon h-5 w-5" aria-hidden="true" />
        </button>
        <a href="/signup" className="landing-nav__cta hidden min-h-11 items-center rounded-full border border-white/20 px-5 font-editorial text-sm text-[#FAFAFA] transition-colors hover:border-white/60 md:flex">
          Get Started
        </a>

        <button
          type="button"
          aria-label={open ? "Close navigation" : "Open navigation"}
          aria-expanded={open}
          onClick={() => setOpen((value) => !value)}
          className="flex h-11 w-11 items-center justify-center rounded-full border border-white/15 text-[#FAFAFA] md:hidden"
        >
          <span className="sr-only">Menu</span>
          <span className="flex w-5 flex-col gap-1.5" aria-hidden="true">
            <span className={`h-px w-full bg-current transition-transform ${open ? "translate-y-1" : ""}`} />
            <span className={`h-px w-full bg-current transition-opacity ${open ? "opacity-0" : ""}`} />
            <span className={`h-px w-full bg-current transition-transform ${open ? "-translate-y-1" : ""}`} />
          </span>
        </button>
        </div>
      </nav>

      {open && (
        <div className="landing-mobile-menu mx-auto mt-2 max-w-6xl rounded-2xl border border-white/[0.08] bg-[#111]/95 p-2 shadow-2xl backdrop-blur-xl md:hidden">
          {links.map(([label, href]) => (
            <a key={href} href={href} onClick={() => setOpen(false)} className="flex min-h-11 items-center rounded-xl px-4 font-ui text-base text-[#A3A3A3] hover:bg-white/[0.05] hover:text-[#FAFAFA]">
              {label}
            </a>
          ))}
          <a href="/signup" onClick={() => setOpen(false)} className="mt-1 flex min-h-11 items-center rounded-xl px-4 font-editorial text-base text-[#FAFAFA] hover:bg-white/[0.05]">
            Get Started
          </a>
        </div>
      )}
    </header>
    </>
  );
}
