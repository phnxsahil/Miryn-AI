"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";
import { Loader2, CheckCircle, ArrowLeft } from "lucide-react";
import AuthShell, { AuthError } from "@/components/Auth/AuthShell";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.forgotPassword(email);
      setSent(true);
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Failed to send reset email"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell mode="centered" title={sent ? "Check your inbox" : "Reset your password"} subtitle={sent ? "If there’s an account for that email, a reset link is on its way." : "Enter your account email and we’ll send a secure reset link."}>
      {sent ? (
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-[color:var(--miryn-surface)] border border-[color:var(--miryn-card-border)] text-[color:var(--miryn-moss)] mx-auto">
            <CheckCircle size={22} />
          </div>
          <p className="text-sm leading-relaxed text-[color:var(--miryn-parchment-muted)]" role="status" aria-live="polite">
            If an account exists for <span className="font-medium text-[color:var(--miryn-parchment)]">{email}</span>, a password reset link is on its way.
          </p>
          <div className="pt-3">
            <Link
              href="/login"
              className="w-full h-11 bg-[color:var(--miryn-parchment)] text-[color:var(--miryn-warm-black)] rounded-full inline-flex items-center justify-center font-semibold text-sm hover:opacity-90 transition-colors"
            >
              Return to log in
            </Link>
          </div>
        </div>
      ) : (
        <>
          {error && <AuthError message={error} />}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-[color:var(--miryn-parchment)] mb-1.5 block" htmlFor="email">
                Email address
              </label>
              <input
                id="email"
                type="email"
                className="miryn-input text-base sm:text-[15px]"
                placeholder="name@example.com"
                autoComplete="email"
                inputMode="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            <button
              type="submit"
              className="flex min-h-12 w-full items-center justify-center gap-2 rounded-full bg-[color:var(--miryn-parchment)] text-sm font-semibold text-[color:var(--miryn-warm-black)] transition-opacity hover:opacity-90 disabled:opacity-60"
              disabled={loading}
              aria-busy={loading}
            >
              {loading ? <><Loader2 size={18} className="animate-spin" aria-hidden="true" /> Sending link</> : "Send reset link"}
            </button>
          </form>

          <div className="text-center mt-6">
            <Link href="/login" className="inline-flex min-h-11 items-center gap-1.5 px-2 text-[13px] text-[color:var(--miryn-parchment-muted)] transition-colors hover:text-[color:var(--miryn-parchment)]">
              <ArrowLeft size={13} /> Back to log in
            </Link>
          </div>
        </>
      )}
    </AuthShell>
  );
}
