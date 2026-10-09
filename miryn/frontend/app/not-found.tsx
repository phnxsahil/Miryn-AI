import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-[color:var(--theme-bg)] px-6 text-center font-ui text-[color:var(--theme-text)]">
      <p className="text-sm text-[color:var(--theme-muted)]">404</p>
      <h1 className="mt-3 font-editorial text-4xl tracking-[-0.03em] md:text-5xl">This page wandered off.</h1>
      <p className="mt-4 max-w-sm text-base leading-7 text-[color:var(--theme-muted)]">The link may be old or mistyped. Head back and pick up where you left off.</p>
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Link href="/" className="inline-flex min-h-12 items-center rounded-full bg-[#fafafa] px-6 font-editorial text-base text-[#0a0a0a] transition-transform hover:-translate-y-0.5">Back home</Link>
        <Link href="/chat" className="inline-flex min-h-12 items-center rounded-full border border-white/15 px-6 font-editorial text-base transition-colors hover:border-white/50">Open chat</Link>
      </div>
    </main>
  );
}
