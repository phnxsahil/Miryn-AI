"use client";

import { useEffect, useState } from "react";
import { GoogleLogin } from "@react-oauth/google";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.ensureAuthenticated().then((authenticated) => {
      if (authenticated) {
        router.replace("/chat");
      }
    });
  }, [router]);

  const handleGoogleSuccess = async (credentialResponse: any) => {
    if (!credentialResponse.credential) return;
    setError(null);
    setLoading(true);
    try {
      const res: any = await api.googleLogin(credentialResponse.credential);
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
      await api.signup(email, password);
      try {
        const res: any = await api.login(email, password);
        api.setSession(res);
        window.location.assign("/onboarding");
      } catch {
        setError("Account created. Please log in manually.");
        window.location.assign("/login?created=1");
      }
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Signup failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-void text-white flex items-center justify-center px-6">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4">
        <h1 className="text-3xl font-serif font-light">Create account</h1>
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <label className="block text-sm text-secondary" htmlFor="signup-email">
          Email address
        </label>
        <input
          id="signup-email"
          type="email"
          className="w-full rounded-md bg-white/5 border border-white/10 px-4 py-3"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          aria-label="Email address"
        />
        <label className="block text-sm text-secondary" htmlFor="signup-password">
          Password
        </label>
        <input
          id="signup-password"
          className="w-full rounded-md bg-white/5 border border-white/10 px-4 py-3"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          aria-label="Password"
        />
        <button className="w-full rounded-md bg-accent text-black py-3" disabled={loading}>
          {loading ? "Signing up..." : "Sign up"}
        </button>

        <div className="flex flex-col items-center pt-2">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={() => setError("Google sign-in failed")}
            theme="filled_black"
            shape="rectangular"
            prompt="select_account"
            width={320}
          />
        </div>
      </form>
    </div>
  );
}
