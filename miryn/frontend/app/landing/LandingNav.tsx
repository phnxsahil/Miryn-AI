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
    <header className="sticky top-0 z-50 px-4 pt-3 sm:px-6 lg:px-8">
      <nav className="mx-auto flex h-[60px] max-w-6xl items-center justify-between rounded-2xl border border-white/[0.08] bg-[#0A0A0A]/80 px-4 shadow-2xl shadow-black/20 backdrop-blur-xl sm:px-5">
        <a href="/" className="font-editorial text-[20px] text-[#FAFAFA]" onClick={() => setOpen(false)}>
          Miryn AI
        </a>

        <div className="hidden items-center gap-7 md:flex">
          {links.map(([label, href]) => (
            <a key={href} href={href} className="flex min-h-11 items-center font-ui text-sm text-[#A3A3A3] transition-colors hover:text-[#FAFAFA]">
              {label}
            </a>
          ))}
        </div>

        <a href="/signup" className="hidden min-h-11 items-center rounded-full border border-white/20 px-5 font-editorial text-sm text-[#FAFAFA] transition-colors hover:border-white/60 md:flex">
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
