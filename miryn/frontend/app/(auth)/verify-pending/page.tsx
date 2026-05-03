"use client";

import { motion } from "framer-motion";
import { Mail, ArrowRight } from "lucide-react";

export default function VerifyPendingPage() {
  const userEmail = "user@example.com"; // In real app, get from context/URL

  return (
    <div className="min-h-screen bg-[#030303] flex flex-col items-center justify-center px-6 relative overflow-hidden font-ui">
      {/* Background Glow */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-[400px] h-[400px] bg-[#c8b8ff]/[0.05] rounded-full blur-[100px]" />
      </div>

      <div className="w-full max-w-[480px] text-center space-y-10 relative z-10">
        {/* Illustrative area */}
        <div className="flex justify-center items-center h-[120px] relative">
          <motion.div 
            initial={{ opacity: 0, rotate: -10 }}
            animate={{ opacity: 1, rotate: 0 }}
            transition={{ duration: 0.8 }}
            className="absolute w-24 h-16 bg-[#1a1a1a] border border-white/[0.06] rounded-lg -translate-x-12 translate-y-4"
          />
          <motion.div 
            initial={{ opacity: 0, rotate: 10 }}
            animate={{ opacity: 1, rotate: 5 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="absolute w-24 h-16 bg-[#1a1a1a] border border-white/[0.06] rounded-lg translate-x-8 -translate-y-2"
          />
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, delay: 0.4 }}
            className="relative w-28 h-20 bg-[#1a1a1a] border border-white/[0.1] rounded-xl flex items-center justify-center shadow-[0_0_30px_rgba(200,184,255,0.1)]"
          >
            <Mail className="text-accent w-8 h-8" />
          </motion.div>
        </div>

        <div className="space-y-4">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-5xl font-medium text-white tracking-tight"
          >
            Check your inbox.
          </motion.h1>
          
          <div className="space-y-1">
            <p className="text-lg text-[#888888]">We sent a verification link to</p>
            <p className="text-lg font-medium text-[#e0e0e0]">{userEmail}</p>
          </div>
        </div>

        <p className="text-[#666666] leading-relaxed text-sm max-w-[400px] mx-auto">
          Click the link in the email to activate your account and start using Miryn. It expires in 24 hours.
        </p>

        <div className="flex flex-col gap-6 pt-4">
          <div className="flex items-center justify-center gap-4">
            <button className="h-11 px-8 rounded-full border border-white/10 text-[#888888] text-sm font-medium hover:bg-white/5 transition-colors">
              Open Gmail →
            </button>
            <button className="h-11 px-8 rounded-full border border-white/10 text-[#888888] text-sm font-medium hover:bg-white/5 transition-colors">
              Open Outlook →
            </button>
          </div>

          <div className="pt-4 space-y-4">
            <p className="text-sm text-[#444444]">
              Didn't receive it? <button className="text-accent hover:underline ml-1">Resend verification email</button>
            </p>
            <p className="text-[13px] text-[#333333]">
              Wrong email? <a href="/signup" className="hover:text-white transition-colors">Sign up with a different address.</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
