"use client";

import { useEffect, useState } from "react";
import { CredentialResponse, GoogleLogin } from "@react-oauth/google";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";
import { ArrowRight, Loader2, Eye, EyeOff } from "lucide-react";
import { motion } from "framer-motion";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
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
      await api.signup(email, password);
      try {
        const res = await api.login(email, password);
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
    <div className="min-h-screen bg-void flex flex-col md:flex-row overflow-hidden font-ui">
      {/* LEFT PANEL (55% width, full height) */}
      <div className="hidden md:flex md:w-[55%] h-screen bg-[#0f0f17] flex-col justify-center items-center p-20 relative border-r border-white/[0.05]">
        <div className="absolute top-10 left-10 text-3xl font-bold tracking-tighter text-accent">
          Miryn
        </div>
        
        <div className="relative z-10 max-w-xl">
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, ease: "easeOut" }}
            className="text-5xl text-dim editorial-italic leading-tight text-center"
          >
            "Every version of you — the one who doubts, the one who grows, the one who keeps showing up — deserves to be remembered."
          </motion.p>
        </div>

        {/* Subtle Purple Glow Orb */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-[500px] h-[500px] bg-accent/[0.04] rounded-full blur-[120px]" />
        </div>

        <div className="absolute bottom-12 left-12 flex gap-8">
          <span className="mono-label !text-dim !text-[12px] uppercase tracking-widest">🔒 End-to-end encrypted</span>
          <span className="mono-label !text-dim !text-[12px] uppercase tracking-widest">🗑 Delete anytime</span>
          <span className="mono-label !text-dim !text-[12px] uppercase tracking-widest">✨ Free during alpha</span>
        </div>
      </div>

      {/* RIGHT PANEL (45% width, full height) */}
      <div className="flex-1 h-screen bg-[#09090e] flex flex-col justify-center items-center p-6 md:p-24">
        <div className="w-full max-w-[400px] space-y-12">
          <div className="space-y-4">
            <h1 className="text-4xl md:text-5xl font-bold text-primary tracking-tighter">Create your matrix.</h1>
            <p className="text-lg text-muted">
              Already have one? <a href="/login" className="text-accent hover:text-accent/80 transition-colors underline decoration-accent/20">Sign in →</a>
            </p>
          </div>

          {/* Google Button */}
          <div className="pt-4">
            {googleClientId && (
              <div className="w-full flex justify-center">
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={() => setError("Google sign-in failed")}
                  theme="filled_black"
                  shape="pill"
                  text="signup_with"
                  width="400"
                />
              </div>
            )}
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-white/[0.06]"></div></div>
            <div className="relative flex justify-center text-[10px] tracking-[0.3em] uppercase"><span className="bg-[#09090e] px-6 text-dim">or</span></div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-4 rounded-2xl bg-[rgba(226,75,74,0.08)] border border-[rgba(226,75,74,0.15)] text-[#c17070] text-[11px] mono-label text-center uppercase tracking-widest"
              >
                {error}
              </motion.div>
            )}

            <div className="space-y-6">
              <div className="space-y-2">
                <label className="mono-label !text-[11px] uppercase tracking-widest text-dim ml-1">Your Email</label>
                <input
                  type="email"
                  className="w-full h-14 bg-white/[0.04] border border-white/[0.08] rounded-2xl px-6 text-primary placeholder-dim focus:outline-none focus:border-accent/40 transition-all"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="mono-label !text-[11px] uppercase tracking-widest text-dim ml-1">Create Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    className="w-full h-14 bg-white/[0.04] border border-white/[0.08] rounded-2xl px-6 pr-14 text-primary placeholder-dim focus:outline-none focus:border-accent/40 transition-all"
                    placeholder="Min. 8 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loading}
                    required
                  />
                  <button 
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-6 top-1/2 -translate-y-1/2 text-dim hover:text-accent transition-colors"
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                {password.length > 0 && (
                  <div className="flex items-center justify-between px-1 mt-4">
                    <div className="flex gap-1.5 flex-1 max-w-[200px]">
                      {[1, 2, 3, 4].map((i) => (
                        <div 
                          key={i} 
                          className={`h-1.5 flex-1 rounded-full transition-colors ${
                            i <= (password.length > 8 ? 3 : password.length > 4 ? 2 : 1) 
                              ? "bg-accent" 
                              : "bg-white/[0.06]"
                          }`} 
                        />
                      ))}
                    </div>
                    <span className="mono-label !text-[11px] uppercase tracking-widest text-dim">
                      {password.length > 8 ? "strong" : password.length > 4 ? "fair" : "weak"}
                    </span>
                  </div>
                )}
              </div>
            </div>

            <button
              type="submit"
              className="w-full h-16 bg-accent text-[#09090e] rounded-2xl font-bold text-sm hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50 shadow-lg shadow-accent/20 uppercase tracking-widest"
              disabled={loading}
            >
              {loading ? <Loader2 size={24} className="animate-spin" /> : <>Create account <ArrowRight size={20} /></>}
            </button>

            <p className="text-[12px] text-dim text-center leading-relaxed">
              By creating an account you agree to our <a href="#" className="underline decoration-white/10 hover:text-accent transition-colors">Terms of Service</a> and <a href="#" className="underline decoration-white/10 hover:text-accent transition-colors">Privacy Policy</a>.
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}

