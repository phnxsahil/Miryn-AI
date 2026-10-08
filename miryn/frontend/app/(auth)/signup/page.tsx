"use client";

import { useEffect, useState } from "react";
import { CredentialResponse, GoogleLogin } from "@react-oauth/google";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";
import { Loader2, Eye, EyeOff } from "lucide-react";
import AuthShell, { AuthError } from "@/components/Auth/AuthShell";
import GoogleAuthProvider from "@/components/GoogleAuthProvider";

type FieldErrors = Partial<Record<"fullName" | "email" | "password" | "confirm" | "terms", string>>;

/** Focus order for the first invalid control after a failed submit. */
const FIELD_ORDER: Array<keyof FieldErrors> = ["fullName", "email", "password", "confirm", "terms"];

const FIELD_IDS: Record<keyof FieldErrors, string> = {
  fullName: "full-name",
  email: "email",
  password: "password",
  confirm: "confirm-password",
  terms: "accept-terms",
};

export default function SignupPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [loading, setLoading] = useState(false);
  const [googleEnabled, setGoogleEnabled] = useState<boolean | null>(null);
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  useEffect(() => {
    api.ensureAuthenticated()
      .then((authenticated) => {
        if (authenticated) {
          router.replace("/chat");
        }
      })
      .catch((err: unknown) => {
        console.error("Failed to verify existing session on signup page", err);
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

  const validate = (): FieldErrors => {
    const next: FieldErrors = {};
    if (fullName.trim().length < 2) {
      next.fullName = "Enter the name you would like Miryn to use.";
    }
    if (!email.trim()) {
      next.email = "Enter your email address.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      next.email = "Enter a valid email address.";
    }
    if (password.length < 8) {
      next.password = "Use at least 8 characters.";
    }
    if (confirm !== password) {
      next.confirm = "Passwords do not match.";
    }
    if (!acceptedTerms) {
      next.terms = "Please accept the Terms and Privacy Policy to continue.";
    }
    return next;
  };

  const clearFieldError = (field: keyof FieldErrors) => {
    setFieldErrors((prev) => {
      if (!prev[field]) return prev;
      const next = { ...prev };
      delete next[field];
      return next;
    });
  };

  const describedBy = (field: keyof FieldErrors, ...extra: string[]) =>
    [...(fieldErrors[field] ? [`${FIELD_IDS[field]}-error`] : []), ...extra].join(" ") || undefined;

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

    const nextErrors = validate();
    setFieldErrors(nextErrors);

    const firstInvalid = FIELD_ORDER.find((field) => nextErrors[field]);
    if (firstInvalid) {
      document.getElementById(FIELD_IDS[firstInvalid])?.focus();
      return;
    }

    setLoading(true);
    try {
      await api.signup(email, password, fullName);
      try {
        const res = await api.login(email, password);
        api.setSession(res);
        window.location.assign("/onboarding");
      } catch {
        window.location.assign("/login?created=1");
      }
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Signup failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <GoogleAuthProvider>
      <AuthShell title="Create your account" subtitle="Start with one conversation. Continue whenever you’re ready.">
      {error && <AuthError message={error} />}

      {showGoogle && (
        <div className="mb-5 flex justify-center w-full">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={() => setError("Google sign-in failed")}
            theme="filled_black"
            shape="pill"
            text="signup_with"
          />
        </div>
      )}

      {showGoogle && (
        <div className="relative my-6 flex items-center justify-center">
          <div className="w-full miryn-rule" />
          <span className="absolute bg-[var(--miryn-warm-black)] px-3 text-[11px] uppercase tracking-wider text-[var(--miryn-parchment-muted)]">OR</span>
        </div>
      )}

      {/* Own the validation so the messages, focus move, and aria wiring match. */}
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div>
          <label className="text-[13px] text-[var(--miryn-parchment-muted)] mb-2 block pl-1" htmlFor="full-name">
            Full name
          </label>
          <input
            id="full-name"
            name="name"
            type="text"
            className="miryn-input text-base sm:text-[15px]"
            placeholder="Aditya Verma"
            autoComplete="name"
            value={fullName}
            onChange={(e) => {
              setFullName(e.target.value);
              clearFieldError("fullName");
            }}
            aria-invalid={fieldErrors.fullName ? true : undefined}
            aria-describedby={describedBy("fullName")}
            disabled={loading}
            required
          />
          {fieldErrors.fullName && (
            <p id="full-name-error" className="mt-1.5 pl-1 text-[12px] text-[var(--error-text)]">
              {fieldErrors.fullName}
            </p>
          )}
        </div>

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
            onChange={(e) => {
              setEmail(e.target.value);
              clearFieldError("email");
            }}
            aria-invalid={fieldErrors.email ? true : undefined}
            aria-describedby={describedBy("email")}
            disabled={loading}
            required
          />
          {fieldErrors.email && (
            <p id="email-error" className="mt-1.5 pl-1 text-[12px] text-[var(--error-text)]">
              {fieldErrors.email}
            </p>
          )}
        </div>

        <div>
          <label className="text-[13px] text-[var(--miryn-parchment-muted)] mb-2 block pl-1" htmlFor="password">
            Password
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              className="miryn-input text-base pe-12 sm:text-[15px]"
              placeholder="Min. 8 characters"
              autoComplete="new-password"
              minLength={8}
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                clearFieldError("password");
                clearFieldError("confirm");
              }}
              aria-invalid={fieldErrors.password ? true : undefined}
              aria-describedby={describedBy("password", "password-hint")}
              disabled={loading}
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              aria-pressed={showPassword}
              className="absolute end-1 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-lg text-[var(--miryn-parchment-muted)] transition-colors hover:text-[var(--miryn-parchment)]"
            >
              {showPassword ? <EyeOff size={16} aria-hidden="true" /> : <Eye size={16} aria-hidden="true" />}
            </button>
          </div>
          {fieldErrors.password ? (
            <p id="password-error" className="mt-1.5 pl-1 text-[12px] text-[var(--error-text)]">
              {fieldErrors.password}
            </p>
          ) : (
            <p id="password-hint" className="mt-1.5 pl-1 text-[12px] text-[var(--text-dim)]">
              At least 8 characters.
            </p>
          )}
          {password.length > 0 && (
            <div className="flex items-center justify-between px-1 mt-2">
              <div className="flex gap-1 flex-1 max-w-[140px]">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className="h-1 flex-1 rounded-full transition-colors"
                    style={{
                      backgroundColor: i <= (password.length > 8 ? 3 : password.length > 4 ? 2 : 1)
                        ? "var(--miryn-moss)"
                        : "var(--miryn-card-border)",
                    }}
                  />
                ))}
              </div>
              <span className="text-[10px] uppercase tracking-wider text-[var(--miryn-parchment-muted)]">
                {password.length > 8 ? "strong" : password.length > 4 ? "fair" : "weak"}
              </span>
            </div>
          )}
        </div>

        <div>
          <label className="text-[13px] text-[var(--miryn-parchment-muted)] mb-2 block pl-1" htmlFor="confirm-password">
            Confirm password
          </label>
          <input
            id="confirm-password"
            type={showPassword ? "text" : "password"}
            className="miryn-input text-base sm:text-[15px]"
            placeholder="Re-enter your password"
            autoComplete="new-password"
            minLength={8}
            value={confirm}
            onChange={(e) => {
              setConfirm(e.target.value);
              clearFieldError("confirm");
            }}
            aria-invalid={fieldErrors.confirm ? true : undefined}
            aria-describedby={describedBy("confirm")}
            disabled={loading}
            required
          />
          {fieldErrors.confirm && (
            <p id="confirm-password-error" className="mt-1.5 pl-1 text-[12px] text-[var(--error-text)]">
              {fieldErrors.confirm}
            </p>
          )}
        </div>

        <div className="pt-1">
          <div className="flex items-start gap-3">
            <input
              id="accept-terms"
              type="checkbox"
              className="mt-0.5 h-5 w-5 shrink-0 accent-[var(--miryn-moss)]"
              checked={acceptedTerms}
              onChange={(e) => {
                setAcceptedTerms(e.target.checked);
                clearFieldError("terms");
              }}
              aria-invalid={fieldErrors.terms ? true : undefined}
              aria-describedby={describedBy("terms")}
              disabled={loading}
              required
            />
            <label htmlFor="accept-terms" className="text-[13px] leading-relaxed text-[var(--miryn-parchment-muted)]">
              I agree to the{" "}
              <Link href="/terms" className="text-[var(--miryn-moss)] underline underline-offset-4 hover:text-[var(--miryn-parchment)]">
                Terms
              </Link>{" "}
              and{" "}
              <Link href="/privacy" className="text-[var(--miryn-moss)] underline underline-offset-4 hover:text-[var(--miryn-parchment)]">
                Privacy Policy
              </Link>
              .
            </label>
          </div>
          {fieldErrors.terms && (
            <p id="accept-terms-error" className="mt-1.5 pl-1 text-[12px] text-[var(--error-text)]">
              {fieldErrors.terms}
            </p>
          )}
        </div>

        <button
          type="submit"
          className="w-full h-[50px] bg-[#fee435] text-[#0a0a0a] rounded-full flex items-center justify-center gap-2 font-semibold text-[15px] hover:bg-[#ffe74d] active:scale-[0.98] transition-all mt-4 disabled:opacity-50 shadow-md shadow-[#fee435]/10"
          disabled={loading}
          aria-busy={loading}
        >
          {loading ? <><Loader2 size={18} className="animate-spin" aria-hidden="true" /> Creating account</> : "Create account"}
        </button>
      </form>

      <p className="text-center md:text-left text-[13px] text-[var(--miryn-parchment-muted)] mt-8 pl-1">
        Already have an account?{" "}
        <Link href="/login" className="text-[var(--miryn-moss)] font-medium hover:underline">
          Log in
        </Link>
      </p>
      </AuthShell>
    </GoogleAuthProvider>
  );
}
