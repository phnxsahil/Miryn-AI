import Link from "next/link";
import { Mail } from "lucide-react";
import AuthShell from "@/components/Auth/AuthShell";
import { ConversationMarks, ThreadLine } from "@/components/visuals";

export default function VerifyPendingPage() {
  return (
    <AuthShell mode="centered" title="Check your inbox" subtitle="Email verification is being prepared for Miryn.">
      <div className="relative mx-auto mb-6 flex h-24 w-40 items-center justify-center" aria-hidden="true">
        <ConversationMarks variant="stub" className="absolute inset-0 h-full w-full opacity-70" />
        <ThreadLine variant="spine" className="absolute start-1/2 top-0 h-24 w-12 -translate-x-1/2 opacity-60" />
        <div className="relative z-10 flex h-14 w-16 items-center justify-center rounded-xl border border-[var(--miryn-card-border)] bg-[var(--miryn-card)] text-[var(--miryn-moss)]">
          <Mail size={24} strokeWidth={1.5} />
        </div>
      </div>

      <div className="space-y-4 text-center">
        <p className="text-sm leading-relaxed text-[var(--miryn-parchment-muted)]">
          Once verification is connected, a link will arrive here so you can confirm your address and continue.
        </p>
        <p className="text-xs leading-relaxed text-[var(--text-dim)]">
          This screen is a preview. No email has been sent from this page.
        </p>
        <Link
          href="/login"
          className="mt-3 inline-flex min-h-12 w-full items-center justify-center rounded-full bg-[var(--miryn-parchment)] px-6 text-sm font-semibold text-[var(--miryn-warm-black)] transition-opacity hover:opacity-90"
        >
          Return to sign in
        </Link>
      </div>
    </AuthShell>
  );
}
