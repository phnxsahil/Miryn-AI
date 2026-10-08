"use client";

import { useEffect, useState } from "react";
import { CredentialResponse, GoogleLogin } from "@react-oauth/google";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";
import { Loader2, Zap } from "lucide-react";
import AuthShell, { AuthError } from "@/components/Auth/AuthShell";
import GoogleAuthProvider from "@/components/GoogleAuthProvider";

// The single demo account. Provisioned server-side by
// miryn/backend/scripts/seed_demo_account.py — there is no seeding endpoint.
const DEMO_ACCOUNT = {
  name: "Aditya (Demo)",
  role: "Interactive Demo",
  email: "persona.alpha@miryn.demo",
  password: "MirynDemo!2026",
};

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState<string | null>(null);
  const [googleEnabled, setGoogleEnabled] = useState<boolean | null>(null);
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  useEffect(() => {
    api.ensureAuthenticated().then((authenticated) => {
      if (authenticated) router.replace("/chat");
    });
  }, [router]);

  // The public client id only says a button can be drawn; the server also has to
  // hold the matching id to verify the token. Only an explicit "disabled" hides
  // Google, so a slow or unreachable config never makes the button disappear.
  useEffect(() => {
    let active = true;
    api
      .getAuthConfig()
      .then((config) => {
        if (active) setGoogleEnabled(config?.providers?.google === true);
      })
      .catch(() => {
        // Leave it unknown: the button stays exactly as it was.
      });
    return () => {
      active = false;
    };
  }, []);

  const showGoogle = Boolean(googleClientId) && googleEnabled !== false;

  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) return;
    setError(null);
    setLoading(true);
    try {
      const res = await api.googleLogin(credentialResponse.credential);
      api.setSession(res);
      window.location.assign(res.is_new ? "/onboarding" : "/chat");
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Google sign-in failed"));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.login(email, password);
      api.setSession(res);
      window.location.assign("/chat");
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Login failed. Check your credentials."));
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError(null);
    setDemoLoading(DEMO_ACCOUNT.name);
    try {
      // A plain sign-in. The old seed-then-retry fallback called
      // /analytics/demo/seed, which no longer exists (404) and could never help.
      await api.quickDemoLogin(DEMO_ACCOUNT.email, DEMO_ACCOUNT.password);
      window.location.assign("/chat");
    } catch (err) {
      setError(getErrorMessage(err, "Demo login failed"));
    } finally {
      setDemoLoading(null);
    }
  };

  return (
    <GoogleAuthProvider>
      <AuthShell title="Welcome back" subtitle="Sign in to continue the conversation.">
      {error && <AuthError message={error} />}

      {showGoogle && (
        <div className="mb-5 flex justify-center w-full">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={() => setError("Google sign-in failed")}
            theme="filled_black"
            shape="pill"
          />
        </div>
      )}

      {showGoogle && (
        <div className="relative my-6 flex items-center justify-center">
          <div className="w-full miryn-rule" />
          <span className="absolute bg-[var(--miryn-warm-black)] px-3 text-[11px] uppercase tracking-wider text-[var(--miryn-parchment-muted)]">OR</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-[13px] text-[var(--miryn-parchment-muted)] mb-2 block pl-1" htmlFor="email">
            Email
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

        <div>
          <div className="flex justify-between items-center mb-2 pl-1 pr-2">
            <label className="text-[13px] text-[var(--miryn-parchment-muted)]" htmlFor="password">
              Password
            </label>
            <Link href="/forgot-password" className="text-[12px] text-[var(--miryn-parchment-muted)] hover:text-[var(--miryn-parchment)] transition-colors">
              Forgot password?
            </Link>
          </div>
          <input
            id="password"
            type="password"
            className="miryn-input text-base sm:text-[15px]"
            placeholder="Enter your password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
            required
          />
        </div>

        <button
          type="submit"
          className="w-full h-[50px] bg-[#fee435] text-[#0a0a0a] rounded-full flex items-center justify-center font-semibold text-[15px] hover:bg-[#ffe74d] active:scale-[0.98] transition-all mt-4 disabled:opacity-50 shadow-md shadow-[#fee435]/10"
          disabled={loading}
          aria-busy={loading}
        >
          {loading ? <><Loader2 size={18} className="animate-spin mr-2" aria-hidden="true" /> Signing in</> : "Sign in"}
        </button>
      </form>

      <p className="text-center md:text-left text-[13px] text-[var(--miryn-parchment-muted)] mt-8 pl-1">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="text-[var(--miryn-moss)] font-medium hover:underline">
          Sign up
        </Link>
      </p>

      <details className="mt-7 border-t border-[var(--miryn-card-border)] pt-4">
        <summary className="flex min-h-11 cursor-pointer list-none items-center gap-2 text-sm text-[var(--miryn-parchment-muted)] marker:hidden focus-visible:outline-offset-4">
          <Zap size={14} aria-hidden="true" style={{ color: "var(--miryn-moss)" }} />
          Explore a demo account
        </summary>
        <div className="mt-3">
          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={!!demoLoading || loading}
            className="flex min-h-11 w-full flex-col justify-center rounded-xl border border-[var(--miryn-card-border)] bg-[var(--miryn-surface)] p-3 text-start transition-colors hover:bg-[var(--miryn-card)] disabled:opacity-60"
          >
            <span className="truncate text-[13px] font-medium text-[var(--miryn-parchment)]">
              {demoLoading ? <><Loader2 size={13} className="me-1 inline animate-spin" aria-hidden="true" /> Opening demo</> : DEMO_ACCOUNT.name}
            </span>
            <span className="mt-0.5 text-[11px] text-[var(--miryn-parchment-muted)]">{DEMO_ACCOUNT.role}</span>
          </button>
        </div>
      </details>
      </AuthShell>
    </GoogleAuthProvider>
  );
}
