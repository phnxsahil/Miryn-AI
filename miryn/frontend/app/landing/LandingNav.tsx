"use client";

import { useState } from "react";

const links = [
  ["About", "#about"],
  ["Features", "#features"],
  ["Insights", "#insights"],
  ["FAQ's", "#faq"],
  ["Contact", "#contact"],
] as const;

export default function LandingNav() {
  const [open, setOpen] = useState(false);

  return (
    <header className="landing-nav-wrap">
      <nav className="landing-nav">
        <a href="/" className="landing-brand" onClick={() => setOpen(false)}>
          <svg className="landing-brand__mark" viewBox="0 0 28 28" fill="none" aria-hidden="true">
            <path d="M3 16.5C6.1 7.8 10.7 7.8 13.2 14.2C15.9 21.2 20.6 20.8 25 10.8" stroke="#F3C7A7" strokeWidth="1.7" strokeLinecap="round" />
            <path d="M3 13.2C6.4 5.1 10.2 5.7 13.4 12.2C16.5 18.7 20.9 17.3 25 7.2" stroke="#B9E7D5" strokeWidth="1.7" strokeLinecap="round" />
            <path d="M3 19.7C6.4 11.5 10.7 12.3 13.4 18.1C16.1 23.8 20.9 23.6 25 14.1" stroke="#A7BDF1" strokeWidth="1.7" strokeLinecap="round" />
          </svg>
          <span>Miryn AI</span>
        </a>

        <div className="hidden items-center gap-7 md:flex">
          {links.map(([label, href]) => (
            <a key={href} href={href} className="flex min-h-11 items-center font-ui text-sm text-[#A3A3A3] transition-colors hover:text-[#FAFAFA]">
              {label}
            </a>
          ))}
        </div>

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
      </nav>

      {open && (
        <div className="mx-auto mt-2 max-w-6xl rounded-2xl border border-white/[0.08] bg-[#111]/95 p-2 shadow-2xl backdrop-blur-xl md:hidden">
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
  );
}
