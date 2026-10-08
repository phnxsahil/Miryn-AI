"use client";

import React from "react";
import Image from "next/image";

interface MirynLogoProps {
  size?: number;
  showText?: boolean;
  className?: string;
  glow?: boolean;
}

export default function MirynLogo({
  size = 32,
  showText = true,
  className = "",
  glow = false,
}: MirynLogoProps) {
  return (
    <div className={`inline-flex items-center gap-3 select-none ${className}`}>
      <div
        className="relative flex items-center justify-center flex-shrink-0"
        style={{ width: size, height: size }}
      >
        {glow && (
          <div
            className="absolute inset-0 rounded-full blur-md opacity-40 -z-10"
            style={{
              background: "radial-gradient(circle, color-mix(in srgb, var(--theme-accent) 42%, transparent) 0%, var(--theme-accent) 60%, transparent 100%)",
            }}
          />
        )}
        <Image
          src="/miryn-logo.png"
          alt="Miryn AI Logo"
          width={size}
          height={size}
          priority
          className="rounded-full object-cover transition-transform duration-300 hover:scale-105"
        />
      </div>

      {showText && (
        <span
          className="font-medium tracking-tight text-[color:var(--theme-text)] flex items-center gap-1.5"
          style={{
            fontSize: Math.max(16, Math.round(size * 0.6)),
            letterSpacing: "-0.02em",
          }}
        >
          Miryn
          <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-[color:var(--theme-overlay)] text-[color:var(--theme-accent)] font-semibold tracking-wider">
            AI
          </span>
        </span>
      )}
    </div>
  );
}
