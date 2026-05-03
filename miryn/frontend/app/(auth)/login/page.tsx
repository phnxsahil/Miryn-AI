"use client";

import { useEffect, useState } from "react";
import { CredentialResponse, GoogleLogin } from "@react-oauth/google";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";
import { Fingerprint, ArrowRight, Loader2, Zap } from "lucide-react";
import { motion } from "framer-motion";

const DEMO_PERSONAS = [
  {
    name: "Aditya Verma",
    role: "Founder · Deep Thinker",
    email: "persona.alpha@miryn.demo",
    password: "MirynDemo!2026",
    avatar: "AV",
    color: "text-accent",
    bg: "bg-accent/10",
    border: "border-accent/20",
    bio: "Tracks creative drift, open loops, and expansion into new ideas.",
  },
  {
    name: "Priya Sharma",
    role: "Analyst · Systems Mind",
    email: "persona.beta@miryn.demo",
    password: "MirynDemo!2026",
    avatar: "PS",
    color: "text-accent-beta",
    bg: "bg-accent-beta/10",
    border: "border-accent-beta/20",
    bio: "Focuses on precision, performance metrics, and retrieval systems.",
  },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState<string | null>(null);
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  useEffect(() => {
    api.ensureAuthenticated().then((authenticated) => {
      if (authenticated) router.replace("/chat");
    });
  }, [router]);

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
      setError(getErrorMessage(err, "Login failed"));
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (persona: (typeof DEMO_PERSONAS)[number]) => {
    setError(null);
    setDemoLoading(persona.name);
    try {
      await api.quickDemoLogin(persona.email, persona.password);
      window.location.assign("/chat");
    } catch {
      try {
        await api.seedDemoPersonas();
        await api.quickDemoLogin(persona.email, persona.password);
        window.location.assign("/chat");
      } catch (err2) {
        setError(getErrorMessage(err2, `Demo login failed for ${persona.name}`));
      }
    } finally {
      setDemoLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-void text-primary flex items-center justify-center px-6 relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-accent/5 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent/10 rounded-full blur-[150px]" />

      <div className="w-full max-w-lg relative z-10">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-accent/[0.08] border border-accent/15 mb-8">
            <Fingerprint className="text-accent w-10 h-10" />
          </div>
          <h1 className="text-5xl font-bold tracking-tighter mb-4 text-primary">Initialize Session</h1>
          <p className="text-xl text-muted editorial-italic">&ldquo;Recognition is the first step of persistence.&rdquo;</p>
        </div>

        <div className="mb-8">
          <div className="flex items-center gap-4 mb-5">
            <div className="h-[1px] flex-1 bg-white/[0.04]" />
            <span className="mono-label !text-[10px] !text-dim uppercase tracking-[0.3em] flex items-center gap-2">
              <Zap size={10} className="text-accent" /> Demo Access
            </span>
            <div className="h-[1px] flex-1 bg-white/[0.04]" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            {DEMO_PERSONAS.map((persona) => (
              <motion.button
                key={persona.name}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleDemoLogin(persona)}
                disabled={!!demoLoading || loading}
                className={`group relative p-5 rounded-[24px] bg-white/[0.03] border ${persona.border} hover:bg-white/[0.05] transition-all text-left overflow-hidden`}
              >
                <div className={`absolute top-0 right-0 w-20 h-20 ${persona.bg} blur-2xl opacity-0 group-hover:opacity-100 transition-opacity`} />
                <div className="flex items-start gap-3 relative z-10">
                  <div className={`w-10 h-10 rounded-full ${persona.bg} flex items-center justify-center shrink-0 text-sm font-bold ${persona.color}`}>
                    {demoLoading === persona.name ? <Loader2 size={16} className="animate-spin" /> : persona.avatar}
                  </div>
                  <div className="min-w-0">
                    <p className="text-[14px] font-bold text-primary truncate">{persona.name}</p>
                    <p className={`text-[10px] mono-label ${persona.color} uppercase tracking-wider`}>{persona.role}</p>
                  </div>
                </div>
                <p className="text-[11px] text-dim mt-3 leading-relaxed line-clamp-2 relative z-10">{persona.bio}</p>
                <div className={`mt-3 flex items-center gap-1.5 ${persona.color} relative z-10`}>
                  <Zap size={10} />
                  <span className="text-[10px] mono-label uppercase tracking-widest">Quick Access</span>
                </div>
              </motion.button>
            ))}
          </div>
        </div>

        <div className="glass-card p-10 rounded-[40px]">
          <form onSubmit={handleSubmit} className="space-y-8">
            {error && <div className="error-surface">{error}</div>}
            <div className="space-y-6">
              <div className="space-y-2">
                <label className="mono-label !text-[11px] uppercase tracking-widest text-dim ml-1" htmlFor="email">Identity (Email)</label>
                <input id="email" type="email" className="input-field h-14 rounded-2xl text-base" placeholder="name@nexus.com" value={email} onChange={(e) => setEmail(e.target.value)} disabled={loading} />
              </div>
              <div className="space-y-2">
                <label className="mono-label !text-[11px] uppercase tracking-widest text-dim ml-1" htmlFor="password">Passkey</label>
                <input id="password" type="password" className="input-field h-14 rounded-2xl text-base" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} disabled={loading} />
              </div>
            </div>
            <button type="submit" className="w-full h-16 bg-accent text-[#09090e] rounded-2xl flex items-center justify-center gap-3 hover:scale-[1.02] transition-all shadow-lg shadow-accent/20 disabled:opacity-50 font-bold" disabled={loading}>
              {loading ? <Loader2 size={20} className="animate-spin" /> : <><span className="uppercase tracking-widest text-sm">Access Matrix</span> <ArrowRight size={18} /></>}
            </button>
          </form>

          <div className="relative my-10">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-white/[0.05]" /></div>
            <div className="relative flex justify-center text-[10px] uppercase tracking-widest"><span className="bg-surface px-6 text-dim">Or recognize via</span></div>
          </div>

          <div className="flex flex-col items-center gap-6">
            {googleClientId && <GoogleLogin onSuccess={handleGoogleSuccess} onError={() => setError("Google sign-in failed")} theme="filled_black" shape="pill" width={360} />}
            <p className="text-sm text-muted">Use demo cards above for your project presentation flow.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

