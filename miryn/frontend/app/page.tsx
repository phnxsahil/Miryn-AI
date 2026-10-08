"use client";

import React from "react";

export default function LandingPage() {
  return (
    <main className="fixed inset-0 w-screen h-[100dvh] overflow-hidden bg-[color:var(--theme-bg)]">
      <iframe
        src="/landing/index.html"
        title="Miryn AI — Persistent Memory & Evolving AI Companion"
        className="w-full h-full border-0 block"
        style={{ width: "100%", height: "100%", border: "none" }}
      />
    </main>
  );
}
