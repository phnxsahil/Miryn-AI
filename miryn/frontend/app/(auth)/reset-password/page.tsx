"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";
import { Loader2, CheckCircle, ArrowLeft } from "lucide-react";
import AuthShell, { AuthError } from "@/components/Auth/AuthShell";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!token) {
      setError("Invalid or missing reset token.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await api.resetPassword(token, password);
      setSuccess(true);
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Reset failed. The link may have expired."));
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="text-center space-y-4">
        <AuthError message="This reset link is incomplete or invalid." />
        <Link href="/forgot-password" className="inline-flex min-h-11 items-center px-2 text-[13px] text-[color:var(--miryn-parchment)] hover:underline">
          Request a new reset link →
        </Link>
      </div>
    );
  }

  if (success) {
    return (
      <div className="space-y-4 text-center" role="status" aria-live="polite">
        <div className="mx-auto inline-flex h-12 w-12 items-center justify-center rounded-full border border-[color:var(--miryn-card-border)] bg-[color:var(--miryn-surface)] text-[color:var(--miryn-moss)]">
          <CheckCircle size={22} aria-hidden="true" />
        </div>
        <p className="text-sm text-[color:var(--miryn-parchment-muted)]">Your password has been updated. Sign in with the new one.</p>
        <div className="pt-3">
          <button
            onClick={() => router.push("/login")}
            className="w-full h-11 bg-[color:var(--miryn-parchment)] text-[color:var(--miryn-warm-black)] rounded-full font-semibold text-sm hover:opacity-90 transition-colors"
          >
            Log in with new password
          </button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <AuthError id="reset-password-error" message={error} />}
      <div>
        <label className="text-xs font-medium text-[color:var(--miryn-parchment)] mb-1.5 block" htmlFor="new-pass">
          New password
        </label>
        <input
          id="new-pass"
          type="password"
          className="miryn-input text-base sm:text-[15px]"
          aria-invalid={!!error && (password.length < 8 || password !== confirm)}
          aria-describedby={error && (password.length < 8 || password !== confirm) ? "reset-password-error" : undefined}
          placeholder="Min. 8 characters"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={loading}
          required
          minLength={8}
        />
      </div>
      <div>
        <label className="text-xs font-medium text-[color:var(--miryn-parchment)] mb-1.5 block" htmlFor="confirm-pass">
          Confirm password
        </label>
        <input
          id="confirm-pass"
          type="password"
          className="miryn-input text-base sm:text-[15px]"
          aria-invalid={!!error && password !== confirm}
          aria-describedby={error && password !== confirm ? "reset-password-error" : undefined}
          placeholder="Re-enter password"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          disabled={loading}
          required
          minLength={8}
        />
      </div>
      <button
        type="submit"
        className="flex min-h-12 w-full items-center justify-center gap-2 rounded-full bg-[color:var(--miryn-parchment)] text-sm font-semibold text-[color:var(--miryn-warm-black)] transition-opacity hover:opacity-90 disabled:opacity-60"
        disabled={loading}
        aria-busy={loading}
      >
        {loading ? <><Loader2 size={18} className="animate-spin" aria-hidden="true" /> Updating password</> : "Reset password"}
      </button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <AuthShell mode="centered" title="Set new password" subtitle="Choose a secure password for your account">
      <Suspense fallback={<div className="text-center text-sm text-[color:var(--miryn-parchment-muted)] py-4">Loading...</div>}>
        <ResetPasswordForm />
      </Suspense>

      <div className="text-center mt-6">
        <Link href="/login" className="inline-flex min-h-11 items-center gap-1.5 px-2 text-[13px] text-[color:var(--miryn-parchment-muted)] transition-colors hover:text-[color:var(--miryn-parchment)]">
          <ArrowLeft size={13} /> Back to log in
        </Link>
      </div>
    </AuthShell>
  );
}
