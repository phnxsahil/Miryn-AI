"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await api.login(email, password);
      api.setToken(res.access_token);
      window.location.href = "/chat";
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Login failed"));
    } finally {
      setLoading(false);
    }
  };

  const demoEnabled = process.env.NEXT_PUBLIC_ENABLE_DEMO === "true";
  const handleAutoLogin = async () => {
    if (!demoEnabled) return;
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/demo-login", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.error || "Auto-login failed");
      }
      if (!data?.access_token) {
        throw new Error("Demo login did not return a token");
      }
      api.setToken(data.access_token);
      window.location.href = "/chat";
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Auto-login failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-void text-white flex items-center justify-center px-6">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4">
        <h1 className="text-3xl font-serif font-light">Welcome back</h1>
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <label className="block text-sm text-secondary" htmlFor="email">
          Email
        </label>
        <input
          id="email"
          type="email"
          className="w-full rounded-md bg-white/5 border border-white/10 px-4 py-3"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          aria-label="Email"
        />
        <label className="block text-sm text-secondary" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          className="w-full rounded-md bg-white/5 border border-white/10 px-4 py-3"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          aria-label="Password"
        />
        <button className="w-full rounded-md bg-accent text-black py-3" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
        {demoEnabled && (
          <button
            type="button"
            className="w-full rounded-md border border-white/10 py-3 text-sm hover:border-white/30 disabled:opacity-60"
            onClick={handleAutoLogin}
            disabled={loading}
          >
            Auto-login (demo)
          </button>
        )}
      </form>
    </div>
  );
}
